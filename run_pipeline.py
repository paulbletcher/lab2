"""Run input validation, cached acquisition, and checked analysis."""

import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    for script in ("pipeline/validate.py", "pipeline/extract.py", "run_analysis.py"):
        subprocess.run([sys.executable, str(root / script)], cwd=root, check=True)


if __name__ == "__main__":
    main()
