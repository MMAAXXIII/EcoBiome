"""Demonstrate persistent event replay into WorldState."""

from pathlib import Path

from ecobiome.core.events import (
    Event,
    EventBus,
    JsonLinesEventStore,
    WaterRemovedEvent,
    create_default_event_registry,
    replay_event_store,
)
from ecobiome.world.water_geometry import RectangularGeometry
from ecobiome.world.water_state import WaterBodyState
from ecobiome.world.world_state import WorldState


def main() -> None:
    """Persist events and reconstruct a water-body state."""
    path = Path("data/events/replay_demo.jsonl")

    store = JsonLinesEventStore(
        path=path,
        registry=create_default_event_registry(),
    )
    store.clear()

    store.append(
        WaterRemovedEvent(
            water_body_name="Aquarium principal",
            removed_height_m=0.10,
            removed_volume_liters=60.0,
            remaining_volume_liters=300.0,
        )
    )
    store.append(
        WaterRemovedEvent(
            water_body_name="Aquarium principal",
            removed_height_m=0.05,
            removed_volume_liters=30.0,
            remaining_volume_liters=270.0,
        )
    )

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
    bus.subscribe(Event, world.handle_event)

    result = replay_event_store(store, bus)
    aquarium = world.get_water_body("Aquarium principal")

    print("=" * 64)
    print("EcoBiome — Generic Event Replay")
    print("=" * 64)
    print(f"Événements chargés   : {result.loaded_event_count}")
    print(f"Événements publiés   : {result.published_event_count}")
    print(f"Livraisons effectuées: {result.delivery_count}")
    print(f"Niveau reconstruit   : {aquarium.water_height_m:.2f} m")
    print(f"Volume reconstruit   : {aquarium.volume_liters:.2f} L")


if __name__ == "__main__":
    main()
