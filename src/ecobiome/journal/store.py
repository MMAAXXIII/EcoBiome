"""Storage contracts and in-memory implementation for journals."""

from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from ecobiome.journal.event import JournalEvent


class JournalEventStore(Protocol):
    """Contract implemented by journal-event repositories."""

    def append(self, event: JournalEvent) -> None:
        """Persist one journal event."""

    def get(self, event_id: UUID) -> JournalEvent:
        """Return one journal event."""

    def all(self) -> tuple[JournalEvent, ...]:
        """Return every journal event chronologically."""


class InMemoryJournalEventStore:
    """Store journal events in memory with deterministic ordering."""

    def __init__(
        self,
        events: Iterable[JournalEvent] = (),
    ) -> None:
        self._events_by_id: dict[UUID, JournalEvent] = {}

        for event in events:
            self.append(event)

    def append(self, event: JournalEvent) -> None:
        """Append one event while rejecting duplicate identifiers."""
        if event.event_id in self._events_by_id:
            raise ValueError(
                f"Duplicate journal event identifier: "
                f"{event.event_id}."
            )

        self._events_by_id[event.event_id] = event

    def get(self, event_id: UUID) -> JournalEvent:
        """Return one event by identifier."""
        try:
            return self._events_by_id[event_id]
        except KeyError as error:
            raise KeyError(
                f"Unknown journal event identifier: {event_id}."
            ) from error

    def all(self) -> tuple[JournalEvent, ...]:
        """Return all events in deterministic chronological order."""
        return tuple(
            sorted(
                self._events_by_id.values(),
                key=lambda event: (
                    event.occurred_at,
                    event.recorded_at,
                    str(event.event_id),
                ),
            )
        )

    def count(self) -> int:
        """Return the number of stored journal events."""
        return len(self._events_by_id)
