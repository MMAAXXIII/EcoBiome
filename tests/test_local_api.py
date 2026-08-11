"""Integration tests for the local EcoBiome runtime API."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

from ecobiome.ui.local_api import start_api_server, stop_api_server


def _get_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=2) as response:
        return json.loads(response.read().decode("utf-8"))


def test_real_workspace_api_bootstraps_empty_project(tmp_path: Path) -> None:
    server, thread, workspace_path = start_api_server(
        tmp_path / "workspace",
        port=0,
        demo_data=False,
    )
    try:
        port = int(server.server_address[1])
        base = f"http://127.0.0.1:{port}/api"

        health = _get_json(f"{base}/health")
        dashboard = _get_json(f"{base}/dashboard")
        water_bodies = _get_json(f"{base}/water-bodies")
        journal = _get_json(f"{base}/journal")
        media = _get_json(f"{base}/media")

        assert health["status"] == "ok"
        assert health["mode"] == "workspace"
        assert workspace_path == (tmp_path / "workspace").resolve()
        assert dashboard["journal_event_count"] == 0
        assert dashboard["media_file_count"] == 0
        assert len(water_bodies) == 1
        assert water_bodies[0]["name"] == "EcoBiome"
        assert journal == []
        assert media == []
    finally:
        stop_api_server(server, thread)


def test_demo_api_populates_all_primary_views(tmp_path: Path) -> None:
    server, thread, _ = start_api_server(
        tmp_path / "demo-workspace",
        port=0,
        demo_data=True,
    )
    try:
        port = int(server.server_address[1])
        base = f"http://127.0.0.1:{port}/api"

        dashboard = _get_json(f"{base}/dashboard")
        water_bodies = _get_json(f"{base}/water-bodies")
        measurements = _get_json(f"{base}/measurements")
        diagnostics = _get_json(f"{base}/diagnostics")
        journal = _get_json(f"{base}/journal")
        media = _get_json(f"{base}/media")
        organisms = _get_json(f"{base}/organisms")

        assert "MODE DEMO" in dashboard["description"]
        assert len(water_bodies) >= 2
        assert len(measurements) >= 8
        assert len(diagnostics) >= 1
        assert len(journal) >= 1
        assert len(media) >= 1
        assert len(organisms) >= 1
    finally:
        stop_api_server(server, thread)
