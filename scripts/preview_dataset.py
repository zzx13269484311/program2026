from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = PROJECT_ROOT / "vision" / "datasets" / "weizhixianjue"
CLASS_NAMES = ["person", "lab_coat", "goggles", "obstacle", "smoke", "fire"]
COLORS = [
    (80, 220, 100),
    (255, 170, 60),
    (80, 200, 255),
    (220, 120, 255),
    (180, 180, 180),
    (60, 80, 255),
]


def read_image(path: Path) -> np.ndarray | None:
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def draw_labels(image: np.ndarray, label_path: Path) -> np.ndarray:
    height, width = image.shape[:2]
    if not label_path.exists():
        return image
    for line in label_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue
        class_id, xc, yc, bw, bh = map(float, parts)
        x1 = int((xc - bw / 2) * width)
        y1 = int((yc - bh / 2) * height)
        x2 = int((xc + bw / 2) * width)
        y2 = int((yc + bh / 2) * height)
        color = COLORS[int(class_id)]
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            image,
            CLASS_NAMES[int(class_id)],
            (x1, max(16, y1 - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )
    return image


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a visual dataset preview sheet.")
    parser.add_argument("--split", choices=["train", "val", "test"], default="train")
    parser.add_argument("--count", type=int, default=16)
    parser.add_argument("--class-id", type=int, choices=range(len(CLASS_NAMES)), default=None)
    args = parser.parse_args()

    images_dir = DATASET_ROOT / "images" / args.split
    labels_dir = DATASET_ROOT / "labels" / args.split
    images = sorted(images_dir.glob("*.jpg"))
    if args.class_id is not None:
        images = [
            image
            for image in images
            if any(
                int(line.split()[0]) == args.class_id
                for line in (labels_dir / f"{image.stem}.txt").read_text(encoding="utf-8").splitlines()
                if line.split()
            )
        ]
    if not images:
        print(f"FAIL: no images in {images_dir}")
        return 1

    random.Random(42).shuffle(images)
    grid_size = math.ceil(math.sqrt(args.count))
    tiles: list[np.ndarray] = []
    for image_path in images[: args.count]:
        image = read_image(image_path)
        if image is None:
            continue
        image = draw_labels(image, labels_dir / f"{image_path.stem}.txt")
        tiles.append(cv2.resize(image, (320, 180)))

    while len(tiles) < grid_size * grid_size:
        tiles.append(np.zeros((180, 320, 3), dtype=np.uint8))
    rows = [
        np.hstack(tiles[index:index + grid_size])
        for index in range(0, grid_size * grid_size, grid_size)
    ]
    sheet = np.vstack(rows)
    suffix = f"_class_{args.class_id}" if args.class_id is not None else ""
    output = DATASET_ROOT / "reports" / f"preview_{args.split}{suffix}.jpg"
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), sheet)
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
