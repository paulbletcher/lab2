"""Run the stage entry points in prerequisite order with bounded execution."""

import os
from pathlib import Path
import re
import subprocess
import sys

from dotenv import dotenv_values
from pipeline import extract, validate
import run_analysis

# Single execution registry: module and maximum elapsed seconds.
STAGES = ((validate, 60), (extract, 3600), (run_analysis, 120))


def main():
    root = Path(__file__).resolve().parent
    key = os.environ.get("TMDB_API_KEY") or dotenv_values(root / ".env").get("TMDB_API_KEY")

    def show(output):
        if output:
            if isinstance(output, bytes):
                output = output.decode("utf-8", errors="replace")
            if key:
                output = output.replace(key, "[REDACTED]")
            print(re.sub(r"(?i)(api_key=)[^&\s]+", r"\1[REDACTED]", output), end="", flush=True)

    for stage, timeout in STAGES:
        name = stage.__name__
        print(f"Starting {name} (timeout {timeout}s)", flush=True)
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"from {name} import main; main()"],
                cwd=root, capture_output=True, text=True, check=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired as error:
            show(error.stdout)
            show(error.stderr)
            raise SystemExit(f"Stage {name} timed out after {timeout}s.") from None
        except subprocess.CalledProcessError as error:
            show(error.stdout)
            show(error.stderr)
            raise SystemExit(f"Stage {name} failed (exit {error.returncode}).") from None
        show(result.stdout)
        show(result.stderr)
        print(f"Completed {name}", flush=True)


if __name__ == "__main__":
    main()
