"""Offline acquisition checks: temporary databases, mocked HTTP and waits."""

import io
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pandas as pd
import requests

from pipeline import extract
from pipeline.checks import check_acquisition


SCHEMA = """CREATE TABLE responses (
    movie_id TEXT NOT NULL, endpoint TEXT NOT NULL, payload TEXT NOT NULL,
    fetched_at TEXT NOT NULL, PRIMARY KEY (movie_id, endpoint))"""
SECRET = "offline-test-key-must-not-appear-in-errors"


def response(status=200, movie_id=1, retry_after=None):
    result = MagicMock(status_code=status)
    result.headers = {} if retry_after is None else {"Retry-After": retry_after}
    result.json.return_value = {"id": movie_id}
    return result


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="lab2-test-acquisition-")
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.output = io.StringIO()
        self.session = MagicMock()
        self.session.__enter__.return_value = self.session
        self.enterContext(redirect_stdout(self.output))
        self.enterContext(patch.object(extract, "load_dotenv"))
        self.enterContext(patch.object(extract.os, "getenv", return_value=SECRET))
        self.enterContext(patch.object(
            requests.sessions.Session, "request", side_effect=AssertionError("Live HTTP forbidden"),
        ))
        self.factory = self.enterContext(patch.object(extract.requests, "Session", return_value=self.session))
        self.sleep = self.enterContext(patch.object(extract, "sleep"))

    def prepare(self, name="project", ids=("1", "2")):
        project = self.root / name
        validated = project / "data/validated"
        validated.mkdir(parents=True)
        (validated / "validated_ids.csv").write_text("tmdb_id\n" + "\n".join(ids) + "\n")
        return project

    def seed(self, project, entries):
        cache = project / "data/cache/tmdb.sqlite"
        cache.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(cache)) as db:
            db.execute(SCHEMA)
            db.executemany("INSERT INTO responses VALUES (?, ?, ?, ?)", [
                (movie_id, endpoint, json.dumps({"id": int(movie_id)}), "original timestamp")
                for movie_id, endpoint in entries
            ])
            db.commit()

    def run_project(self, project, effects):
        self.session.get.reset_mock()
        self.session.get.side_effect = effects
        self.sleep.reset_mock()
        with patch.object(extract, "__file__", str(project / "pipeline/extract.py")):
            extract.main()
        self.assertNotIn(SECRET, self.output.getvalue())

    def audit(self, project):
        result = pd.read_csv(project / "data/cache/fetch_audit.csv", dtype=str)
        self.assertEqual(result.columns.tolist(), ["tmdb_id", "details", "credits"])
        validated = pd.read_csv(project / "data/validated/validated_ids.csv", dtype=str)
        with closing(sqlite3.connect(project / "data/cache/tmdb.sqlite")) as db:
            rows = db.execute("SELECT movie_id, endpoint, payload FROM responses").fetchall()
        check_acquisition(validated, rows, result)
        return result.set_index("tmdb_id")

    def test_cache_hits_make_zero_http_calls(self):
        project = self.prepare(ids=("1",))
        self.seed(project, [("1", "details"), ("1", "credits")])
        self.run_project(project, [])
        self.session.get.assert_not_called()
        self.sleep.assert_not_called()
        self.factory.assert_called_once_with()
        self.assertTrue(self.audit(project).eq("ok").all().all())
        with closing(sqlite3.connect(project / "data/cache/tmdb.sqlite")) as db:
            self.assertEqual(db.execute("SELECT DISTINCT fetched_at FROM responses").fetchall(), [("original timestamp",)])

    def test_timeout_and_connection_error_recover(self):
        for error in (requests.Timeout, requests.ConnectionError):
            with self.subTest(error=error.__name__):
                project = self.prepare(error.__name__, ids=("1",))
                self.run_project(project, [error(SECRET), response(), response()])
                self.assertEqual(self.session.get.call_count, 3)
                self.sleep.assert_called_once_with(1)
                self.assertTrue(self.audit(project).eq("ok").all().all())

    def test_retry_after_seconds_and_http_date(self):
        for name, header, expected in [
            ("seconds", "7", 7),
            ("date", "Fri, 20 Nov 2026 12:00:09 GMT", 9),
        ]:
            with self.subTest(header=header):
                project = self.prepare(name, ids=("1",))
                with patch.object(extract, "datetime", wraps=datetime) as clock:
                    clock.now.return_value = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)
                    self.run_project(project, [response(429, retry_after=header), response(), response()])
                self.sleep.assert_called_once_with(expected)
                self.assertTrue(self.audit(project).eq("ok").all().all())
        self.assertEqual(extract.retry_delay("0", 4), 0)
        for invalid in (None, "", "nonsense", "-1", "1.5"):
            self.assertEqual(extract.retry_delay(invalid, 4), 4)

    def test_exhausted_failures_and_404_continue_to_next_endpoint(self):
        cases = [(str(status), [response(status)] * 4) for status in (500, 502, 503, 504)]
        cases += [(error.__name__, [error(SECRET)] * 4) for error in (requests.Timeout, requests.ConnectionError)]
        cases += [("404", [response(404)])]
        for name, failures in cases:
            with self.subTest(failure=name):
                project = self.prepare(name)
                self.run_project(project, failures + [response(), response(movie_id=2), response(movie_id=2)])
                audit = self.audit(project)
                self.assertNotEqual(audit.loc["1", "details"], "ok")
                self.assertTrue(audit["credits"].eq("ok").all())
                self.assertEqual(audit.loc["2", "details"], "ok")
                self.assertEqual(self.session.get.call_count, len(failures) + 3)
                self.assertEqual(self.sleep.call_args_list, [] if name == "404" else [call(1), call(2), call(4)])

    def test_fatal_stops_preserve_complete_audit_and_rerun_reuses_cache(self):
        for status in (401, 403, 429):
            with self.subTest(status=status):
                project = self.prepare(str(status), ids=("1", "2", "3"))
                self.seed(project, [("2", "details")])  # Cached but not yet reached in this run.
                failures = [response(status)] * (4 if status == 429 else 1)
                with self.assertRaisesRegex(SystemExit, f"HTTP {status}"):
                    self.run_project(project, [response()] + failures)
                self.assertEqual(self.session.get.call_count, 1 + len(failures))
                self.assertEqual(self.sleep.call_args_list, [call(1), call(2), call(4)] if status == 429 else [])
                audit = self.audit(project)
                self.assertEqual(audit.index.tolist(), ["1", "2", "3"])
                self.assertEqual(audit.loc["1", "details"], "ok")
                self.assertIn(f"HTTP {status}", audit.loc["1", "credits"])
                self.assertEqual(audit.loc["2", "details"], "ok")
                self.assertEqual(audit.loc["2", "credits"], "not attempted")
                self.assertTrue(audit.loc["3"].eq("not attempted").all())
                self.assertNotIn(SECRET, self.output.getvalue())
                self.run_project(project, [response(), response(movie_id=2), response(movie_id=3), response(movie_id=3)])
                self.assertEqual(self.session.get.call_count, 4)
                self.assertTrue(self.audit(project).eq("ok").all().all())

    def test_invalid_json_error_is_sanitized(self):
        project = self.prepare(ids=("1",))
        invalid = response()
        invalid.json.side_effect = ValueError(SECRET)
        self.run_project(project, [invalid, response()])
        audit = self.audit(project)
        self.assertIn("invalid JSON response", audit.loc["1", "details"])
        self.assertNotIn(SECRET, audit.to_csv())

    def test_failed_atomic_replace_preserves_previous_audit(self):
        path = self.root / "fetch_audit.csv"
        original = "tmdb_id,details,credits\n1,ok,ok\n"
        path.write_text(original)
        with patch.object(Path, "replace", side_effect=OSError("mocked write failure")):
            with self.assertRaises(OSError):
                extract.write_audit([{"tmdb_id": "2", "details": "not attempted", "credits": "not attempted"}], path)
        self.assertEqual(path.read_text(), original)
        self.assertEqual(list(self.root.glob(".fetch_audit.csv-*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
