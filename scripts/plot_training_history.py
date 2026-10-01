from pathlib import Path
import argparse
import csv

import matplotlib.pyplot as plt


def find_column(columns: list[str], *names: str) -> str | None:
    for name in names:
        if name in columns:
            return name
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot Ultralytics YOLO training history.")
    parser.add_argument(
        "results_csv",
        help="Path to the Ultralytics results.csv file.",
    )
    parser.add_argument(
        "--output",
        default="training_history.png",
        help="Path for the generated PNG graph.",
    )
    args = parser.parse_args()

    results_path = Path(args.results_csv)
    if not results_path.is_file():
        raise FileNotFoundError(f"Training log not found: {results_path}")

    with results_path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, skipinitialspace=True)
        rows = [{key.strip(): value.strip() for key, value in row.items()} for row in reader]

    columns = list(rows[0]) if rows else []
    epoch_column = find_column(columns, "epoch")
    if epoch_column is None:
        raise ValueError("The training log does not contain an epoch column.")

    epochs = [float(row[epoch_column]) for row in rows]
    groups = {
        "Loss": [
            column
            for column in (
                "train/box_loss",
                "train/cls_loss",
                "train/dfl_loss",
                "train/l1_loss",
                "val/box_loss",
                "val/cls_loss",
                "val/dfl_loss",
                "val/l1_loss",
            )
            if column in columns
        ],
        "Validation metrics": [
            column
            for column in (
                "metrics/precision(B)",
                "metrics/recall(B)",
                "metrics/mAP50(B)",
                "metrics/mAP50-95(B)",
            )
            if column in columns
        ],
    }
    groups = {title: columns for title, columns in groups.items() if columns}
    if not groups:
        raise ValueError("No supported training or validation columns were found.")

    figure, axes = plt.subplots(len(groups), 1, figsize=(12, 5 * len(groups)), squeeze=False)
    for axis, (title, metric_columns) in zip(axes[:, 0], groups.items()):
        for column in metric_columns:
            values = [float(row[column]) for row in rows]
            axis.plot(epochs, values, label=column)
        axis.set_title(title)
        axis.set_xlabel("Epoch")
        axis.set_ylabel("Value")
        axis.grid(alpha=0.25)
        axis.legend()

    figure.suptitle(f"Training History: {results_path.parent.name}")
    figure.tight_layout()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=180)
    print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
