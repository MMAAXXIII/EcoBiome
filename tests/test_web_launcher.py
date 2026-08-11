"""Regression tests for the canonical EcoBiome web launcher."""

from __future__ import annotations

from pathlib import Path

import pytest

from ecobiome import app
from ecobiome.ui import web_launcher


def test_app_run_delegates_to_canonical_web_frontend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        app,
        "run_web_frontend",
        lambda: calls.append("web"),
    )

    app.run()

    assert calls == ["web"]


def test_find_frontend_directory_from_nested_source_tree(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    frontend = repository / "frontend"
    nested = repository / "src" / "ecobiome" / "ui" / "web_launcher.py"

    frontend.mkdir(parents=True)
    nested.parent.mkdir(parents=True)
    (frontend / "package.json").write_text("{}", encoding="utf-8")
    (frontend / "index.html").write_text("<html></html>", encoding="utf-8")
    nested.write_text("", encoding="utf-8")

    assert web_launcher.find_frontend_directory(nested) == frontend


def test_frontend_directory_environment_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text("{}", encoding="utf-8")
    (frontend / "index.html").write_text("<html></html>", encoding="utf-8")

    monkeypatch.setenv(
        web_launcher.FRONTEND_DIRECTORY_ENV,
        str(frontend),
    )

    assert web_launcher.find_frontend_directory() == frontend.resolve()


def test_build_vite_command_is_explicit_and_strict() -> None:
    command = web_launcher.build_vite_command(
        "npm.cmd",
        host="127.0.0.1",
        port=5173,
    )

    assert command == [
        "npm.cmd",
        "run",
        "dev",
        "--",
        "--host",
        "127.0.0.1",
        "--port",
        "5173",
        "--strictPort",
    ]
