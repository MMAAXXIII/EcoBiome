"""Water-level command-line operations."""

import argparse
from collections.abc import Sequence

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
        help="Calculate the effects of lowering a water level.",
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
        help="Geometry of the body of water.",
    )
    parser.add_argument("--length", type=float)
    parser.add_argument("--width", type=float)
    parser.add_argument("--radius", type=float)
    parser.add_argument("--container-height", type=float)
    parser.add_argument(
        "--current-height",
        required=True,
        type=float,
        help="Current water height in meters.",
    )
    parser.add_argument(
        "--remove",
        required=True,
        type=float,
        help="Water-height reduction in meters.",
    )


def _required_dimension(
    value: float | None,
    option_name: str,
) -> float:
    """Require one geometry-specific command-line dimension."""
    if value is None:
        raise ValueError(
            f"{option_name} is required for the selected shape."
        )

    return value


def build_geometry(args: argparse.Namespace) -> WaterGeometry:
    """Construct the requested geometry from command-line arguments."""
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
    """Calculate and display one water-level reduction."""
    geometry = build_geometry(args)

    previous_state = WaterBodyState(
        name=args.name,
        geometry=geometry,
        water_height_m=args.current_height,
    )

    updated_state, result = previous_state.remove_height(args.remove)

    print("=" * 64)
    print("EcoBiome — Changement du niveau d'eau")
    print("=" * 64)
    print(f"Plan d'eau             : {previous_state.name}")
    print(f"Forme                  : {args.shape}")
    print(f"Ancien niveau          : {result.previous_height_m:.3f} m")
    print(f"Nouveau niveau         : {updated_state.water_height_m:.3f} m")
    print(f"Hauteur réellement ôtée: {result.removed_height_m:.3f} m")
    print(f"Volume initial         : {result.previous_volume_m3 * 1000:.2f} L")
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

    ratio = result.surface_to_volume_ratio

    if ratio is None:
        print("Rapport surface/volume : non défini (plan d'eau vide)")
    else:
        print(f"Rapport surface/volume : {ratio:.4f} m⁻¹")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the standalone water-level command."""
    parser = argparse.ArgumentParser(prog="ecobiome water-level")
    subparsers = parser.add_subparsers(dest="command")
    add_water_level_parser(subparsers)

    arguments = ["water-level", *(argv or [])]
    args = parser.parse_args(arguments)

    return water_level_command(args)
