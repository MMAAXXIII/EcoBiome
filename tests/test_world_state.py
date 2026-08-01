"""Tests for the global EcoBiome WorldState."""

import pytest

from ecobiome.core.events import EventBus, WaterRemovedEvent
from ecobiome.world.water_geometry import RectangularGeometry
from ecobiome.world.water_state import WaterBodyState
from ecobiome.world.world_state import WorldState


def make_world() -> WorldState:
    """Create a world containing one rectangular aquarium."""
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

    return world


def make_removal_event() -> WaterRemovedEvent:
    """Create one consistent water-removal event."""
    return WaterRemovedEvent(
        water_body_name="Aquarium principal",
        removed_height_m=0.10,
        removed_volume_liters=60.0,
        remaining_volume_liters=300.0,
    )


def test_world_registers_water_body() -> None:
    world = make_world()

    state = world.get_water_body("Aquarium principal")

    assert world.water_body_count == 1
    assert state.volume_liters == pytest.approx(360.0)


def test_event_bus_updates_world_state() -> None:
    world = make_world()
    bus = EventBus()

    bus.subscribe(WaterRemovedEvent, world.handle_event)

    delivered = bus.publish(make_removal_event())
    updated = world.get_water_body("Aquarium principal")

    assert delivered == 1
    assert updated.water_height_m == pytest.approx(0.50)
    assert updated.volume_liters == pytest.approx(300.0)
    assert world.processed_event_count == 1


def test_same_event_is_not_applied_twice() -> None:
    world = make_world()
    event = make_removal_event()

    world.handle_event(event)
    world.handle_event(event)

    updated = world.get_water_body("Aquarium principal")

    assert updated.water_height_m == pytest.approx(0.50)
    assert world.processed_event_count == 1


def test_inconsistent_removed_volume_is_rejected() -> None:
    world = make_world()

    event = WaterRemovedEvent(
        water_body_name="Aquarium principal",
        removed_height_m=0.10,
        removed_volume_liters=50.0,
        remaining_volume_liters=300.0,
    )

    with pytest.raises(
        ValueError,
        match="removed volume is inconsistent",
    ):
        world.handle_event(event)


def test_inconsistent_remaining_volume_is_rejected() -> None:
    world = make_world()

    event = WaterRemovedEvent(
        water_body_name="Aquarium principal",
        removed_height_m=0.10,
        removed_volume_liters=60.0,
        remaining_volume_liters=250.0,
    )

    with pytest.raises(
        ValueError,
        match="remaining volume is inconsistent",
    ):
        world.handle_event(event)


def test_duplicate_water_body_is_rejected() -> None:
    world = make_world()
    existing = world.get_water_body("Aquarium principal")

    with pytest.raises(ValueError, match="already registered"):
        world.add_water_body(existing)


def test_unknown_water_body_is_reported() -> None:
    world = WorldState()

    with pytest.raises(KeyError, match="Unknown water body"):
        world.get_water_body("Bassin inconnu")
