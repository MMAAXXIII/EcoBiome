"""Save and restore EcoBiome world-state snapshots."""

import json
from pathlib import Path
from typing import cast

from ecobiome.world.water_geometry import (
    CylindricalGeometry,
    RectangularGeometry,
    SphericalGeometry,
    WaterGeometry,
)
from ecobiome.world.water_state import WaterBodyState
from ecobiome.world.world_state import WorldState


def _geometry_to_record(
    geometry: WaterGeometry,
) -> dict[str, object]:
    """Convert a supported geometry into a JSON record."""
    if isinstance(geometry, RectangularGeometry):
        return {
            "type": "rectangular",
            "length_m": geometry.length_m,
            "width_m": geometry.width_m,
            "height_m": geometry.height_m,
        }

    if isinstance(geometry, CylindricalGeometry):
        return {
            "type": "cylindrical",
            "radius_m": geometry.radius_m,
            "height_m": geometry.height_m,
        }

    if isinstance(geometry, SphericalGeometry):
        return {
            "type": "spherical",
            "radius_m": geometry.radius_m,
        }

    raise TypeError(
        f"Unsupported water geometry: {type(geometry).__name__}."
    )


def _required_float(
    record: dict[str, object],
    field_name: str,
) -> float:
    """Read one required numeric field."""
    value = record.get(field_name)

    if not isinstance(value, int | float):
        raise TypeError(
            f"Snapshot field {field_name!r} must be numeric."
        )

    return float(value)


def _required_string(
    record: dict[str, object],
    field_name: str,
) -> str:
    """Read one required non-empty string field."""
    value = record.get(field_name)

    if not isinstance(value, str) or not value.strip():
        raise TypeError(
            f"Snapshot field {field_name!r} must be a string."
        )

    return value.strip()


def _geometry_from_record(
    record: dict[str, object],
) -> WaterGeometry:
    """Restore one supported geometry."""
    geometry_type = _required_string(record, "type")

    if geometry_type == "rectangular":
        return RectangularGeometry(
            length_m=_required_float(record, "length_m"),
            width_m=_required_float(record, "width_m"),
            height_m=_required_float(record, "height_m"),
        )

    if geometry_type == "cylindrical":
        return CylindricalGeometry(
            radius_m=_required_float(record, "radius_m"),
            height_m=_required_float(record, "height_m"),
        )

    if geometry_type == "spherical":
        return SphericalGeometry(
            radius_m=_required_float(record, "radius_m"),
        )

    raise ValueError(
        f"Unsupported geometry type in snapshot: {geometry_type!r}."
    )


def world_state_to_record(
    world: WorldState,
) -> dict[str, object]:
    """Convert a complete world state into a JSON-compatible record."""
    return {
        "schema_version": "0.1",
        "water_bodies": [
            {
                "name": water_body.name,
                "water_height_m": water_body.water_height_m,
                "geometry": _geometry_to_record(
                    water_body.geometry
                ),
            }
            for water_body in world.list_water_bodies()
        ],
    }


def world_state_from_record(
    record: dict[str, object],
) -> WorldState:
    """Restore a world state from a validated record."""
    raw_water_bodies = record.get("water_bodies")

    if not isinstance(raw_water_bodies, list):
        raise TypeError(
            "Snapshot field 'water_bodies' must be a list."
        )

    world = WorldState()

    for raw_water_body in raw_water_bodies:
        if not isinstance(raw_water_body, dict):
            raise TypeError(
                "Each water-body snapshot must be a mapping."
            )

        water_body_record = cast(
            dict[str, object],
            raw_water_body,
        )

        raw_geometry = water_body_record.get("geometry")

        if not isinstance(raw_geometry, dict):
            raise TypeError(
                "Water-body field 'geometry' must be a mapping."
            )

        geometry_record = cast(
            dict[str, object],
            raw_geometry,
        )

        world.add_water_body(
            WaterBodyState(
                name=_required_string(
                    water_body_record,
                    "name",
                ),
                geometry=_geometry_from_record(
                    geometry_record
                ),
                water_height_m=_required_float(
                    water_body_record,
                    "water_height_m",
                ),
            )
        )

    return world


def save_world_state(
    world: WorldState,
    path: Path,
) -> None:
    """Save one complete world-state snapshot as UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            world_state_to_record(world),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def load_world_state(path: Path) -> WorldState:
    """Load one complete world-state snapshot."""
    if not path.is_file():
        raise FileNotFoundError(
            f"World-state snapshot not found: {path}"
        )

    raw_record = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(raw_record, dict):
        raise TypeError(
            "A world-state snapshot must contain a JSON object."
        )

    return world_state_from_record(
        cast(dict[str, object], raw_record)
    )
