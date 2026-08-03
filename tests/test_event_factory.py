"""Tests for secure event reconstruction."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from ecobiome.core.events import (
    EventTypeRegistry,
    WaterRemovedEvent,
    create_default_event_registry,
    decode_water_removed_event,
    event_to_record,
)


def make_event() -> WaterRemovedEvent:
    """Create one deterministic test event."""
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


def test_record_round_trip_restores_event() -> None:
    original = make_event()
    registry = create_default_event_registry()

    restored = registry.create(event_to_record(original))

    assert restored == original
    assert isinstance(restored, WaterRemovedEvent)


def test_default_registry_authorizes_water_removed_event() -> None:
    registry = create_default_event_registry()

    assert registry.is_registered(WaterRemovedEvent) is True
    assert registry.registered_type_count == 1


def test_unknown_event_type_is_rejected() -> None:
    registry = create_default_event_registry()
    record = event_to_record(make_event())

    record["event_type"] = "malicious.module.ArbitraryClass"

    with pytest.raises(
        ValueError,
        match="Unregistered event type",
    ):
        registry.create(record)


def test_duplicate_registration_is_rejected() -> None:
    registry = EventTypeRegistry()

    registry.register(
        WaterRemovedEvent,
        decode_water_removed_event,
    )

    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        registry.register(
            WaterRemovedEvent,
            decode_water_removed_event,
        )


def test_invalid_schema_version_is_rejected() -> None:
    registry = create_default_event_registry()
    record = event_to_record(make_event())

    record["schema_version"] = "99.0"

    with pytest.raises(
        ValueError,
        match="Unsupported event schema version",
    ):
        registry.create(record)


def test_naive_datetime_is_rejected() -> None:
    registry = create_default_event_registry()
    record = event_to_record(make_event())

    payload = record["payload"]

    assert isinstance(payload, dict)

    payload["occurred_at"] = "2026-08-01T12:30:00"

    with pytest.raises(
        ValueError,
        match="must include a timezone",
    ):
        registry.create(record)


def test_invalid_uuid_is_rejected() -> None:
    registry = create_default_event_registry()
    record = event_to_record(make_event())

    payload = record["payload"]

    assert isinstance(payload, dict)

    payload["event_id"] = "not-a-valid-uuid"

    with pytest.raises(
        ValueError,
        match="must contain a valid UUID",
    ):
        registry.create(record)


def test_boolean_is_not_accepted_as_number() -> None:
    registry = create_default_event_registry()
    record = event_to_record(make_event())

    payload = record["payload"]

    assert isinstance(payload, dict)

    payload["removed_height_m"] = True

    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        registry.create(record)
