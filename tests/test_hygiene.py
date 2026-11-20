"""Offline schema, write-failure, numeric-order, and deterministic benchmark checks."""
import json
from contextlib import closing
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from benchmarks.benchmark_500 import prepare_benchmark
from pipeline.csv_io import write_csv_atomic
from pipeline.transform import flatten_lead_actors, flatten_movie_details
from pipeline.validate import validate_ids

ROOT = Path(__file__).resolve().parents[1]

class HygieneTests(unittest.TestCase):
    def test_validator_schema_and_normalization_without_io(self):
        for table in (pd.DataFrame(), pd.DataFrame({"movie_id": [1]})):
            with self.assertRaisesRegex(ValueError, "Expected input column 'tmdb_id'; actual columns"):
                validate_ids(table)
        source = pd.DataFrame({"tmdb_id": ["001", "1", "000", "0", "", None, "tt1", "-1", "2"]})
        original = source.copy(deep=True)
        ids, audit = validate_ids(source)
        self.assertEqual(ids.tmdb_id.tolist(), ["1", "2"])
        self.assertEqual(audit.status.tolist(), ["ready_to_fetch", "duplicate", "invalid_format", "invalid_format", "missing", "missing", "invalid_format", "invalid_format", "ready_to_fetch"])
        pd.testing.assert_frame_equal(source, original)

    def test_equivalent_billing_orders_and_invalid_orders(self):
        for value in (0, 0.0, "0", "0.0", " 0 "):
            with self.subTest(value=value):
                cast = [{"id": 1, "name": "First", "order": value}, {"id": 2, "name": "Tie", "order": 0}]
                self.assertEqual(flatten_lead_actors({"a": {"cast": cast}}).lead_actor_id.tolist(), [1])
        for value in (None, True, False, "bad", "", -1, "-1", 0.5, "0.5", float("inf"), float("nan")):
            with self.subTest(value=value):
                cast = [{"id": 1, "name": "Invalid", "order": value}, {"id": 2, "name": "Valid", "order": 2}]
                self.assertEqual(flatten_lead_actors({"a": {"cast": cast}}).lead_actor_id.tolist(), [2])
                self.assertTrue(flatten_lead_actors({"a": {"cast": cast[:1]}}).empty)

    def test_collection_contract_and_financial_coercion_counts(self):
        base = dict(title="Test", release_date="2001-01-01", vote_average=7, vote_count=1)
        rows = pd.DataFrame([
            dict(base, tmdb_id="1", budget=None, revenue="invalid", belongs_to_collection=None),
            dict(base, tmdb_id="2", budget="bad", revenue=None, belongs_to_collection={"id": 1, "name": "  "}),
            dict(base, tmdb_id="3", budget="10", revenue="30", belongs_to_collection={"id": 2, "name": " Series "}),
        ], index=[3, 1, 3])
        result = flatten_movie_details(rows)
        self.assertEqual(str(result.collection_name.dtype), "string")
        self.assertEqual(str(result.collection_id.dtype), "Int64")
        self.assertEqual(result.collection_name.iloc[2], "Series")
        self.assertTrue(result.collection_name.iloc[:2].isna().all())
        self.assertEqual(result.collection_id.iloc[1], 1)
        for field in ("budget", "revenue"):
            self.assertEqual(result.attrs["financial_coercion"][field], {"originally_missing": 1, "invalid_non_null": 1, "missing_after_coercion": 2})
        self.assertEqual(len(result), 3)
        self.assertEqual(result.revenue_to_budget.iloc[2], 3)

    def test_atomic_csv_preserves_format_and_previous_file_on_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "table.csv"
            table = pd.DataFrame({"name": ["caf\u00e9", None], "value": [1.25, 2]})
            expected = Path(folder) / "expected.csv"
            table.to_csv(expected, index=False)
            write_csv_atomic(table, destination)
            self.assertEqual(destination.read_bytes(), expected.read_bytes())
            before = destination.read_bytes()
            for target in ("pandas.DataFrame.to_csv", "pathlib.Path.replace"):
                with self.subTest(target=target), patch(target, side_effect=OSError("simulated failure")):
                    with self.assertRaises(OSError):
                        write_csv_atomic(table, destination)
                self.assertEqual(destination.read_bytes(), before)
                self.assertEqual(list(Path(folder).glob(".*.tmp")), [])

    def test_benchmark_is_identical_after_source_row_order_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sources = []
            for number, ids in enumerate((["2", "10"], ["10", "2"])):
                source = root / f"source{number}"
                source.mkdir()
                for name in ("pipeline", "benchmarks"):
                    shutil.copytree(ROOT / name, source / name, ignore=shutil.ignore_patterns("__pycache__"))
                shutil.copy2(ROOT / "run_analysis.py", source / "run_analysis.py")
                cache = source / "data/cache"
                cache.mkdir(parents=True)
                pd.DataFrame({"tmdb_id": ids, "details": "ok", "credits": "ok"}).to_csv(cache / "fetch_audit.csv", index=False)
                with closing(sqlite3.connect(cache / "tmdb.sqlite")) as db:
                    db.execute("CREATE TABLE responses (movie_id TEXT, endpoint TEXT, payload TEXT, PRIMARY KEY(movie_id,endpoint))")
                    for movie_id in ids:
                        details = dict(id=int(movie_id), title=f"Movie {movie_id}", release_date="2001-01-01", budget=10, revenue=int(movie_id)*10, vote_average=7, vote_count=2, belongs_to_collection=None)
                        for endpoint, payload in (("details", details), ("credits", {"id": int(movie_id), "cast": [], "crew": []})):
                            db.execute("INSERT INTO responses VALUES (?,?,?)", (movie_id, endpoint, json.dumps(payload)))
                    db.commit()
                project = root / f"project{number}"
                project.mkdir()
                prepare_benchmark(source, project)
                run = subprocess.run([sys.executable, "-B", "run_analysis.py"], cwd=project, capture_output=True, text=True, check=True, timeout=120)
                self.assertIn("Analyzed 500 of 500", run.stdout)
                ids_table = pd.read_csv(project / "data/validated/validated_ids.csv")
                self.assertEqual(len(ids_table), 500)
                self.assertTrue(ids_table.tmdb_id.is_unique)
                sources.append(project)
            for relative in ("data/validated/validated_ids.csv", "data/cache/fetch_audit.csv"):
                self.assertEqual((sources[0]/relative).read_bytes(), (sources[1]/relative).read_bytes())
            def rows(project):
                with closing(sqlite3.connect(project / "data/cache/tmdb.sqlite")) as db:
                    return db.execute("SELECT * FROM responses ORDER BY movie_id, endpoint").fetchall()
            self.assertEqual(rows(sources[0]), rows(sources[1]))
            files = list((sources[0]/"data/analysis").glob("*.csv"))
            self.assertEqual(len(files), 9)
            for file in files:
                self.assertEqual(file.read_bytes(), (sources[1]/"data/analysis"/file.name).read_bytes())

if __name__ == "__main__":
    unittest.main()
