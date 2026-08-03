"""Tests for the water-level CLI command."""

import pytest

from ecobiome.cli import main


def test_rectangular_water_level_command(
    capsys: pytest.CaptureFixture[str],
) -> None:
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
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Volume retiré" in output
    assert "60.00 L" in output
    assert "300.00 L" in output


def test_spherical_water_level_command(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "water-level",
            "--shape",
            "spherical",
            "--radius",
            "1.0",
            "--current-height",
            "1.1",
            "--remove",
            "0.1",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Forme                  : spherical" in output
