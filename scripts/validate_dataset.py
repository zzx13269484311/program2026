from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_YAML = PROJECT_ROOT / "vision" / "datasets" / "weizhixianjue" / "data.yaml"
EXPECTED_NAMES = ["person", "lab_coat", "goggles", "obstacle", "smoke", "fire"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SPLITS = ("train", "val", "test")


@dataclass(frozen=True)
class Issue:
    severity: str
    split: str
    file: str
    message: str


def load_config(data_yaml: Path) -> tuple[Path, list[str]]:
    with data_yaml.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("data.yaml must contain a mapping")

    names = config.get("names")
    if isinstance(names, dict):
        names = [names[index] for index in sorted(names)]
    if names != EXPECTED_NAMES:
        raise ValueError(f"Expected six classes {EXPECTED_NAMES!r}, got {names!r}")

    root = Path(config.get("path", "."))
    if not root.is_absolute():
        root = (PROJECT_ROOT / root).resolve()

    for split in SPLITS:
        if split not in config:
            raise ValueError(f"data.yaml is missing split: {split}")

    return root, names


def image_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode_image(path: Path) -> tuple[int, int] | None:
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        return None
    height, width = image.shape[:2]
    return width, height


def validate_label_file(
    label_path: Path,
    split: str,
    names: list[str],
    class_counts: Counter[str],
    issues: list[Issue],
) -> int:
    box_count = 0
    seen_rows: set[tuple[str, ...]] = set()

    for line_number, raw_line in enumerate(
        label_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        stripped = raw_line.strip()
        if not stripped:
            continue

        parts = stripped.split()
        if len(parts) != 5:
            issues.append(
                Issue("error", split, str(label_path), f"line {line_number}: expected 5 values, got {len(parts)}")
            )
            continue

        try:
            class_id = int(parts[0])
            x_center, y_center, width, height = map(float, parts[1:])
        except ValueError:
            issues.append(
                Issue("error", split, str(label_path), f"line {line_number}: contains a non-numeric value")
            )
            continue

        if not 0 <= class_id < len(names):
            issues.append(
                Issue("error", split, str(label_path), f"line {line_number}: invalid class id {class_id}")
            )
            continue

        values_valid = all(0.0 <= value <= 1.0 for value in (x_center, y_center, width, height))
        if not values_valid or width <= 0.0 or height <= 0.0:
            issues.append(
                Issue("error", split, str(label_path), f"line {line_number}: invalid normalized box")
            )
            continue

        epsilon = 1e-6
        if (
            x_center - width / 2 < -epsilon
            or x_center + width / 2 > 1 + epsilon
            or y_center - height / 2 < -epsilon
            or y_center + height / 2 > 1 + epsilon
        ):
            issues.append(
                Issue("error", split, str(label_path), f"line {line_number}: box extends outside image bounds")
            )
            continue

        normalized_row = tuple(parts)
        if normalized_row in seen_rows:
            issues.append(
                Issue("warning", split, str(label_path), f"line {line_number}: duplicate box row")
            )
        seen_rows.add(normalized_row)
        class_counts[names[class_id]] += 1
        box_count += 1

    return box_count


def validate_split(
    dataset_root: Path,
    split: str,
    split_value: str,
    names: list[str],
    issues: list[Issue],
) -> tuple[dict[str, Any], dict[str, str]]:
    images_dir = (dataset_root / split_value).resolve()
    labels_dir = dataset_root / "labels" / split
    class_counts: Counter[str] = Counter()
    split_info: dict[str, Any] = {
        "images": 0,
        "labels": 0,
        "boxes": 0,
        "class_counts": {},
    }
    image_hashes: dict[str, str] = {}

    if not images_dir.is_dir():
        issues.append(Issue("error", split, str(images_dir), "image directory is missing"))
        return split_info, image_hashes
    if not labels_dir.is_dir():
        issues.append(Issue("error", split, str(labels_dir), "label directory is missing"))

    images = sorted(
        path for path in images_dir.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )

    for image_path in images:
        split_info["images"] += 1
        relative = image_path.relative_to(images_dir)
        label_path = labels_dir / relative.with_suffix(".txt")

        dimensions = decode_image(image_path)
        if dimensions is None:
            issues.append(Issue("error", split, str(image_path), "image cannot be decoded"))
        else:
            split_info.setdefault("resolutions", Counter())[f"{dimensions[0]}x{dimensions[1]}"] += 1

        image_hashes[str(image_path)] = image_hash(image_path)

        if not label_path.exists():
            issues.append(Issue("error", split, str(image_path), f"missing label file: {label_path}"))
            continue

        split_info["labels"] += 1
        split_info["boxes"] += validate_label_file(
            label_path,
            split,
            names,
            class_counts,
            issues,
        )

    if labels_dir.is_dir():
        image_stems = {image_path.relative_to(images_dir).with_suffix("") for image_path in images}
        for label_path in labels_dir.rglob("*.txt"):
            relative = label_path.relative_to(labels_dir)
            if relative.with_suffix("") not in image_stems:
                issues.append(Issue("warning", split, str(label_path), "label file has no matching image"))

    split_info["class_counts"] = dict(class_counts)
    if "resolutions" in split_info:
        split_info["resolutions"] = dict(split_info["resolutions"])
    return split_info, image_hashes


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the six-class YOLO dataset.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_YAML, help="Path to data.yaml")
    args = parser.parse_args()

    data_yaml = args.data.resolve()
    if not data_yaml.exists():
        print(f"FAIL: data.yaml not found: {data_yaml}")
        return 1

    try:
        dataset_root, names = load_config(data_yaml)
    except Exception as exc:
        print(f"FAIL: invalid dataset configuration: {exc}")
        return 1

    with data_yaml.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    issues: list[Issue] = []
    split_reports: dict[str, Any] = {}
    all_hashes: dict[str, str] = {}

    for split in SPLITS:
        split_info, hashes = validate_split(
            dataset_root,
            split,
            config[split],
            names,
            issues,
        )
        split_reports[split] = split_info
        all_hashes.update(hashes)

    by_hash: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for image_path, digest in all_hashes.items():
        split = next(
            split
            for split in SPLITS
            if Path(image_path).is_relative_to((dataset_root / config[split]).resolve())
        )
        by_hash[digest].append((split, image_path))

    for digest, entries in by_hash.items():
        if len(entries) < 2:
            continue
        splits = {split for split, _ in entries}
        severity = "error" if len(splits) > 1 else "warning"
        message = "identical image appears in multiple splits" if severity == "error" else "duplicate image"
        for split, image_path in entries:
            issues.append(Issue(severity, split, image_path, f"{message}: sha256={digest}"))

    total_images = sum(split["images"] for split in split_reports.values())
    if total_images == 0:
        issues.append(Issue("error", "all", str(dataset_root), "no images found"))

    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_root": str(dataset_root),
        "classes": names,
        "totals": {
            "images": total_images,
            "boxes": sum(split["boxes"] for split in split_reports.values()),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "splits": split_reports,
        "issues": [asdict(issue) for issue in issues],
        "status": "pass" if not errors else "fail",
    }

    reports_dir = dataset_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "validation.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Dataset: {dataset_root}")
    for split, split_info in split_reports.items():
        print(
            f"{split:5} images={split_info['images']:4} "
            f"labels={split_info['labels']:4} boxes={split_info['boxes']:5}"
        )
    print(f"Total images: {total_images}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Report: {report_path}")

    for issue in issues[:20]:
        print(f"{issue.severity.upper():7} [{issue.split}] {issue.file}: {issue.message}")
    if len(issues) > 20:
        print(f"... {len(issues) - 20} more issue(s) in the JSON report.")

    if errors:
        print("FAIL: dataset validation found errors.")
        return 1

    print("PASS: dataset validation completed without errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
