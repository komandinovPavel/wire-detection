from __future__ import annotations

from pathlib import Path


def find_missing_labels(
    images_dir: Path = Path("dataset/train/images"),
    labels_dir: Path = Path("dataset/train/labels"),
) -> list[Path]:
    images = sorted(images_dir.glob("*.jpg"))
    return [image for image in images if not (labels_dir / f"{image.stem}.txt").exists()]


def main() -> None:
    images_dir = Path("dataset/train/images")
    labels_dir = Path("dataset/train/labels")
    images = sorted(images_dir.glob("*.jpg"))
    labels = sorted(labels_dir.glob("*.txt"))
    missing = find_missing_labels(images_dir, labels_dir)

    print(f"Images: {len(images)}, Labels: {len(labels)}")
    if not missing:
        print("All train images have matching labels.")
        return

    print("Missing labels:")
    for image in missing:
        print(f"- {image.name}")


if __name__ == "__main__":
    main()
