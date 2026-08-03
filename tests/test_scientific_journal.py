"""Tests for the unified EcoBiome scientific journal."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from ecobiome.journal import (
    InMemoryJournalEventStore,
    JournalEvent,
    JournalEventType,
    JournalQuery,
    JournalReference,
    ScientificJournal,
    journal_event_to_dict,
    journal_timeline_to_dict,
)

OCCURRED_AT = datetime(
    2026,
    8,
    2,
    18,
    42,
    tzinfo=UTC,
)

PROJECT_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)

MEDIA_ID = UUID(
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
)

DIAGNOSTIC_ID = UUID(
    "cccccccc-cccc-cccc-cccc-cccccccccccc"
)


def make_journal() -> ScientificJournal:
    """Create an empty in-memory scientific journal."""
    return ScientificJournal(
        InMemoryJournalEventStore()
    )


def test_record_creates_traceable_journal_event() -> None:
    journal = make_journal()

    event = journal.record(
        event_type=JournalEventType.BIOLOGICAL_EVENT,
        title=" Naissance de mes premiers guppys ",
        description=" Premiers alevins observés. ",
        occurred_at=OCCURRED_AT,
        project_id=PROJECT_ID,
        tags=(
            "Guppy",
            "Alevins",
            "guppy",
        ),
        attributes=(
            ("aquarium", "principal"),
            ("species", "Poecilia reticulata"),
        ),
        payload=(
            ("estimated_count", 18),
        ),
        references=(
            JournalReference(
                entity_type="media_asset",
                entity_id=MEDIA_ID,
                relation="illustrated_by",
            ),
        ),
    )

    assert event.title == (
        "Naissance de mes premiers guppys"
    )
    assert event.description == (
        "Premiers alevins observés."
    )
    assert event.tags == (
        "guppy",
        "alevins",
    )
    assert event.project_id == PROJECT_ID
    assert event.attribute_map["aquarium"] == "principal"
    assert event.payload_map["estimated_count"] == 18
    assert event.references[0].entity_id == MEDIA_ID


def test_store_returns_events_chronologically() -> None:
    journal = make_journal()

    later = journal.record(
        event_type=JournalEventType.NOTE,
        title="Later note",
        occurred_at=OCCURRED_AT + timedelta(hours=1),
    )

    earlier = journal.record(
        event_type=JournalEventType.MEDIA,
        title="First photo",
        occurred_at=OCCURRED_AT,
    )

    assert journal.timeline() == (
        earlier,
        later,
    )


def test_query_filters_by_project_and_event_type() -> None:
    journal = make_journal()

    expected = journal.record(
        event_type=JournalEventType.MEDIA,
        title="Guppy photograph",
        occurred_at=OCCURRED_AT,
        project_id=PROJECT_ID,
    )

    journal.record(
        event_type=JournalEventType.NOTE,
        title="Unrelated note",
        occurred_at=OCCURRED_AT,
    )

    assert journal.timeline(
        JournalQuery(
            project_id=PROJECT_ID,
            event_types=(JournalEventType.MEDIA,),
        )
    ) == (expected,)


def test_query_filters_by_tags_and_text() -> None:
    journal = make_journal()

    expected = journal.record(
        event_type=JournalEventType.BIOLOGICAL_EVENT,
        title="Naissance de guppys",
        description="Alevins près des plantes flottantes.",
        occurred_at=OCCURRED_AT,
        tags=("guppy", "reproduction", "alevins"),
    )

    journal.record(
        event_type=JournalEventType.INTERVENTION,
        title="Taille des tomates",
        occurred_at=OCCURRED_AT,
        tags=("potager",),
    )

    assert journal.timeline(
        JournalQuery(
            tags=("guppy", "alevins"),
            text="plantes flottantes",
        )
    ) == (expected,)


def test_query_filters_by_period() -> None:
    journal = make_journal()

    expected = journal.record(
        event_type=JournalEventType.MEASUREMENT,
        title="Water temperature",
        occurred_at=OCCURRED_AT,
    )

    journal.record(
        event_type=JournalEventType.MEASUREMENT,
        title="Later temperature",
        occurred_at=OCCURRED_AT + timedelta(days=5),
    )

    assert journal.timeline(
        JournalQuery(
            occurred_from=OCCURRED_AT - timedelta(hours=1),
            occurred_to=OCCURRED_AT + timedelta(hours=1),
        )
    ) == (expected,)


def test_query_filters_by_referenced_entity() -> None:
    journal = make_journal()

    expected = journal.record(
        event_type=JournalEventType.DIAGNOSTIC,
        title="Camera diagnostic",
        occurred_at=OCCURRED_AT,
        references=(
            JournalReference(
                entity_type="diagnostic_session",
                entity_id=DIAGNOSTIC_ID,
            ),
        ),
    )

    journal.record(
        event_type=JournalEventType.NOTE,
        title="General note",
        occurred_at=OCCURRED_AT,
    )

    assert journal.timeline(
        JournalQuery(
            referenced_entity_id=DIAGNOSTIC_ID,
        )
    ) == (expected,)


def test_latest_returns_reverse_chronological_events() -> None:
    journal = make_journal()

    first = journal.record(
        event_type=JournalEventType.NOTE,
        title="First",
        occurred_at=OCCURRED_AT,
    )

    second = journal.record(
        event_type=JournalEventType.NOTE,
        title="Second",
        occurred_at=OCCURRED_AT + timedelta(minutes=1),
    )

    third = journal.record(
        event_type=JournalEventType.NOTE,
        title="Third",
        occurred_at=OCCURRED_AT + timedelta(minutes=2),
    )

    assert journal.latest(limit=2) == (
        third,
        second,
    )

    assert first not in journal.latest(limit=2)


def test_duplicate_event_identifier_is_rejected() -> None:
    event = JournalEvent(
        event_type=JournalEventType.NOTE,
        title="Unique event",
        occurred_at=OCCURRED_AT,
    )

    store = InMemoryJournalEventStore((event,))

    with pytest.raises(
        ValueError,
        match="Duplicate journal event identifier",
    ):
        store.append(event)


def test_unknown_event_identifier_is_rejected() -> None:
    journal = make_journal()

    unknown_id = UUID(
        "dddddddd-dddd-dddd-dddd-dddddddddddd"
    )

    with pytest.raises(
        KeyError,
        match="Unknown journal event identifier",
    ):
        journal.get(unknown_id)


def test_naive_event_timestamp_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        JournalEvent(
            event_type=JournalEventType.NOTE,
            title="Invalid event",
            occurred_at=OCCURRED_AT.replace(
                tzinfo=None
            ),
        )


def test_invalid_query_period_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="cannot follow",
    ):
        JournalQuery(
            occurred_from=OCCURRED_AT,
            occurred_to=OCCURRED_AT - timedelta(days=1),
        )


def test_negative_latest_limit_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        make_journal().latest(limit=-1)


def test_event_serialization_contains_references() -> None:
    journal = make_journal()

    event = journal.record(
        event_type=JournalEventType.MEDIA,
        title="Guppy photograph",
        occurred_at=OCCURRED_AT,
        project_id=PROJECT_ID,
        tags=("guppy",),
        references=(
            JournalReference(
                entity_type="media_asset",
                entity_id=MEDIA_ID,
                relation="source",
            ),
        ),
    )

    payload = journal_event_to_dict(event)

    assert payload["event_type"] == "media"
    assert payload["title"] == "Guppy photograph"
    assert payload["project_id"] == str(PROJECT_ID)
    assert payload["tags"] == ["guppy"]
    assert payload["references"] == [
        {
            "entity_type": "media_asset",
            "entity_id": str(MEDIA_ID),
            "relation": "source",
        }
    ]


def test_timeline_serialization_preserves_order() -> None:
    journal = make_journal()

    first = journal.record(
        event_type=JournalEventType.MEDIA,
        title="First photograph",
        occurred_at=OCCURRED_AT,
    )

    second = journal.record(
        event_type=JournalEventType.NOTE,
        title="Later note",
        occurred_at=OCCURRED_AT + timedelta(minutes=1),
    )

    payload = journal_timeline_to_dict(
        journal.timeline()
    )

    assert [
        item["event_id"]
        for item in payload
    ] == [
        str(first.event_id),
        str(second.event_id),
    ]
