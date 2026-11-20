import json
import os
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from time import sleep

import pandas as pd
import requests
from dotenv import load_dotenv

# Keep direct `python pipeline/extract.py` execution available.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.csv_io import write_csv_atomic


def retry_delay(retry_after, fallback):
    """Use Retry-After seconds or an HTTP date, otherwise the backoff."""
    if retry_after is not None:
        value = retry_after.strip()
        if value.isascii() and value.isdigit():
            return int(value)
        try:
            retry_at = parsedate_to_datetime(value)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(0, (retry_at - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            pass
    return fallback


def get_response(connection, movie_id, endpoint, url, session, api_key):
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
    for attempt in range(4):
        try:
            response = session.get(url, params={"api_key": api_key}, timeout=20)
        except (requests.ConnectionError, requests.Timeout):
            if attempt == 3:
                raise RuntimeError(
                    f"{movie_id} {endpoint}: network request failed after 4 attempts"
                ) from None
            delay = 2 ** attempt
        except requests.RequestException:
            raise RuntimeError(f"{movie_id} {endpoint}: network request failed") from None
        else:
            status = response.status_code
            if status in (401, 403):
                raise SystemExit(f"TMDb returned HTTP {status}. Batch stopped.")
            if status not in (429, 500, 502, 503, 504):
                break
            if attempt == 3:
                if status == 429:
                    raise SystemExit(
                        "TMDb returned HTTP 429 after 4 attempts. "
                        "Retry limit reached; batch stopped."
                    )
                raise RuntimeError(
                    f"{movie_id} {endpoint}: HTTP {status} after 4 attempts"
                )
            delay = retry_delay(response.headers.get("Retry-After"), 2 ** attempt)
        print(f"{movie_id} {endpoint}: retry {attempt + 1}/3 in {delay:g} seconds")
        sleep(delay)

    if response.status_code != 200:
        raise RuntimeError(f"{movie_id} {endpoint}: HTTP {response.status_code}")

    try:
        payload = response.json()
    except ValueError:
        raise ValueError(f"{movie_id} {endpoint}: invalid JSON response") from None
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


def write_audit(results, audit_path):
    """Replace the audit atomically, preserving the existing CSV layout."""
    audit = pd.DataFrame(results, columns=["tmdb_id", "details", "credits"])
    write_csv_atomic(audit, audit_path)
    return audit


def main():
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        raise ValueError("TMDB_API_KEY is missing from .env")

    ids_path = project_root / "data" / "validated" / "validated_ids.csv"
    validated_ids = pd.read_csv(ids_path, dtype={"tmdb_id": str})
    cache_path = project_root / "data" / "cache" / "tmdb.sqlite"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path = cache_path.parent / "fetch_audit.csv"

    with closing(sqlite3.connect(cache_path)) as connection, requests.Session() as session:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                movie_id TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                payload TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                PRIMARY KEY (movie_id, endpoint)
            )
        """)

        cached = set(connection.execute("SELECT movie_id, endpoint FROM responses"))
        results = [
            {
                "tmdb_id": movie_id,
                "details": "ok" if (movie_id, "details") in cached else "not attempted",
                "credits": "ok" if (movie_id, "credits") in cached else "not attempted",
            }
            for movie_id in validated_ids["tmdb_id"]
        ]
        write_audit(results, audit_path)

        for result in results:
            movie_id = result["tmdb_id"]
            url = f"https://api.themoviedb.org/3/movie/{movie_id}"

            for endpoint, endpoint_url in (("details", url), ("credits", f"{url}/credits")):
                try:
                    get_response(connection, movie_id, endpoint, endpoint_url, session, api_key)
                    result[endpoint] = "ok"
                except SystemExit as exc:
                    result[endpoint] = str(exc)
                    raise
                except (RuntimeError, ValueError) as exc:
                    result[endpoint] = str(exc)
                    print(exc)
                finally:
                    write_audit(results, audit_path)

    audit = pd.DataFrame(results, columns=["tmdb_id", "details", "credits"])

    complete = audit[["details", "credits"]].eq("ok").all(axis=1)
    print(f"Movies with both responses: {complete.sum()}/{len(audit)}")
    print(f"Fetch audit saved to {audit_path}")


if __name__ == "__main__":
    main()
