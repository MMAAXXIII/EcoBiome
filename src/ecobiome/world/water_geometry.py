"""Geometry models for changing bodies of water."""

from dataclasses import dataclass
from math import pi
from typing import Protocol


class WaterGeometry(Protocol):
    """Interface implemented by water-container geometries."""

    @property
    def maximum_height_m(self) -> float:
        """Return the maximum supported water height."""

    def cross_section_area_m2(self, height_m: float) -> float:
        """Return horizontal area at a given height."""

    def volume_at_height_m3(self, height_m: float) -> float:
        """Return water volume below a given height."""

    def wetted_surface_area_m2(self, height_m: float) -> float:
        """Return the container surface currently in contact with water."""


def _validate_positive(value: float, name: str) -> None:
    """Reject zero and negative dimensions."""
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")


def _validate_height(height_m: float, maximum_height_m: float) -> None:
    """Ensure a height belongs to the geometry."""
    if not 0.0 <= height_m <= maximum_height_m:
        raise ValueError(
            f"height_m must be between 0 and {maximum_height_m}."
        )


@dataclass(frozen=True, slots=True)
class RectangularGeometry:
    """Rectangular tank or pond geometry."""

    length_m: float
    width_m: float
    height_m: float

    def __post_init__(self) -> None:
        """Validate dimensions."""
        _validate_positive(self.length_m, "length_m")
        _validate_positive(self.width_m, "width_m")
        _validate_positive(self.height_m, "height_m")

    @property
    def maximum_height_m(self) -> float:
        """Return the container height."""
        return self.height_m

    def cross_section_area_m2(self, height_m: float) -> float:
        """Return the constant horizontal section."""
        _validate_height(height_m, self.maximum_height_m)

        if height_m == 0:
            return 0.0

        return self.length_m * self.width_m

    def volume_at_height_m3(self, height_m: float) -> float:
        """Return volume below the selected height."""
        _validate_height(height_m, self.maximum_height_m)
        return self.length_m * self.width_m * height_m

    def wetted_surface_area_m2(self, height_m: float) -> float:
        """Return bottom and submerged wall area."""
        _validate_height(height_m, self.maximum_height_m)

        if height_m == 0:
            return 0.0

        bottom_area = self.length_m * self.width_m
        perimeter = 2 * (self.length_m + self.width_m)

        return bottom_area + perimeter * height_m


@dataclass(frozen=True, slots=True)
class CylindricalGeometry:
    """Vertical cylindrical tank geometry."""

    radius_m: float
    height_m: float

    def __post_init__(self) -> None:
        """Validate dimensions."""
        _validate_positive(self.radius_m, "radius_m")
        _validate_positive(self.height_m, "height_m")

    @property
    def maximum_height_m(self) -> float:
        """Return the cylinder height."""
        return self.height_m

    def cross_section_area_m2(self, height_m: float) -> float:
        """Return the constant circular section."""
        _validate_height(height_m, self.maximum_height_m)

        if height_m == 0:
            return 0.0

        return pi * self.radius_m**2

    def volume_at_height_m3(self, height_m: float) -> float:
        """Return volume below the selected height."""
        _validate_height(height_m, self.maximum_height_m)
        return pi * self.radius_m**2 * height_m

    def wetted_surface_area_m2(self, height_m: float) -> float:
        """Return bottom and submerged lateral area."""
        _validate_height(height_m, self.maximum_height_m)

        if height_m == 0:
            return 0.0

        bottom_area = pi * self.radius_m**2
        lateral_area = 2 * pi * self.radius_m * height_m

        return bottom_area + lateral_area


@dataclass(frozen=True, slots=True)
class SphericalGeometry:
    """Spherical basin measured upward from its lowest point."""

    radius_m: float

    def __post_init__(self) -> None:
        """Validate the radius."""
        _validate_positive(self.radius_m, "radius_m")

    @property
    def maximum_height_m(self) -> float:
        """Return the sphere diameter."""
        return 2 * self.radius_m

    def cross_section_area_m2(self, height_m: float) -> float:
        """Return the horizontal circular section at a height."""
        _validate_height(height_m, self.maximum_height_m)

        if height_m == 0 or height_m == self.maximum_height_m:
            return 0.0

        return pi * (
            2 * self.radius_m * height_m - height_m**2
        )

    def volume_at_height_m3(self, height_m: float) -> float:
        """Return spherical-cap volume below a height."""
        _validate_height(height_m, self.maximum_height_m)

        return (
            pi
            * height_m**2
            * (self.radius_m - height_m / 3)
        )

    def wetted_surface_area_m2(self, height_m: float) -> float:
        """Return submerged inner spherical surface area."""
        _validate_height(height_m, self.maximum_height_m)
        return 2 * pi * self.radius_m * height_m
