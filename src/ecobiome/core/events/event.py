"""Core event models used throughout EcoBiome."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class Event:
    """Base class for every event circulating through EcoBiome."""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class WaterRemovedEvent(Event):
    """Report that water has been removed from a water body."""

    water_body_name: str
    removed_height_m: float
    removed_volume_liters: float
    remaining_volume_liters: float
    cause: str = "user_removal"
    note: str = ""

    def __post_init__(self) -> None:
        """Validate and normalize the event payload."""
        water_body_name = self.water_body_name.strip()
        cause = self.cause.strip().lower()
        note = self.note.strip()

        if not water_body_name:
            raise ValueError(
                "WaterRemovedEvent requires a water-body name."
            )

        if self.removed_height_m < 0:
            raise ValueError(
                "removed_height_m cannot be negative."
            )

        if self.removed_volume_liters < 0:
            raise ValueError(
                "removed_volume_liters cannot be negative."
            )

        if self.remaining_volume_liters < 0:
            raise ValueError(
                "remaining_volume_liters cannot be negative."
            )

        if not cause:
            raise ValueError(
                "WaterRemovedEvent requires a cause."
            )

        object.__setattr__(
            self,
            "water_body_name",
            water_body_name,
        )
        object.__setattr__(self, "cause", cause)
        object.__setattr__(self, "note", note)
