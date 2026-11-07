from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VIDEO_PATH = PROJECT_ROOT / "simulation" / "videos" / "stage1_test.mp4"


def create_test_video() -> None:
    VIDEO_PATH.parent.mkdir(parents=True, exist_ok=True)
    width, height, fps, frame_count = 640, 360, 24, 48
    writer = cv2.VideoWriter(
        str(VIDEO_PATH),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    if not writer.isOpened():
        raise RuntimeError("OpenCV could not open the MP4 video writer.")

    for index in range(frame_count):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (18, 28, 24)
        x = 80 + index * 9
        cv2.rectangle(frame, (x, 120), (x + 80, 250), (98, 196, 123), -1)
        cv2.putText(
            frame,
            f"WeiZhiXianJue stage 1 | frame {index + 1}",
            (24, 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (220, 240, 225),
            1,
            cv2.LINE_AA,
        )
        writer.write(frame)

    writer.release()


def main() -> int:
    if not VIDEO_PATH.exists():
        create_test_video()

    capture = cv2.VideoCapture(str(VIDEO_PATH))
    if not capture.isOpened():
        print(f"FAIL: OpenCV could not open {VIDEO_PATH}")
        return 1

    reported_fps = capture.get(cv2.CAP_PROP_FPS)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames = 0
    first_shape = None

    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if first_shape is None:
            first_shape = frame.shape
        frames += 1

    capture.release()

    print(f"OpenCV version: {cv2.__version__}")
    print(f"Video: {VIDEO_PATH}")
    print(f"Reported FPS: {reported_fps:.2f}")
    print(f"Resolution: {width}x{height}")
    print(f"Decoded frames: {frames}")
    print(f"First frame shape: {first_shape}")

    if frames < 1:
        print("FAIL: No frames were decoded.")
        return 1

    print("PASS: OpenCV created and read the local test video.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
