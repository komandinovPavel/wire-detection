from pathlib import Path

images = sorted(Path("dataset/train/images").glob("*.jpg"))
labels = sorted(Path("dataset/train/labels").glob("*.txt"))

print(f"Images: {len(images)}, Labels: {len(labels)}")

for img in images:
    lbl = Path("dataset/train/labels") / (img.stem + ".txt")
    if not lbl.exists():
        print(f"Label missing for {img.name}")
