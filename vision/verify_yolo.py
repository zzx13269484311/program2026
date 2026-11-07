from __future__ import annotations

import sys
from pathlib import Path

import requests
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_URL = "https://ultralytics.com/images/bus.jpg"
SAMPLE_PATH = PROJECT_ROOT / "simulation" / "evidence" / "stage1_bus.jpg"
OUTPUT_DIR = PROJECT_ROOT / "simulation" / "evidence"
WEIGHTS_DIR = PROJECT_ROOT / "vision" / "weights"


def ensure_sample_image() -> Path:
    if not SAMPLE_PATH.exists():
        SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading sample image: {SAMPLE_URL}")
        response = requests.get(SAMPLE_URL, timeout=60, allow_redirects=True)
        response.raise_for_status()
        SAMPLE_PATH.write_bytes(response.content)
    return SAMPLE_PATH


def main() -> int:
    sample = ensure_sample_image()
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading yolo11n.pt (Ultralytics may download the weights on first use)...")
    model = YOLO(str(WEIGHTS_DIR / "yolo11n.pt"))

    results = model.predict(
        source=str(sample),
        conf=0.25,
        save=True,
        project=str(OUTPUT_DIR),
        name="yolo_stage1",
        exist_ok=True,
        verbose=False,
    )

    if not results:
        print("FAIL: Ultralytics returned no result object.")
        return 1

    result = results[0]
    box_count = len(result.boxes) if result.boxes is not None else 0
    names = result.names
    labels = [
        names[int(class_id)]
        for class_id in result.boxes.cls.tolist()
    ] if box_count else []

    print(f"PASS: YOLO11n inference completed with {box_count} detection(s).")
    print(f"Detected classes: {labels}")
    print(f"Annotated image: {OUTPUT_DIR / 'yolo_stage1' / sample.name}")

    if box_count < 1:
        print("FAIL: The sample image produced zero detections.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
