"""Tests for dynamic water geometry."""

from math import pi

import pytest

from ecobiome.world.water_geometry import (
    CylindricalGeometry,
    RectangularGeometry,
    SphericalGeometry,
)
from ecobiome.world.water_level import remove_water_height


def test_remove_ten_centimeters_from_rectangular_tank() -> None:
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

    assert result.new_height_m == pytest.approx(0.50)
    assert result.removed_volume_liters == pytest.approx(60.0)
    assert result.remaining_volume_liters == pytest.approx(300.0)
    assert result.free_surface_area_m2 == pytest.approx(0.60)
    assert result.wetted_surface_area_m2 == pytest.approx(2.30)


def test_cylindrical_volume_changes_linearly_with_height() -> None:
    geometry = CylindricalGeometry(
        radius_m=0.50,
        height_m=1.00,
    )

    result = remove_water_height(
        geometry,
        current_height_m=1.00,
        removed_height_m=0.10,
    )

    assert result.removed_volume_m3 == pytest.approx(
        pi * 0.50**2 * 0.10
    )


def test_spherical_volume_depends_on_water_level() -> None:
    geometry = SphericalGeometry(radius_m=1.00)

    near_bottom = remove_water_height(
        geometry,
        current_height_m=0.20,
        removed_height_m=0.10,
    )

    near_middle = remove_water_height(
        geometry,
        current_height_m=1.10,
        removed_height_m=0.10,
    )

    assert (
        near_middle.removed_volume_m3
        > near_bottom.removed_volume_m3
    )


def test_removal_cannot_lower_level_below_zero() -> None:
    geometry = RectangularGeometry(
        length_m=1.00,
        width_m=1.00,
        height_m=1.00,
    )

    result = remove_water_height(
        geometry,
        current_height_m=0.08,
        removed_height_m=0.10,
    )

    assert result.new_height_m == 0.0
    assert result.removed_height_m == pytest.approx(0.08)
    assert result.remaining_volume_m3 == 0.0
    assert result.surface_to_volume_ratio is None


def test_invalid_removed_height_is_rejected() -> None:
    geometry = RectangularGeometry(
        length_m=1.00,
        width_m=1.00,
        height_m=1.00,
    )

    with pytest.raises(
        ValueError,
        match="removed_height_m must be greater than zero",
    ):
        remove_water_height(
            geometry,
            current_height_m=0.50,
            removed_height_m=0.0,
        )
