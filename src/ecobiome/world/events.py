"""Canonical water-level events for EcoBiome world operations."""

from enum import StrEnum
from pathlib import Path

from ecobiome.core.events import (
    JsonLinesEventStore,
    WaterRemovedEvent,
    create_default_event_registry,
)
from ecobiome.world.water_level import WaterLevelChangeResult


class WaterLevelEventType(StrEnum):
    """Supported causes of water-level reduction."""

    USER_REMOVAL = "user_removal"
    EVAPORATION = "evaporation"
    LEAK = "leak"
    DRAINAGE = "drainage"
    OVERFLOW = "overflow"
    UNKNOWN = "unknown"


def create_water_level_event(
    *,
    water_body_name: str,
    event_type: WaterLevelEventType,
    change: WaterLevelChangeResult,
    note: str = "",
) -> WaterRemovedEvent:
    """Create one canonical event from a completed level calculation."""
    return WaterRemovedEvent(
        water_body_name=water_body_name,
        removed_height_m=change.removed_height_m,
        removed_volume_liters=change.removed_volume_liters,
        remaining_volume_liters=change.remaining_volume_liters,
        cause=event_type.value,
        note=note,
    )


def append_event_jsonl(
    event: WaterRemovedEvent,
    path: Path,
) -> None:
    """Append one canonical event to a replayable JSONL history."""
    store = JsonLinesEventStore(
        path=path,
        registry=create_default_event_registry(),
    )
    store.append(event)
