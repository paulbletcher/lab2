"""Integrity checks that must pass before analysis results are loaded."""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_movies(validated, details, movies):
    require(validated["tmdb_id"].notna().all() and validated["tmdb_id"].is_unique,
            "Expected unique, non-null validated movie IDs.")
    require(movies["tmdb_id"].notna().all() and movies["tmdb_id"].is_unique,
            "Expected one row per movie after flattening details.")
    require(len(details) == len(movies), "Flattening changed the movie row count.")
    require(set(movies["tmdb_id"]) <= set(validated["tmdb_id"]),
            "Movie details contain IDs outside the validated input.")


def join_movie_ratios(credits, movie_ratios, relationship):
    """Check the expected relationship and ensure an inner join loses no rows."""
    require(set(credits["tmdb_id"]) <= set(movie_ratios["tmdb_id"]),
            "Credits contain movie IDs without movie details.")
    joined = credits.merge(movie_ratios, on="tmdb_id", how="inner",
                           validate=relationship)
    require(len(joined) == len(credits), "The credits join changed the row count.")
    return joined


def check_results(movies, actor_films, director_films, outputs):
    require(actor_films["tmdb_id"].is_unique,
            "Expected at most one lead actor per movie.")
    require(not director_films.duplicated(["tmdb_id", "director_id"]).any(),
            "Expected unique movie-director pairs.")
    expected = {"comparison"}
    for window in ("all_years", "2000_onward"):
        expected.update({f"franchises_{window}", f"standalones_{window}"})
    for role in ("actors", "directors"):
        expected.update(f"{role}_min_{cutoff}_films" for cutoff in (3, 2))
    require(set(outputs) == expected, "Expected the nine analysis tables.")
    comparison = outputs["comparison"]
    require(comparison["time_window"].tolist() == ["all_years", "2000_onward"],
            "Expected both analysis windows in order.")
    for row in comparison.to_dict("records"):
        films = movies if row["time_window"] == "all_years" else movies.loc[
            movies["release_date"].dt.year.ge(2000)]
        require(row["franchise_films"] + row["standalone_films"] == len(films),
                "Franchise and standalone counts do not reconcile.")
        require(row["franchise_films_with_ratio"] + row["standalone_films_with_ratio"]
                == films["revenue_to_budget"].count(),
                "Usable ratio counts do not reconcile.")


def check_acquisition(validated, cached_responses, audit):
    """Reconcile cache coverage with the audit; acquisition failures are diagnostic."""
    valid_ids = set(validated["tmdb_id"])
    require(audit["tmdb_id"].is_unique and set(audit["tmdb_id"]) == valid_ids,
            "Fetch audit must contain one row per validated movie ID.")
    cached = {(movie_id, endpoint) for movie_id, endpoint, _ in cached_responses
              if movie_id in valid_ids}
    failures = []
    for row in audit.to_dict("records"):
        for endpoint in ("details", "credits"):
            status = row[endpoint]
            require(isinstance(status, str) and bool(status.strip()),
                    "Fetch audit contains an empty endpoint outcome.")
            require((status == "ok") == ((row["tmdb_id"], endpoint) in cached),
                    f"Cache and fetch audit disagree for {row['tmdb_id']} {endpoint}.")
            if status != "ok":
                failures.append(f"{row['tmdb_id']} {endpoint}: {status}")
    return failures
