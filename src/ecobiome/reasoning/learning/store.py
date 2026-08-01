"""Storage contracts and in-memory persistence for learning events."""

from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from ecobiome.reasoning.learning.event import LearningEvent


class LearningEventStore(Protocol):
    """Storage contract for scientific learning events."""

    def append(self, event: LearningEvent) -> None:
        """Persist one learning event."""

    def load(self) -> tuple[LearningEvent, ...]:
        """Return every stored learning event."""

    def load_for_hypothesis(
        self,
        hypothesis_id: UUID,
    ) -> tuple[LearningEvent, ...]:
        """Return events associated with one hypothesis."""


class InMemoryLearningEventStore:
    """Store learning events deterministically in memory."""

    def __init__(
        self,
        events: Iterable[LearningEvent] = (),
    ) -> None:
        self._events: list[LearningEvent] = []
        self._event_ids: set[UUID] = set()

        for event in events:
            self.append(event)

    def append(self, event: LearningEvent) -> None:
        """Append one event while rejecting duplicate identifiers."""
        if event.event_id in self._event_ids:
            raise ValueError(
                f"Duplicate learning-event identifier: "
                f"{event.event_id}."
            )

        self._events.append(event)
        self._event_ids.add(event.event_id)

    def load(self) -> tuple[LearningEvent, ...]:
        """Return all events in deterministic chronological order."""
        return tuple(
            sorted(
                self._events,
                key=lambda event: (
                    event.occurred_at,
                    str(event.event_id),
                ),
            )
        )

    def load_for_hypothesis(
        self,
        hypothesis_id: UUID,
    ) -> tuple[LearningEvent, ...]:
        """Return chronological events for one hypothesis."""
        return tuple(
            event
            for event in self.load()
            if event.hypothesis_id == hypothesis_id
        )
