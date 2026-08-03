"""Tests for plausible numerical range validation."""

from datetime import UTC, datetime

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    DataQuality,
    DiagnosticCode,
    Observation,
    ObservationQualityEngine,
    ScientificMeasurement,
)
from ecobiome.core.units import Measurement
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.reasoning import RuleDomain
from ecobiome.reasoning.rules import PlausibleRangeRule

OBSERVED_AT = datetime(
    2026,
    8,
    1,
    12,
    0,
    tzinfo=UTC,
)


def make_variable() -> ScientificVariable:
    """Create a water-temperature variable."""
    return ScientificVariable(
        identifier="physics.water_temperature",
        name="Water temperature",
        description="Temperature of the water body.",
        unit="kelvin",
        display_unit="degC",
        category="physics",
    )


def make_observation(
    value: float,
    unit: str = "degC",
) -> Observation:
    """Create one controlled temperature observation."""
    return Observation(
        source="DS18B20-01",
        variable=make_variable(),
        value=ScientificMeasurement(
            quantity=Measurement(value, unit),
            uncertainty=0.1,
        ),
        acquisition_method=AcquisitionMethod.SENSOR,
        confidence=0.99,
        observed_at=OBSERVED_AT,
    )


def make_rule() -> PlausibleRangeRule:
    """Create a physical water-temperature range rule."""
    return PlausibleRangeRule(
        identifier="hardware.water_temperature_plausibility",
        name="Water temperature plausibility",
        description=(
            "Reject water temperatures outside a physical range."
        ),
        domain=RuleDomain.HARDWARE,
        priority=110,
        variable_id="physics.water_temperature",
        minimum=Measurement(-5.0, "degC"),
        maximum=Measurement(60.0, "degC"),
    )


def test_value_inside_range_is_valid() -> None:
    assessment = make_rule().assess(
        make_observation(23.5)
    )

    assert assessment.quality is DataQuality.VALID
    assert assessment.score == pytest.approx(1.0)


def test_lower_and_upper_bounds_are_inclusive() -> None:
    assert make_rule().assess(
        make_observation(-5.0)
    ).quality is DataQuality.VALID

    assert make_rule().assess(
        make_observation(60.0)
    ).quality is DataQuality.VALID


def test_value_below_range_is_invalid() -> None:
    assessment = make_rule().assess(
        make_observation(-20.0)
    )

    assert assessment.quality is DataQuality.INVALID
    assert assessment.score == pytest.approx(0.0)
    assert assessment.diagnostics == (
        DiagnosticCode.IMPOSSIBLE_VALUE,
    )
    assert "outside the plausible range" in assessment.reasons[0]


def test_value_above_range_is_invalid() -> None:
    assessment = make_rule().assess(
        make_observation(90.0)
    )

    assert assessment.quality is DataQuality.INVALID


def test_compatible_units_are_converted() -> None:
    assessment = make_rule().assess(
        make_observation(293.15, "kelvin")
    )

    assert assessment.quality is DataQuality.VALID


def test_incompatible_unit_is_invalid() -> None:
    assessment = make_rule().assess(
        make_observation(20.0, "liter")
    )

    assert assessment.quality is DataQuality.INVALID
    assert "incompatible" in assessment.reasons[0]


def test_other_variable_is_ignored() -> None:
    variable = ScientificVariable(
        identifier="chemistry.ph",
        name="pH",
        description="Water acidity.",
        unit=None,
        display_unit=None,
        category="chemistry",
    )

    observation = Observation(
        source="ph-probe-01",
        variable=variable,
        value=7.0,
        acquisition_method=AcquisitionMethod.SENSOR,
        observed_at=OBSERVED_AT,
    )

    assessment = make_rule().assess(observation)

    assert assessment.quality is DataQuality.VALID


def test_rule_integrates_with_quality_engine() -> None:
    report = ObservationQualityEngine(
        [make_rule()]
    ).evaluate(make_observation(-100.0))

    assert report.assessment.quality is DataQuality.INVALID
    assert report.assessment.is_usable_for_reasoning is False
    assert report.failed_rule_count == 0


def test_incompatible_boundaries_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="compatible dimensions",
    ):
        PlausibleRangeRule(
            identifier="hardware.invalid_range",
            name="Invalid range",
            description="Test invalid dimensions.",
            domain=RuleDomain.HARDWARE,
            variable_id="physics.water_temperature",
            minimum=Measurement(0.0, "degC"),
            maximum=Measurement(10.0, "liter"),
        )


def test_reversed_range_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="maximum cannot be lower",
    ):
        PlausibleRangeRule(
            identifier="hardware.reversed_range",
            name="Reversed range",
            description="Test reversed boundaries.",
            domain=RuleDomain.HARDWARE,
            variable_id="physics.water_temperature",
            minimum=Measurement(50.0, "degC"),
            maximum=Measurement(10.0, "degC"),
        )
