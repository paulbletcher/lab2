import pandas as pd


def flatten_movie_details(movies: pd.DataFrame) -> pd.DataFrame:
    """Turn cached movie details into a table with one row per movie."""
    flat = movies[
        ["tmdb_id", "title", "release_date", "budget", "revenue",
         "vote_average", "vote_count"]
    ].copy()

    collections = pd.json_normalize([
        value if isinstance(value, dict) else {}
        for value in movies["belongs_to_collection"]
    ]).reindex(columns=["id", "name"])
    collections.index = movies.index
    flat["collection_id"] = collections["id"].astype("Int64")
    flat["collection_name"] = collections["name"]

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
    columns = ["tmdb_id", "lead_actor_id", "lead_actor_name"]
    movies = pd.DataFrame.from_dict(credits_by_movie, orient="index")
    cast = movies.reindex(columns=["cast"])["cast"].explode()
    # Check original values before normalization can coerce orders to floats.
    cast = cast[cast.map(
        lambda actor: isinstance(actor, dict)
        and isinstance(actor.get("order"), int)
    )]
    if cast.empty:
        return pd.DataFrame(columns=columns)

    actors = pd.json_normalize(cast.tolist())
    actors["tmdb_id"] = cast.index.to_numpy()
    leads = actors.loc[actors.groupby("tmdb_id", sort=False)["order"].idxmin()]
    return leads.rename(columns={
        "id": "lead_actor_id", "name": "lead_actor_name",
    })[columns].reset_index(drop=True)


def flatten_directors(credits_by_movie: dict) -> pd.DataFrame:
    """Return one row per movie–director pair."""
    columns = ["tmdb_id", "director_id", "director_name"]
    movies = pd.DataFrame.from_dict(credits_by_movie, orient="index")
    crew = movies.reindex(columns=["crew"])["crew"].explode()
    crew = crew[crew.map(
        lambda person: isinstance(person, dict) and person.get("job") == "Director"
    )]
    if crew.empty:
        return pd.DataFrame(columns=columns)

    directors = pd.json_normalize(crew.tolist())
    directors["tmdb_id"] = crew.index.to_numpy()
    return directors.rename(columns={
        "id": "director_id", "name": "director_name",
    })[columns].drop_duplicates(
        subset=["tmdb_id", "director_id"], ignore_index=True,
    )