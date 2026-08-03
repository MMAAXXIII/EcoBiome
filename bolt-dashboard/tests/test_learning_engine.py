"""Tests for traceable scientific learning memory."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from ecobiome.reasoning.learning import (
    InMemoryLearningEventStore,
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

EVIDENCE_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)

OCCURRED_AT = datetime(
    2026,
    8,
    2,
    12,
    0,
    tzinfo=UTC,
)


def test_confirmed_result_increases_confidence() -> None:
    engine = LearningEngine(
        InMemoryLearningEventStore()
    )

    event = engine.record(
        hypothesis_id=HYPOTHESIS_ID,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.CONFIRMED,
        confidence_before=0.40,
        strength=0.50,
        occurred_at=OCCURRED_AT,
        evidence_ids=(EVIDENCE_ID,),
    )

    assert event.confidence_before == pytest.approx(0.40)
    assert event.confidence_after == pytest.approx(0.70)
    assert event.confidence_delta == pytest.approx(0.30)
    assert event.changed_confidence is True


def test_refuted_result_reduces_confidence() -> None:
    engine = LearningEngine(
        InMemoryLearningEventStore()
    )

    event = engine.record(
        hypothesis_id=HYPOTHESIS_ID,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.REFUTED,
        confidence_before=0.80,
        strength=0.75,
        occurred_at=OCCURRED_AT,
    )

    assert event.confidence_after == pytest.approx(0.20)
    assert event.confidence_delta == pytest.approx(-0.60)


def test_inconclusive_result_preserves_confidence() -> None:
    engine = LearningEngine(
        InMemoryLearningEventStore()
    )

    event = engine.record(
        hypothesis_id=HYPOTHESIS_ID,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.INCONCLUSIVE,
        confidence_before=0.45,
        strength=1.0,
        occurred_at=OCCURRED_AT,
    )

    assert event.confidence_after == pytest.approx(0.45)
    assert event.changed_confidence is False


def test_learning_history_is_summarized() -> None:
    store = InMemoryLearningEventStore()
    engine = LearningEngine(store)

    first = engine.record(
        hypothesis_id=HYPOTHESIS_ID,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.CONFIRMED,
        confidence_before=0.40,
        strength=0.50,
        occurred_at=OCCURRED_AT,
    )

    second = engine.record(
        hypothesis_id=HYPOTHESIS_ID,
        experiment_id="camera.second_capture",
        outcome=LearningOutcome.REFUTED,
        confidence_before=first.confidence_after,
        strength=0.20,
        occurred_at=OCCURRED_AT + timedelta(minutes=5),
    )

    engine.record(
        hypothesis_id=HYPOTHESIS_ID,
        experiment_id="camera.manual_inspection",
        outcome=LearningOutcome.INCONCLUSIVE,
        confidence_before=second.confidence_after,
        strength=0.80,
        occurred_at=OCCURRED_AT + timedelta(minutes=10),
    )

    summary = engine.summarize(HYPOTHESIS_ID)

    assert summary.has_history is True
    assert summary.event_count == 3
    assert summary.confirmed_count == 1
    assert summary.refuted_count == 1
    assert summary.inconclusive_count == 1
    assert summary.current_confidence == pytest.approx(0.56)
    assert len(summary.event_ids) == 3


def test_history_is_isolated_by_hypothesis() -> None:
    store = InMemoryLearningEventStore()
    engine = LearningEngine(store)

    engine.record(
        hypothesis_id=HYPOTHESIS_ID,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.CONFIRMED,
        confidence_before=0.40,
        strength=0.50,
        occurred_at=OCCURRED_AT,
    )

    engine.record(
        hypothesis_id=OTHER_HYPOTHESIS_ID,
        experiment_id="lighting.compare_lux",
        outcome=LearningOutcome.REFUTED,
        confidence_before=0.60,
        strength=0.50,
        occurred_at=OCCURRED_AT,
    )

    assert engine.summarize(HYPOTHESIS_ID).event_count == 1
    assert (
        engine.summarize(OTHER_HYPOTHESIS_ID).event_count
        == 1
    )


def test_empty_history_returns_no_current_confidence() -> None:
    summary = LearningEngine(
        InMemoryLearningEventStore()
    ).summarize(HYPOTHESIS_ID)

    assert summary.has_history is False
    assert summary.event_count == 0
    assert summary.current_confidence is None


def test_duplicate_learning_event_is_rejected() -> None:
    event = LearningEvent(
        hypothesis_id=HYPOTHESIS_ID,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.CONFIRMED,
        confidence_before=0.40,
        confidence_after=0.70,
        occurred_at=OCCURRED_AT,
    )

    store = InMemoryLearningEventStore([event])

    with pytest.raises(
        ValueError,
        match="Duplicate learning-event identifier",
    ):
        store.append(event)


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        LearningEvent(
            hypothesis_id=HYPOTHESIS_ID,
            experiment_id="camera.clean_lens",
            outcome=LearningOutcome.CONFIRMED,
            confidence_before=0.40,
            confidence_after=0.70,
            occurred_at=OCCURRED_AT.replace(tzinfo=None),
        )


def test_invalid_probability_is_rejected() -> None:
    engine = LearningEngine(
        InMemoryLearningEventStore()
    )

    with pytest.raises(
        ValueError,
        match="strength must be between",
    ):
        engine.record(
            hypothesis_id=HYPOTHESIS_ID,
            experiment_id="camera.clean_lens",
            outcome=LearningOutcome.CONFIRMED,
            confidence_before=0.40,
            strength=1.20,
            occurred_at=OCCURRED_AT,
        )


def test_duplicate_evidence_ids_are_normalized() -> None:
    event = LearningEvent(
        hypothesis_id=HYPOTHESIS_ID,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.CONFIRMED,
        confidence_before=0.40,
        confidence_after=0.70,
        occurred_at=OCCURRED_AT,
        evidence_ids=(EVIDENCE_ID, EVIDENCE_ID),
        notes="  Lens cleaning restored the image.  ",
    )

    assert event.evidence_ids == (EVIDENCE_ID,)
    assert event.notes == "Lens cleaning restored the image."
