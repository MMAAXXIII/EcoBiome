"""Tests for the water-level CLI event history."""

import json
from pathlib import Path

import pytest

from ecobiome.cli import main


def test_water_level_command_records_event(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    history_path = tmp_path / "events.jsonl"

    exit_code = main(
        [
            "water-level",
            "--name",
            "Aquarium principal",
            "--shape",
            "rectangular",
            "--length",
            "1.2",
            "--width",
            "0.5",
            "--container-height",
            "0.6",
            "--current-height",
            "0.6",
            "--remove",
            "0.1",
            "--cause",
            "user_removal",
            "--note",
            "Entretien du bac.",
            "--event-log",
            str(history_path),
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert history_path.is_file()
    assert "Identifiant événement" in output
    assert "Entretien du bac." in output

    record = json.loads(
        history_path.read_text(encoding="utf-8").splitlines()[0]
    )

    assert record["event_type"] == "user_removal"
    assert record["remaining_volume_m3"] == pytest.approx(0.30)
