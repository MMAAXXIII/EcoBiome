"""Dynamic state of a body of water."""

from dataclasses import dataclass, replace

from ecobiome.world.water_geometry import WaterGeometry
from ecobiome.world.water_level import (
    WaterLevelChangeResult,
    remove_water_height,
)


@dataclass(frozen=True, slots=True)
class WaterBodyState:
    """Represent the current geometrical state of a body of water."""

    name: str
    geometry: WaterGeometry
    water_height_m: float

    def __post_init__(self) -> None:
        """Validate and normalize the state."""
        name = self.name.strip()

        if not name:
            raise ValueError("A water body state requires a name.")

        if not 0.0 <= self.water_height_m <= self.geometry.maximum_height_m:
            raise ValueError(
                "water_height_m is outside the geometry limits."
            )

        object.__setattr__(self, "name", name)

    @property
    def volume_m3(self) -> float:
        """Return the current water volume."""
        return self.geometry.volume_at_height_m3(self.water_height_m)

    @property
    def volume_liters(self) -> float:
        """Return the current water volume in liters."""
        return self.volume_m3 * 1_000

    @property
    def free_surface_area_m2(self) -> float:
        """Return the current air-water interface area."""
        return self.geometry.cross_section_area_m2(self.water_height_m)

    @property
    def wetted_surface_area_m2(self) -> float:
        """Return the current submerged container surface."""
        return self.geometry.wetted_surface_area_m2(self.water_height_m)

    def remove_height(
        self,
        removed_height_m: float,
    ) -> tuple[WaterBodyState, WaterLevelChangeResult]:
        """Return the updated state and the geometrical change report."""
        result = remove_water_height(
            self.geometry,
            current_height_m=self.water_height_m,
            removed_height_m=removed_height_m,
        )

        updated_state = replace(
            self,
            water_height_m=result.new_height_m,
        )

        return updated_state, result
