import csv
import json
import shutil
import sqlite3
import subprocess
import sys
from contextlib import closing
from itertools import cycle, islice
from pathlib import Path
from tempfile import TemporaryDirectory

root = Path(__file__).resolve().parents[1]

# Read only movies with both endpoints marked successful in your current audit.
with (root / "data/cache/fetch_audit.csv").open(newline="", encoding="utf-8-sig") as file:
    source_ids = [
        row["tmdb_id"] for row in csv.DictReader(file)
        if row["details"] == row["credits"] == "ok"
    ]

with closing(sqlite3.connect(root / "data/cache/tmdb.sqlite")) as db:
    cached = {
        (movie_id, endpoint): payload
        for movie_id, endpoint, payload in db.execute(
            "SELECT movie_id, endpoint, payload FROM responses"
        )
    }

if not source_ids:
    raise SystemExit("The fetch audit has no movies with both responses.")

with TemporaryDirectory(prefix="lab2-benchmark-") as folder:
    test_root = Path(folder)
    shutil.copytree(
        root / "pipeline", test_root / "pipeline",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copy2(root / "run_analysis.py", test_root / "run_analysis.py")
    benchmarks_dir = test_root / "benchmarks"
    benchmarks_dir.mkdir()
    shutil.copy2(
        root / "benchmarks/benchmark_analysis.py",
        benchmarks_dir / "benchmark_analysis.py",
    )

    cache_dir = test_root / "data/cache"
    ids_dir = test_root / "data/validated"
    cache_dir.mkdir(parents=True)
    ids_dir.mkdir(parents=True)

    ids = []
    responses = []
    for number, source_id in enumerate(islice(cycle(source_ids), 500), start=1):
        movie_id = str(1_000_000 + number)
        ids.append(movie_id)

        for endpoint in ("details", "credits"):
            payload = json.loads(cached[(source_id, endpoint)])
            payload["id"] = int(movie_id)
            responses.append((movie_id, endpoint, json.dumps(payload)))

    with closing(sqlite3.connect(cache_dir / "tmdb.sqlite")) as db:
        db.execute("""
            CREATE TABLE responses (
                movie_id TEXT,
                endpoint TEXT,
                payload TEXT,
                PRIMARY KEY (movie_id, endpoint)
            )
        """)
        db.executemany("INSERT INTO responses VALUES (?, ?, ?)", responses)
        db.commit()

    with (ids_dir / "validated_ids.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["tmdb_id"])
        writer.writerows((movie_id,) for movie_id in ids)

    with (cache_dir / "fetch_audit.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["tmdb_id", "details", "credits"])
        writer.writerows((movie_id, "ok", "ok") for movie_id in ids)

    subprocess.run(
        [sys.executable, str(benchmarks_dir / "benchmark_analysis.py")],
        cwd=test_root,
        check=True,
    )
