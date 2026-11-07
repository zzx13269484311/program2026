from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = PROJECT_ROOT / "vision" / "datasets" / "weizhixianjue"
DATA_YAML = DATASET_ROOT / "data.yaml"
SPLITS = ("train", "val", "test")
EXPECTED_NAMES = ["person", "lab_coat", "goggles", "obstacle", "smoke", "fire"]


def load_names() -> list[str]:
    with DATA_YAML.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    names = config.get("names")
    if isinstance(names, dict):
        names = [names[index] for index in sorted(names)]
    if names != EXPECTED_NAMES:
        raise ValueError(f"Unexpected class contract: {names!r}")
    return names


def main() -> int:
    if not DATA_YAML.exists():
        print(f"FAIL: missing dataset config: {DATA_YAML}")
        return 1

    try:
        names = load_names()
    except Exception as exc:
        print(f"FAIL: invalid data.yaml: {exc}")
        return 1

    directories = [
        DATASET_ROOT / "raw" / "incoming",
        DATASET_ROOT / "reports",
    ]
    directories.extend(DATASET_ROOT / "images" / split for split in SPLITS)
    directories.extend(DATASET_ROOT / "labels" / split for split in SPLITS)

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    print(f"Dataset root: {DATASET_ROOT}")
    print("Classes:")
    for index, name in enumerate(names):
        print(f"  {index}: {name}")

    print("Created or verified:")
    for directory in directories:
        print(f"  {directory.relative_to(PROJECT_ROOT)}")

    print("\nPASS: dataset structure is ready.")
    print("Next: put source images under raw/incoming, annotate them, then run validate_dataset.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
