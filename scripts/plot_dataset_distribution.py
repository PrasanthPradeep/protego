from collections import Counter
from pathlib import Path
import argparse

import matplotlib.pyplot as plt
import yaml


SPLITS = ("train", "valid", "test")


def count_classes(dataset: Path, split: str, names: list[str]) -> list[int]:
    counts = Counter()
    for label_path in (dataset / split / "labels").glob("*.txt"):
        for line in label_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                counts[int(line.split()[0])] += 1
    return [counts[index] for index in range(len(names))]


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot YOLO dataset class counts.")
    parser.add_argument(
        "dataset",
        nargs="?",
        default="Construction Site Safety.v27-yolov8s.yolo26",
        help="Dataset directory containing data.yaml and split folders.",
    )
    parser.add_argument(
        "--output",
        default="assets/dataset_class_distribution.png",
        help="Path for the generated PNG graph.",
    )
    arguments = parser.parse_args()
    dataset = Path(arguments.dataset)
    output = Path(arguments.output)
    data = yaml.safe_load((dataset / "data.yaml").read_text(encoding="utf-8"))
    names = data["names"]
    values = {split: count_classes(dataset, split, names) for split in SPLITS}

    figure, axis = plt.subplots(figsize=(13, 7))
    positions = list(range(len(names)))
    width = 0.25
    for offset, split in enumerate(SPLITS):
        axis.bar(
            [position + (offset - 1) * width for position in positions],
            values[split],
            width,
            label=split,
        )

    axis.set_title("Construction Site Safety v27: Class Distribution")
    axis.set_xlabel("Class")
    axis.set_ylabel("Annotated objects")
    axis.set_xticks(positions)
    axis.set_xticklabels(names, rotation=35, ha="right")
    axis.grid(axis="y", alpha=0.25)
    axis.legend(title="Split")
    figure.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180)
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
