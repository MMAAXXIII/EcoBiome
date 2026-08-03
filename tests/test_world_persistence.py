"""Tests for WorldState persistence."""

import json
from pathlib import Path

import pytest

from ecobiome.world.persistence import (
    load_world_state,
    save_world_state,
    world_state_from_record,
)
from ecobiome.world.water_geometry import (
    CylindricalGeometry,
    RectangularGeometry,
    SphericalGeometry,
)
from ecobiome.world.water_state import WaterBodyState
from ecobiome.world.world_state import WorldState


def make_world() -> WorldState:
    """Create a world containing several geometries."""
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

    world.add_water_body(
        WaterBodyState(
            name="Cuve cylindrique",
            geometry=CylindricalGeometry(
                radius_m=0.40,
                height_m=1.00,
            ),
            water_height_m=0.80,
        )
    )

    world.add_water_body(
        WaterBodyState(
            name="Bassin sphérique",
            geometry=SphericalGeometry(radius_m=1.00),
            water_height_m=1.10,
        )
    )

    return world


def test_save_and_restore_complete_world(
    tmp_path: Path,
) -> None:
    snapshot_path = tmp_path / "world.json"

    save_world_state(make_world(), snapshot_path)
    restored = load_world_state(snapshot_path)

    assert restored.water_body_count == 3

    aquarium = restored.get_water_body("Aquarium principal")

    assert aquarium.water_height_m == pytest.approx(0.50)
    assert aquarium.volume_liters == pytest.approx(300.0)
    assert isinstance(
        aquarium.geometry,
        RectangularGeometry,
    )

    sphere = restored.get_water_body("Bassin sphérique")

    assert isinstance(sphere.geometry, SphericalGeometry)
    assert sphere.water_height_m == pytest.approx(1.10)


def test_snapshot_is_readable_json(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "world.json"

    save_world_state(make_world(), snapshot_path)

    record = json.loads(
        snapshot_path.read_text(encoding="utf-8")
    )

    assert record["schema_version"] == "0.1"
    assert len(record["water_bodies"]) == 3


def test_unknown_geometry_type_is_rejected() -> None:
    record: dict[str, object] = {
        "schema_version": "0.1",
        "water_bodies": [
            {
                "name": "Unknown basin",
                "water_height_m": 0.5,
                "geometry": {
                    "type": "pyramid",
                },
            }
        ],
    }

    with pytest.raises(
        ValueError,
        match="Unsupported geometry type",
    ):
        world_state_from_record(record)


def test_missing_snapshot_is_reported(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        FileNotFoundError,
        match="snapshot not found",
    ):
        load_world_state(tmp_path / "missing.json")
