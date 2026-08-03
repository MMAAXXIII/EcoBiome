"""Tests for generic event-store replay."""

from ecobiome.core.events import (
    Event,
    EventBus,
    InMemoryEventStore,
    WaterRemovedEvent,
    replay_event_store,
)


def make_event(
    *,
    removed_height_m: float,
    remaining_volume_liters: float,
) -> WaterRemovedEvent:
    """Create one reusable water-removal event."""
    return WaterRemovedEvent(
        water_body_name="Aquarium principal",
        removed_height_m=removed_height_m,
        removed_volume_liters=removed_height_m * 600.0,
        remaining_volume_liters=remaining_volume_liters,
    )


def test_replay_publishes_every_stored_event() -> None:
    first = make_event(
        removed_height_m=0.10,
        remaining_volume_liters=300.0,
    )
    second = make_event(
        removed_height_m=0.05,
        remaining_volume_liters=270.0,
    )

    store = InMemoryEventStore([first, second])
    bus = EventBus()
    received: list[Event] = []

    bus.subscribe(Event, received.append)

    result = replay_event_store(store, bus)

    assert result.loaded_event_count == 2
    assert result.published_event_count == 2
    assert result.delivery_count == 2
    assert received == [first, second]


def test_replay_preserves_storage_order() -> None:
    first = make_event(
        removed_height_m=0.10,
        remaining_volume_liters=300.0,
    )
    second = make_event(
        removed_height_m=0.05,
        remaining_volume_liters=270.0,
    )

    store = InMemoryEventStore([first, second])
    bus = EventBus()
    received: list[Event] = []

    bus.subscribe(Event, received.append)

    replay_event_store(store, bus)

    assert received[0].event_id == first.event_id
    assert received[1].event_id == second.event_id


def test_multiple_subscribers_are_all_counted() -> None:
    event = make_event(
        removed_height_m=0.10,
        remaining_volume_liters=300.0,
    )

    store = InMemoryEventStore([event])
    bus = EventBus()
    first_listener: list[Event] = []
    second_listener: list[Event] = []

    bus.subscribe(Event, first_listener.append)
    bus.subscribe(Event, second_listener.append)

    result = replay_event_store(store, bus)

    assert result.published_event_count == 1
    assert result.delivery_count == 2
    assert first_listener == [event]
    assert second_listener == [event]


def test_replay_without_subscribers_remains_valid() -> None:
    event = make_event(
        removed_height_m=0.10,
        remaining_volume_liters=300.0,
    )

    store = InMemoryEventStore([event])
    bus = EventBus()

    result = replay_event_store(store, bus)

    assert result.loaded_event_count == 1
    assert result.published_event_count == 1
    assert result.delivery_count == 0
    assert result.event_without_subscriber_count == 1


def test_empty_store_produces_empty_replay() -> None:
    store = InMemoryEventStore()
    bus = EventBus()

    result = replay_event_store(store, bus)

    assert result.loaded_event_count == 0
    assert result.published_event_count == 0
    assert result.delivery_count == 0
