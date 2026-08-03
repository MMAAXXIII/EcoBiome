"""Tests for stale-observation hardware validation."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    Observation,
)
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.reasoning import (
    EvidenceRelation,
    RuleDomain,
    RuleEngine,
)
from ecobiome.reasoning.rules import StaleObservationRule

REFERENCE_TIME = datetime(
    2026,
    8,
    1,
    12,
    0,
    tzinfo=UTC,
)

HYPOTHESIS_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)


def make_observation(
    *,
    age_seconds: float,
    confidence: float = 1.0,
) -> Observation:
    """Create an observation with a controlled age."""
    variable = ScientificVariable(
        identifier="physics.water_temperature",
        name="Water temperature",
        description="Temperature of the water body.",
        unit="kelvin",
        display_unit="degC",
        category="physics",
    )

    return Observation(
        source="DS18B20-01",
        variable=variable,
        value=23.5,
        acquisition_method=AcquisitionMethod.SENSOR,
        confidence=confidence,
        observed_at=(
            REFERENCE_TIME
            - timedelta(seconds=age_seconds)
        ),
    )


def make_rule(
    *,
    maximum_age_seconds: float = 60.0,
) -> StaleObservationRule:
    """Create a deterministic stale-observation rule."""
    return StaleObservationRule(
        identifier="hardware.stale_observation",
        name="Stale observation",
        description=(
            "Detect observations older than the permitted age."
        ),
        domain=RuleDomain.HARDWARE,
        priority=100,
        hypothesis_id=HYPOTHESIS_ID,
        maximum_age_seconds=maximum_age_seconds,
        evidence_weight=0.70,
        clock=lambda: REFERENCE_TIME,
    )


def test_recent_observation_generates_no_evidence() -> None:
    assert make_rule().evaluate(
        make_observation(age_seconds=30.0)
    ) == ()


def test_age_equal_to_limit_is_accepted() -> None:
    assert make_rule().evaluate(
        make_observation(age_seconds=60.0)
    ) == ()


def test_stale_observation_generates_contradiction() -> None:
    evidence = make_rule().evaluate(
        make_observation(age_seconds=120.0)
    )

    assert len(evidence) == 1

    result = evidence[0]

    assert result.relation is EvidenceRelation.CONTRADICTS
    assert result.hypothesis_id == HYPOTHESIS_ID
    assert result.weight == pytest.approx(0.70)
    assert result.source_rule == "hardware.stale_observation"
    assert "120.0 seconds old" in result.explanation


def test_observation_confidence_affects_effective_weight() -> None:
    evidence = make_rule().evaluate(
        make_observation(
            age_seconds=120.0,
            confidence=0.50,
        )
    )[0]

    assert evidence.quality_score == pytest.approx(0.50)
    assert evidence.signed_weight == pytest.approx(-0.35)


def test_rule_integrates_with_rule_engine() -> None:
    report = RuleEngine([make_rule()]).evaluate(
        make_observation(age_seconds=120.0)
    )

    assert report.executed_rule_ids == (
        "hardware.stale_observation",
    )
    assert report.evidence_count == 1
    assert report.failed_rule_count == 0
    assert report.succeeded is True


def test_future_observation_is_reported_as_failure() -> None:
    report = RuleEngine([make_rule()]).evaluate(
        make_observation(age_seconds=-10.0)
    )

    assert report.failed_rule_count == 1
    assert report.evidence_count == 0
    assert "cannot be in the future" in report.failures[0].message


def test_invalid_maximum_age_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="must be greater than zero",
    ):
        make_rule(maximum_age_seconds=0.0)


def test_invalid_evidence_weight_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="must be between 0 and 1",
    ):
        StaleObservationRule(
            identifier="hardware.stale_observation",
            name="Stale observation",
            description="Detect stale observations.",
            domain=RuleDomain.HARDWARE,
            hypothesis_id=HYPOTHESIS_ID,
            maximum_age_seconds=60.0,
            evidence_weight=1.20,
            clock=lambda: REFERENCE_TIME,
        )


def test_naive_clock_is_reported_as_failure() -> None:
    rule = StaleObservationRule(
        identifier="hardware.stale_observation",
        name="Stale observation",
        description="Detect stale observations.",
        domain=RuleDomain.HARDWARE,
        hypothesis_id=HYPOTHESIS_ID,
        maximum_age_seconds=60.0,
        clock=lambda: datetime(2026, 8, 1, 12, 0),  # noqa: DTZ001
    )

    report = RuleEngine([rule]).evaluate(
        make_observation(age_seconds=120.0)
    )

    assert report.failed_rule_count == 1
    assert report.evidence_count == 0
    assert "timezone-aware" in report.failures[0].message
