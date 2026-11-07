from __future__ import annotations

import importlib.metadata
import json
import platform
import sys
from typing import Any


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> int:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "packages": {},
        "cuda": {},
    }

    for package in ("torch", "torchvision", "ultralytics", "opencv-python", "fastapi", "uvicorn"):
        report["packages"][package] = package_version(package)

    try:
        import torch
    except Exception as exc:
        report["cuda"] = {"status": "fail", "error": f"torch import failed: {exc}"}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    report["cuda"]["torch_version"] = torch.__version__
    report["cuda"]["torch_cuda_build"] = torch.version.cuda
    report["cuda"]["available"] = torch.cuda.is_available()
    report["cuda"]["device_count"] = torch.cuda.device_count()

    if not torch.cuda.is_available():
        report["cuda"]["status"] = "fail"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print("FAIL: CUDA is not available to PyTorch.")
        return 1

    device = torch.device("cuda:0")
    report["cuda"]["device_name"] = torch.cuda.get_device_name(device)
    report["cuda"]["capability"] = ".".join(map(str, torch.cuda.get_device_capability(device)))

    left = torch.rand((512, 512), device=device)
    right = torch.rand((512, 512), device=device)
    result = left @ right
    torch.cuda.synchronize()

    report["cuda"]["matmul_shape"] = list(result.shape)
    report["cuda"]["matmul_finite"] = bool(torch.isfinite(result).all().item())
    report["cuda"]["allocated_mb"] = round(torch.cuda.memory_allocated(device) / 1024**2, 1)
    report["cuda"]["status"] = "pass" if report["cuda"]["matmul_finite"] else "fail"

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if report["cuda"]["status"] != "pass":
        print("FAIL: GPU matrix multiplication produced invalid values.")
        return 1

    print("PASS: Python and CUDA-enabled PyTorch are operational.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
