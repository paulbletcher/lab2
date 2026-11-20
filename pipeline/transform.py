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


def flatten_lead_actors(credits_by_movie: dict) -> pd.DataFrame:
    """Return the first-billed actor for each movie with usable cast data."""
    rows = []

    for movie_id, credits in credits_by_movie.items():
        ranked_cast = [
            actor
            for actor in credits.get("cast", [])
            if isinstance(actor.get("order"), int)
        ]

        if ranked_cast:
            lead = min(ranked_cast, key=lambda actor: actor["order"])
            rows.append({
                "tmdb_id": movie_id,
                "lead_actor_id": lead["id"],
                "lead_actor_name": lead["name"],
            })

    return pd.DataFrame(
        rows, columns=["tmdb_id", "lead_actor_id", "lead_actor_name"]
    )


def flatten_directors(credits_by_movie: dict) -> pd.DataFrame:
    """Return one row per movie–director pair."""
    rows = []

    for movie_id, credits in credits_by_movie.items():
        for person in credits.get("crew") or []:
            if person.get("job") == "Director":
                rows.append({
                    "tmdb_id": movie_id,
                    "director_id": person["id"],
                    "director_name": person["name"],
                })

    return pd.DataFrame(
        rows, columns=["tmdb_id", "director_id", "director_name"]
    ).drop_duplicates(subset=["tmdb_id", "director_id"], ignore_index=True)