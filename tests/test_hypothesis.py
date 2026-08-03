"""Tests for scientific hypotheses."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from ecobiome.reasoning import Hypothesis, HypothesisStatus

FIRST_OBSERVATION_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)

SECOND_OBSERVATION_ID = UUID(
    "22222222-2222-2222-2222-222222222222"
)


def make_hypothesis() -> Hypothesis:
    """Create one provisional nitrite-spike hypothesis."""
    return Hypothesis(
        identifier="chemistry.possible_nitrite_spike",
        title="Possible nitrite spike",
        statement=(
            "The recent observations may indicate "
            "an abnormal nitrite increase."
        ),
        confidence=0.55,
        supporting_observation_ids=(FIRST_OBSERVATION_ID,),
    )


def test_create_pending_hypothesis() -> None:
    hypothesis = make_hypothesis()

    assert hypothesis.status is HypothesisStatus.PENDING
    assert hypothesis.confidence == pytest.approx(0.55)
    assert hypothesis.evidence_count == 1


def test_duplicate_observation_ids_are_removed() -> None:
    hypothesis = Hypothesis(
        identifier="biology.possible_gravid_female",
        title="Possible gravid female",
        statement="The camera may have detected a gravid shrimp.",
        confidence=0.70,
        supporting_observation_ids=(
            FIRST_OBSERVATION_ID,
            FIRST_OBSERVATION_ID,
            SECOND_OBSERVATION_ID,
        ),
    )

    assert hypothesis.supporting_observation_ids == (
        FIRST_OBSERVATION_ID,
        SECOND_OBSERVATION_ID,
    )
    assert hypothesis.evidence_count == 2


def test_hypothesis_can_be_revised_immutably() -> None:
    original = make_hypothesis()

    revised = original.revise(
        status=HypothesisStatus.SUPPORTED,
        confidence=0.82,
        supporting_observation_ids=(
            FIRST_OBSERVATION_ID,
            SECOND_OBSERVATION_ID,
        ),
    )

    assert original.status is HypothesisStatus.PENDING
    assert original.confidence == pytest.approx(0.55)

    assert revised.status is HypothesisStatus.SUPPORTED
    assert revised.confidence == pytest.approx(0.82)
    assert revised.evidence_count == 2
    assert revised.hypothesis_id == original.hypothesis_id
    assert revised.updated_at >= original.updated_at


def test_invalid_confidence_is_rejected() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        Hypothesis(
            identifier="chemistry.invalid_confidence",
            title="Invalid hypothesis",
            statement="This confidence is outside the valid range.",
            confidence=1.20,
        )


def test_identifier_requires_domain_prefix() -> None:
    with pytest.raises(ValueError, match="domain prefix"):
        Hypothesis(
            identifier="possible_nitrite_spike",
            title="Possible nitrite spike",
            statement="A domain prefix is required.",
        )


def test_naive_timestamp_is_rejected() -> None:
    naive_datetime = datetime(2026, 8, 1, 12, 0)  # noqa: DTZ001

    with pytest.raises(ValueError, match="include a timezone"):
        Hypothesis(
            identifier="chemistry.possible_nitrite_spike",
            title="Possible nitrite spike",
            statement="A timezone-aware timestamp is required.",
            created_at=naive_datetime,
        )


def test_updated_at_cannot_precede_creation() -> None:
    created_at = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="cannot precede"):
        Hypothesis(
            identifier="chemistry.invalid_timeline",
            title="Invalid timeline",
            statement="The update cannot precede creation.",
            created_at=created_at,
            updated_at=created_at - timedelta(seconds=1),
        )
