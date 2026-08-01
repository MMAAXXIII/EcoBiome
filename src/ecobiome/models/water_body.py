"""Physical description of a body of water."""

from dataclasses import dataclass
from enum import StrEnum


class WaterBodyType(StrEnum):
    """User-facing categories of aquatic environments."""

    AQUARIUM = "aquarium"
    POND = "pond"
    NATURAL_POOL = "natural_pool"
    AQUAPONICS = "aquaponics"
    RESERVOIR = "reservoir"
    OTHER = "other"


class WaterBodyShape(StrEnum):
    """Supported geometric shapes."""

    RECTANGULAR = "rectangular"
    CYLINDRICAL = "cylindrical"
    FREEFORM = "freeform"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class WaterBody:
    """Represent the basic physical properties of an aquatic system."""

    name: str
    body_type: WaterBodyType
    shape: WaterBodyShape
    volume_m3: float | None = None
    length_m: float | None = None
    width_m: float | None = None
    water_height_m: float | None = None
    radius_m: float | None = None

    def __post_init__(self) -> None:
        """Validate supplied values and calculate volume when possible."""
        self.name = self.name.strip()

        if not self.name:
            raise ValueError("A water body must have a non-empty name.")

        for field_name in (
            "volume_m3",
            "length_m",
            "width_m",
            "water_height_m",
            "radius_m",
        ):
            value = getattr(self, field_name)

            if value is not None and value <= 0:
                raise ValueError(f"{field_name} must be greater than zero.")

        if self.volume_m3 is None:
            self.volume_m3 = self._calculate_volume()

    def _calculate_volume(self) -> float | None:
        """Calculate volume from known dimensions when possible."""
        if (
            self.shape is WaterBodyShape.RECTANGULAR
            and self.length_m is not None
            and self.width_m is not None
            and self.water_height_m is not None
        ):
            return self.length_m * self.width_m * self.water_height_m

        if (
            self.shape is WaterBodyShape.CYLINDRICAL
            and self.radius_m is not None
            and self.water_height_m is not None
        ):
            from math import pi

            return pi * self.radius_m**2 * self.water_height_m

        return None

    @property
    def volume_liters(self) -> float | None:
        """Return the volume in liters for display purposes."""
        if self.volume_m3 is None:
            return None

        return self.volume_m3 * 1_000