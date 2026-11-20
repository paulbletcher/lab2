import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

import json
import sqlite3
from datetime import datetime, timezone

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

api_key = os.getenv("TMDB_API_KEY")
if not api_key:
    raise ValueError("TMDB_API_KEY is missing from .env")

ids_path = project_root / "data" / "validated" / "validated_ids.csv"
validated_ids = pd.read_csv(ids_path, dtype={"tmdb_id": str})
#movie_id = validated_ids.loc[0, "tmdb_id"]

cache_path = project_root / "data" / "cache" / "tmdb.sqlite"
cache_path.parent.mkdir(parents=True, exist_ok=True)


def get_response(connection, movie_id, endpoint, url):
    cached_row = connection.execute(
        """
        SELECT payload
        FROM responses
        WHERE movie_id = ? AND endpoint = ?
        """,
        (movie_id, endpoint),
    ).fetchone()

    if cached_row is not None:
        print(f"{movie_id} {endpoint}: cache hit")
        return json.loads(cached_row[0])

    print(f"{movie_id} {endpoint}: fetching from TMDb")
    try:
        response = requests.get(url, params={"api_key": api_key}, timeout=20)
    except requests.RequestException:
        raise RuntimeError(f"{movie_id} {endpoint}: network request failed") from None

    if response.status_code in (401, 403, 429):
        raise SystemExit(f"TMDb returned HTTP {response.status_code}. Batch stopped.")

    if response.status_code != 200:
        raise RuntimeError(f"{movie_id} {endpoint}: HTTP {response.status_code}")

    payload = response.json()
    if str(payload.get("id")) != movie_id:
        raise ValueError(f"{movie_id} {endpoint}: unexpected movie ID in response")

    connection.execute(
        """
        INSERT INTO responses (movie_id, endpoint, payload, fetched_at)
        VALUES (?, ?, ?, ?)
        """,
        (movie_id, endpoint, json.dumps(payload), datetime.now(timezone.utc).isoformat()),
    )
    connection.commit()
    return payload


results = []

connection = sqlite3.connect(cache_path)
try:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            movie_id TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            payload TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (movie_id, endpoint)
        )
    """)

    for movie_id in validated_ids["tmdb_id"]:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        result = {"tmdb_id": movie_id}

        for endpoint, endpoint_url in (("details", url), ("credits", f"{url}/credits")):
            try:
                get_response(connection, movie_id, endpoint, endpoint_url)
                result[endpoint] = "ok"
            except (RuntimeError, ValueError) as exc:
                result[endpoint] = str(exc)
                print(exc)

        results.append(result)
finally:
    connection.close()

audit = pd.DataFrame(results, columns=["tmdb_id", "details", "credits"])
audit_path = cache_path.parent / "fetch_audit.csv"
audit.to_csv(audit_path, index=False)

complete = audit[["details", "credits"]].eq("ok").all(axis=1)
print(f"Movies with both responses: {complete.sum()}/{len(audit)}")
print(f"Fetch audit saved to {audit_path}")