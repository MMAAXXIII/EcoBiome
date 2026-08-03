"""Tests for the multi-observation consistency engine."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    Observation,
)
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.reasoning.consistency import (
    ConsistencyAssessment,
    ConsistencyEngine,
    ConsistencyStatus,
)

FIRST_OBSERVATION_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)

SECOND_OBSERVATION_ID = UUID(
    "22222222-2222-2222-2222-222222222222"
)


def make_observation(
    *,
    observation_id: UUID,
    source: str,
    value: float,
) -> Observation:
    """Create one deterministic light observation."""
    variable = ScientificVariable(
        identifier="weather.ambient_light",
        name="Ambient light",
        description="Ambient light measured near the ecosystem.",
        unit="lux",
        display_unit="lux",
        category="weather",
    )

    return Observation(
        observation_id=observation_id,
        source=source,
        variable=variable,
        value=value,
        acquisition_method=AcquisitionMethod.SENSOR,
        observed_at=datetime(
            2026,
            8,
            1,
            12,
            0,
            tzinfo=UTC,
        ),
    )


def make_observations() -> tuple[Observation, ...]:
    """Create two observations used by the tests."""
    return (
        make_observation(
            observation_id=FIRST_OBSERVATION_ID,
            source="light-sensor-01",
            value=500.0,
        ),
        make_observation(
            observation_id=SECOND_OBSERVATION_ID,
            source="light-sensor-02",
            value=510.0,
        ),
    )


@dataclass(frozen=True)
class ConsistentRule:
    """Rule returning one consistent assessment."""

    identifier: str = "consistency.test_consistent"

    def evaluate(
        self,
        observations: tuple[Observation, ...],
    ) -> ConsistencyAssessment:
        return ConsistencyAssessment(
            status=ConsistencyStatus.CONSISTENT,
            confidence=0.95,
            involved_observations=tuple(
                observation.observation_id
                for observation in observations
            ),
            reason="The observations agree.",
        )


@dataclass(frozen=True)
class InconsistentRule:
    """Rule returning one inconsistent assessment."""

    identifier: str = "consistency.test_inconsistent"

    def evaluate(
        self,
        observations: tuple[Observation, ...],
    ) -> ConsistencyAssessment:
        return ConsistencyAssessment(
            status=ConsistencyStatus.INCONSISTENT,
            confidence=0.90,
            involved_observations=tuple(
                observation.observation_id
                for observation in observations
            ),
            reason="The observations contradict each other.",
        )


@dataclass(frozen=True)
class FailingRule:
    """Rule used to verify failure isolation."""

    identifier: str = "consistency.test_failure"

    def evaluate(
        self,
        observations: tuple[Observation, ...],
    ) -> ConsistencyAssessment:
        raise RuntimeError("Simulated consistency-rule failure.")


@dataclass(frozen=True)
class InvalidRule:
    """Object that does not implement evaluate()."""

    identifier: str = "consistency.invalid"


def test_empty_engine_returns_unknown_assessment() -> None:
    observations = make_observations()

    report = ConsistencyEngine().evaluate(observations)

    assert report.executed_rule_ids == ()
    assert report.failures == ()
    assert report.succeeded is True
    assert report.has_inconsistency is False
    assert len(report.assessments) == 1

    assessment = report.assessments[0]

    assert assessment.status is ConsistencyStatus.UNKNOWN
    assert assessment.confidence == pytest.approx(0.0)
    assert assessment.involved_observations == (
        FIRST_OBSERVATION_ID,
        SECOND_OBSERVATION_ID,
    )
    assert assessment.reason == (
        "No consistency rule is configured."
    )


def test_consistent_rule_is_executed() -> None:
    report = ConsistencyEngine(
        [ConsistentRule()]
    ).evaluate(make_observations())

    assert report.executed_rule_ids == (
        "consistency.test_consistent",
    )
    assert report.failed_rule_count == 0
    assert report.succeeded is True
    assert report.has_inconsistency is False
    assert report.assessments[0].is_consistent is True


def test_inconsistent_rule_requires_attention() -> None:
    report = ConsistencyEngine(
        [InconsistentRule()]
    ).evaluate(make_observations())

    assessment = report.assessments[0]

    assert report.has_inconsistency is True
    assert assessment.status is ConsistencyStatus.INCONSISTENT
    assert assessment.requires_attention is True
    assert assessment.confidence == pytest.approx(0.90)


def test_multiple_rules_preserve_registration_order() -> None:
    report = ConsistencyEngine(
        [
            ConsistentRule(),
            InconsistentRule(),
        ]
    ).evaluate(make_observations())

    assert report.executed_rule_ids == (
        "consistency.test_consistent",
        "consistency.test_inconsistent",
    )
    assert len(report.assessments) == 2
    assert report.has_inconsistency is True


def test_failed_rule_does_not_stop_following_rule() -> None:
    report = ConsistencyEngine(
        [
            FailingRule(),
            ConsistentRule(),
        ]
    ).evaluate(make_observations())

    assert report.executed_rule_ids == (
        "consistency.test_failure",
        "consistency.test_consistent",
    )
    assert report.failed_rule_count == 1
    assert report.succeeded is False
    assert len(report.assessments) == 1
    assert report.assessments[0].is_consistent is True

    failure = report.failures[0]

    assert failure.rule_identifier == (
        "consistency.test_failure"
    )
    assert failure.exception_type == "RuntimeError"
    assert failure.message == (
        "Simulated consistency-rule failure."
    )


def test_duplicate_rule_identifier_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Duplicate consistency-rule identifier",
    ):
        ConsistencyEngine(
            [
                ConsistentRule(),
                ConsistentRule(),
            ]
        )


def test_rule_without_evaluate_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="must implement evaluate",
    ):
        ConsistencyEngine(
            [InvalidRule()]  # type: ignore[list-item]
        )


def test_confidence_must_be_between_zero_and_one() -> None:
    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):
        ConsistencyAssessment(
            status=ConsistencyStatus.UNKNOWN,
            confidence=1.20,
        )


def test_boolean_confidence_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        ConsistencyAssessment(
            status=ConsistencyStatus.UNKNOWN,
            confidence=True,
        )


def test_reason_is_optional() -> None:
    assessment = ConsistencyAssessment(
        status=ConsistencyStatus.INSUFFICIENT_DATA,
        confidence=0.0,
    )

    assert assessment.reason == ""
    assert assessment.involved_observations == ()
    assert assessment.is_consistent is False
    assert assessment.requires_attention is False
