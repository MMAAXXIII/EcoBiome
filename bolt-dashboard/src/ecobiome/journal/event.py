"""Immutable entries for chronological scientific journals."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from ecobiome.journal.event_type import JournalEventType
from ecobiome.journal.reference import JournalReference


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True, kw_only=True)
class JournalEvent:
    """Describe one traceable event in an EcoBiome project."""

    event_type: JournalEventType
    title: str
    occurred_at: datetime
    description: str = ""
    project_id: UUID | None = None
    references: tuple[JournalReference, ...] = ()
    tags: tuple[str, ...] = ()
    attributes: tuple[tuple[str, str], ...] = ()
    payload: tuple[tuple[str, Any], ...] = ()
    event_id: UUID = field(default_factory=uuid4)
    recorded_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        """Validate and normalize one journal event."""
        title = self.title.strip()
        description = self.description.strip()

        if not title:
            raise ValueError(
                "Journal event title cannot be empty."
            )

        if self.occurred_at.tzinfo is None:
            raise ValueError(
                "Journal event timestamp must be timezone-aware."
            )

        if self.recorded_at.tzinfo is None:
            raise ValueError(
                "Journal recording timestamp must be timezone-aware."
            )

        normalized_tags = tuple(
            dict.fromkeys(
                tag.strip().lower()
                for tag in self.tags
                if tag.strip()
            )
        )

        normalized_attributes: dict[str, str] = {}

        for raw_key, raw_value in self.attributes:
            key = raw_key.strip()
            value = raw_value.strip()

            if not key:
                raise ValueError(
                    "Journal attribute keys cannot be empty."
                )

            normalized_attributes[key] = value

        normalized_payload: dict[str, Any] = {}

        for raw_key, value in self.payload:
            key = raw_key.strip()

            if not key:
                raise ValueError(
                    "Journal payload keys cannot be empty."
                )

            normalized_payload[key] = value

        normalized_references = tuple(
            dict.fromkeys(self.references)
        )

        object.__setattr__(self, "title", title)
        object.__setattr__(
            self,
            "description",
            description,
        )
        object.__setattr__(
            self,
            "tags",
            normalized_tags,
        )
        object.__setattr__(
            self,
            "attributes",
            tuple(normalized_attributes.items()),
        )
        object.__setattr__(
            self,
            "payload",
            tuple(normalized_payload.items()),
        )
        object.__setattr__(
            self,
            "references",
            normalized_references,
        )

    @property
    def attribute_map(self) -> dict[str, str]:
        """Return journal attributes as an independent dictionary."""
        return dict(self.attributes)

    @property
    def payload_map(self) -> dict[str, Any]:
        """Return the event payload as an independent dictionary."""
        return dict(self.payload)
