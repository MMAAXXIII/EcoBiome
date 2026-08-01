"""Demonstrate secure JSON event reconstruction."""

from ecobiome.core.events import (
    WaterRemovedEvent,
    create_default_event_registry,
    event_to_json,
)


def main() -> None:
    """Serialize and restore one event."""
    original = WaterRemovedEvent(
        water_body_name="Aquarium principal",
        removed_height_m=0.10,
        removed_volume_liters=60.0,
        remaining_volume_liters=300.0,
    )

    serialized = event_to_json(original, indent=2)

    registry = create_default_event_registry()
    restored = registry.create_from_json(serialized)

    print("=" * 64)
    print("EcoBiome — JSON Event Reconstruction")
    print("=" * 64)
    print(serialized)
    print()
    print(f"Type restauré       : {type(restored).__name__}")
    print(f"Événement identique : {restored == original}")


if __name__ == "__main__":
    main()
