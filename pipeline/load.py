"""Load checked analysis tables into their final CSV destinations."""


def load_analysis(outputs, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in outputs.items():
        table.to_csv(output_dir / f"{name}.csv", index=False)
