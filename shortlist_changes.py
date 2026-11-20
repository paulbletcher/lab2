"""Save and compare the ranked licensing shortlists from run_analysis.py."""

import argparse
import csv
import shutil
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path


WINDOWS = ("all_years", "2000_onward")
CATEGORIES = {
    "franchises": ("collection_id", "collection_name", "median_ratio"),
    "standalones": ("tmdb_id", "title", "revenue_to_budget"),
}


@dataclass(frozen=True)
class Entry:
    rank: int
    title: str
    ratio: Decimal


def load_shortlists(folder):
    shortlists = {}
    for window in WINDOWS:
        for category, (id_field, title_field, ratio_field) in CATEGORIES.items():
            path = folder / f"{category}_{window}.csv"
            entries = {}
            with path.open(encoding="utf-8-sig", newline="") as source:
                reader = csv.DictReader(source)
                if not {id_field, title_field, ratio_field}.issubset(reader.fieldnames or []):
                    raise ValueError(f"{path} is missing expected shortlist columns.")
                # run_analysis.py writes shortlist rows in rank order.
                for rank, row in enumerate(reader, 1):
                    item_id = (row[id_field] or "").strip()
                    title = (row[title_field] or "").strip()
                    if not item_id or item_id in entries or not title:
                        raise ValueError(f"{path}, row {rank + 1}: invalid ID or title.")
                    try:
                        ratio = Decimal(row[ratio_field] or "")
                    except InvalidOperation:
                        raise ValueError(f"{path}, row {rank + 1}: invalid ratio.") from None
                    if not ratio.is_finite() or ratio <= 0:
                        raise ValueError(f"{path}, row {rank + 1}: invalid ratio.")
                    entries[item_id] = Entry(rank, title, ratio)
            shortlists[window, category] = entries
    return shortlists


def snapshot(source, destination):
    shortlists = load_shortlists(source)
    destination.mkdir(parents=True, exist_ok=False)
    for window, category in shortlists:
        filename = f"{category}_{window}.csv"
        shutil.copyfile(source / filename, destination / filename)


def markdown_cell(value):
    return str(value).replace("|", r"\|").replace("\n", " ").replace("\r", " ")


def change_rows(previous, current):
    for item_id, new in current.items():
        old = previous.get(item_id)
        if old is None:
            yield new.title, "Entered", "—", new.rank, "—", f"{new.ratio:.2f}×"
        elif old.rank != new.rank or round(old.ratio, 2) != round(new.ratio, 2):
            if old.rank != new.rank:
                change = "Moved up" if new.rank < old.rank else "Moved down"
            else:
                change = "Ratio changed"
            yield new.title, change, old.rank, new.rank, f"{old.ratio:.2f}×", f"{new.ratio:.2f}×"

    for item_id, old in previous.items():
        if item_id not in current:
            yield old.title, "Dropped out", old.rank, "—", f"{old.ratio:.2f}×", "—"


def make_report(previous_folder, current_folder):
    previous = load_shortlists(previous_folder)
    current = load_shortlists(current_folder)
    report = [
        "# Shortlist changes",
        "",
        f"Previous run **{markdown_cell(previous_folder.name)}**",
        "",
        f"Current run **{markdown_cell(current_folder.name)}**",
        "",
        "The ratio compares reported ticket sales with production budget. "
        "For franchises it is the median of the observed film ratios. "
        "The snapshots show ranking and ratio changes. They do not establish "
        "why a title entered or left. Ratio changes are reported to two decimal places.",
    ]
    for (window, category), entries in current.items():
        changes = list(change_rows(previous[window, category], entries))
        report.extend(["", f"## {category.title()} · {window.replace('_', ' ').capitalize()}", ""])
        if not changes:
            report.append("No changes in shortlist membership, rank, or displayed ratio.")
            continue

        report.extend([
            "| Title or collection | Change | Prior rank | Current rank | Prior ratio | Current ratio |",
            "|---|---|---:|---:|---:|---:|",
        ])
        for row in changes:
            report.append("| " + " | ".join(map(markdown_cell, row)) + " |")

    return "\n".join(report) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    save = commands.add_parser("snapshot", help="save the four ranked CSVs to a new folder")
    save.add_argument("destination", type=Path)
    save.add_argument("--source", type=Path, default=Path("data/analysis"))

    compare = commands.add_parser("compare", help="compare equivalent shortlists from two runs")
    compare.add_argument("previous", type=Path)
    compare.add_argument("current", type=Path)
    compare.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    try:
        if args.command == "snapshot":
            snapshot(args.source, args.destination)
            print(f"Saved four shortlist CSVs to {args.destination}")
        else:
            report = make_report(args.previous, args.current)
            with args.output.open("x", encoding="utf-8") as destination:
                destination.write(report)
            print(f"Saved {args.output}")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
