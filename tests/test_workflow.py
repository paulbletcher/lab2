"""Portable offline checks; no real data, cache, credentials or network needed."""

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import requests

from pipeline import validate
import run_pipeline


ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def test_runner_calls_imported_stages_in_prerequisite_order(self):
        result = subprocess.CompletedProcess([], 0, "ok\n", "")
        with patch("run_pipeline.subprocess.run", return_value=result) as run, redirect_stdout(io.StringIO()) as output:
            run_pipeline.main()
        self.assertEqual([call.args[0][-1] for call in run.call_args_list],
                         [f"from {stage.__name__} import main; main()" for stage, _ in run_pipeline.STAGES])
        self.assertEqual([call.kwargs["timeout"] for call in run.call_args_list], [60, 3600, 120])
        self.assertIn("Completed run_analysis", output.getvalue())

    def test_runner_stops_and_redacts_failed_stage_output(self):
        failure = subprocess.CalledProcessError(1, [], output="api_key=secret\n", stderr="failed secret\n")
        with patch.dict(os.environ, {"TMDB_API_KEY": "secret"}), \
                patch("run_pipeline.subprocess.run", side_effect=failure) as run, redirect_stdout(io.StringIO()) as output:
            with self.assertRaisesRegex(SystemExit, "pipeline.validate failed"):
                run_pipeline.main()
        self.assertEqual(run.call_count, 1)
        self.assertNotIn("secret", output.getvalue())
        self.assertIn("[REDACTED]", output.getvalue())

    def test_runner_stops_and_names_timed_out_stage(self):
        result = subprocess.CompletedProcess([], 0, "", "")
        failure = subprocess.TimeoutExpired([], 3600, output=b"waiting\n")
        with patch("run_pipeline.subprocess.run", side_effect=[result, failure]) as run, redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(SystemExit, "pipeline.extract timed out after 3600s"):
                run_pipeline.main()
        self.assertEqual(run.call_count, 2)

    def test_importing_validation_and_acquisition_does_no_io(self):
        for filename in ("validate.py", "extract.py"):
            with self.subTest(filename=filename), patch("pandas.read_csv") as read, \
                    patch("sqlite3.connect") as connect, patch("dotenv.load_dotenv") as dotenv, \
                    patch("requests.Session") as session:
                spec = importlib.util.spec_from_file_location("import_test", ROOT / "pipeline" / filename)
                spec.loader.exec_module(importlib.util.module_from_spec(spec))
                for mocked in (read, connect, dotenv, session):
                    mocked.assert_not_called()

    def test_validator_uses_its_project_root_and_normalizes_ids(self):
        with tempfile.TemporaryDirectory(prefix="lab2-test-validator-") as folder:
            root = Path(folder)
            (root / "data/input").mkdir(parents=True)
            (root / "data/input/id_list.csv").write_text("tmdb_id\n 00155 \n155\ntt0468569\n0\n\n0002\n2\n-1\n")
            unrelated = root / "elsewhere"
            unrelated.mkdir()
            previous_cwd = Path.cwd()
            try:
                os.chdir(unrelated)
                with patch.object(validate, "__file__", str(root / "pipeline/validate.py")), redirect_stdout(io.StringIO()):
                    validate.main()
            finally:
                os.chdir(previous_cwd)
            ids = pd.read_csv(root / "data/validated/validated_ids.csv", dtype=str)
            self.assertEqual(ids.tmdb_id.tolist(), ["155", "2"])
            audit = pd.read_csv(root / "data/validated/id_audit.csv", keep_default_na=False)
            self.assertEqual(audit.status.tolist(), ["ready_to_fetch", "duplicate", "invalid_format", "invalid_format", "missing", "ready_to_fetch", "duplicate", "invalid_format"])
            self.assertEqual(audit.source_line.tolist(), list(range(2, 10)))
            self.assertFalse((unrelated / "data").exists())

    def test_notebook_live_checks_are_disabled_without_credentials(self):
        notebook = json.loads((ROOT / "data_profile/tmdb_data_profile.ipynb").read_text(encoding="utf-8"))
        sources = ["".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"]
        live_sources = [source for source in sources if "requests.get(" in source]
        self.assertEqual(len(live_sources), 2)
        namespace = {}
        with patch.object(requests.sessions.Session, "request", side_effect=AssertionError("Live HTTP forbidden")) as network, \
                patch("dotenv.load_dotenv") as dotenv, redirect_stdout(io.StringIO()) as output:
            for source in live_sources:
                exec(compile(source, "<notebook-live-check>", "exec"), namespace)
            network.assert_not_called()
            dotenv.assert_not_called()
        self.assertEqual(output.getvalue().count("skipped"), 2)
        self.assertNotIn("pipeline/fetch.py", "\n".join(sources))

    def test_synthetic_shortlist_snapshot_and_compare_commands(self):
        fixtures = ROOT / "tests/fixtures/shortlists"
        with tempfile.TemporaryDirectory(prefix="lab2-test-shortlists-") as folder:
            root = Path(folder)
            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"

            def command(*args):
                return subprocess.run(
                    [sys.executable, "-B", str(ROOT / "shortlist_changes.py"), *map(str, args)],
                    cwd=root, env=env, capture_output=True, text=True, check=True,
                )

            previous, current = root / "synthetic_baseline", root / "synthetic_current"
            command("snapshot", previous, "--source", fixtures / "baseline")
            command("snapshot", current, "--source", fixtures / "current")
            report = root / "synthetic_report.md"
            command("compare", previous, current, "--output", report)
            text = report.read_text(encoding="utf-8")
            sections = dict(part.split("\n", 1) for part in text.split("\n## ")[1:])
            changed = sections["Standalones · All years"]
            expected = [
                "| Pulp Fiction | Ratio changed | 2 | 2 | 26.74× | 27.00× |",
                "| Spirited Away | Moved up | 4 | 3 | 14.47× | 14.47× |",
                "| SYNTHETIC Example Film | Entered | — | 4 | — | 14.00× |",
                "| Schindler's List | Dropped out | 3 | — | 14.61× | — |",
            ]
            rows = [line for line in changed.splitlines()
                    if line.startswith("| ") and not line.startswith("| Title or collection |")]
            self.assertEqual(rows, expected)
            for title in ("Franchises · All years", "Franchises · 2000 onward", "Standalones · 2000 onward"):
                self.assertEqual(sections[title].strip(), "No changes in shortlist membership, rank, or displayed ratio.")
            before = report.read_bytes()
            with self.assertRaises(subprocess.CalledProcessError):
                command("compare", previous, current, "--output", report)
            self.assertEqual(report.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
