"""Tests for traceable scientific observations."""

from datetime import datetime

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    Observation,
    ScientificMeasurement,
)
from ecobiome.core.units import Measurement
from ecobiome.knowledge.variable import ScientificVariable


def make_temperature_variable() -> ScientificVariable:
    """Create the water-temperature variable used by the tests."""
    return ScientificVariable(
        identifier="physics.water_temperature",
        name="Water temperature",
        description="Temperature of the water body.",
        unit="kelvin",
        display_unit="degC",
        category="physics",
    )


def test_create_sensor_measurement_observation() -> None:
    observation = Observation(
        source="DS18B20-01",
        variable=make_temperature_variable(),
        value=ScientificMeasurement(
            quantity=Measurement(23.5, "degC"),
            uncertainty=0.1,
        ),
        acquisition_method=AcquisitionMethod.SENSOR,
        confidence=0.99,
    )

    assert observation.variable_id == "physics.water_temperature"
    assert observation.is_measurement is True
    assert observation.confidence == pytest.approx(0.99)

    assert isinstance(
        observation.value,
        ScientificMeasurement,
    )

    assert observation.value.lower_bound.value == pytest.approx(23.4)
    assert observation.value.upper_bound.value == pytest.approx(23.6)


def test_create_camera_detection_observation() -> None:
    variable = ScientificVariable(
        identifier="biology.shrimp_gravid",
        name="Gravid shrimp detected",
        description="Presence of a gravid shrimp.",
        unit=None,
        display_unit=None,
        category="biology",
    )

    observation = Observation(
        source="nursery-camera-01",
        variable=variable,
        value=True,
        acquisition_method=AcquisitionMethod.AI_INFERENCE,
        confidence=0.87,
        raw_reference="frames/observation-001.jpg",
    )

    assert observation.is_measurement is False
    assert observation.value is True
    assert observation.raw_reference == (
        "frames/observation-001.jpg"
    )


def test_textual_observation_is_normalized() -> None:
    variable = ScientificVariable(
        identifier="biology.fish_behavior",
        name="Fish behavior",
        description="Observed fish behavior.",
        unit=None,
        display_unit=None,
        category="biology",
    )

    observation = Observation(
        source="operator:maxime",
        variable=variable,
        value="  reduced feeding activity  ",
        acquisition_method=AcquisitionMethod.HUMAN,
        confidence=0.70,
    )

    assert observation.value == "reduced feeding activity"


def test_invalid_confidence_is_rejected() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        Observation(
            source="camera-01",
            variable=make_temperature_variable(),
            value=True,
            acquisition_method=AcquisitionMethod.CAMERA,
            confidence=1.20,
        )


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="include a timezone"):
        Observation(
            source="sensor-01",
            variable=make_temperature_variable(),
            value=ScientificMeasurement(
                quantity=Measurement(20.0, "degC"),
                uncertainty=0.1,
            ),
            acquisition_method=AcquisitionMethod.SENSOR,
            observed_at=datetime(2026, 8, 1, 12, 0),  # noqa: DTZ001
        )


def test_empty_source_is_rejected() -> None:
    with pytest.raises(ValueError, match="requires a source"):
        Observation(
            source="   ",
            variable=make_temperature_variable(),
            value=20.0,
            acquisition_method=AcquisitionMethod.HUMAN,
        )

