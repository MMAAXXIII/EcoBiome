"""Tests for camera and ambient-light consistency."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    Observation,
    ScientificMeasurement,
)
from ecobiome.core.units import Measurement
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.reasoning.consistency import (
    ConsistencyEngine,
    ConsistencyStatus,
)
from ecobiome.reasoning.consistency.rules import (
    CameraLuxConsistencyRule,
)

START_TIME = datetime(
    2026,
    8,
    1,
    12,
    0,
    tzinfo=UTC,
)

CAMERA_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)

LUX_ID = UUID(
    "22222222-2222-2222-2222-222222222222"
)


def make_camera_variable() -> ScientificVariable:
    """Create the normalized camera-luminance variable."""
    return ScientificVariable(
        identifier="vision.frame_mean_luminance",
        name="Frame mean luminance",
        description="Normalized mean luminance of one camera frame.",
        unit="dimensionless",
        display_unit=None,
        category="vision",
    )


def make_lux_variable() -> ScientificVariable:
    """Create the ambient-light variable."""
    return ScientificVariable(
        identifier="weather.ambient_light",
        name="Ambient light",
        description="Ambient light measured near the ecosystem.",
        unit="lux",
        display_unit="lux",
        category="weather",
    )


def make_camera_observation(
    luminance: float,
    *,
    observed_at: datetime = START_TIME,
    observation_id: UUID = CAMERA_ID,
) -> Observation:
    """Create one camera-luminance observation."""
    return Observation(
        observation_id=observation_id,
        source="camera-01",
        variable=make_camera_variable(),
        value=luminance,
        acquisition_method=AcquisitionMethod.CAMERA,
        confidence=0.99,
        observed_at=observed_at,
    )


def make_lux_observation(
    lux: float,
    *,
    observed_at: datetime = START_TIME,
    observation_id: UUID = LUX_ID,
) -> Observation:
    """Create one ambient-light observation."""
    return Observation(
        observation_id=observation_id,
        source="lux-sensor-01",
        variable=make_lux_variable(),
        value=lux,
        acquisition_method=AcquisitionMethod.SENSOR,
        confidence=0.99,
        observed_at=observed_at,
    )


def test_black_camera_and_daylight_are_inconsistent() -> None:
    assessment = CameraLuxConsistencyRule().evaluate(
        (
            make_camera_observation(0.01),
            make_lux_observation(40_000.0),
        )
    )

    assert assessment.status is ConsistencyStatus.INCONSISTENT
    assert assessment.confidence == pytest.approx(0.98)
    assert assessment.requires_attention is True
    assert assessment.involved_observations == (
        CAMERA_ID,
        LUX_ID,
    )
    assert "camera may be" in assessment.reason.lower()


def test_black_camera_and_dark_lux_are_consistent() -> None:
    assessment = CameraLuxConsistencyRule().evaluate(
        (
            make_camera_observation(0.01),
            make_lux_observation(0.5),
        )
    )

    assert assessment.status is ConsistencyStatus.CONSISTENT
    assert assessment.confidence == pytest.approx(0.95)
    assert assessment.is_consistent is True
    assert "dark environment" in assessment.reason


def test_bright_camera_and_daylight_are_consistent() -> None:
    assessment = CameraLuxConsistencyRule().evaluate(
        (
            make_camera_observation(0.40),
            make_lux_observation(30_000.0),
        )
    )

    assert assessment.status is ConsistencyStatus.CONSISTENT
    assert "lit environment" in assessment.reason


def test_ambiguous_values_return_unknown() -> None:
    assessment = CameraLuxConsistencyRule().evaluate(
        (
            make_camera_observation(0.20),
            make_lux_observation(300.0),
        )
    )

    assert assessment.status is ConsistencyStatus.UNKNOWN
    assert assessment.confidence == pytest.approx(0.25)


def test_missing_lux_returns_insufficient_data() -> None:
    assessment = CameraLuxConsistencyRule().evaluate(
        (make_camera_observation(0.01),)
    )

    assert (
        assessment.status
        is ConsistencyStatus.INSUFFICIENT_DATA
    )
    assert assessment.confidence == pytest.approx(0.0)
    assert assessment.involved_observations == (CAMERA_ID,)


def test_missing_camera_returns_insufficient_data() -> None:
    assessment = CameraLuxConsistencyRule().evaluate(
        (make_lux_observation(500.0),)
    )

    assert (
        assessment.status
        is ConsistencyStatus.INSUFFICIENT_DATA
    )
    assert assessment.involved_observations == (LUX_ID,)


def test_invalid_camera_value_returns_unknown() -> None:
    assessment = CameraLuxConsistencyRule().evaluate(
        (
            make_camera_observation(1.50),
            make_lux_observation(30_000.0),
        )
    )

    assert assessment.status is ConsistencyStatus.UNKNOWN
    assert assessment.confidence == pytest.approx(0.0)


def test_negative_lux_returns_unknown() -> None:
    assessment = CameraLuxConsistencyRule().evaluate(
        (
            make_camera_observation(0.01),
            make_lux_observation(-1.0),
        )
    )

    assert assessment.status is ConsistencyStatus.UNKNOWN


def test_scientific_measurements_are_supported() -> None:
    camera = Observation(
        source="camera-01",
        variable=make_camera_variable(),
        value=ScientificMeasurement(
            quantity=Measurement(0.01, "dimensionless"),
            uncertainty=0.001,
        ),
        acquisition_method=AcquisitionMethod.CAMERA,
        observed_at=START_TIME,
    )

    lux = Observation(
        source="lux-sensor-01",
        variable=make_lux_variable(),
        value=ScientificMeasurement(
            quantity=Measurement(40_000.0, "lux"),
            uncertainty=10.0,
        ),
        acquisition_method=AcquisitionMethod.SENSOR,
        observed_at=START_TIME,
    )

    assessment = CameraLuxConsistencyRule().evaluate(
        (camera, lux)
    )

    assert assessment.status is ConsistencyStatus.INCONSISTENT


def test_latest_relevant_observations_are_used() -> None:
    older_camera = make_camera_observation(
        0.50,
        observed_at=START_TIME,
        observation_id=UUID(
            "33333333-3333-3333-3333-333333333333"
        ),
    )

    newer_camera = make_camera_observation(
        0.01,
        observed_at=START_TIME + timedelta(seconds=10),
    )

    older_lux = make_lux_observation(
        0.5,
        observed_at=START_TIME,
        observation_id=UUID(
            "44444444-4444-4444-4444-444444444444"
        ),
    )

    newer_lux = make_lux_observation(
        40_000.0,
        observed_at=START_TIME + timedelta(seconds=10),
    )

    assessment = CameraLuxConsistencyRule().evaluate(
        (
            older_camera,
            newer_camera,
            older_lux,
            newer_lux,
        )
    )

    assert assessment.status is ConsistencyStatus.INCONSISTENT
    assert assessment.involved_observations == (
        CAMERA_ID,
        LUX_ID,
    )


def test_rule_integrates_with_consistency_engine() -> None:
    report = ConsistencyEngine(
        [CameraLuxConsistencyRule()]
    ).evaluate(
        (
            make_camera_observation(0.01),
            make_lux_observation(40_000.0),
        )
    )

    assert report.executed_rule_ids == (
        "consistency.camera_lux",
    )
    assert report.failed_rule_count == 0
    assert report.has_inconsistency is True
    assert report.assessments[0].status is (
        ConsistencyStatus.INCONSISTENT
    )


def test_invalid_configuration_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="maximum_black_luminance must be between",
    ):
        CameraLuxConsistencyRule(
            maximum_black_luminance=1.20
        )

    with pytest.raises(
        ValueError,
        match="minimum_daylight_lux must be greater",
    ):
        CameraLuxConsistencyRule(
            maximum_dark_lux=10.0,
            minimum_daylight_lux=5.0,
        )

    with pytest.raises(
        ValueError,
        match="consistent_confidence must be between",
    ):
        CameraLuxConsistencyRule(
            consistent_confidence=1.20
        )
