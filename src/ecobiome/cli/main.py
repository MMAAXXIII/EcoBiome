"""Central command-line interface for EcoBiome."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path


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

    from ecobiome.cli.replay_events import add_replay_events_parser
    from ecobiome.cli.water_level import add_water_level_parser

    add_water_level_parser(subparsers)
    add_replay_events_parser(subparsers)

    return parser


def explain_command(args: argparse.Namespace) -> int:
    """Load scientific knowledge and print a causal explanation."""
    from ecobiome.knowledge.directory_loader import load_knowledge_directory
    from ecobiome.reasoning import CausalChainEngine

    registry = load_knowledge_directory(args.knowledge_base)
    engine = CausalChainEngine(registry)

    result = engine.trace_to(
        args.target,
        maximum_depth=args.maximum_depth,
    )

    print("=" * 64)
    print("EcoBiome - Causal Explanation")
    print("=" * 64)
    print(f"Variables loaded : {len(registry.variables)}")
    print(f"Relations loaded : {len(registry.relations)}")
    print()
    print(result.text)

    return 0 if result.found else 2


def main(argv: Sequence[str] | None = None) -> int:
    """Run the central EcoBiome command-line interface."""
    arguments = list(argv) if argv is not None else sys.argv[1:]

    if arguments and arguments[0] == "collector":
        from ecobiome.knowledge_acquisition.collector_cli import (
            main as collector_main,
        )

        return collector_main(arguments[1:])

    if arguments and arguments[0] == "import-transcript":
        from ecobiome.knowledge_acquisition.cli import (
            main as acquisition_main,
        )

        return acquisition_main(arguments)

    parser = build_parser()
    args = parser.parse_args(arguments)

    if args.command == "explain":
        return explain_command(args)

    if args.command == "water-level":
        from ecobiome.cli.water_level import water_level_command

        return water_level_command(args)

    if args.command == "replay-events":
        from ecobiome.cli.replay_events import replay_events_command

        return replay_events_command(args)

    parser.print_help()
    return 0