"""Tests for aggregated observation-quality evaluation."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    DataQuality,
    DiagnosticCode,
    InMemoryObservationStore,
    Observation,
    ObservationQualityEngine,
    QualityAssessment,
)
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.reasoning import RuleDomain
from ecobiome.reasoning.rules import (
    FrozenSensorRule,
    StaleObservationRule,
)

NOW = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)

HYPOTHESIS_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)


def make_observation(
    *,
    minute: int = 0,
    value: float = 23.5,
) -> Observation:
    """Create one controlled observation."""
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
        value=value,
        acquisition_method=AcquisitionMethod.SENSOR,
        confidence=0.99,
        observed_at=NOW + timedelta(minutes=minute),
    )


def make_stale_rule() -> StaleObservationRule:
    """Create a deterministic stale rule."""
    return StaleObservationRule(
        identifier="hardware.stale_observation",
        name="Stale observation",
        description="Detect stale observations.",
        domain=RuleDomain.HARDWARE,
        hypothesis_id=HYPOTHESIS_ID,
        maximum_age_seconds=60.0,
        clock=lambda: NOW,
    )


def test_no_rules_accepts_observation() -> None:
    observation = make_observation()

    report = ObservationQualityEngine().evaluate(observation)

    assert report.assessment.quality is DataQuality.VALID
    assert report.assessment.score == pytest.approx(1.0)
    assert report.succeeded is True


def test_stale_rule_produces_stale_assessment() -> None:
    observation = make_observation(minute=-5)

    report = ObservationQualityEngine(
        [make_stale_rule()]
    ).evaluate(observation)

    assert report.assessment.quality is DataQuality.STALE
    assert report.assessment.score == pytest.approx(0.0)
    assert report.assessment.diagnostics == (
        DiagnosticCode.STALE_OBSERVATION,
    )
    assert report.assessment.is_usable_for_reasoning is False


def test_frozen_rule_produces_suspect_assessment() -> None:
    history = InMemoryObservationStore(
        [
            make_observation(minute=-4),
            make_observation(minute=-3),
            make_observation(minute=-2),
            make_observation(minute=-1),
        ]
    )

    rule = FrozenSensorRule(
        identifier="hardware.frozen_sensor",
        name="Frozen sensor",
        description="Detect fixed sensor values.",
        domain=RuleDomain.HARDWARE,
        observation_store=history,
        hypothesis_id=HYPOTHESIS_ID,
        minimum_observation_count=5,
        minimum_frozen_duration_seconds=240.0,
        tolerance=0.0,
        evidence_weight=0.75,
    )

    report = ObservationQualityEngine(
        [rule]
    ).evaluate(make_observation())

    assert report.assessment.quality is DataQuality.SUSPECT
    assert report.assessment.score == pytest.approx(0.25)
    assert report.assessment.diagnostics == (
        DiagnosticCode.FROZEN_SENSOR,
    )
    assert report.assessment.is_usable_for_reasoning is True


def test_worst_quality_wins_during_aggregation() -> None:
    history = InMemoryObservationStore(
        [
            make_observation(minute=-9),
            make_observation(minute=-8),
            make_observation(minute=-7),
            make_observation(minute=-6),
        ]
    )

    frozen_rule = FrozenSensorRule(
        identifier="hardware.frozen_sensor",
        name="Frozen sensor",
        description="Detect fixed sensor values.",
        domain=RuleDomain.HARDWARE,
        observation_store=history,
        hypothesis_id=HYPOTHESIS_ID,
        minimum_observation_count=5,
        minimum_frozen_duration_seconds=240.0,
        tolerance=0.0,
    )

    current = make_observation(minute=-5)

    report = ObservationQualityEngine(
        [frozen_rule, make_stale_rule()]
    ).evaluate(current)

    assert report.assessment.quality is DataQuality.STALE
    assert report.assessment.score == pytest.approx(0.0)
    assert set(report.assessment.diagnostics) == {
        DiagnosticCode.FROZEN_SENSOR,
        DiagnosticCode.STALE_OBSERVATION,
    }


@dataclass(frozen=True)
class FailingQualityRule:
    """Quality rule used to test failure isolation."""

    identifier: str = "hardware.failing_quality_rule"

    def assess(
        self,
        observation: Observation,
    ) -> QualityAssessment:
        raise RuntimeError("Simulated quality-rule failure.")


def test_rule_failure_marks_observation_suspect() -> None:
    report = ObservationQualityEngine(
        [FailingQualityRule()]
    ).evaluate(make_observation())

    assert report.failed_rule_count == 1
    assert report.assessment.quality is DataQuality.SUSPECT
    assert report.assessment.score == pytest.approx(0.50)
    assert report.assessment.diagnostics == (
        DiagnosticCode.UNKNOWN,
    )
    assert report.succeeded is False


def test_duplicate_rule_identifier_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Duplicate quality-rule identifier",
    ):
        ObservationQualityEngine(
            [make_stale_rule(), make_stale_rule()]
        )
