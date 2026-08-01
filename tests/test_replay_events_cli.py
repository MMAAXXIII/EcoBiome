"""Tests for the replay-events command."""

from pathlib import Path

import pytest

from ecobiome.cli import main
from ecobiome.core.events import (
    JsonLinesEventStore,
    WaterRemovedEvent,
    create_default_event_registry,
)
from ecobiome.world.persistence import (
    load_world_state,
    save_world_state,
)
from ecobiome.world.water_geometry import RectangularGeometry
from ecobiome.world.water_state import WaterBodyState
from ecobiome.world.world_state import WorldState


def create_initial_world(path: Path) -> None:
    """Create and save one full rectangular aquarium."""
    world = WorldState()

    world.add_water_body(
        WaterBodyState(
            name="Aquarium principal",
            geometry=RectangularGeometry(
                length_m=1.20,
                width_m=0.50,
                height_m=0.60,
            ),
            water_height_m=0.60,
        )
    )

    save_world_state(world, path)


def create_event_history(path: Path) -> None:
    """Create two compatible water-removal events."""
    store = JsonLinesEventStore(
        path=path,
        registry=create_default_event_registry(),
    )

    store.append(
        WaterRemovedEvent(
            water_body_name="Aquarium principal",
            removed_height_m=0.10,
            removed_volume_liters=60.0,
            remaining_volume_liters=300.0,
        )
    )

    store.append(
        WaterRemovedEvent(
            water_body_name="Aquarium principal",
            removed_height_m=0.05,
            removed_volume_liters=30.0,
            remaining_volume_liters=270.0,
        )
    )


def test_replay_events_command_reconstructs_world(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    initial_path = tmp_path / "initial.json"
    events_path = tmp_path / "events.jsonl"
    output_path = tmp_path / "current.json"

    create_initial_world(initial_path)
    create_event_history(events_path)

    exit_code = main(
        [
            "replay-events",
            "--world",
            str(initial_path),
            "--events",
            str(events_path),
            "--output",
            str(output_path),
        ]
    )

    output = capsys.readouterr().out
    restored = load_world_state(output_path)
    aquarium = restored.get_water_body("Aquarium principal")

    assert exit_code == 0
    assert output_path.is_file()
    assert "Événements chargés    : 2" in output
    assert "Volume                : 270.00 L" in output
    assert aquarium.water_height_m == pytest.approx(0.45)
    assert aquarium.volume_liters == pytest.approx(270.0)


def test_replay_events_command_accepts_empty_history(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    initial_path = tmp_path / "initial.json"
    events_path = tmp_path / "empty.jsonl"
    output_path = tmp_path / "current.json"

    create_initial_world(initial_path)
    events_path.write_text("", encoding="utf-8")

    exit_code = main(
        [
            "replay-events",
            "--world",
            str(initial_path),
            "--events",
            str(events_path),
            "--output",
            str(output_path),
        ]
    )

    output = capsys.readouterr().out
    restored = load_world_state(output_path)
    aquarium = restored.get_water_body("Aquarium principal")

    assert exit_code == 0
    assert "Événements chargés    : 0" in output
    assert aquarium.volume_liters == pytest.approx(360.0)
