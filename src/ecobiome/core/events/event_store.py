"""Generic storage interfaces for EcoBiome events."""

from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from ecobiome.core.events.event import Event


class EventStore(Protocol):
    """Storage interface implemented by every event repository."""

    def append(self, event: Event) -> None:
        """Store one event."""

    def load(self) -> tuple[Event, ...]:
        """Return every stored event in insertion order."""

    def contains(self, event_id: UUID) -> bool:
        """Return whether an event identifier is already stored."""

    @property
    def count(self) -> int:
        """Return the number of stored events."""

    def clear(self) -> None:
        """Remove every stored event."""


class InMemoryEventStore:
    """Store events temporarily in process memory."""

    def __init__(
        self,
        events: Iterable[Event] = (),
    ) -> None:
        self._events: list[Event] = []
        self._event_ids: set[UUID] = set()

        for event in events:
            self.append(event)

    def append(self, event: Event) -> None:
        """Store one event while rejecting duplicate identifiers."""
        if event.event_id in self._event_ids:
            raise ValueError(
                f"Event {event.event_id} is already stored."
            )

        self._events.append(event)
        self._event_ids.add(event.event_id)

    def load(self) -> tuple[Event, ...]:
        """Return an immutable snapshot in insertion order."""
        return tuple(self._events)

    def contains(self, event_id: UUID) -> bool:
        """Return whether an event identifier is already stored."""
        return event_id in self._event_ids

    @property
    def count(self) -> int:
        """Return the number of stored events."""
        return len(self._events)

    def clear(self) -> None:
        """Remove every stored event."""
        self._events.clear()
        self._event_ids.clear()
