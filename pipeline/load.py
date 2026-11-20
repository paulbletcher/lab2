"""Load checked analysis tables into their final CSV destinations."""

from pipeline.csv_io import write_csv_atomic


def load_analysis(outputs, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in outputs.items():
        write_csv_atomic(table, output_dir / f"{name}.csv")
