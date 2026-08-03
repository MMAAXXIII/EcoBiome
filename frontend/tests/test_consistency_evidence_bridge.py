"""Tests for converting consistency assessments into evidence."""

from uuid import UUID

import pytest

from ecobiome.reasoning import (
    ConsistencyAssessment,
    ConsistencyEvidenceBridge,
    ConsistencyStatus,
    EvidenceRelation,
)

CAMERA_OBSERVATION_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)

LUX_OBSERVATION_ID = UUID(
    "22222222-2222-2222-2222-222222222222"
)

CAMERA_RELIABILITY_HYPOTHESIS_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)


def make_bridge() -> ConsistencyEvidenceBridge:
    """Create a bridge targeting camera-reliability reasoning."""
    return ConsistencyEvidenceBridge(
        identifier="consistency.camera_reliability",
        hypothesis_id=CAMERA_RELIABILITY_HYPOTHESIS_ID,
        target_observation_id=CAMERA_OBSERVATION_ID,
        supporting_weight=0.35,
        contradicting_weight=0.80,
    )


def make_assessment(
    status: ConsistencyStatus,
    *,
    confidence: float = 0.90,
    reason: str = "Camera and lux sensor contradict each other.",
) -> ConsistencyAssessment:
    """Create one deterministic multi-sensor assessment."""
    return ConsistencyAssessment(
        status=status,
        confidence=confidence,
        involved_observations=(
            CAMERA_OBSERVATION_ID,
            LUX_OBSERVATION_ID,
        ),
        reason=reason,
    )


def test_inconsistency_generates_contradicting_evidence() -> None:
    evidence = make_bridge().build(
        make_assessment(
            ConsistencyStatus.INCONSISTENT,
            confidence=0.95,
        )
    )

    assert len(evidence) == 1

    result = evidence[0]

    assert result.relation is EvidenceRelation.CONTRADICTS
    assert result.observation_id == CAMERA_OBSERVATION_ID
    assert (
        result.hypothesis_id
        == CAMERA_RELIABILITY_HYPOTHESIS_ID
    )
    assert result.weight == pytest.approx(0.80)
    assert result.quality_score == pytest.approx(0.95)
    assert result.signed_weight == pytest.approx(-0.76)
    assert result.source_rule == (
        "consistency.camera_reliability"
    )


def test_consistency_generates_supporting_evidence() -> None:
    evidence = make_bridge().build(
        make_assessment(
            ConsistencyStatus.CONSISTENT,
            confidence=0.90,
            reason="Camera and lux sensor agree.",
        )
    )

    result = evidence[0]

    assert result.relation is EvidenceRelation.SUPPORTS
    assert result.weight == pytest.approx(0.35)
    assert result.quality_score == pytest.approx(0.90)
    assert result.signed_weight == pytest.approx(0.315)


def test_unknown_assessment_generates_no_evidence() -> None:
    evidence = make_bridge().build(
        make_assessment(ConsistencyStatus.UNKNOWN)
    )

    assert evidence == ()


def test_insufficient_data_generates_no_evidence() -> None:
    evidence = make_bridge().build(
        make_assessment(
            ConsistencyStatus.INSUFFICIENT_DATA,
            confidence=0.0,
        )
    )

    assert evidence == ()


def test_target_must_be_involved_in_assessment() -> None:
    assessment = ConsistencyAssessment(
        status=ConsistencyStatus.INCONSISTENT,
        confidence=0.90,
        involved_observations=(LUX_OBSERVATION_ID,),
        reason="Only the lux observation is involved.",
    )

    with pytest.raises(
        ValueError,
        match="target observation is not involved",
    ):
        make_bridge().build(assessment)


def test_empty_reason_receives_fallback_explanation() -> None:
    evidence = make_bridge().build(
        make_assessment(
            ConsistencyStatus.INCONSISTENT,
            reason="",
        )
    )

    assert "inconsistent" in evidence[0].explanation


def test_invalid_weights_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="supporting_weight must be between",
    ):
        ConsistencyEvidenceBridge(
            identifier="consistency.invalid_support",
            hypothesis_id=CAMERA_RELIABILITY_HYPOTHESIS_ID,
            target_observation_id=CAMERA_OBSERVATION_ID,
            supporting_weight=1.20,
        )

    with pytest.raises(
        ValueError,
        match="contradicting_weight must be between",
    ):
        ConsistencyEvidenceBridge(
            identifier="consistency.invalid_contradiction",
            hypothesis_id=CAMERA_RELIABILITY_HYPOTHESIS_ID,
            target_observation_id=CAMERA_OBSERVATION_ID,
            contradicting_weight=-0.10,
        )


def test_identifier_requires_domain_prefix() -> None:
    with pytest.raises(ValueError, match="domain prefix"):
        ConsistencyEvidenceBridge(
            identifier="camera_reliability",
            hypothesis_id=CAMERA_RELIABILITY_HYPOTHESIS_ID,
            target_observation_id=CAMERA_OBSERVATION_ID,
        )
