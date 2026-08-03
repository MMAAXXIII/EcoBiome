"""Tests for camera/lux temporal synchronization constraints."""

from datetime import UTC, datetime, timedelta

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    Observation,
)
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.reasoning.consistency import ConsistencyStatus
from ecobiome.reasoning.consistency.rules import (
    CameraLuxConsistencyRule,
)

REFERENCE_TIME = datetime(
    2026,
    8,
    1,
    12,
    0,
    tzinfo=UTC,
)


def make_variable(
    identifier: str,
    *,
    unit: str,
    category: str,
) -> ScientificVariable:
    """Create one controlled scientific variable."""
    return ScientificVariable(
        identifier=identifier,
        name=identifier,
        description=identifier,
        unit=unit,
        display_unit=unit,
        category=category,
    )


def make_camera(
    observed_at: datetime,
) -> Observation:
    """Create one dark camera observation."""
    return Observation(
        source="camera-01",
        variable=make_variable(
            "vision.frame_mean_luminance",
            unit="dimensionless",
            category="vision",
        ),
        value=0.01,
        acquisition_method=AcquisitionMethod.CAMERA,
        observed_at=observed_at,
    )


def make_lux(
    observed_at: datetime,
) -> Observation:
    """Create one daylight lux observation."""
    return Observation(
        source="lux-sensor-01",
        variable=make_variable(
            "weather.ambient_light",
            unit="lux",
            category="weather",
        ),
        value=40_000.0,
        acquisition_method=AcquisitionMethod.SENSOR,
        observed_at=observed_at,
    )


def test_synchronized_observations_can_be_compared() -> None:
    assessment = CameraLuxConsistencyRule(
        maximum_time_delta_seconds=5.0,
    ).evaluate(
        (
            make_camera(REFERENCE_TIME),
            make_lux(
                REFERENCE_TIME + timedelta(seconds=4)
            ),
        )
    )

    assert assessment.status is ConsistencyStatus.INCONSISTENT


def test_desynchronized_observations_are_insufficient() -> None:
    assessment = CameraLuxConsistencyRule(
        maximum_time_delta_seconds=5.0,
    ).evaluate(
        (
            make_camera(REFERENCE_TIME),
            make_lux(
                REFERENCE_TIME + timedelta(seconds=30)
            ),
        )
    )

    assert (
        assessment.status
        is ConsistencyStatus.INSUFFICIENT_DATA
    )
    assert assessment.confidence == pytest.approx(0.0)
    assert "30.0 seconds" in assessment.reason
    assert "synchronization window" in assessment.reason


def test_invalid_time_window_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="maximum_time_delta_seconds must be greater",
    ):
        CameraLuxConsistencyRule(
            maximum_time_delta_seconds=0.0
        )
