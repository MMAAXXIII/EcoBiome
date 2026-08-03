"""Tests for evidence-based scientific findings."""

from datetime import datetime
from uuid import UUID

import pytest

from ecobiome.reasoning import Finding, FindingSeverity

HYPOTHESIS_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)

FIRST_OBSERVATION_ID = UUID(
    "22222222-2222-2222-2222-222222222222"
)

SECOND_OBSERVATION_ID = UUID(
    "33333333-3333-3333-3333-333333333333"
)


def make_finding() -> Finding:
    """Create one confirmed nitrite-spike finding."""
    return Finding(
        identifier="chemistry.nitrite_spike",
        title="Nitrite spike detected",
        statement=(
            "Repeated observations indicate an abnormal "
            "increase in nitrite concentration."
        ),
        severity=FindingSeverity.HIGH,
        confidence=0.94,
        supporting_hypothesis_ids=(HYPOTHESIS_ID,),
        supporting_observation_ids=(
            FIRST_OBSERVATION_ID,
            SECOND_OBSERVATION_ID,
        ),
    )


def test_create_evidence_based_finding() -> None:
    finding = make_finding()

    assert finding.identifier == "chemistry.nitrite_spike"
    assert finding.severity is FindingSeverity.HIGH
    assert finding.confidence == pytest.approx(0.94)
    assert finding.evidence_count == 3
    assert finding.requires_immediate_attention is True


def test_low_severity_does_not_require_immediate_attention() -> None:
    finding = Finding(
        identifier="biology.reduced_feeding_activity",
        title="Reduced feeding activity",
        statement="Fish feeding activity appears slightly reduced.",
        severity=FindingSeverity.LOW,
        confidence=0.68,
        supporting_observation_ids=(FIRST_OBSERVATION_ID,),
    )

    assert finding.requires_immediate_attention is False


def test_duplicate_evidence_identifiers_are_removed() -> None:
    finding = Finding(
        identifier="biology.gravid_female_detected",
        title="Gravid female detected",
        statement="Repeated camera observations confirm a gravid shrimp.",
        severity=FindingSeverity.INFORMATIONAL,
        confidence=0.96,
        supporting_observation_ids=(
            FIRST_OBSERVATION_ID,
            FIRST_OBSERVATION_ID,
            SECOND_OBSERVATION_ID,
        ),
    )

    assert finding.supporting_observation_ids == (
        FIRST_OBSERVATION_ID,
        SECOND_OBSERVATION_ID,
    )
    assert finding.evidence_count == 2


def test_finding_requires_evidence() -> None:
    with pytest.raises(
        ValueError,
        match="requires at least one supporting",
    ):
        Finding(
            identifier="chemistry.unsupported_finding",
            title="Unsupported finding",
            statement="This conclusion has no recorded evidence.",
            severity=FindingSeverity.MEDIUM,
            confidence=0.80,
        )


def test_invalid_confidence_is_rejected() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        Finding(
            identifier="chemistry.invalid_confidence",
            title="Invalid confidence",
            statement="Confidence cannot exceed one.",
            severity=FindingSeverity.MEDIUM,
            confidence=1.20,
            supporting_observation_ids=(FIRST_OBSERVATION_ID,),
        )


def test_identifier_requires_domain_prefix() -> None:
    with pytest.raises(ValueError, match="domain prefix"):
        Finding(
            identifier="nitrite_spike",
            title="Nitrite spike",
            statement="A domain prefix is required.",
            severity=FindingSeverity.HIGH,
            confidence=0.90,
            supporting_observation_ids=(FIRST_OBSERVATION_ID,),
        )


def test_naive_timestamp_is_rejected() -> None:
    naive_datetime = datetime(2026, 8, 1, 12, 0)  # noqa: DTZ001

    with pytest.raises(ValueError, match="include a timezone"):
        Finding(
            identifier="chemistry.nitrite_spike",
            title="Nitrite spike",
            statement="The timestamp must be timezone-aware.",
            severity=FindingSeverity.HIGH,
            confidence=0.90,
            supporting_observation_ids=(FIRST_OBSERVATION_ID,),
            created_at=naive_datetime,
        )
