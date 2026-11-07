from __future__ import annotations

import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORK_DIR = PROJECT_ROOT / "work" / "downloads" / "openimages_labcoat"
CSV_DIR = WORK_DIR / "annotations"
DOWNLOAD_DIR = WORK_DIR / "downloaded"
SELECTED_DIR = WORK_DIR / "selected"

SPLITS = {
    "validation": {
        "annotations": "https://storage.googleapis.com/openimages/v5/validation-annotations-bbox.csv",
        "image": "https://open-images-dataset.s3.amazonaws.com/validation/{image_id}.jpg",
    },
    "test": {
        "annotations": "https://storage.googleapis.com/openimages/v5/test-annotations-bbox.csv",
        "image": "https://open-images-dataset.s3.amazonaws.com/test/{image_id}.jpg",
    },
}

COAT_LABEL = "/m/01xygc"
PERSON_LABEL = "/m/01g317"


def download_file(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 0:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=(20, 120), verify=False) as response:
        response.raise_for_status()
        temporary = destination.with_suffix(destination.suffix + ".part")
        with temporary.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)
        temporary.replace(destination)


def load_candidates(scan_limit: int) -> list[dict[str, Any]]:
    rows: list[pd.DataFrame] = []
    for split, config in SPLITS.items():
        csv_path = CSV_DIR / f"{split}-annotations-bbox.csv"
        if not csv_path.exists():
            print(f"Downloading annotations: {split}")
            download_file(config["annotations"], csv_path)
        frame = pd.read_csv(
            csv_path,
            usecols=["ImageID", "LabelName", "Confidence", "XMin", "XMax", "YMin", "YMax"],
        )
        frame = frame[frame["LabelName"].isin([COAT_LABEL, PERSON_LABEL])]
        frame = frame[frame["Confidence"] == 1]
        frame["split"] = split
        rows.append(frame)

    data = pd.concat(rows, ignore_index=True)
    candidates: list[dict[str, Any]] = []
    for (split, image_id), group in data.groupby(["split", "ImageID"], sort=True):
        coat_count = int((group["LabelName"] == COAT_LABEL).sum())
        person_count = int((group["LabelName"] == PERSON_LABEL).sum())
        if coat_count < 1 or person_count < 1:
            continue
        candidates.append(
            {
                "split": split,
                "image_id": image_id,
                "coat_count": coat_count,
                "person_count": person_count,
            }
        )

    candidates.sort(key=lambda item: (item["split"], item["image_id"]))
    return candidates[:scan_limit]


