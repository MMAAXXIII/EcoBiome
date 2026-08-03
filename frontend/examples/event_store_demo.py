"""Demonstrate EventBus and EventStore integration."""

from ecobiome.core.events import (
    Event,
    EventBus,
    InMemoryEventStore,
    WaterRemovedEvent,
)


def main() -> None:
    """Publish and store one event."""
    bus = EventBus()
    store = InMemoryEventStore()

    def record_event(event: Event) -> None:
        store.append(event)

    bus.subscribe(Event, record_event)

    event = WaterRemovedEvent(
        water_body_name="Aquarium principal",
        removed_height_m=0.10,
        removed_volume_liters=60.0,
        remaining_volume_liters=300.0,
    )

    bus.publish(event)

    print("=" * 64)
    print("EcoBiome — EventStore")
    print("=" * 64)
    print(f"Événements stockés : {store.count}")

    for stored_event in store.load():
        print(f"Type               : {type(stored_event).__name__}")
        print(f"Identifiant        : {stored_event.event_id}")
        print(f"Date UTC           : {stored_event.occurred_at.isoformat()}")


if __name__ == "__main__":
    main()
