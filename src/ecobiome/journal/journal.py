"""Creation and querying of unified scientific timelines."""

from collections.abc import Iterable
from datetime import datetime
from typing import Any
from uuid import UUID

from ecobiome.journal.event import JournalEvent
from ecobiome.journal.event_type import JournalEventType
from ecobiome.journal.query import JournalQuery
from ecobiome.journal.reference import JournalReference
from ecobiome.journal.store import JournalEventStore


class ScientificJournal:
    """Create and query one unified EcoBiome event timeline."""

    def __init__(
        self,
        store: JournalEventStore,
    ) -> None:
        self._store = store

    @property
    def store(self) -> JournalEventStore:
        """Return the configured journal-event store."""
        return self._store

    def record(
        self,
        *,
        event_type: JournalEventType,
        title: str,
        occurred_at: datetime,
        description: str = "",
        project_id: UUID | None = None,
        references: tuple[JournalReference, ...] = (),
        tags: tuple[str, ...] = (),
        attributes: tuple[tuple[str, str], ...] = (),
        payload: tuple[tuple[str, Any], ...] = (),
    ) -> JournalEvent:
        """Create and persist one journal event."""
        event = JournalEvent(
            event_type=event_type,
            title=title,
            occurred_at=occurred_at,
            description=description,
            project_id=project_id,
            references=references,
            tags=tags,
            attributes=attributes,
            payload=payload,
        )

        self._store.append(event)

        return event

    def get(self, event_id: UUID) -> JournalEvent:
        """Return one journal event by identifier."""
        return self._store.get(event_id)

    def timeline(
        self,
        query: JournalQuery | None = None,
    ) -> tuple[JournalEvent, ...]:
        """Return a filtered chronological timeline."""
        events = self._store.all()

        if query is None:
            return events

        event_type_filter = set(query.event_types)
        tag_filter = set(query.tags)

        filtered: list[JournalEvent] = []

        for event in events:
            if (
                query.project_id is not None
                and event.project_id != query.project_id
            ):
                continue

            if (
                event_type_filter
                and event.event_type not in event_type_filter
            ):
                continue

            if not tag_filter.issubset(set(event.tags)):
                continue

            if (
                query.occurred_from is not None
                and event.occurred_at < query.occurred_from
            ):
                continue

            if (
                query.occurred_to is not None
                and event.occurred_at > query.occurred_to
            ):
                continue

            if (
                query.referenced_entity_id is not None
                and not self._references_entity(
                    event.references,
                    query.referenced_entity_id,
                )
            ):
                continue

            if query.text:
                searchable_text = " ".join(
                    (
                        event.title,
                        event.description,
                        *event.tags,
                        *(
                            f"{key} {value}"
                            for key, value in event.attributes
                        ),
                    )
                ).casefold()

                if query.text not in searchable_text:
                    continue

            filtered.append(event)

        return tuple(filtered)

    def latest(
        self,
        *,
        limit: int = 10,
        query: JournalQuery | None = None,
    ) -> tuple[JournalEvent, ...]:
        """Return the newest events in reverse chronological order."""
        if limit < 0:
            raise ValueError(
                "Journal latest-event limit cannot be negative."
            )

        events = self.timeline(query)

        if limit == 0:
            return ()

        return tuple(reversed(events[-limit:]))

    @staticmethod
    def _references_entity(
        references: Iterable[JournalReference],
        entity_id: UUID,
    ) -> bool:
        """Return whether references contain one entity identifier."""
        return any(
            reference.entity_id == entity_id
            for reference in references
        )
