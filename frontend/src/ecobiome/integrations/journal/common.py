"""Shared helpers for idempotent scientific-journal bridges."""

from uuid import UUID

from ecobiome.journal import (
    JournalEvent,
    JournalEventType,
    JournalQuery,
    ScientificJournal,
)


def find_linked_event(
    journal: ScientificJournal,
    *,
    entity_type: str,
    entity_id: UUID,
    event_type: JournalEventType,
) -> JournalEvent | None:
    """Return an existing event linked to one exact entity."""
    normalized_entity_type = entity_type.strip().lower()

    candidates = journal.timeline(
        JournalQuery(
            event_types=(event_type,),
            referenced_entity_id=entity_id,
        )
    )

    for event in candidates:
        for reference in event.references:
            if (
                reference.entity_type == normalized_entity_type
                and reference.entity_id == entity_id
            ):
                return event

    return None
