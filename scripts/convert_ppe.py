from __future__ import annotations

import csv
import random
import shutil
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "work" / "datasets" / "ppe_v1"
TARGET_ROOT = PROJECT_ROOT / "vision" / "datasets" / "weizhixianjue"
SOURCE_SPLITS = {"train": "train", "valid": "val", "test": "test"}
TARGET_COUNTS = {"train": 2500, "val": 450, "test": 450}
SOURCE_NAMES = ["boots", "gloves", "goggles", "helmet", "person", "vest"]
CLASS_MAP = {2: 2, 4: 0}
TARGET_NAMES = ["person", "lab_coat", "goggles", "obstacle", "smoke", "fire"]


def parse_label(path: Path) -> list[tuple[int, str]]:
    mapped: list[tuple[int, str]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        class_id = int(float(parts[0]))
        if class_id not in CLASS_MAP:
            continue

        coordinates = [float(value) for value in parts[1:]]
        if len(coordinates) == 4:
            x_center, y_center, width, height = coordinates
        elif len(coordinates) % 2 == 0:
            xs = coordinates[0::2]
            ys = coordinates[1::2]
            x_min, x_max = max(0.0, min(xs)), min(1.0, max(xs))
            y_min, y_max = max(0.0, min(ys)), min(1.0, max(ys))
            width, height = x_max - x_min, y_max - y_min
            x_center, y_center = (x_min + x_max) / 2, (y_min + y_max) / 2
        else:
            continue

        if width <= 0 or height <= 0:
            continue
        mapped.append(
            (
                CLASS_MAP[class_id],
                f"{x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}",
            )
        )
    return mapped


def main() -> int:
    if not SOURCE_ROOT.is_dir():
        print(f"FAIL: PPE source not found: {SOURCE_ROOT}")
        return 1

    rng = random.Random(42)
    manifest_rows: list[dict[str, str]] = []
    total_stats: dict[str, Counter[str]] = {}

    for split in TARGET_COUNTS:
        for directory in (
            TARGET_ROOT / "images" / split,
            TARGET_ROOT / "labels" / split,
        ):
            for path in directory.glob("ppe_*"):
                path.unlink()

    for source_split, target_split in SOURCE_SPLITS.items():
        images_dir = SOURCE_ROOT / source_split / "images"
        labels_dir = SOURCE_ROOT / source_split / "labels"
        if not images_dir.is_dir() or not labels_dir.is_dir():
            print(f"FAIL: missing split directory: {source_split}")
            return 1

        items: list[tuple[Path, Path, list[tuple[int, str]], bool, bool]] = []
        for image_path in sorted(images_dir.iterdir()):
            if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue
            label_path = labels_dir / f"{image_path.stem}.txt"
            if not label_path.exists():
                continue
            mapped = parse_label(label_path)
            has_person = any(class_id == 0 for class_id, _ in mapped)
            has_goggles = any(class_id == 2 for class_id, _ in mapped)
            if mapped:
                items.append((image_path, label_path, mapped, has_person, has_goggles))

        rng.shuffle(items)
        selected = [item for item in items if item[3]]
        if len(selected) < TARGET_COUNTS[target_split]:
            selected_ids = {item[0].name for item in selected}
            selected.extend(
                item
                for item in items
                if item[0].name not in selected_ids and item[4]
            )
        selected = selected[: TARGET_COUNTS[target_split]]

        stats: Counter[str] = Counter()
        for image_path, label_path, mapped, _, _ in selected:
            target_name = f"ppe_{target_split}_{image_path.stem}"
            target_image = TARGET_ROOT / "images" / target_split / f"{target_name}{image_path.suffix.lower()}"
            target_label = TARGET_ROOT / "labels" / target_split / f"{target_name}.txt"
            target_image.parent.mkdir(parents=True, exist_ok=True)
            target_label.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image_path, target_image)
            target_label.write_text(
                "\n".join(f"{class_id} {box}" for class_id, box in mapped) + "\n",
                encoding="utf-8",
            )
            for class_id, _ in mapped:
                stats[TARGET_NAMES[class_id]] += 1
            manifest_rows.append(
                {
                    "target_split": target_split,
                    "target_name": target_name,
                    "source": "Kaggle PPE_Detection_V1 / Roboflow ppe-6-classes-ntld9 v6",
                    "source_split": source_split,
                    "source_image": image_path.name,
                    "license": "MIT",
                    "source_url": "https://www.kaggle.com/datasets/beyzakucuk/ppe-detection-v1",
                }
            )

        total_stats[target_split] = stats
        print(f"{target_split:5} selected={len(selected):4} {dict(stats)}")

    manifest_path = PROJECT_ROOT / "work" / "downloads" / "ppe_manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(manifest_rows[0].keys()))
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"Manifest: {manifest_path}")
    print("PASS: PPE conversion complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
