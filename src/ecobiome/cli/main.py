"""Central command-line interface for EcoBiome."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from ecobiome.cli.water_level import (
    add_water_level_parser,
    water_level_command,
)
from ecobiome.knowledge.directory_loader import load_knowledge_directory
from ecobiome.knowledge_acquisition.cli import main as acquisition_main
from ecobiome.reasoning import CausalChainEngine


def build_parser() -> argparse.ArgumentParser:
    """Create the main EcoBiome command parser."""
    parser = argparse.ArgumentParser(
        prog="ecobiome",
        description="EcoBiome scientific ecosystem platform.",
    )

    subparsers = parser.add_subparsers(dest="command")

    explain_parser = subparsers.add_parser(
        "explain",
        help="Explain the upstream causal chain of a variable.",
    )
    explain_parser.add_argument("target")
    explain_parser.add_argument(
        "--knowledge-base",
        type=Path,
        default=Path("src/ecobiome/knowledge/base"),
    )
    explain_parser.add_argument(
        "--maximum-depth",
        type=int,
        default=8,
    )

    add_water_level_parser(subparsers)

    return parser


def explain_command(args: argparse.Namespace) -> int:
    """Load scientific knowledge and print a causal explanation."""
    registry = load_knowledge_directory(args.knowledge_base)
    engine = CausalChainEngine(registry)

    result = engine.trace_to(
        args.target,
        maximum_depth=args.maximum_depth,
    )

    print("=" * 64)
    print("EcoBiome — Causal Explanation")
    print("=" * 64)
    print(f"Variables loaded : {len(registry.variables)}")
    print(f"Relations loaded : {len(registry.relations)}")
    print()
    print(result.text)

    return 0 if result.found else 2


def main(argv: Sequence[str] | None = None) -> int:
    """Run the central EcoBiome command-line interface."""
    arguments = list(argv) if argv is not None else None

    if arguments and arguments[0] == "import-transcript":
        return acquisition_main(arguments)

    parser = build_parser()
    args = parser.parse_args(arguments)

    if args.command == "explain":
        return explain_command(args)

    if args.command == "water-level":
        return water_level_command(args)

    parser.print_help()
    return 0
