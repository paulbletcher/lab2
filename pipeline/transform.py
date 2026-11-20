import pandas as pd


def flatten_movie_details(movies: pd.DataFrame) -> pd.DataFrame:
    """Turn cached movie details into a table with one row per movie."""
    flat = movies[
        ["tmdb_id", "title", "release_date", "budget", "revenue",
         "vote_average", "vote_count"]
    ].copy()

    collections = movies["belongs_to_collection"]
    flat["collection_id"] = collections.map(
        lambda value: value.get("id") if isinstance(value, dict) else None
    ).astype("Int64")
    flat["collection_name"] = collections.map(
        lambda value: value.get("name") if isinstance(value, dict) else None
    )

    flat["release_date"] = pd.to_datetime(
        flat["release_date"], format="%Y-%m-%d", errors="coerce"
    )
    flat["budget"] = pd.to_numeric(flat["budget"], errors="coerce")
    flat["revenue"] = pd.to_numeric(flat["revenue"], errors="coerce")

    positive_amounts = flat["budget"].gt(0) & flat["revenue"].gt(0)
    flat["revenue_to_budget"] = (
        flat["revenue"].where(positive_amounts)
        / flat["budget"].where(positive_amounts)
    )

    return flat