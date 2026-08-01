"""Tests for JSONLines learning-event persistence."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from ecobiome.reasoning.learning import (
    JsonlLearningEventStore,
    LearningEngine,
    LearningEvent,
    LearningOutcome,
)

HYPOTHESIS_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)

OTHER_HYPOTHESIS_ID = UUID(
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
)

FIRST_EVENT_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)

SECOND_EVENT_ID = UUID(
    "22222222-2222-2222-2222-222222222222"
)

EVIDENCE_ID = UUID(
    "33333333-3333-3333-3333-333333333333"
)

OCCURRED_AT = datetime(
    2026,
    8,
    2,
    12,
    0,
    tzinfo=UTC,
)


def make_event(
    *,
    event_id: UUID = FIRST_EVENT_ID,
    hypothesis_id: UUID = HYPOTHESIS_ID,
    experiment_id: str = "camera.clean_lens",
    outcome: LearningOutcome = LearningOutcome.CONFIRMED,
    occurred_at: datetime = OCCURRED_AT,
) -> LearningEvent:
    """Create one deterministic learning event."""
    return LearningEvent(
        event_id=event_id,
        hypothesis_id=hypothesis_id,
        experiment_id=experiment_id,
        outcome=outcome,
        confidence_before=0.40,
        confidence_after=0.70,
        occurred_at=occurred_at,
        evidence_ids=(EVIDENCE_ID,),
        notes="Lens cleaning restored the image.",
    )


def test_missing_file_returns_empty_store(
    tmp_path: Path,
) -> None:
    path = tmp_path / "learning.jsonl"
    store = JsonlLearningEventStore(path)

    assert store.path == path
    assert store.load() == ()
    assert store.load_for_hypothesis(HYPOTHESIS_ID) == ()


def test_event_survives_store_recreation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "learning.jsonl"
    event = make_event()

    JsonlLearningEventStore(path).append(event)

    reopened_store = JsonlLearningEventStore(path)

    assert reopened_store.load() == (event,)


def test_multiple_events_are_loaded_chronologically(
    tmp_path: Path,
) -> None:
    path = tmp_path / "learning.jsonl"
    store = JsonlLearningEventStore(path)

    later_event = make_event(
        event_id=SECOND_EVENT_ID,
        experiment_id="camera.second_capture",
        occurred_at=OCCURRED_AT + timedelta(minutes=5),
    )

    earlier_event = make_event(
        event_id=FIRST_EVENT_ID,
        occurred_at=OCCURRED_AT,
    )

    store.append(later_event)
    store.append(earlier_event)

    assert store.load() == (
        earlier_event,
        later_event,
    )


def test_history_is_filtered_by_hypothesis(
    tmp_path: Path,
) -> None:
    path = tmp_path / "learning.jsonl"
    store = JsonlLearningEventStore(path)

    first = make_event()

    second = make_event(
        event_id=SECOND_EVENT_ID,
        hypothesis_id=OTHER_HYPOTHESIS_ID,
        experiment_id="lighting.compare_lux",
        outcome=LearningOutcome.REFUTED,
    )

    store.append(first)
    store.append(second)

    assert store.load_for_hypothesis(
        HYPOTHESIS_ID
    ) == (first,)

    assert store.load_for_hypothesis(
        OTHER_HYPOTHESIS_ID
    ) == (second,)


def test_duplicate_event_identifier_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "learning.jsonl"
    store = JsonlLearningEventStore(path)
    event = make_event()

    store.append(event)

    with pytest.raises(
        ValueError,
        match="Duplicate learning-event identifier",
    ):
        store.append(event)


def test_invalid_json_reports_line_number(
    tmp_path: Path,
) -> None:
    path = tmp_path / "learning.jsonl"

    path.write_text(
        "{invalid-json}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="line 1",
    ):
        JsonlLearningEventStore(path).load()


def test_invalid_event_reports_line_number(
    tmp_path: Path,
) -> None:
    path = tmp_path / "learning.jsonl"

    path.write_text(
        '{"valid": true}\n',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Invalid learning event at line 1",
    ):
        JsonlLearningEventStore(path).load()


def test_non_object_json_line_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "learning.jsonl"

    path.write_text(
        '["not", "an", "object"]\n',
        encoding="utf-8",
    )

    with pytest.raises(
        TypeError,
        match="must contain a JSON object",
    ):
        JsonlLearningEventStore(path).load()


def test_duplicate_identifiers_inside_file_are_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "learning.jsonl"
    store = JsonlLearningEventStore(path)
    event = make_event()

    store.append(event)

    line = path.read_text(encoding="utf-8")

    with path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as stream:
        stream.write(line)

    with pytest.raises(
        ValueError,
        match="Duplicate learning-event identifier",
    ):
        store.load()


def test_learning_engine_uses_jsonl_store(
    tmp_path: Path,
) -> None:
    path = tmp_path / "learning.jsonl"

    engine = LearningEngine(
        JsonlLearningEventStore(path)
    )

    recorded = engine.record(
        hypothesis_id=HYPOTHESIS_ID,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.CONFIRMED,
        confidence_before=0.40,
        strength=0.50,
        occurred_at=OCCURRED_AT,
        evidence_ids=(EVIDENCE_ID,),
    )

    reopened_engine = LearningEngine(
        JsonlLearningEventStore(path)
    )

    summary = reopened_engine.summarize(
        HYPOTHESIS_ID
    )

    assert summary.event_count == 1
    assert summary.confirmed_count == 1
    assert summary.current_confidence == pytest.approx(0.70)
    assert summary.event_ids == (recorded.event_id,)


def test_parent_directory_is_created_automatically(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "nested"
        / "learning"
        / "events.jsonl"
    )

    store = JsonlLearningEventStore(path)
    store.append(make_event())

    assert path.is_file()


def test_serialized_line_contains_traceability_fields(
    tmp_path: Path,
) -> None:
    path = tmp_path / "learning.jsonl"

    JsonlLearningEventStore(path).append(
        make_event()
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        ).strip()
    )

    assert payload["event_id"] == str(FIRST_EVENT_ID)
    assert payload["hypothesis_id"] == str(HYPOTHESIS_ID)
    assert payload["experiment_id"] == "camera.clean_lens"
    assert payload["outcome"] == "confirmed"
    assert payload["evidence_ids"] == [str(EVIDENCE_ID)]
    assert payload["occurred_at"] == OCCURRED_AT.isoformat()
