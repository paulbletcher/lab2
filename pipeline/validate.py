from pathlib import Path

import pandas as pd


def main():
    project_root = Path(__file__).resolve().parents[1]
    candidates = pd.read_csv(
        project_root / "data/input/id_list.csv",
        dtype=str,
        keep_default_na=False,
        skip_blank_lines=False,
    )

    # Inspect input IDs.
    print("Columns:", candidates.columns.tolist())
    print("Input rows:", len(candidates))

    raw_ids = candidates["tmdb_id"]
    clean_ids = raw_ids.str.strip()

    is_blank = clean_ids.eq("")
    is_positive_integer = clean_ids.str.fullmatch(r"[0-9]+") & ~clean_ids.str.fullmatch(r"0+")
    is_invalid = ~is_blank & ~is_positive_integer

    print("Blank IDs:", is_blank.sum())
    print("Invalid IDs:", raw_ids[is_invalid].tolist())

    # Check for duplicates.
    valid_ids = clean_ids[is_positive_integer].str.lstrip("0")
    is_duplicate = valid_ids.duplicated(keep="first")

    duplicate_ids = valid_ids[is_duplicate]
    ids_to_fetch = valid_ids[~is_duplicate].tolist()

    print("Repeated IDs:", duplicate_ids.tolist())
    print("Duplicate rows:", len(duplicate_ids))
    print("Unique IDs ready to fetch:", len(ids_to_fetch))

    # Confirm that every input row is accounted for.
    assert len(candidates) == (
        is_blank.sum() + is_invalid.sum() + len(duplicate_ids) + len(ids_to_fetch)
    ), "The validation counts do not add up to the input row count."

    output_dir = project_root / "data/validated"
    output_dir.mkdir(parents=True, exist_ok=True)

    audit = candidates.copy()
    audit.insert(0, "source_line", range(2, len(audit) + 2))
    audit["status"] = "ready_to_fetch"
    audit.loc[is_blank, "status"] = "missing"
    audit.loc[is_invalid, "status"] = "invalid_format"
    audit.loc[duplicate_ids.index, "status"] = "duplicate"

    audit.to_csv(output_dir / "id_audit.csv", index=False)
    pd.DataFrame({"tmdb_id": ids_to_fetch}).to_csv(
        output_dir / "validated_ids.csv", index=False
    )

    print(audit["status"].value_counts())
    print(f"Saved {len(ids_to_fetch)} unique IDs to {output_dir / 'validated_ids.csv'}")


if __name__ == "__main__":
    main()
