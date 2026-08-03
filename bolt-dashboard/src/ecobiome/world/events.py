"""Environmental events affecting bodies of water."""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from ecobiome.world.water_level import WaterLevelChangeResult


class WaterLevelEventType(StrEnum):
    """Supported causes of water-level reduction."""

    USER_REMOVAL = "user_removal"
    EVAPORATION = "evaporation"
    LEAK = "leak"
    DRAINAGE = "drainage"
    OVERFLOW = "overflow"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class WaterLevelEvent:
    """Record one traceable change in water level."""

    water_body_name: str
    event_type: WaterLevelEventType
    previous_height_m: float
    new_height_m: float
    removed_height_m: float
    removed_volume_m3: float
    remaining_volume_m3: float
    free_surface_area_m2: float
    wetted_surface_area_m2: float
    note: str = ""
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        """Validate and normalize the event."""
        name = self.water_body_name.strip()

        if not name:
            raise ValueError("A water-level event requires a water-body name.")

        if self.removed_height_m < 0:
            raise ValueError("removed_height_m cannot be negative.")

        if self.removed_volume_m3 < 0:
            raise ValueError("removed_volume_m3 cannot be negative.")

        object.__setattr__(self, "water_body_name", name)
        object.__setattr__(self, "note", self.note.strip())

    @property
    def removed_volume_liters(self) -> float:
        """Return the removed volume in liters."""
        return self.removed_volume_m3 * 1_000

    def to_record(self) -> dict[str, object]:
        """Convert the event into a JSON-compatible record."""
        return {
            "schema_version": "0.1",
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
            "water_body_name": self.water_body_name,
            "event_type": self.event_type.value,
            "previous_height_m": self.previous_height_m,
            "new_height_m": self.new_height_m,
            "removed_height_m": self.removed_height_m,
            "removed_volume_m3": self.removed_volume_m3,
            "removed_volume_liters": self.removed_volume_liters,
            "remaining_volume_m3": self.remaining_volume_m3,
            "free_surface_area_m2": self.free_surface_area_m2,
            "wetted_surface_area_m2": self.wetted_surface_area_m2,
            "note": self.note,
        }


def create_water_level_event(
    *,
    water_body_name: str,
    event_type: WaterLevelEventType,
    change: WaterLevelChangeResult,
    note: str = "",
) -> WaterLevelEvent:
    """Create an event from a completed geometry calculation."""
    return WaterLevelEvent(
        water_body_name=water_body_name,
        event_type=event_type,
        previous_height_m=change.previous_height_m,
        new_height_m=change.new_height_m,
        removed_height_m=change.removed_height_m,
        removed_volume_m3=change.removed_volume_m3,
        remaining_volume_m3=change.remaining_volume_m3,
        free_surface_area_m2=change.free_surface_area_m2,
        wetted_surface_area_m2=change.wetted_surface_area_m2,
        note=note,
    )


def append_event_jsonl(
    event: WaterLevelEvent,
    path: Path,
) -> None:
    """Append one event to a newline-delimited JSON history."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as file:
        json.dump(event.to_record(), file, ensure_ascii=False)
        file.write("\n")
