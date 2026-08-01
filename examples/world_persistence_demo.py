"""Demonstrate saving and restoring a WorldState."""

from pathlib import Path

from ecobiome.world.persistence import (
    load_world_state,
    save_world_state,
)
from ecobiome.world.water_geometry import RectangularGeometry
from ecobiome.world.water_state import WaterBodyState
from ecobiome.world.world_state import WorldState


def main() -> None:
    """Save and reload one aquarium state."""
    snapshot_path = Path("data/world/demo_world.json")

    world = WorldState()
    world.add_water_body(
        WaterBodyState(
            name="Aquarium principal",
            geometry=RectangularGeometry(
                length_m=1.20,
                width_m=0.50,
                height_m=0.60,
            ),
            water_height_m=0.50,
        )
    )

    save_world_state(world, snapshot_path)
    restored = load_world_state(snapshot_path)
    aquarium = restored.get_water_body("Aquarium principal")

    print("=" * 64)
    print("EcoBiome — WorldState Persistence")
    print("=" * 64)
    print(f"Fichier restauré : {snapshot_path}")
    print(f"Plan d'eau       : {aquarium.name}")
    print(f"Niveau           : {aquarium.water_height_m:.2f} m")
    print(f"Volume           : {aquarium.volume_liters:.2f} L")


if __name__ == "__main__":
    main()
