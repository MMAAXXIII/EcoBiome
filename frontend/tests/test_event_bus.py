"""Tests for the EcoBiome event bus."""

from ecobiome.core.events import (
    Event,
    EventBus,
    WaterRemovedEvent,
)


def make_water_removed_event() -> WaterRemovedEvent:
    """Create a reusable water-removal event."""
    return WaterRemovedEvent(
        water_body_name="Aquarium principal",
        removed_height_m=0.10,
        removed_volume_liters=60.0,
        remaining_volume_liters=300.0,
    )


def test_publish_event_to_subscriber() -> None:
    bus = EventBus()
    received_events: list[Event] = []

    bus.subscribe(
        WaterRemovedEvent,
        received_events.append,
    )

    delivered_count = bus.publish(
        make_water_removed_event()
    )

    assert delivered_count == 1
    assert len(received_events) == 1

    event = received_events[0]

    assert isinstance(event, WaterRemovedEvent)
    assert event.removed_volume_liters == 60.0


def test_base_event_subscriber_receives_specialized_events() -> None:
    bus = EventBus()
    received_events: list[Event] = []

    bus.subscribe(Event, received_events.append)
    bus.publish(make_water_removed_event())

    assert len(received_events) == 1
    assert isinstance(received_events[0], WaterRemovedEvent)


def test_multiple_independent_subscribers_receive_event() -> None:
    bus = EventBus()
    geometry_events: list[Event] = []
    history_events: list[Event] = []

    bus.subscribe(
        WaterRemovedEvent,
        geometry_events.append,
    )
    bus.subscribe(
        WaterRemovedEvent,
        history_events.append,
    )

    delivered_count = bus.publish(
        make_water_removed_event()
    )

    assert delivered_count == 2
    assert len(geometry_events) == 1
    assert len(history_events) == 1


def test_unsubscribe_stops_event_delivery() -> None:
    bus = EventBus()
    received_events: list[Event] = []

    subscription = bus.subscribe(
        WaterRemovedEvent,
        received_events.append,
    )

    assert bus.unsubscribe(subscription) is True
    assert bus.unsubscribe(subscription) is False

    delivered_count = bus.publish(
        make_water_removed_event()
    )

    assert delivered_count == 0
    assert received_events == []


def test_duplicate_subscription_is_not_registered_twice() -> None:
    bus = EventBus()
    received_events: list[Event] = []

    bus.subscribe(
        WaterRemovedEvent,
        received_events.append,
    )
    bus.subscribe(
        WaterRemovedEvent,
        received_events.append,
    )

    assert bus.subscriber_count(WaterRemovedEvent) == 1

    bus.publish(make_water_removed_event())

    assert len(received_events) == 1


def test_clear_removes_all_subscribers() -> None:
    bus = EventBus()

    bus.subscribe(WaterRemovedEvent, lambda event: None)
    bus.subscribe(Event, lambda event: None)

    bus.clear()

    assert bus.subscriber_count() == 0
