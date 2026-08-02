"""Primitive serialization of scientific-journal entries."""

from typing import Any

from ecobiome.journal.event import JournalEvent


def journal_event_to_dict(
    event: JournalEvent,
) -> dict[str, Any]:
    """Convert one journal event to JSON-compatible primitives."""
    return {
        "event_id": str(event.event_id),
        "event_type": event.event_type.value,
        "title": event.title,
        "description": event.description,
        "occurred_at": event.occurred_at.isoformat(),
        "recorded_at": event.recorded_at.isoformat(),
        "project_id": (
            str(event.project_id)
            if event.project_id is not None
            else None
        ),
        "tags": list(event.tags),
        "attributes": dict(event.attributes),
        "payload": dict(event.payload),
        "references": [
            {
                "entity_type": reference.entity_type,
                "entity_id": str(reference.entity_id),
                "relation": reference.relation,
            }
            for reference in event.references
        ],
    }


def journal_timeline_to_dict(
    events: tuple[JournalEvent, ...],
) -> list[dict[str, Any]]:
    """Serialize a complete journal timeline."""
    return [
        journal_event_to_dict(event)
        for event in events
    ]
