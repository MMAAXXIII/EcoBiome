"""Tests for secure event reconstruction from JSON."""

import json
from datetime import UTC, datetime
from uuid import UUID

import pytest

from ecobiome.core.events import (
    WaterRemovedEvent,
    create_default_event_registry,
    event_to_json,
)


def make_event() -> WaterRemovedEvent:
    """Create one deterministic event."""
    return WaterRemovedEvent(
        event_id=UUID(
            "12345678-1234-5678-1234-567812345678"
        ),
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


def test_json_round_trip_restores_event() -> None:
    original = make_event()
    registry = create_default_event_registry()

    serialized = event_to_json(original)
    restored = registry.create_from_json(serialized)

    assert restored == original
    assert isinstance(restored, WaterRemovedEvent)


def test_invalid_json_is_rejected() -> None:
    registry = create_default_event_registry()

    with pytest.raises(
        ValueError,
        match="Invalid event JSON",
    ):
        registry.create_from_json("{invalid json}")


def test_json_array_is_rejected() -> None:
    registry = create_default_event_registry()

    with pytest.raises(
        TypeError,
        match="must contain a JSON object",
    ):
        registry.create_from_json("[]")


def test_unregistered_json_event_type_is_rejected() -> None:
    registry = create_default_event_registry()

    record = json.loads(event_to_json(make_event()))
    record["event_type"] = "unknown.module.UnknownEvent"

    with pytest.raises(
        ValueError,
        match="Unregistered event type",
    ):
        registry.create_from_json(json.dumps(record))


def test_json_without_payload_is_rejected() -> None:
    registry = create_default_event_registry()

    serialized = json.dumps(
        {
            "schema_version": "0.1",
            "event_type": (
                "ecobiome.core.events.event."
                "WaterRemovedEvent"
            ),
        }
    )

    with pytest.raises(
        TypeError,
        match="'payload' must be an object",
    ):
        registry.create_from_json(serialized)
