"""Time three cached analysis runs, including startup, checks, and CSV writes."""

import subprocess
import sys
from pathlib import Path
from statistics import median
from time import perf_counter

project_root = Path(__file__).resolve().parents[1]
analysis_script = project_root / "run_analysis.py"
timings = []

for run_number in range(1, 4):
    start = perf_counter()

    result = subprocess.run(
        [sys.executable, str(analysis_script)],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )

    elapsed = perf_counter() - start
    timings.append(elapsed)

    print(f"Run {run_number}: {elapsed:.3f} seconds")
    for line in result.stdout.splitlines():
        if line.startswith(("Analyzed ", "Saved ")):
            print(f"  {line}")

print(f"\nMedian runtime: {median(timings):.3f} seconds")
