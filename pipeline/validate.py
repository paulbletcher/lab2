"""Validate and normalize candidate TMDb IDs, preserving a row-level audit."""

from pathlib import Path

import pandas as pd


def validate_ids(candidates):
    """Return (unique normalized IDs, input audit) without reading or writing files."""
    if "tmdb_id" not in candidates.columns:
        raise ValueError(
            "Expected input column 'tmdb_id'; actual columns: "
            + repr(candidates.columns.tolist())
        )
    clean_ids = candidates["tmdb_id"].fillna("").astype(str).str.strip()
    is_blank = clean_ids.eq("")
    # Zero is not a positive TMDb ID: reject 0/00/etc., but normalize 00155 to 155.
    is_positive_integer = clean_ids.str.fullmatch(r"[0-9]+") & ~clean_ids.str.fullmatch(r"0+")
    is_invalid = ~is_blank & ~is_positive_integer
    valid_ids = clean_ids[is_positive_integer].str.lstrip("0")
    duplicate_ids = valid_ids[valid_ids.duplicated(keep="first")]
    validated_ids = pd.DataFrame({"tmdb_id": valid_ids[~valid_ids.duplicated(keep="first")].tolist()})

    if len(candidates) != is_blank.sum() + is_invalid.sum() + len(duplicate_ids) + len(validated_ids):
        raise ValueError("The validation counts do not add up to the input row count.")

    audit = candidates.copy()
    audit.insert(0, "source_line", range(2, len(audit) + 2))
    audit["status"] = "ready_to_fetch"
    audit.loc[is_blank, "status"] = "missing"
    audit.loc[is_invalid, "status"] = "invalid_format"
    audit.loc[duplicate_ids.index, "status"] = "duplicate"
    return validated_ids, audit


def main():
    project_root = Path(__file__).resolve().parents[1]
    candidates = pd.read_csv(
        project_root / "data/input/id_list.csv", dtype=str,
        keep_default_na=False, skip_blank_lines=False,
    )
    validated_ids, audit = validate_ids(candidates)
    print("Columns:", candidates.columns.tolist())
    print("Input rows:", len(candidates))
    print("Blank IDs:", int(audit["status"].eq("missing").sum()))
    print("Invalid IDs:", audit.loc[audit["status"].eq("invalid_format"), "tmdb_id"].tolist())
    repeated = audit.loc[audit["status"].eq("duplicate"), "tmdb_id"].str.strip().str.lstrip("0")
    print("Repeated IDs:", repeated.tolist())
    print("Duplicate rows:", len(repeated))
    print("Unique IDs ready to fetch:", len(validated_ids))

    output_dir = project_root / "data/validated"
    output_dir.mkdir(parents=True, exist_ok=True)
    audit.to_csv(output_dir / "id_audit.csv", index=False)
    validated_ids.to_csv(output_dir / "validated_ids.csv", index=False)
    print(audit["status"].value_counts())
    print(f"Saved {len(validated_ids)} unique IDs to {output_dir / 'validated_ids.csv'}")


if __name__ == "__main__":
    main()
