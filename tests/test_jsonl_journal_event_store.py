"""Tests for persistent JSONLines scientific journals."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from ecobiome.integrations.journal import (
    JournalIntegrationService,
)
from ecobiome.journal import (
    JournalEvent,
    JournalEventType,
    JournalQuery,
    JournalReference,
    JsonlJournalEventStore,
    ScientificJournal,
)

OCCURRED_AT = datetime(
    2026,
    8,
    2,
    18,
    42,
    tzinfo=UTC,
)

RECORDED_AT = OCCURRED_AT + timedelta(
    seconds=10
)

PROJECT_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)

EVENT_ID = UUID(
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
)

SECOND_EVENT_ID = UUID(
    "cccccccc-cccc-cccc-cccc-cccccccccccc"
)

MEDIA_ID = UUID(
    "dddddddd-dddd-dddd-dddd-dddddddddddd"
)

HYPOTHESIS_ID = UUID(
    "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
)


def make_event(
    *,
    event_id: UUID = EVENT_ID,
    event_type: JournalEventType = (
        JournalEventType.BIOLOGICAL_EVENT
    ),
    title: str = "Naissance de mes premiers guppys",
    occurred_at: datetime = OCCURRED_AT,
) -> JournalEvent:
    """Create one deterministic journal event."""
    return JournalEvent(
        event_id=event_id,
        event_type=event_type,
        title=title,
        description="Premiers alevins observés.",
        occurred_at=occurred_at,
        recorded_at=RECORDED_AT,
        project_id=PROJECT_ID,
        tags=("guppy", "reproduction", "alevins"),
        attributes=(
            ("aquarium", "principal"),
            ("species", "Poecilia reticulata"),
        ),
        payload=(
            ("estimated_count", 18),
            ("confirmed", True),
            ("ratio", 0.75),
            ("optional_note", None),
            ("media_id", MEDIA_ID),
            ("measured_at", OCCURRED_AT),
            (
                "evidence_ids",
                (MEDIA_ID, HYPOTHESIS_ID),
            ),
            (
                "water_parameters",
                {
                    "temperature": 25.2,
                    "ph": 7.3,
                },
            ),
            (
                "observations",
                ["alevins", "plantes flottantes"],
            ),
        ),
        references=(
            JournalReference(
                entity_type="media_asset",
                entity_id=MEDIA_ID,
                relation="illustrated_by",
            ),
        ),
    )


def test_missing_file_returns_empty_store(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"
    store = JsonlJournalEventStore(path)

    assert store.path == path
    assert store.all() == ()
    assert store.count() == 0


def test_event_survives_store_recreation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"
    event = make_event()

    JsonlJournalEventStore(path).append(event)

    reopened = JsonlJournalEventStore(path)

    assert reopened.all() == (event,)
    assert reopened.get(EVENT_ID) == event


def test_complex_payload_types_survive_round_trip(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"
    event = make_event()

    JsonlJournalEventStore(path).append(event)

    restored = JsonlJournalEventStore(path).get(
        EVENT_ID
    )

    payload = restored.payload_map

    assert payload["estimated_count"] == 18
    assert payload["confirmed"] is True
    assert payload["ratio"] == pytest.approx(0.75)
    assert payload["optional_note"] is None
    assert payload["media_id"] == MEDIA_ID
    assert payload["measured_at"] == OCCURRED_AT
    assert payload["evidence_ids"] == (
        MEDIA_ID,
        HYPOTHESIS_ID,
    )
    assert payload["water_parameters"] == {
        "temperature": 25.2,
        "ph": 7.3,
    }
    assert payload["observations"] == [
        "alevins",
        "plantes flottantes",
    ]


def test_events_are_loaded_chronologically(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"
    store = JsonlJournalEventStore(path)

    later = make_event(
        event_id=SECOND_EVENT_ID,
        title="Later event",
        occurred_at=OCCURRED_AT + timedelta(hours=1),
    )

    earlier = make_event(
        event_id=EVENT_ID,
        title="Earlier event",
        occurred_at=OCCURRED_AT,
    )

    store.append(later)
    store.append(earlier)

    assert store.all() == (
        earlier,
        later,
    )


def test_duplicate_identifier_is_rejected_on_append(
    tmp_path: Path,
) -> None:
    store = JsonlJournalEventStore(
        tmp_path / "journal.jsonl"
    )

    event = make_event()
    store.append(event)

    with pytest.raises(
        ValueError,
        match="Duplicate journal event identifier",
    ):
        store.append(event)


def test_duplicate_identifier_inside_file_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"
    store = JsonlJournalEventStore(path)
    store.append(make_event())

    serialized = path.read_text(
        encoding="utf-8"
    )

    with path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as stream:
        stream.write(serialized)

    with pytest.raises(
        ValueError,
        match="Duplicate journal event identifier",
    ):
        store.all()


def test_invalid_json_reports_line_number(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"

    path.write_text(
        "\n{invalid-json}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="line 2",
    ):
        JsonlJournalEventStore(path).all()


def test_non_object_json_line_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"

    path.write_text(
        '["not", "an", "event"]\n',
        encoding="utf-8",
    )

    with pytest.raises(
        TypeError,
        match="must contain a JSON object",
    ):
        JsonlJournalEventStore(path).all()


def test_invalid_event_reports_line_number(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"

    path.write_text(
        '{"event_id": "incomplete"}\n',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Invalid journal event at line 1",
    ):
        JsonlJournalEventStore(path).all()


def test_unknown_identifier_is_rejected(
    tmp_path: Path,
) -> None:
    store = JsonlJournalEventStore(
        tmp_path / "journal.jsonl"
    )

    with pytest.raises(
        KeyError,
        match="Unknown journal event identifier",
    ):
        store.get(EVENT_ID)


def test_parent_directory_is_created(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "nested"
        / "journals"
        / "events.jsonl"
    )

    store = JsonlJournalEventStore(path)
    store.append(make_event())

    assert path.is_file()


def test_scientific_journal_uses_persistent_store(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"

    first_journal = ScientificJournal(
        JsonlJournalEventStore(path)
    )

    recorded = first_journal.record(
        event_type=JournalEventType.NOTE,
        title="Aquarium observation",
        description="Les alevins restent près des plantes.",
        occurred_at=OCCURRED_AT,
        project_id=PROJECT_ID,
        tags=("guppy", "alevins"),
    )

    reopened_journal = ScientificJournal(
        JsonlJournalEventStore(path)
    )

    assert reopened_journal.get(
        recorded.event_id
    ) == recorded

    assert reopened_journal.timeline(
        JournalQuery(
            project_id=PROJECT_ID,
            tags=("guppy",),
            text="plantes",
        )
    ) == (recorded,)


def test_bridge_idempotence_survives_restart(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"

    first_journal = ScientificJournal(
        JsonlJournalEventStore(path)
    )

    first_integrations = JournalIntegrationService(
        first_journal
    )

    media_event = make_event(
        event_type=JournalEventType.MEDIA,
        title="Guppy photograph",
    )

    first_journal.store.append(media_event)

    reopened_journal = ScientificJournal(
        JsonlJournalEventStore(path)
    )

    assert reopened_journal.timeline() == (
        media_event,
    )

    integrations = JournalIntegrationService(
        reopened_journal
    )

    assert integrations.media is not None
    assert first_integrations.media is not None


def test_unsupported_payload_type_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"

    event = JournalEvent(
        event_type=JournalEventType.NOTE,
        title="Unsupported payload",
        occurred_at=OCCURRED_AT,
        payload=(
            ("unsupported", object()),
        ),
    )

    with pytest.raises(
        TypeError,
        match="Unsupported journal payload value type",
    ):
        JsonlJournalEventStore(path).append(event)

    assert not path.exists()


def test_naive_payload_datetime_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"

    event = JournalEvent(
        event_type=JournalEventType.NOTE,
        title="Naive payload datetime",
        occurred_at=OCCURRED_AT,
        payload=(
            (
                "measured_at",
                OCCURRED_AT.replace(tzinfo=None),
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="payload datetimes must be timezone-aware",
    ):
        JsonlJournalEventStore(path).append(event)
