"""Tests for generic EcoBiome event storage."""

import pytest

from ecobiome.core.events import (
    Event,
    EventBus,
    InMemoryEventStore,
    WaterRemovedEvent,
)


def make_event(
    *,
    removed_height_m: float = 0.10,
    removed_volume_liters: float = 60.0,
    remaining_volume_liters: float = 300.0,
) -> WaterRemovedEvent:
    """Create one reusable domain event."""
    return WaterRemovedEvent(
        water_body_name="Aquarium principal",
        removed_height_m=removed_height_m,
        removed_volume_liters=removed_volume_liters,
        remaining_volume_liters=remaining_volume_liters,
    )


def test_store_appends_and_loads_event() -> None:
    store = InMemoryEventStore()
    event = make_event()

    store.append(event)

    assert store.count == 1
    assert store.contains(event.event_id) is True
    assert store.load() == (event,)


def test_store_preserves_insertion_order() -> None:
    first_event = make_event()
    second_event = make_event(
        removed_height_m=0.05,
        removed_volume_liters=30.0,
        remaining_volume_liters=270.0,
    )

    store = InMemoryEventStore(
        [first_event, second_event]
    )

    assert store.load() == (
        first_event,
        second_event,
    )


def test_duplicate_event_identifier_is_rejected() -> None:
    store = InMemoryEventStore()
    event = make_event()

    store.append(event)

    with pytest.raises(ValueError, match="already stored"):
        store.append(event)

    assert store.count == 1


def test_store_can_receive_events_from_event_bus() -> None:
    bus = EventBus()
    store = InMemoryEventStore()
    event = make_event()

    def record_event(received_event: Event) -> None:
        store.append(received_event)

    bus.subscribe(Event, record_event)

    delivered_count = bus.publish(event)

    assert delivered_count == 1
    assert store.load() == (event,)


def test_clear_removes_events_and_identifiers() -> None:
    store = InMemoryEventStore()
    event = make_event()

    store.append(event)
    store.clear()

    assert store.count == 0
    assert store.load() == ()
    assert store.contains(event.event_id) is False
