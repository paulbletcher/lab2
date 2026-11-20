import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

from pipeline.analysis import analyze_licensing, summarize_talent
from pipeline.checks import (
    check_acquisition, check_movies, check_results, join_movie_ratios,
)
from pipeline.load import load_analysis
from pipeline.transform import (
    flatten_directors,
    flatten_lead_actors,
    flatten_movie_details,
)


def main():
    root = Path(__file__).resolve().parent
    ids_path = root / "data" / "validated" / "validated_ids.csv"
    cache_path = root / "data" / "cache" / "tmdb.sqlite"

    if not ids_path.is_file() or not cache_path.is_file():
        raise SystemExit("Generate validated_ids.csv and the TMDb cache first.")

    audit_path = cache_path.parent / "fetch_audit.csv"
    if not audit_path.is_file():
        raise SystemExit(
            "Missing data/cache/fetch_audit.csv. "
            "Run python pipeline/extract.py to rebuild it, then rerun this script."
        )

    validated = pd.read_csv(ids_path, dtype={"tmdb_id": str})
    valid_ids = set(validated["tmdb_id"])

    with closing(sqlite3.connect(cache_path)) as connection:
        rows = connection.execute(
            "SELECT movie_id, endpoint, payload FROM responses ORDER BY movie_id"
        ).fetchall()

    detail_records = []
    credits_by_movie = {}

    for movie_id, endpoint, raw_payload in rows:
        if movie_id not in valid_ids:
            continue

        if endpoint == "details":
            detail_records.append({**json.loads(raw_payload), "tmdb_id": movie_id})
        elif endpoint == "credits":
            credits_by_movie[movie_id] = json.loads(raw_payload)

    if not detail_records:
        raise SystemExit("The cache has no movie details for the validated IDs.")

    movies = flatten_movie_details(pd.DataFrame(detail_records))
    check_movies(validated, detail_records, movies)

    movie_ids = set(movies["tmdb_id"])
    credits_by_movie = {
        movie_id: credits
        for movie_id, credits in credits_by_movie.items()
        if movie_id in movie_ids
    }

    movie_ratios = movies[["tmdb_id", "revenue_to_budget"]]
    actor_films = join_movie_ratios(
        flatten_lead_actors(credits_by_movie), movie_ratios, "one_to_one"
    )
    director_films = join_movie_ratios(
        flatten_directors(credits_by_movie), movie_ratios, "many_to_one"
    )

    outputs = analyze_licensing(movies)
    talent = {
        "actors": summarize_talent(actor_films, "lead_actor_id", "lead_actor_name"),
        "directors": summarize_talent(director_films, "director_id", "director_name"),
    }

    for role, summary in talent.items():
        for cutoff in (3, 2):
            outputs[f"{role}_min_{cutoff}_films"] = summary.loc[
                summary["films_with_ratio"].ge(cutoff)
            ]

    output_dir = root / "data" / "analysis"
    audit = pd.read_csv(audit_path, dtype={"tmdb_id": str})
    failures = check_acquisition(validated, rows, audit)
    for failure in failures:
        print(f"Acquisition audit: {failure}")
    check_results(movies, actor_films, director_films, outputs)
    load_analysis(outputs, output_dir)

    print(f"Analyzed {len(movies)} of {len(valid_ids)} validated movie IDs.")
    print(outputs["comparison"].round(2).to_string(index=False))
    print(f"Saved {len(outputs)} tables to {output_dir}")


if __name__ == "__main__":
    main()
