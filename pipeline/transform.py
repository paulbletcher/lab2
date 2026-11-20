import pandas as pd


def flatten_movie_details(movies: pd.DataFrame) -> pd.DataFrame:
    """Preserve movie rows; use Int64 IDs, nullable string collection names.

    Missing IDs mean standalone; their names are also missing. Blank collection
    names become missing without changing a present collection ID. Financial
    coercion counts are available in result.attrs["financial_coercion"].
    """
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
    flat["collection_name"] = (
        collections["name"].astype("string").str.strip().replace("", pd.NA)
        .where(flat["collection_id"].notna())
    )

    flat["release_date"] = pd.to_datetime(
        flat["release_date"], format="%Y-%m-%d", errors="coerce"
    )
    financial_coercion = {}
    for field in ("budget", "revenue"):
        original = flat[field]
        converted = pd.to_numeric(original, errors="coerce")
        financial_coercion[field] = {
            "originally_missing": int(original.isna().sum()),
            "invalid_non_null": int((original.notna() & converted.isna()).sum()),
            "missing_after_coercion": int(converted.isna().sum()),
        }
        flat[field] = converted
    flat.attrs["financial_coercion"] = financial_coercion

    positive_amounts = flat["budget"].gt(0) & flat["revenue"].gt(0)
    flat["revenue_to_budget"] = (
        flat["revenue"].where(positive_amounts)
        / flat["budget"].where(positive_amounts)
    )

    return flat


def flatten_lead_actors(credits_by_movie: dict) -> pd.DataFrame:
    """Select the first minimum nonnegative integer billing position per movie.

    Accept equivalent integers, integral floats, and numeric strings. Exclude
    missing, boolean, nonnumeric, nonfinite, negative, and fractional positions.
    """
    columns = ["tmdb_id", "lead_actor_id", "lead_actor_name"]
    movies = pd.DataFrame.from_dict(credits_by_movie, orient="index")
    cast = movies.reindex(columns=["cast"])["cast"].explode()
    cast = cast[cast.map(lambda actor: isinstance(actor, dict))]
    if cast.empty:
        return pd.DataFrame(columns=columns)

    actors = pd.json_normalize(cast.tolist())
    actors["tmdb_id"] = cast.index.to_numpy()
    original_order = actors.reindex(columns=["order"])["order"]
    orders = pd.to_numeric(original_order, errors="coerce")
    finite = orders.notna() & orders.ge(0) & orders.lt(float("inf"))
    orders = orders.where(finite)
    valid = orders.mod(1).eq(0) & ~original_order.map(lambda value: isinstance(value, bool))
    actors["order"] = orders
    actors = actors.loc[valid]
    if actors.empty:
        return pd.DataFrame(columns=columns)
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
