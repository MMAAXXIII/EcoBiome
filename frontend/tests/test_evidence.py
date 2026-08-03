"""Tests for traceable scientific evidence."""

from datetime import datetime
from uuid import UUID

import pytest

from ecobiome.reasoning import Evidence, EvidenceRelation

OBSERVATION_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)

HYPOTHESIS_ID = UUID(
    "22222222-2222-2222-2222-222222222222"
)


def make_evidence(
    *,
    relation: EvidenceRelation = EvidenceRelation.SUPPORTS,
    weight: float = 0.80,
    quality_score: float = 1.0,
) -> Evidence:
    """Create one reusable evidence record."""
    return Evidence(
        observation_id=OBSERVATION_ID,
        hypothesis_id=HYPOTHESIS_ID,
        relation=relation,
        weight=weight,
        quality_score=quality_score,
        explanation=(
            "The measured nitrite concentration exceeds "
            "the configured biological threshold."
        ),
        source_rule="chemistry.nitrite_threshold",
    )


def test_supporting_evidence_has_positive_weight() -> None:
    evidence = make_evidence(
        relation=EvidenceRelation.SUPPORTS,
        weight=0.80,
    )

    assert evidence.is_supporting is True
    assert evidence.is_contradicting is False
    assert evidence.signed_weight == pytest.approx(0.80)


def test_contradicting_evidence_has_negative_weight() -> None:
    evidence = make_evidence(
        relation=EvidenceRelation.CONTRADICTS,
        weight=0.65,
    )

    assert evidence.is_supporting is False
    assert evidence.is_contradicting is True
    assert evidence.signed_weight == pytest.approx(-0.65)


def test_neutral_evidence_has_zero_weight() -> None:
    evidence = make_evidence(
        relation=EvidenceRelation.NEUTRAL,
        weight=0.90,
    )

    assert evidence.signed_weight == pytest.approx(0.0)


def test_quality_score_reduces_effective_weight() -> None:
    evidence = make_evidence(
        relation=EvidenceRelation.SUPPORTS,
        weight=0.80,
        quality_score=0.25,
    )

    assert evidence.signed_weight == pytest.approx(0.20)


def test_text_fields_are_normalized() -> None:
    evidence = Evidence(
        observation_id=OBSERVATION_ID,
        hypothesis_id=HYPOTHESIS_ID,
        relation=EvidenceRelation.SUPPORTS,
        weight=0.50,
        explanation="  Supporting observation.  ",
        source_rule="  chemistry.test_rule  ",
    )

    assert evidence.explanation == "Supporting observation."
    assert evidence.source_rule == "chemistry.test_rule"


def test_invalid_weight_is_rejected() -> None:
    with pytest.raises(ValueError, match="weight must be between"):
        make_evidence(weight=1.20)


def test_invalid_quality_score_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="quality_score must be between",
    ):
        make_evidence(quality_score=-0.10)


def test_empty_explanation_is_rejected() -> None:
    with pytest.raises(ValueError, match="requires an explanation"):
        Evidence(
            observation_id=OBSERVATION_ID,
            hypothesis_id=HYPOTHESIS_ID,
            relation=EvidenceRelation.SUPPORTS,
            weight=0.50,
            explanation="   ",
            source_rule="chemistry.test_rule",
        )


def test_naive_timestamp_is_rejected() -> None:
    naive_datetime = datetime(2026, 8, 1, 12, 0)  # noqa: DTZ001

    with pytest.raises(ValueError, match="include a timezone"):
        Evidence(
            observation_id=OBSERVATION_ID,
            hypothesis_id=HYPOTHESIS_ID,
            relation=EvidenceRelation.SUPPORTS,
            weight=0.50,
            explanation="Supporting observation.",
            source_rule="chemistry.test_rule",
            created_at=naive_datetime,
        )
