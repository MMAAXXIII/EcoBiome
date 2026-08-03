"""Tests for the generic scientific inference engine."""

from uuid import UUID

import pytest

from ecobiome.reasoning import (
    Evidence,
    EvidenceRelation,
    Hypothesis,
    HypothesisStatus,
    InferenceEngine,
    InferenceThresholds,
)

FIRST_OBSERVATION_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)
SECOND_OBSERVATION_ID = UUID(
    "22222222-2222-2222-2222-222222222222"
)


def make_hypothesis(
    *,
    confidence: float = 0.40,
) -> Hypothesis:
    """Create one provisional nitrite hypothesis."""
    return Hypothesis(
        hypothesis_id=UUID(
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        ),
        identifier="chemistry.possible_nitrite_spike",
        title="Possible nitrite spike",
        statement="Nitrite concentration may be increasing.",
        confidence=confidence,
    )


def make_evidence(
    hypothesis: Hypothesis,
    *,
    observation_id: UUID = FIRST_OBSERVATION_ID,
    relation: EvidenceRelation = EvidenceRelation.SUPPORTS,
    weight: float = 0.30,
    quality_score: float = 1.0,
) -> Evidence:
    """Create evidence targeting the supplied hypothesis."""
    return Evidence(
        observation_id=observation_id,
        hypothesis_id=hypothesis.hypothesis_id,
        relation=relation,
        weight=weight,
        quality_score=quality_score,
        explanation="Observation contributes to the hypothesis.",
        source_rule="chemistry.test_rule",
    )


def test_supporting_evidence_increases_confidence() -> None:
    hypothesis = make_hypothesis(confidence=0.40)
    evidence = make_evidence(hypothesis, weight=0.30)

    result = InferenceEngine().revise(
        hypothesis,
        [evidence],
    )

    assert result.revised_hypothesis.confidence == pytest.approx(
        0.70
    )
    assert (
        result.revised_hypothesis.status
        is HypothesisStatus.SUPPORTED
    )
    assert result.supporting_weight == pytest.approx(0.30)
    assert result.contradicting_weight == pytest.approx(0.0)


def test_contradicting_evidence_reduces_confidence() -> None:
    hypothesis = make_hypothesis(confidence=0.82)

    evidence = make_evidence(
        hypothesis,
        relation=EvidenceRelation.CONTRADICTS,
        weight=0.50,
    )

    result = InferenceEngine().revise(
        hypothesis,
        [evidence],
    )

    assert result.revised_hypothesis.confidence == pytest.approx(
        0.32
    )
    assert (
        result.revised_hypothesis.status
        is HypothesisStatus.PENDING
    )
    assert result.net_weight == pytest.approx(-0.50)


def test_multiple_evidence_items_are_combined() -> None:
    hypothesis = make_hypothesis(confidence=0.40)

    evidence = [
        make_evidence(
            hypothesis,
            observation_id=FIRST_OBSERVATION_ID,
            weight=0.20,
        ),
        make_evidence(
            hypothesis,
            observation_id=SECOND_OBSERVATION_ID,
            weight=0.15,
        ),
        make_evidence(
            hypothesis,
            relation=EvidenceRelation.CONTRADICTS,
            weight=0.10,
        ),
    ]

    result = InferenceEngine().revise(
        hypothesis,
        evidence,
    )

    assert result.net_weight == pytest.approx(0.25)
    assert result.revised_hypothesis.confidence == pytest.approx(
        0.65
    )
    assert result.revised_hypothesis.evidence_count == 2


def test_confidence_is_bounded_at_one() -> None:
    hypothesis = make_hypothesis(confidence=0.95)
    evidence = make_evidence(hypothesis, weight=0.40)

    result = InferenceEngine().revise(
        hypothesis,
        [evidence],
    )

    assert result.revised_hypothesis.confidence == pytest.approx(
        1.0
    )
    assert (
        result.revised_hypothesis.status
        is HypothesisStatus.CONFIRMED
    )


def test_confidence_is_bounded_at_zero() -> None:
    hypothesis = make_hypothesis(confidence=0.10)

    evidence = make_evidence(
        hypothesis,
        relation=EvidenceRelation.CONTRADICTS,
        weight=0.50,
    )

    result = InferenceEngine().revise(
        hypothesis,
        [evidence],
    )

    assert result.revised_hypothesis.confidence == pytest.approx(
        0.0
    )
    assert (
        result.revised_hypothesis.status
        is HypothesisStatus.REJECTED
    )


def test_quality_score_reduces_influence() -> None:
    hypothesis = make_hypothesis(confidence=0.40)

    evidence = make_evidence(
        hypothesis,
        weight=0.80,
        quality_score=0.25,
    )

    result = InferenceEngine().revise(
        hypothesis,
        [evidence],
    )

    assert result.net_weight == pytest.approx(0.20)
    assert result.revised_hypothesis.confidence == pytest.approx(
        0.60
    )


def test_duplicate_evidence_is_applied_only_once() -> None:
    hypothesis = make_hypothesis(confidence=0.40)
    evidence = make_evidence(hypothesis, weight=0.20)

    result = InferenceEngine().revise(
        hypothesis,
        [evidence, evidence],
    )

    assert result.net_weight == pytest.approx(0.20)
    assert len(result.applied_evidence_ids) == 1


def test_evidence_for_another_hypothesis_is_rejected() -> None:
    hypothesis = make_hypothesis()
    other_hypothesis = Hypothesis(
        identifier="hardware.possible_sensor_failure",
        title="Possible sensor failure",
        statement="The sensor may be defective.",
    )

    evidence = make_evidence(other_hypothesis)

    with pytest.raises(
        ValueError,
        match="different hypothesis",
    ):
        InferenceEngine().revise(
            hypothesis,
            [evidence],
        )


def test_result_explains_status_change() -> None:
    hypothesis = make_hypothesis(confidence=0.60)
    evidence = make_evidence(hypothesis, weight=0.35)

    result = InferenceEngine().revise(
        hypothesis,
        [evidence],
    )

    assert result.changed_status is True
    assert result.confidence_change == pytest.approx(0.35)
    assert (
        result.revised_hypothesis.status
        is HypothesisStatus.CONFIRMED
    )


def test_custom_thresholds_are_supported() -> None:
    thresholds = InferenceThresholds(
        rejected_below=0.20,
        supported_from=0.60,
        confirmed_from=0.80,
    )

    hypothesis = make_hypothesis(confidence=0.50)
    evidence = make_evidence(hypothesis, weight=0.15)

    result = InferenceEngine(thresholds).revise(
        hypothesis,
        [evidence],
    )

    assert (
        result.revised_hypothesis.status
        is HypothesisStatus.SUPPORTED
    )


def test_invalid_threshold_order_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be ordered"):
        InferenceThresholds(
            rejected_below=0.70,
            supported_from=0.40,
            confirmed_from=0.90,
        )
