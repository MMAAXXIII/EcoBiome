"""Water-level command-line operations."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from ecobiome.world.events import (
    WaterLevelEventType,
    append_event_jsonl,
    create_water_level_event,
)
from ecobiome.world.water_geometry import (
    CylindricalGeometry,
    RectangularGeometry,
    SphericalGeometry,
    WaterGeometry,
)
from ecobiome.world.water_state import WaterBodyState


def add_water_level_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the water-level command to the main parser."""
    parser = subparsers.add_parser(
        "water-level",
        help="Calculate and record the effects of lowering a water level.",
    )

    parser.add_argument(
        "--name",
        default="Water body",
        help="Name of the aquarium, pond, or reservoir.",
    )
    parser.add_argument(
        "--shape",
        required=True,
        choices=("rectangular", "cylindrical", "spherical"),
    )
    parser.add_argument("--length", type=float)
    parser.add_argument("--width", type=float)
    parser.add_argument("--radius", type=float)
    parser.add_argument("--container-height", type=float)
    parser.add_argument("--current-height", required=True, type=float)
    parser.add_argument("--remove", required=True, type=float)
    parser.add_argument(
        "--cause",
        choices=[event_type.value for event_type in WaterLevelEventType],
        default=WaterLevelEventType.USER_REMOVAL.value,
        help="Cause of the water-level reduction.",
    )
    parser.add_argument(
        "--note",
        default="",
        help="Optional observation associated with the event.",
    )
    parser.add_argument(
        "--event-log",
        type=Path,
        default=None,
        help="Optional JSONL history file receiving the event.",
    )


def _required_dimension(
    value: float | None,
    option_name: str,
) -> float:
    """Require one geometry-specific dimension."""
    if value is None:
        raise ValueError(
            f"{option_name} is required for the selected shape."
        )

    return value


def build_geometry(args: argparse.Namespace) -> WaterGeometry:
    """Construct the requested geometry."""
    if args.shape == "rectangular":
        return RectangularGeometry(
            length_m=_required_dimension(args.length, "--length"),
            width_m=_required_dimension(args.width, "--width"),
            height_m=_required_dimension(
                args.container_height,
                "--container-height",
            ),
        )

    if args.shape == "cylindrical":
        return CylindricalGeometry(
            radius_m=_required_dimension(args.radius, "--radius"),
            height_m=_required_dimension(
                args.container_height,
                "--container-height",
            ),
        )

    if args.shape == "spherical":
        return SphericalGeometry(
            radius_m=_required_dimension(args.radius, "--radius"),
        )

    raise ValueError(f"Unsupported geometry: {args.shape}")


def water_level_command(args: argparse.Namespace) -> int:
    """Calculate, display, and optionally record a level reduction."""
    geometry = build_geometry(args)

    previous_state = WaterBodyState(
        name=args.name,
        geometry=geometry,
        water_height_m=args.current_height,
    )

    updated_state, result = previous_state.remove_height(args.remove)

    event = create_water_level_event(
        water_body_name=previous_state.name,
        event_type=WaterLevelEventType(args.cause),
        change=result,
        note=args.note,
    )

    if args.event_log is not None:
        append_event_jsonl(event, args.event_log)

    print("=" * 64)
    print("EcoBiome — Changement du niveau d'eau")
    print("=" * 64)
    print(f"Plan d'eau             : {previous_state.name}")
    print(f"Forme                  : {args.shape}")
    print(f"Cause                  : {event.event_type.value}")
    print(f"Date UTC               : {event.occurred_at.isoformat()}")
    print(f"Identifiant événement  : {event.event_id}")
    print(f"Ancien niveau          : {result.previous_height_m:.3f} m")
    print(f"Nouveau niveau         : {updated_state.water_height_m:.3f} m")
    print(f"Volume retiré          : {result.removed_volume_liters:.2f} L")
    print(f"Volume restant         : {updated_state.volume_liters:.2f} L")
    print(
        f"Surface libre          : "
        f"{updated_state.free_surface_area_m2:.4f} m²"
    )
    print(
        f"Surface immergée       : "
        f"{updated_state.wetted_surface_area_m2:.4f} m²"
    )

    if args.note:
        print(f"Observation            : {args.note}")

    if args.event_log is not None:
        print(f"Historique             : {args.event_log}")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the standalone water-level command."""
    parser = argparse.ArgumentParser(prog="ecobiome water-level")
    subparsers = parser.add_subparsers(dest="command")
    add_water_level_parser(subparsers)

    arguments = ["water-level", *(argv or [])]
    args = parser.parse_args(arguments)

    return water_level_command(args)
