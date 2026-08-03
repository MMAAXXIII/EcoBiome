"""Tests for water-level environmental events."""

import json
from pathlib import Path

import pytest

from ecobiome.world.events import (
    WaterLevelEventType,
    append_event_jsonl,
    create_water_level_event,
)
from ecobiome.world.water_geometry import RectangularGeometry
from ecobiome.world.water_level import remove_water_height


def make_change():
    """Create a reusable water-level change."""
    geometry = RectangularGeometry(
        length_m=1.20,
        width_m=0.50,
        height_m=0.60,
    )

    return remove_water_height(
        geometry,
        current_height_m=0.60,
        removed_height_m=0.10,
    )


def test_create_traceable_water_level_event() -> None:
    event = create_water_level_event(
        water_body_name="Aquarium principal",
        event_type=WaterLevelEventType.USER_REMOVAL,
        change=make_change(),
        note="Changement d'eau hebdomadaire.",
    )

    assert event.event_type is WaterLevelEventType.USER_REMOVAL
    assert event.removed_volume_liters == pytest.approx(60.0)
    assert event.note == "Changement d'eau hebdomadaire."


def test_append_event_to_jsonl_history(tmp_path: Path) -> None:
    history_path = tmp_path / "water_events.jsonl"

    event = create_water_level_event(
        water_body_name="Bassin extérieur",
        event_type=WaterLevelEventType.EVAPORATION,
        change=make_change(),
    )

    append_event_jsonl(event, history_path)

    lines = history_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 1

    record = json.loads(lines[0])

    assert record["water_body_name"] == "Bassin extérieur"
    assert record["event_type"] == "evaporation"
    assert record["removed_volume_liters"] == pytest.approx(60.0)
