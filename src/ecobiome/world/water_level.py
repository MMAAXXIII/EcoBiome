"""Water-level change calculations."""

from dataclasses import dataclass

from ecobiome.world.water_geometry import WaterGeometry


@dataclass(frozen=True, slots=True)
class WaterLevelChangeResult:
    """Geometrical consequences of a water-level reduction."""

    previous_height_m: float
    new_height_m: float
    removed_height_m: float
    previous_volume_m3: float
    removed_volume_m3: float
    remaining_volume_m3: float
    free_surface_area_m2: float
    wetted_surface_area_m2: float

    @property
    def removed_volume_liters(self) -> float:
        """Return removed volume in liters."""
        return self.removed_volume_m3 * 1_000

    @property
    def remaining_volume_liters(self) -> float:
        """Return remaining volume in liters."""
        return self.remaining_volume_m3 * 1_000

    @property
    def surface_to_volume_ratio(self) -> float | None:
        """Return free-surface area divided by remaining volume."""
        if self.remaining_volume_m3 == 0:
            return None

        return self.free_surface_area_m2 / self.remaining_volume_m3


def remove_water_height(
    geometry: WaterGeometry,
    *,
    current_height_m: float,
    removed_height_m: float,
) -> WaterLevelChangeResult:
    """Calculate the consequences of lowering a water level."""
    if not 0.0 <= current_height_m <= geometry.maximum_height_m:
        raise ValueError(
            "current_height_m is outside the geometry limits."
        )

    if removed_height_m <= 0:
        raise ValueError(
            "removed_height_m must be greater than zero."
        )

    new_height_m = max(0.0, current_height_m - removed_height_m)
    effective_removed_height_m = current_height_m - new_height_m

    previous_volume_m3 = geometry.volume_at_height_m3(
        current_height_m
    )
    remaining_volume_m3 = geometry.volume_at_height_m3(
        new_height_m
    )

    return WaterLevelChangeResult(
        previous_height_m=current_height_m,
        new_height_m=new_height_m,
        removed_height_m=effective_removed_height_m,
        previous_volume_m3=previous_volume_m3,
        removed_volume_m3=(
            previous_volume_m3 - remaining_volume_m3
        ),
        remaining_volume_m3=remaining_volume_m3,
        free_surface_area_m2=geometry.cross_section_area_m2(
            new_height_m
        ),
        wetted_surface_area_m2=geometry.wetted_surface_area_m2(
            new_height_m
        ),
    )
