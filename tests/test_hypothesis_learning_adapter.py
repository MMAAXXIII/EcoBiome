"""Tests for learning-informed hypothesis ranking."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from ecobiome.reasoning.abduction import (
    HypothesisProposal,
)
from ecobiome.reasoning.learning import (
    HypothesisLearningAdapter,
    InMemoryLearningEventStore,
    JsonlLearningEventStore,
    LearningOutcome,
    hypothesis_uuid,
)

OCCURRED_AT = datetime(
    2026,
    8,
    2,
    14,
    0,
    tzinfo=UTC,
)

EVIDENCE_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)


def make_proposal(
    identifier: str,
    *,
    confidence: float,
) -> HypothesisProposal:
    """Create one deterministic hypothesis proposal."""
    return HypothesisProposal(
        identifier=identifier,
        title=identifier,
        statement=f"Possible cause: {identifier}.",
        confidence=confidence,
        source_rule="abduction.camera_lux_contradiction",
        supporting_observation_ids=(),
        rationale="Camera/lux contradiction.",
    )


def test_hypothesis_uuid_is_deterministic() -> None:
    first = hypothesis_uuid(
        "hardware.possible_camera_failure"
    )

    second = hypothesis_uuid(
        "hardware.possible_camera_failure"
    )

    assert first == second


def test_different_identifiers_have_different_uuids() -> None:
    assert hypothesis_uuid(
        "hardware.possible_camera_failure"
    ) != hypothesis_uuid(
        "vision.possible_lens_obstruction"
    )


def test_identifier_whitespace_is_normalized() -> None:
    assert hypothesis_uuid(
        " hardware.possible_camera_failure "
    ) == hypothesis_uuid(
        "hardware.possible_camera_failure"
    )


def test_invalid_identifier_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="domain prefix",
    ):
        hypothesis_uuid("camera_failure")


def test_proposal_without_history_is_unchanged() -> None:
    proposal = make_proposal(
        "hardware.possible_camera_failure",
        confidence=0.45,
    )

    adapter = HypothesisLearningAdapter(
        InMemoryLearningEventStore()
    )

    assert adapter.adjust((proposal,)) == (proposal,)


def test_confirmed_outcome_increases_future_confidence() -> None:
    proposal = make_proposal(
        "vision.possible_lens_obstruction",
        confidence=0.30,
    )

    adapter = HypothesisLearningAdapter(
        InMemoryLearningEventStore()
    )

    event = adapter.record_outcome(
        proposal=proposal,
        experiment_id="camera.clean_lens_and_recapture",
        outcome=LearningOutcome.CONFIRMED,
        strength=0.50,
        occurred_at=OCCURRED_AT,
        evidence_ids=(EVIDENCE_ID,),
    )

    adjusted = adapter.adjust((proposal,))[0]

    assert event.confidence_before == pytest.approx(0.30)
    assert event.confidence_after == pytest.approx(0.65)
    assert adjusted.confidence == pytest.approx(0.65)


def test_refuted_outcome_reduces_future_confidence() -> None:
    proposal = make_proposal(
        "hardware.possible_camera_failure",
        confidence=0.80,
    )

    adapter = HypothesisLearningAdapter(
        InMemoryLearningEventStore()
    )

    adapter.record_outcome(
        proposal=proposal,
        experiment_id="camera.clean_lens_and_recapture",
        outcome=LearningOutcome.REFUTED,
        strength=0.75,
        occurred_at=OCCURRED_AT,
    )

    adjusted = adapter.adjust((proposal,))[0]

    assert adjusted.confidence == pytest.approx(0.20)


def test_repeated_learning_continues_from_latest_confidence() -> None:
    proposal = make_proposal(
        "vision.possible_lens_obstruction",
        confidence=0.40,
    )

    adapter = HypothesisLearningAdapter(
        InMemoryLearningEventStore()
    )

    first = adapter.record_outcome(
        proposal=proposal,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.CONFIRMED,
        strength=0.50,
        occurred_at=OCCURRED_AT,
    )

    second = adapter.record_outcome(
        proposal=proposal,
        experiment_id="camera.second_capture",
        outcome=LearningOutcome.CONFIRMED,
        strength=0.50,
        occurred_at=OCCURRED_AT,
    )

    assert first.confidence_after == pytest.approx(0.70)
    assert second.confidence_before == pytest.approx(0.70)
    assert second.confidence_after == pytest.approx(0.85)


def test_learning_can_change_proposal_ranking() -> None:
    camera = make_proposal(
        "hardware.possible_camera_failure",
        confidence=0.60,
    )

    lens = make_proposal(
        "vision.possible_lens_obstruction",
        confidence=0.30,
    )

    adapter = HypothesisLearningAdapter(
        InMemoryLearningEventStore()
    )

    adapter.record_outcome(
        proposal=lens,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.CONFIRMED,
        strength=0.80,
        occurred_at=OCCURRED_AT,
    )

    ranked = adapter.adjust((camera, lens))

    assert ranked[0].identifier == (
        "vision.possible_lens_obstruction"
    )
    assert ranked[0].confidence == pytest.approx(0.86)
    assert ranked[1].identifier == (
        "hardware.possible_camera_failure"
    )


def test_adjustment_preserves_proposal_traceability() -> None:
    proposal = make_proposal(
        "vision.possible_lens_obstruction",
        confidence=0.30,
    )

    adapter = HypothesisLearningAdapter(
        InMemoryLearningEventStore()
    )

    adapter.record_outcome(
        proposal=proposal,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.CONFIRMED,
        strength=0.50,
        occurred_at=OCCURRED_AT,
    )

    adjusted = adapter.adjust((proposal,))[0]

    assert adjusted.identifier == proposal.identifier
    assert adjusted.title == proposal.title
    assert adjusted.statement == proposal.statement
    assert adjusted.source_rule == proposal.source_rule
    assert adjusted.rationale == proposal.rationale
    assert (
        adjusted.supporting_observation_ids
        == proposal.supporting_observation_ids
    )


def test_jsonl_history_affects_new_adapter_instance(
    tmp_path: Path,
) -> None:
    path = tmp_path / "learning.jsonl"

    proposal = make_proposal(
        "vision.possible_lens_obstruction",
        confidence=0.30,
    )

    first_adapter = HypothesisLearningAdapter(
        JsonlLearningEventStore(path)
    )

    first_adapter.record_outcome(
        proposal=proposal,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.CONFIRMED,
        strength=0.50,
        occurred_at=OCCURRED_AT,
    )

    reopened_adapter = HypothesisLearningAdapter(
        JsonlLearningEventStore(path)
    )

    adjusted = reopened_adapter.adjust((proposal,))[0]

    assert adjusted.confidence == pytest.approx(0.65)
