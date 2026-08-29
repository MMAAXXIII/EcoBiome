from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from ecobiome.cli.main import build_parser, main
from ecobiome.cli.nitrogen_demo import nitrogen_demo_command


class _FakeDemonstration:
    canonical_sha256 = "d" * 64

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "test",
            "demo_id": "fake-demo",
            "artifact_sha256": self.canonical_sha256,
        }

    def render_markdown(self) -> str:
        return "# Fake nitrogen demo\n\nNo kinetics."


def test_parser_registers_nitrogen_demo() -> None:
    args = build_parser().parse_args(
        [
            "nitrogen-demo",
            "--scientific-foundation",
            "foundation.sqlite3",
        ]
    )
    assert args.command == "nitrogen-demo"
    assert args.scientific_foundation == Path("foundation.sqlite3")
    assert args.format == "markdown"
    assert args.output is None


def test_nitrogen_demo_writes_markdown_file(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "ecobiome.cli.nitrogen_demo."
        "build_frozen_g7a_nitrogen_vertical_demonstration_v1",
        lambda _path: _FakeDemonstration(),
    )
    output = tmp_path / "demo.md"
    args = SimpleNamespace(
        scientific_foundation=Path("unused.sqlite3"),
        format="markdown",
        output=output,
    )
    assert nitrogen_demo_command(args) == 0
    assert output.read_text(encoding="utf-8") == (
        "# Fake nitrogen demo\n\nNo kinetics.\n"
    )


def test_nitrogen_demo_writes_pretty_json_file(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "ecobiome.cli.nitrogen_demo."
        "build_frozen_g7a_nitrogen_vertical_demonstration_v1",
        lambda _path: _FakeDemonstration(),
    )
    output = tmp_path / "demo.json"
    args = SimpleNamespace(
        scientific_foundation=Path("unused.sqlite3"),
        format="json",
        output=output,
    )
    assert nitrogen_demo_command(args) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["demo_id"] == "fake-demo"
    assert payload["artifact_sha256"] == "d" * 64


def test_main_dispatches_nitrogen_demo(
    monkeypatch: Any,
) -> None:
    observed: dict[str, object] = {}

    def fake_command(args: Any) -> int:
        observed["format"] = args.format
        observed["database"] = args.scientific_foundation
        return 17

    monkeypatch.setattr(
        "ecobiome.cli.nitrogen_demo.nitrogen_demo_command",
        fake_command,
    )
    result = main(
        [
            "nitrogen-demo",
            "--scientific-foundation",
            "foundation.sqlite3",
            "--format",
            "json",
        ]
    )
    assert result == 17
    assert observed == {
        "format": "json",
        "database": Path("foundation.sqlite3"),
    }
