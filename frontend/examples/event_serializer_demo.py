"""Demonstrate generic event serialization."""

from ecobiome.core.events import (
    WaterRemovedEvent,
    event_to_json,
)


def main() -> None:
    """Serialize one event and print its JSON representation."""
    event = WaterRemovedEvent(
        water_body_name="Aquarium principal",
        removed_height_m=0.10,
        removed_volume_liters=60.0,
        remaining_volume_liters=300.0,
    )

    print("=" * 64)
    print("EcoBiome — Event Serialization")
    print("=" * 64)
    print(event_to_json(event, indent=2))


if __name__ == "__main__":
    main()
