"""Write complete UTF-8 CSVs without exposing partially written files."""

from pathlib import Path
from tempfile import NamedTemporaryFile


def write_csv_atomic(table, destination):
    """Replace one CSV only after its index-free UTF-8 write succeeds."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=destination.parent,
            prefix=f".{destination.name}-", suffix=".tmp", delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            table.to_csv(temporary_file, index=False)
        temporary_path.replace(destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
