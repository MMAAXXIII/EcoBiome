"""Tests for the central EcoBiome CLI."""

import pytest

from ecobiome.cli import main


def test_explain_command_displays_causal_chain(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "explain",
            "physics.temperature_fluctuation",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "physics.water_volume" in output
    assert "physics.thermal_inertia" in output
    assert "physics.temperature_fluctuation" in output


def test_explain_command_reports_unknown_target(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "explain",
            "biology.unknown",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 2
    assert "No causal chain" in output


def test_cli_without_command_displays_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main([])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "EcoBiome scientific ecosystem platform" in output
