from pathlib import Path

import pandas as pd


def main():
    csv_path = Path(__file__).resolve().parent / "data" / "id_list.csv"
    candidates = pd.read_csv(
        csv_path,
        dtype="string",
        skip_blank_lines=False,
        keep_default_na=False,
    )
    if "tmdb_id" not in candidates.columns:
        raise ValueError(
            f"Expected column 'tmdb_id' in {csv_path}; "
            f"found {candidates.columns.tolist()}"
        )

    ids = candidates[["tmdb_id"]].copy()
    ids = ids.rename(columns={"tmdb_id": "original_id"})
    ids.insert(0, "csv_record", ids.index + 2)
    ids["stripped_id"] = ids["original_id"].str.strip()

    blank_mask = ids["stripped_id"].eq("")
    blank_count = int(blank_mask.sum())
    digits_only = ids["stripped_id"].str.fullmatch(r"[0-9]+", na=False)
    positive = ids["stripped_id"].str.lstrip("0").ne("")
    valid_mask = ~blank_mask & digits_only & positive
    malformed_mask = ~blank_mask & ~valid_mask
    malformed_count = int(malformed_mask.sum())

    ids["normalized_id"] = ids["stripped_id"].where(valid_mask).str.lstrip("0")
    valid_ids = ids.loc[valid_mask].copy()
    extra_duplicate_count = int(valid_ids["normalized_id"].duplicated().sum())
    distinct_valid_ids = valid_ids["normalized_id"].drop_duplicates().tolist()
    distinct_valid_count = len(distinct_valid_ids)

    observed_count = len(candidates)
    reconciled_count = (
        blank_count + malformed_count + extra_duplicate_count + distinct_valid_count
    )
    print("Source rows:", observed_count)
    print("Blank rows:", blank_count)
    print("Malformed rows:", malformed_count)
    print("Extra duplicate rows:", extra_duplicate_count)
    print("Distinct valid IDs:", distinct_valid_count)
    print(
        f"Reconciliation: {observed_count} = {blank_count} + "
        f"{malformed_count} + {extra_duplicate_count} + {distinct_valid_count}"
    )
    assert observed_count == reconciled_count, "Row counts do not reconcile"
    print("Reconciles: yes")

    # Retain normalized, distinct IDs for the next pipeline step.
    return distinct_valid_ids


if __name__ == "__main__":
    distinct_valid_ids = main()
