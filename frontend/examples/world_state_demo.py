"""Demonstrate event-driven WorldState updates."""

from ecobiome.core.events import EventBus, WaterRemovedEvent
from ecobiome.world.water_geometry import RectangularGeometry
from ecobiome.world.water_state import WaterBodyState
from ecobiome.world.world_state import WorldState


def main() -> None:
    """Publish one event and display the updated world."""
    world = WorldState()

    world.add_water_body(
        WaterBodyState(
            name="Aquarium principal",
            geometry=RectangularGeometry(
                length_m=1.20,
                width_m=0.50,
                height_m=0.60,
            ),
            water_height_m=0.60,
        )
    )

    bus = EventBus()
    bus.subscribe(WaterRemovedEvent, world.handle_event)

    before = world.get_water_body("Aquarium principal")

    event = WaterRemovedEvent(
        water_body_name="Aquarium principal",
        removed_height_m=0.10,
        removed_volume_liters=60.0,
        remaining_volume_liters=300.0,
    )

    bus.publish(event)

    after = world.get_water_body("Aquarium principal")

    print("=" * 64)
    print("EcoBiome — WorldState")
    print("=" * 64)
    print(f"Volume avant       : {before.volume_liters:.2f} L")
    print(f"Événement          : {event.__class__.__name__}")
    print(f"Volume après       : {after.volume_liters:.2f} L")
    print(f"Niveau après       : {after.water_height_m:.2f} m")
    print(f"Événements traités : {world.processed_event_count}")


if __name__ == "__main__":
    main()
