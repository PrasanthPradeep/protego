from pathlib import Path
import shutil


SOURCE = Path("Construction Site Safety.v30-raw-images_latestversion.yolo26")
DESTINATION = Path("Construction Site Safety.v30-10class.yolo26")

SOURCE_NAMES = [
    "Excavator", "Gloves", "Hardhat", "Ladder", "Mask", "NO-Hardhat",
    "NO-Mask", "NO-Safety Vest", "Person", "SUV", "Safety Cone",
    "Safety Vest", "bus", "dump truck", "fire hydrant", "machinery",
    "mini-van", "sedan", "semi", "trailer", "truck", "truck and trailer",
    "van", "vehicle", "wheel loader",
]

TARGET_NAMES = [
    "Hardhat", "Mask", "NO-Hardhat", "NO-Mask", "NO-Safety Vest",
    "Person", "Safety Cone", "Safety Vest", "machinery", "vehicle",
]

TARGET_BY_SOURCE = {
    "Hardhat": "Hardhat", "Mask": "Mask", "NO-Hardhat": "NO-Hardhat",
    "NO-Mask": "NO-Mask", "NO-Safety Vest": "NO-Safety Vest",
    "Person": "Person", "Safety Cone": "Safety Cone",
    "Safety Vest": "Safety Vest", "machinery": "machinery",
    "Excavator": "machinery", "wheel loader": "machinery",
    "SUV": "vehicle", "bus": "vehicle", "dump truck": "vehicle",
    "mini-van": "vehicle", "sedan": "vehicle", "semi": "vehicle",
    "trailer": "vehicle", "truck": "vehicle",
    "truck and trailer": "vehicle", "van": "vehicle", "vehicle": "vehicle",
}


def convert_label(source_label: Path, destination_label: Path, source_to_target: dict[int, int]) -> None:
    converted = []
    for line in source_label.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields:
            continue
        target_id = source_to_target.get(int(fields[0]))
        if target_id is not None:
            converted.append(" ".join([str(target_id), *fields[1:]]))
    destination_label.write_text("\n".join(converted) + ("\n" if converted else ""), encoding="utf-8")


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Dataset not found: {SOURCE}")
    if DESTINATION.exists():
        raise FileExistsError(f"Destination already exists: {DESTINATION}")

    source_to_target = {
        source_id: TARGET_NAMES.index(TARGET_BY_SOURCE[source_name])
        for source_id, source_name in enumerate(SOURCE_NAMES)
        if source_name in TARGET_BY_SOURCE
    }

    for split in ("train", "valid", "test"):
        source_images = SOURCE / split / "images"
        source_labels = SOURCE / split / "labels"
        destination_images = DESTINATION / split / "images"
        destination_labels = DESTINATION / split / "labels"
        destination_images.mkdir(parents=True)
        destination_labels.mkdir(parents=True)

        for image in source_images.iterdir():
            if image.is_file():
                shutil.copy2(image, destination_images / image.name)
        for label in source_labels.glob("*.txt"):
            convert_label(label, destination_labels / label.name, source_to_target)

    data_yaml = """train: ../train/images
val: ../valid/images
test: ../test/images

nc: 10
names: ['Hardhat', 'Mask', 'NO-Hardhat', 'NO-Mask', 'NO-Safety Vest', 'Person', 'Safety Cone', 'Safety Vest', 'machinery', 'vehicle']
"""
    (DESTINATION / "data.yaml").write_text(data_yaml, encoding="utf-8")
    print(f"Created: {DESTINATION}")


if __name__ == "__main__":
    main()