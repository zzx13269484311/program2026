from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Iterator

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=3) as response:
        assert response.status == 200
        return json.loads(response.read().decode("utf-8"))


@pytest.fixture(scope="module")
def api_base_url() -> Iterator[str]:
    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise RuntimeError(f"Uvicorn exited during startup:\n{output}")
            try:
                get_json(f"{base_url}/api/health")
                break
            except (OSError, AssertionError, json.JSONDecodeError):
                time.sleep(0.2)
        else:
            raise RuntimeError("Uvicorn did not become ready within 20 seconds.")

        yield base_url
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def test_root(api_base_url: str) -> None:
    payload = get_json(f"{api_base_url}/")
    assert payload["service"] == "危知先觉"
    assert payload["version"] == "0.1.0"


def test_health(api_base_url: str) -> None:
    payload = get_json(f"{api_base_url}/api/health")
    assert payload["status"] == "ok"
    assert payload["version"] == "0.1.0"
    assert payload["timestamp"]
