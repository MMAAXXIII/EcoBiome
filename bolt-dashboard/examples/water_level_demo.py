"""Demonstrate a user-requested water-level reduction."""

from ecobiome.world.water_geometry import RectangularGeometry
from ecobiome.world.water_level import remove_water_height


def main() -> None:
    """Calculate removal of ten centimeters of water."""
    geometry = RectangularGeometry(
        length_m=1.20,
        width_m=0.50,
        height_m=0.60,
    )

    result = remove_water_height(
        geometry,
        current_height_m=0.60,
        removed_height_m=0.10,
    )

    print("=" * 60)
    print("EcoBiome — Changement du niveau d'eau")
    print("=" * 60)
    print(f"Ancien niveau       : {result.previous_height_m:.2f} m")
    print(f"Nouveau niveau      : {result.new_height_m:.2f} m")
    print(f"Volume retiré       : {result.removed_volume_liters:.1f} L")
    print(
        f"Volume restant      : "
        f"{result.remaining_volume_liters:.1f} L"
    )
    print(
        f"Surface libre       : "
        f"{result.free_surface_area_m2:.3f} m²"
    )
    print(
        f"Surface immergée    : "
        f"{result.wetted_surface_area_m2:.3f} m²"
    )


if __name__ == "__main__":
    main()