def download_candidate(candidate: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    split = candidate["split"]
    image_id = candidate["image_id"]
    image_path = DOWNLOAD_DIR / f"{split}_{image_id}.jpg"
    if not image_path.exists():
        download_file(SPLITS[split]["image"].format(image_id=image_id), image_path)
    return candidate, image_path


def read_image(path: Path) -> np.ndarray | None:
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def white_ratio(image: np.ndarray, box: tuple[float, float, float, float]) -> float:
    height, width = image.shape[:2]
    x_min, x_max, y_min, y_max = box
    x1 = max(0, min(width - 1, int(x_min * width)))
    x2 = max(x1 + 1, min(width, int(x_max * width)))
    y1 = max(0, min(height - 1, int(y_min * height)))
    y2 = max(y1 + 1, min(height, int(y_max * height)))
    crop = image[y1:y2, x1:x2]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask = (hsv[:, :, 1] <= 65) & (hsv[:, :, 2] >= 115)
    return float(mask.mean())


def overlap_ratio(
    coat: tuple[float, float, float, float],
    person: tuple[float, float, float, float],
) -> float:
    x1 = max(coat[0], person[0])
    y1 = max(coat[2], person[2])
    x2 = min(coat[1], person[1])
    y2 = min(coat[3], person[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    coat_area = max(1e-9, (coat[1] - coat[0]) * (coat[3] - coat[2]))
    return intersection / coat_area


def convert_candidate(
    candidate: dict[str, Any],
    image_path: Path,
    annotations: pd.DataFrame,
    white_threshold: float,
) -> dict[str, Any] | None:
    image = read_image(image_path)
    if image is None:
        return None

    rows = annotations[
        (annotations["split"] == candidate["split"])
        & (annotations["ImageID"] == candidate["image_id"])
    ]
    coat_boxes = [
        (row.XMin, row.XMax, row.YMin, row.YMax)
        for row in rows[rows["LabelName"] == COAT_LABEL].itertuples()
    ]
    person_boxes = [
        (row.XMin, row.XMax, row.YMin, row.YMax)
        for row in rows[rows["LabelName"] == PERSON_LABEL].itertuples()
    ]

    kept_coats: list[tuple[tuple[float, float, float, float], float]] = []
    for coat in coat_boxes:
        area = (coat[1] - coat[0]) * (coat[3] - coat[2])
        if area < 0.004:
            continue
        if not any(overlap_ratio(coat, person) >= 0.25 for person in person_boxes):
            continue
        ratio = white_ratio(image, coat)
        if ratio >= white_threshold:
            kept_coats.append((coat, ratio))

    if not kept_coats:
        return None

    lines = [f"0 {((p[0] + p[1]) / 2):.6f} {((p[2] + p[3]) / 2):.6f} {(p[1] - p[0]):.6f} {(p[3] - p[2]):.6f}" for p in person_boxes]
    lines.extend(
        f"1 {((c[0] + c[1]) / 2):.6f} {((c[2] + c[3]) / 2):.6f} {(c[1] - c[0]):.6f} {(c[3] - c[2]):.6f}"
        for c, _ in kept_coats
    )

    split = candidate["split"]
    output_name = f"openimages_{candidate['image_id']}"
    target_image = SELECTED_DIR / "images" / split / f"{output_name}.jpg"
    target_label = SELECTED_DIR / "labels" / split / f"{output_name}.txt"
    target_image.parent.mkdir(parents=True, exist_ok=True)
    target_label.parent.mkdir(parents=True, exist_ok=True)
    image_path.replace(target_image)
    target_label.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "image_id": candidate["image_id"],
        "split": split,
        "source_url": SPLITS[split]["image"].format(image_id=candidate["image_id"]),
        "person_boxes": len(person_boxes),
        "lab_coat_boxes": len(kept_coats),
        "mean_white_ratio": round(sum(ratio for _, ratio in kept_coats) / len(kept_coats), 4),
    }


def make_contact_sheet(records: list[dict[str, Any]], output: Path) -> None:
    selected_images = sorted((SELECTED_DIR / "images").rglob("*.jpg"))
    tiles: list[np.ndarray] = []
    for image_path in selected_images[:16]:
        image = read_image(image_path)
        if image is None:
            continue
        label_path = SELECTED_DIR / "labels" / image_path.parent.name / f"{image_path.stem}.txt"
        if label_path.exists():
            height, width = image.shape[:2]
            for line in label_path.read_text(encoding="utf-8").splitlines():
                class_id, xc, yc, bw, bh = map(float, line.split())
                x1 = int((xc - bw / 2) * width)
                y1 = int((yc - bh / 2) * height)
                x2 = int((xc + bw / 2) * width)
                y2 = int((yc + bh / 2) * height)
                color = (0, 220, 0) if int(class_id) == 0 else (255, 140, 0)
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        tiles.append(cv2.resize(image, (320, 180)))

    while len(tiles) < 16:
        tiles.append(np.zeros((180, 320, 3), dtype=np.uint8))
    sheet = np.vstack([np.hstack(tiles[index:index + 4]) for index in range(0, 16, 4)])
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), sheet)


def main() -> int:
    parser = argparse.ArgumentParser(description="Find white-coat candidates in Open Images.")
    parser.add_argument("--scan-limit", type=int, default=900)
    parser.add_argument("--white-threshold", type=float, default=0.42)
    parser.add_argument("--max-selected", type=int, default=250)
    args = parser.parse_args()

    candidates = load_candidates(args.scan_limit)
    print(f"Coat+Person candidates: {len(candidates)}")

    annotations = pd.concat(
        [
            pd.read_csv(
                CSV_DIR / f"{split}-annotations-bbox.csv",
                usecols=["ImageID", "LabelName", "Confidence", "XMin", "XMax", "YMin", "YMax"],
            ).assign(split=split)
            for split in SPLITS
        ],
        ignore_index=True,
    )
    annotations = annotations[
        annotations["LabelName"].isin([COAT_LABEL, PERSON_LABEL]) & (annotations["Confidence"] == 1)
    ]

    records: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(download_candidate, candidate): candidate for candidate in candidates}
        for future in as_completed(futures):
            try:
                candidate, image_path = future.result()
                record = convert_candidate(candidate, image_path, annotations, args.white_threshold)
                if record:
                    records.append(record)
                    print(
                        f"selected {len(records):3}: {record['image_id']} "
                        f"coats={record['lab_coat_boxes']} white={record['mean_white_ratio']}"
                    )
                if len(records) >= args.max_selected:
                    for pending in futures:
                        pending.cancel()
                    break
            except Exception as exc:
                print(f"WARNING: candidate failed: {exc}")

    manifest_path = WORK_DIR / "manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0].keys()) if records else ["image_id"])
        writer.writeheader()
        writer.writerows(records)

    make_contact_sheet(records, WORK_DIR / "contact_sheet.jpg")
    print(f"Selected: {len(records)}")
    print(f"Manifest: {manifest_path}")
    print(f"Contact sheet: {WORK_DIR / 'contact_sheet.jpg'}")
    return 0 if records else 1


if __name__ == "__main__":
    sys.exit(main())
