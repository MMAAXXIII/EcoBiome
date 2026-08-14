"""Composable filters for scientific-journal timelines."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ecobiome.journal.event_type import JournalEventType


@dataclass(frozen=True, slots=True, kw_only=True)
class JournalQuery:
    """Describe cumulative filters applied to journal events."""

    project_id: UUID | None = None
    event_types: tuple[JournalEventType, ...] = ()
    tags: tuple[str, ...] = ()
    occurred_from: datetime | None = None
    occurred_to: datetime | None = None
    text: str = ""
    referenced_entity_id: UUID | None = None

    def __post_init__(self) -> None:
        """Validate and normalize journal filters."""
        if (
            self.occurred_from is not None
            and self.occurred_from.tzinfo is None
        ):
            raise ValueError(
                "Journal query start timestamp must be timezone-aware."
            )

        if (
            self.occurred_to is not None
            and self.occurred_to.tzinfo is None
        ):
            raise ValueError(
                "Journal query end timestamp must be timezone-aware."
            )

        if (
            self.occurred_from is not None
            and self.occurred_to is not None
            and self.occurred_from > self.occurred_to
        ):
            raise ValueError(
                "Journal query start cannot follow its end."
            )

        event_types = tuple(
            dict.fromkeys(self.event_types)
        )

        tags = tuple(
            dict.fromkeys(
                tag.strip().lower()
                for tag in self.tags
                if tag.strip()
            )
        )

        object.__setattr__(
            self,
            "event_types",
            event_types,
        )
        object.__setattr__(
            self,
            "tags",
            tags,
        )
        object.__setattr__(
            self,
            "text",
            self.text.strip().casefold(),
        )
