"""Demonstrate persistent JSONL event storage."""

from pathlib import Path

from ecobiome.core.events import (
    JsonLinesEventStore,
    WaterRemovedEvent,
    create_default_event_registry,
)


def main() -> None:
    """Store and reload one event from disk."""
    path = Path("data/events/event_store_demo.jsonl")

    store = JsonLinesEventStore(
        path=path,
        registry=create_default_event_registry(),
    )
    store.clear()

    event = WaterRemovedEvent(
        water_body_name="Aquarium principal",
        removed_height_m=0.10,
        removed_volume_liters=60.0,
        remaining_volume_liters=300.0,
    )

    store.append(event)

    restored_store = JsonLinesEventStore(
        path=path,
        registry=create_default_event_registry(),
    )

    restored = restored_store.load()

    print("=" * 64)
    print("EcoBiome — Persistent JSONL EventStore")
    print("=" * 64)
    print(f"Fichier             : {path}")
    print(f"Événements stockés  : {restored_store.count}")
    print(f"Type restauré       : {type(restored[0]).__name__}")
    print(f"Événement identique : {restored[0] == event}")


if __name__ == "__main__":
    main()
