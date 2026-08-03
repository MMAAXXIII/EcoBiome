"""Tests for frozen-sensor hardware detection."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    InMemoryObservationStore,
    Observation,
    ScientificMeasurement,
)
from ecobiome.core.units import Measurement
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.reasoning import (
    EvidenceRelation,
    RuleDomain,
    RuleEngine,
)
from ecobiome.reasoning.rules import FrozenSensorRule

START_TIME = datetime(
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


def make_variable() -> ScientificVariable:
    """Create the water-temperature variable."""
    return ScientificVariable(
        identifier="physics.water_temperature",
        name="Water temperature",
        description="Temperature of the water body.",
        unit="kelvin",
        display_unit="degC",
        category="physics",
    )


def make_observation(
    *,
    minute: int,
    value: float = 23.5,
    source: str = "DS18B20-01",
    confidence: float = 0.99,
) -> Observation:
    """Create one controlled temperature observation."""
    return Observation(
        source=source,
        variable=make_variable(),
        value=ScientificMeasurement(
            quantity=Measurement(value, "degC"),
            uncertainty=0.1,
        ),
        acquisition_method=AcquisitionMethod.SENSOR,
        confidence=confidence,
        observed_at=START_TIME + timedelta(minutes=minute),
    )


def make_rule(
    store: InMemoryObservationStore,
    *,
    tolerance: float = 0.0,
    minimum_count: int = 5,
    minimum_duration_seconds: float = 240.0,
) -> FrozenSensorRule:
    """Create one deterministic frozen-sensor rule."""
    return FrozenSensorRule(
        identifier="hardware.frozen_sensor",
        name="Frozen sensor",
        description=(
            "Detect a sensor returning an unchanged value for too long."
        ),
        domain=RuleDomain.HARDWARE,
        priority=90,
        observation_store=store,
        hypothesis_id=HYPOTHESIS_ID,
        minimum_observation_count=minimum_count,
        minimum_frozen_duration_seconds=minimum_duration_seconds,
        tolerance=tolerance,
        evidence_weight=0.75,
    )


def test_identical_values_over_time_generate_contradiction() -> None:
    history = [
        make_observation(minute=minute)
        for minute in range(4)
    ]

    store = InMemoryObservationStore(history)
    current = make_observation(minute=4)

    evidence = make_rule(store).evaluate(current)

    assert len(evidence) == 1

    result = evidence[0]

    assert result.relation is EvidenceRelation.CONTRADICTS
    assert result.hypothesis_id == HYPOTHESIS_ID
    assert result.weight == pytest.approx(0.75)
    assert result.quality_score == pytest.approx(0.99)
    assert result.source_rule == "hardware.frozen_sensor"
    assert "5 nearly identical values" in result.explanation
    assert "240.0 seconds" in result.explanation


def test_value_variation_prevents_false_alarm() -> None:
    history = [
        make_observation(minute=0, value=23.5),
        make_observation(minute=1, value=23.5),
        make_observation(minute=2, value=23.6),
        make_observation(minute=3, value=23.5),
    ]

    store = InMemoryObservationStore(history)
    current = make_observation(minute=4, value=23.5)

    evidence = make_rule(store, tolerance=0.01).evaluate(current)

    assert evidence == ()


def test_small_variation_can_be_accepted_by_tolerance() -> None:
    history = [
        make_observation(minute=0, value=23.500),
        make_observation(minute=1, value=23.501),
        make_observation(minute=2, value=23.499),
        make_observation(minute=3, value=23.500),
    ]

    store = InMemoryObservationStore(history)
    current = make_observation(minute=4, value=23.500)

    evidence = make_rule(store, tolerance=0.01).evaluate(current)

    assert len(evidence) == 1


def test_insufficient_observations_generate_no_evidence() -> None:
    store = InMemoryObservationStore(
        [
            make_observation(minute=0),
            make_observation(minute=1),
        ]
    )

    current = make_observation(minute=2)

    assert make_rule(store).evaluate(current) == ()


def test_short_duration_generates_no_evidence() -> None:
    history = [
        make_observation(minute=minute)
        for minute in range(4)
    ]

    store = InMemoryObservationStore(history)
    current = make_observation(minute=4)

    rule = make_rule(
        store,
        minimum_duration_seconds=600.0,
    )

    assert rule.evaluate(current) == ()


def test_other_sources_are_ignored() -> None:
    history = [
        make_observation(
            minute=minute,
            source="DS18B20-OTHER",
        )
        for minute in range(5)
    ]

    store = InMemoryObservationStore(history)
    current = make_observation(minute=5)

    assert make_rule(store).evaluate(current) == ()


def test_non_numeric_observation_is_ignored() -> None:
    variable = ScientificVariable(
        identifier="hardware.sensor_status",
        name="Sensor status",
        description="Reported sensor status.",
        unit=None,
        display_unit=None,
        category="hardware",
    )

    observation = Observation(
        source="sensor-01",
        variable=variable,
        value="online",
        acquisition_method=AcquisitionMethod.SENSOR,
        observed_at=START_TIME,
    )

    store = InMemoryObservationStore()

    assert make_rule(store).evaluate(observation) == ()


def test_lowest_confidence_controls_evidence_quality() -> None:
    history = [
        make_observation(minute=0, confidence=0.95),
        make_observation(minute=1, confidence=0.80),
        make_observation(minute=2, confidence=0.90),
        make_observation(minute=3, confidence=0.85),
    ]

    store = InMemoryObservationStore(history)
    current = make_observation(minute=4, confidence=0.99)

    evidence = make_rule(store).evaluate(current)

    assert evidence[0].quality_score == pytest.approx(0.80)
    assert evidence[0].signed_weight == pytest.approx(-0.60)


def test_rule_integrates_with_rule_engine() -> None:
    history = [
        make_observation(minute=minute)
        for minute in range(4)
    ]

    store = InMemoryObservationStore(history)
    rule = make_rule(store)

    report = RuleEngine([rule]).evaluate(
        make_observation(minute=4)
    )

    assert report.executed_rule_ids == (
        "hardware.frozen_sensor",
    )
    assert report.evidence_count == 1
    assert report.failed_rule_count == 0


def test_invalid_configuration_is_rejected() -> None:
    store = InMemoryObservationStore()

    with pytest.raises(ValueError, match="at least two"):
        make_rule(store, minimum_count=1)

    with pytest.raises(ValueError, match="cannot be negative"):
        make_rule(store, tolerance=-0.1)

    with pytest.raises(ValueError, match="greater than zero"):
        make_rule(
            store,
            minimum_duration_seconds=0.0,
        )
