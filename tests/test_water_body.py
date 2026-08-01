"""Tests for the WaterBody model."""

import pytest

from ecobiome.world import WaterBody, WaterBodyShape, WaterBodyType


def test_rectangular_volume_is_calculated() -> None:
    water_body = WaterBody(
        name="Aquarium principal",
        body_type=WaterBodyType.AQUARIUM,
        shape=WaterBodyShape.RECTANGULAR,
        length_m=1.0,
        width_m=0.5,
        water_height_m=0.5,
    )

    assert water_body.volume_m3 == pytest.approx(0.25)
    assert water_body.volume_liters == pytest.approx(250.0)


def test_cylindrical_volume_is_calculated() -> None:
    water_body = WaterBody(
        name="Bassin rond",
        body_type=WaterBodyType.POND,
        shape=WaterBodyShape.CYLINDRICAL,
        radius_m=0.5,
        water_height_m=0.8,
    )

    assert water_body.volume_m3 == pytest.approx(0.6283185)
    assert water_body.volume_liters == pytest.approx(628.3185)


def test_unknown_dimensions_keep_volume_unknown() -> None:
    water_body = WaterBody(
        name="Mare découverte",
        body_type=WaterBodyType.NATURAL_POOL,
        shape=WaterBodyShape.FREEFORM,
    )

    assert water_body.volume_m3 is None
    assert water_body.volume_liters is None


def test_negative_dimension_is_rejected() -> None:
    with pytest.raises(ValueError, match="length_m must be greater than zero"):
        WaterBody(
            name="Bac invalide",
            body_type=WaterBodyType.AQUARIUM,
            shape=WaterBodyShape.RECTANGULAR,
            length_m=-1.0,
        )
