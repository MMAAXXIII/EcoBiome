"""Integration test for persistent event replay into WorldState."""

from pathlib import Path

import pytest

from ecobiome.core.events import (
    Event,
    EventBus,
    JsonLinesEventStore,
    WaterRemovedEvent,
    create_default_event_registry,
    replay_event_store,
)
from ecobiome.world.water_geometry import RectangularGeometry
from ecobiome.world.water_state import WaterBodyState
from ecobiome.world.world_state import WorldState


def test_jsonl_replay_reconstructs_world_state(
    tmp_path: Path,
) -> None:
    event_path = tmp_path / "events.jsonl"

    store = JsonLinesEventStore(
        path=event_path,
        registry=create_default_event_registry(),
    )

    first_event = WaterRemovedEvent(
        water_body_name="Aquarium principal",
        removed_height_m=0.10,
        removed_volume_liters=60.0,
        remaining_volume_liters=300.0,
    )
    second_event = WaterRemovedEvent(
        water_body_name="Aquarium principal",
        removed_height_m=0.05,
        removed_volume_liters=30.0,
        remaining_volume_liters=270.0,
    )

    store.append(first_event)
    store.append(second_event)

    world = WorldState()
    world.add_water_body(
        WaterBodyState(
            name="Aquarium principal",
            geometry=RectangularGeometry(
                length_m=1.20,
                width_m=0.50,
                height_m=0.60,
            ),
            water_height_m=0.60,
        )
    )

    bus = EventBus()
    bus.subscribe(Event, world.handle_event)

    result = replay_event_store(store, bus)
    aquarium = world.get_water_body("Aquarium principal")

    assert result.loaded_event_count == 2
    assert result.delivery_count == 2
    assert world.processed_event_count == 2
    assert aquarium.water_height_m == pytest.approx(0.45)
    assert aquarium.volume_liters == pytest.approx(270.0)
