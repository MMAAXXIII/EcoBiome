"""Tests for dynamic WaterBodyState."""

import pytest

from ecobiome.world.water_geometry import RectangularGeometry
from ecobiome.world.water_state import WaterBodyState


def test_water_body_state_updates_after_removal() -> None:
    state = WaterBodyState(
        name="Aquarium principal",
        geometry=RectangularGeometry(
            length_m=1.20,
            width_m=0.50,
            height_m=0.60,
        ),
        water_height_m=0.60,
    )

    updated, result = state.remove_height(0.10)

    assert state.water_height_m == pytest.approx(0.60)
    assert updated.water_height_m == pytest.approx(0.50)
    assert updated.volume_liters == pytest.approx(300.0)
    assert result.removed_volume_liters == pytest.approx(60.0)


def test_state_rejects_height_above_container() -> None:
    geometry = RectangularGeometry(
        length_m=1.00,
        width_m=1.00,
        height_m=0.50,
    )

    with pytest.raises(
        ValueError,
        match="outside the geometry limits",
    ):
        WaterBodyState(
            name="Invalid pond",
            geometry=geometry,
            water_height_m=0.60,
        )
