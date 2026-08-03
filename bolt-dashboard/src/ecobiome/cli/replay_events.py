"""Command for reconstructing a world from stored events."""

import argparse

from ecobiome.core.events import (
    Event,
    EventBus,
    JsonLinesEventStore,
    create_default_event_registry,
    replay_event_store,
)
from ecobiome.world.persistence import (
    load_world_state,
    save_world_state,
)


def add_replay_events_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the replay-events command to the central parser."""
    parser = subparsers.add_parser(
        "replay-events",
        help=(
            "Reconstruct a WorldState by replaying a persistent "
            "event history."
        ),
    )

    parser.add_argument(
        "--world",
        required=True,
        type=str,
        help="Path to the initial WorldState JSON snapshot.",
    )
    parser.add_argument(
        "--events",
        required=True,
        type=str,
        help="Path to the JSONL event history.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=str,
        help="Path receiving the reconstructed WorldState snapshot.",
    )


def replay_events_command(args: argparse.Namespace) -> int:
    """Replay stored events and save the reconstructed world."""
    from pathlib import Path

    world_path = Path(args.world)
    events_path = Path(args.events)
    output_path = Path(args.output)

    world = load_world_state(world_path)

    store = JsonLinesEventStore(
        path=events_path,
        registry=create_default_event_registry(),
    )

    bus = EventBus()
    bus.subscribe(Event, world.handle_event)

    result = replay_event_store(store, bus)

    save_world_state(world, output_path)

    print("=" * 64)
    print("EcoBiome — Reconstruction du WorldState")
    print("=" * 64)
    print(f"Snapshot initial      : {world_path}")
    print(f"Historique            : {events_path}")
    print(f"Événements chargés    : {result.loaded_event_count}")
    print(f"Événements publiés    : {result.published_event_count}")
    print(f"Livraisons effectuées : {result.delivery_count}")
    print(f"Snapshot reconstruit  : {output_path}")
    print()

    for water_body in world.list_water_bodies():
        print(f"Plan d'eau            : {water_body.name}")
        print(f"Niveau                : {water_body.water_height_m:.3f} m")
        print(f"Volume                : {water_body.volume_liters:.2f} L")
        print()

    return 0
