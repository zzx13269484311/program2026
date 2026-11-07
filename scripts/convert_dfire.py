from __future__ import annotations

import csv
import random
import shutil
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "work" / "datasets" / "dfire" / "data"
TARGET_ROOT = PROJECT_ROOT / "vision" / "datasets" / "weizhixianjue"
SOURCE_SPLITS = {"train": "train", "val": "val", "test": "test"}
TARGET_COUNTS = {"train": 1600, "val": 300, "test": 300}
SOURCE_CLASS_MAP = {0: 4, 1: 5}
TARGET_NAMES = ["person", "lab_coat", "goggles", "obstacle", "smoke", "fire"]


def parse_label(path: Path) -> list[tuple[int, str]]:
    mapped: list[tuple[int, str]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue
        class_id = int(float(parts[0]))
        if class_id not in SOURCE_CLASS_MAP:
            continue
        try:
            x_center, y_center, width, height = map(float, parts[1:])
        except ValueError:
            continue

        x1 = max(0.0, min(1.0, x_center - width / 2))
        y1 = max(0.0, min(1.0, y_center - height / 2))
        x2 = max(0.0, min(1.0, x_center + width / 2))
        y2 = max(0.0, min(1.0, y_center + height / 2))
        clipped_width = x2 - x1
        clipped_height = y2 - y1
        if clipped_width <= 0 or clipped_height <= 0:
            continue

        mapped.append(
            (
                SOURCE_CLASS_MAP[class_id],
                f"{(x1 + x2) / 2:.6f} {(y1 + y2) / 2:.6f} {clipped_width:.6f} {clipped_height:.6f}",
            )
        )
    return mapped


def main() -> int:
    if not SOURCE_ROOT.is_dir():
        print(f"FAIL: D-Fire source not found: {SOURCE_ROOT}")
        return 1

    rng = random.Random(42)
    manifest_rows: list[dict[str, str]] = []

    for split in TARGET_COUNTS:
        for directory in (
            TARGET_ROOT / "images" / split,
            TARGET_ROOT / "labels" / split,
        ):
            for path in directory.glob("dfire_*"):
                path.unlink()

    for source_split, target_split in SOURCE_SPLITS.items():
        images_dir = SOURCE_ROOT / source_split / "images"
        labels_dir = SOURCE_ROOT / source_split / "labels"
        if not images_dir.is_dir() or not labels_dir.is_dir():
            print(f"FAIL: missing split directory: {source_split}")
            return 1

        fire_images: list[tuple[Path, Path, list[tuple[int, str]]]] = []
        smoke_images: list[tuple[Path, Path, list[tuple[int, str]]]] = []
        negative_images: list[tuple[Path, Path, list[tuple[int, str]]]] = []

        for image_path in sorted(images_dir.iterdir()):
            if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue
            label_path = labels_dir / f"{image_path.stem}.txt"
            if not label_path.exists():
                continue
            mapped = parse_label(label_path)
            record = (image_path, label_path, mapped)
            classes = {class_id for class_id, _ in mapped}
            if 5 in classes:
                fire_images.append(record)
            if 4 in classes:
                smoke_images.append(record)
            if not mapped:
                negative_images.append(record)

        rng.shuffle(fire_images)
        rng.shuffle(smoke_images)
        rng.shuffle(negative_images)

        target = TARGET_COUNTS[target_split]
        negative_target = max(1, int(target * 0.12))
        selected = negative_images[:negative_target]
        selected_names = {item[0].name for item in selected}
        remaining = target - len(selected)

        fire_target = remaining // 2
        smoke_target = remaining - fire_target
        for record in fire_images:
            if len(selected) >= negative_target + fire_target:
                break
            if record[0].name not in selected_names:
                selected.append(record)
                selected_names.add(record[0].name)
        for record in smoke_images:
            if len(selected) >= target:
                break
            if record[0].name not in selected_names:
                selected.append(record)
                selected_names.add(record[0].name)
        for record in fire_images + smoke_images:
            if len(selected) >= target:
                break
            if record[0].name not in selected_names:
                selected.append(record)
                selected_names.add(record[0].name)

        stats: Counter[str] = Counter()
        for image_path, label_path, mapped in selected:
            target_name = f"dfire_{target_split}_{image_path.stem}"
            target_image = TARGET_ROOT / "images" / target_split / f"{target_name}{image_path.suffix.lower()}"
            target_label = TARGET_ROOT / "labels" / target_split / f"{target_name}.txt"
            target_image.parent.mkdir(parents=True, exist_ok=True)
            target_label.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image_path, target_image)
            target_label.write_text(
                "\n".join(f"{class_id} {box}" for class_id, box in mapped) + ("\n" if mapped else ""),
                encoding="utf-8",
            )
            for class_id, _ in mapped:
                stats[TARGET_NAMES[class_id]] += 1
            if not mapped:
                stats["negative"] += 1
            manifest_rows.append(
                {
                    "target_split": target_split,
                    "target_name": target_name,
                    "source": "D-Fire via Kaggle smoke-fire-detection-yolo",
                    "source_split": source_split,
                    "source_image": image_path.name,
                    "license": "CC0 metadata; original D-Fire images retain source terms",
                    "source_url": "https://www.kaggle.com/datasets/sayedgamal99/smoke-fire-detection-yolo",
                }
            )

        print(f"{target_split:5} selected={len(selected):4} {dict(stats)}")

    manifest_path = PROJECT_ROOT / "work" / "downloads" / "dfire_manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(manifest_rows[0].keys()))
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"Manifest: {manifest_path}")
    print("PASS: D-Fire conversion complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
