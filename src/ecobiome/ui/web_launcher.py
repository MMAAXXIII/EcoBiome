"""Launch the canonical EcoBiome Bolt/React frontend and local API."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

from ecobiome.ui.local_api import (
    DEFAULT_API_HOST,
    DEFAULT_API_PORT,
    start_api_server,
    stop_api_server,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5173
FRONTEND_DIRECTORY_ENV = "ECOBIOME_FRONTEND_DIR"

def find_frontend_directory(start: Path | None = None) -> Path:
    override = os.environ.get(FRONTEND_DIRECTORY_ENV)
    if override:
        candidate = Path(override).expanduser().resolve()
        _validate_frontend_directory(candidate)
        return candidate

    origin = (start or Path(__file__)).resolve()
    for root in (origin, *origin.parents):
        candidate = root / "frontend"
        if (candidate / "package.json").is_file() and (candidate / "index.html").is_file():
            return candidate

    raise RuntimeError(
        "EcoBiome frontend not found. "
        f"Set {FRONTEND_DIRECTORY_ENV} to the frontend directory."
    )

def _validate_frontend_directory(directory: Path) -> None:
    if not directory.is_dir():
        raise RuntimeError(f"EcoBiome frontend directory does not exist: {directory}")
    if not (directory / "package.json").is_file():
        raise RuntimeError(f"EcoBiome frontend package.json is missing: {directory / 'package.json'}")
    if not (directory / "index.html").is_file():
        raise RuntimeError(f"EcoBiome frontend index.html is missing: {directory / 'index.html'}")

def _find_npm() -> str:
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if npm is None:
        raise RuntimeError("npm was not found in PATH. Install Node.js before launching EcoBiome.")
    return npm

def _choose_port(host: str, preferred_port: int) -> int:
    for port in range(preferred_port, preferred_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind((host, port))
            except OSError:
                continue
            return port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((host, 0))
        return int(probe.getsockname()[1])

def build_vite_command(
    npm_executable: str,
    *,
    host: str,
    port: int,
) -> list[str]:
    return [
        npm_executable,
        "run",
        "dev",
        "--",
        "--host",
        host,
        "--port",
        str(port),
        "--strictPort",
    ]

def _wait_until_ready(
    url: str,
    process: subprocess.Popen[bytes] | None = None,
    *,
    timeout_seconds: float = 30.0,
) -> None:
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        if process is not None:
            return_code = process.poll()
            if return_code is not None:
                raise RuntimeError(
                    "EcoBiome frontend stopped before becoming ready "
                    f"(exit code {return_code})."
                )

        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                if 200 <= response.status < 500:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)

    raise RuntimeError(
        f"EcoBiome runtime did not become ready within {timeout_seconds:.0f} seconds."
    )

def _stop_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)

def run_web_frontend() -> None:
    frontend_directory = find_frontend_directory()
    npm_executable = _find_npm()
    frontend_port = _choose_port(DEFAULT_HOST, DEFAULT_PORT)
    frontend_url = f"http://{DEFAULT_HOST}:{frontend_port}/"
    api_url = f"http://{DEFAULT_API_HOST}:{DEFAULT_API_PORT}/api/health"
    command = build_vite_command(
        npm_executable,
        host=DEFAULT_HOST,
        port=frontend_port,
    )

    print("=" * 64)
    print("EcoBiome - integrated local runtime")
    print(f"Frontend : {frontend_directory}")
    print(f"UI URL   : {frontend_url}")
    print(f"API URL  : {api_url}")
    print("=" * 64)
    print("Starting the EcoBiome local API and Bolt frontend...")
    print("Press Ctrl+C in this console to stop EcoBiome.")
    print()

    api_server = None
    api_thread = None
    process = None

    try:
        api_server, api_thread, workspace_path = start_api_server()
        _wait_until_ready(api_url, timeout_seconds=10.0)
        print(f"Workspace : {workspace_path}")
        print("Data mode : " + ("DEMO" if api_server.demo_data else "WORKSPACE"))

        process = subprocess.Popen(command, cwd=frontend_directory)
        _wait_until_ready(frontend_url, process)

        print(f"EcoBiome is ready: {frontend_url}")
        webbrowser.open(frontend_url, new=2)

        return_code = process.wait()
        if return_code != 0:
            raise RuntimeError(f"EcoBiome frontend exited with code {return_code}.")
    except KeyboardInterrupt:
        print()
        print("Stopping EcoBiome...")
    finally:
        if process is not None:
            _stop_process_tree(process)
        if api_server is not None and api_thread is not None:
            stop_api_server(api_server, api_thread)
