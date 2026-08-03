"""Tests for generic event serialization."""

import json
from datetime import UTC, datetime
from uuid import UUID

from ecobiome.core.events import (
    WaterRemovedEvent,
    event_to_json,
    event_to_record,
    event_type_name,
)


def make_event() -> WaterRemovedEvent:
    """Create one deterministic event."""
    return WaterRemovedEvent(
        event_id=UUID("12345678-1234-5678-1234-567812345678"),
        occurred_at=datetime(
            2026,
            8,
            1,
            12,
            30,
            tzinfo=UTC,
        ),
        water_body_name="Aquarium principal",
        removed_height_m=0.10,
        removed_volume_liters=60.0,
        remaining_volume_liters=300.0,
        cause="user_removal",
    )


def test_event_type_name_is_fully_qualified() -> None:
    event = make_event()

    type_name = event_type_name(event)

    assert type_name.endswith(
        ".WaterRemovedEvent"
    )
    assert type_name.startswith(
        "ecobiome.core.events.event."
    )


def test_event_is_converted_to_versioned_record() -> None:
    record = event_to_record(make_event())

    assert record["schema_version"] == "0.1"
    assert record["event_type"] == (
        "ecobiome.core.events.event."
        "WaterRemovedEvent"
    )

    payload = record["payload"]

    assert isinstance(payload, dict)
    assert payload["water_body_name"] == "Aquarium principal"
    assert payload["removed_volume_liters"] == 60.0
    assert payload["event_id"] == (
        "12345678-1234-5678-1234-567812345678"
    )
    assert payload["occurred_at"] == (
        "2026-08-01T12:30:00+00:00"
    )


def test_event_serializes_to_valid_json() -> None:
    serialized = event_to_json(
        make_event(),
        indent=2,
    )

    record = json.loads(serialized)

    assert record["schema_version"] == "0.1"
    assert record["payload"]["cause"] == "user_removal"
    assert record["payload"]["remaining_volume_liters"] == 300.0


def test_serialization_is_deterministic() -> None:
    event = make_event()

    first = event_to_json(event)
    second = event_to_json(event)

    assert first == second
