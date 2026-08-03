"""Tests for consecutive black-frame camera detection."""

from datetime import UTC, datetime, timedelta

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    DataQuality,
    DiagnosticCode,
    InMemoryObservationStore,
    Observation,
    ObservationQualityEngine,
)
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.reasoning import RuleDomain
from ecobiome.reasoning.rules import BlackFrameRule

START_TIME = datetime(
    2026,
    8,
    1,
    12,
    0,
    tzinfo=UTC,
)


def make_variable() -> ScientificVariable:
    """Create the normalized frame-luminance variable."""
    return ScientificVariable(
        identifier="vision.frame_mean_luminance",
        name="Frame mean luminance",
        description=(
            "Normalized mean luminance of one camera frame."
        ),
        unit="dimensionless",
        display_unit=None,
        category="vision",
    )


def make_observation(
    *,
    second: int,
    luminance: float,
    source: str = "camera-01",
) -> Observation:
    """Create one controlled camera-luminance observation."""
    return Observation(
        source=source,
        variable=make_variable(),
        value=luminance,
        acquisition_method=AcquisitionMethod.CAMERA,
        confidence=0.99,
        observed_at=START_TIME + timedelta(seconds=second),
    )


def make_rule(
    store: InMemoryObservationStore,
    *,
    maximum_luminance: float = 0.02,
    minimum_frame_count: int = 3,
) -> BlackFrameRule:
    """Create one deterministic black-frame rule."""
    return BlackFrameRule(
        identifier="vision.camera_black_frame",
        name="Camera black frame",
        description=(
            "Detect consecutive frames whose mean luminance "
            "is abnormally low."
        ),
        domain=RuleDomain.VISION,
        priority=120,
        observation_store=store,
        maximum_luminance=maximum_luminance,
        minimum_frame_count=minimum_frame_count,
        suspect_score=0.20,
    )


def test_consecutive_black_frames_are_suspect() -> None:
    store = InMemoryObservationStore(
        [
            make_observation(second=0, luminance=0.005),
            make_observation(second=1, luminance=0.010),
        ]
    )

    assessment = make_rule(store).assess(
        make_observation(second=2, luminance=0.008)
    )

    assert assessment.quality is DataQuality.SUSPECT
    assert assessment.score == pytest.approx(0.20)
    assert assessment.diagnostics == (
        DiagnosticCode.CAMERA_BLACK_FRAME,
    )
    assert "does not establish that it is night" not in (
        assessment.reasons[0]
    )
    assert "darkness, obstruction" in assessment.reasons[0]


def test_one_bright_frame_prevents_black_frame_diagnosis() -> None:
    store = InMemoryObservationStore(
        [
            make_observation(second=0, luminance=0.005),
            make_observation(second=1, luminance=0.400),
        ]
    )

    assessment = make_rule(store).assess(
        make_observation(second=2, luminance=0.008)
    )

    assert assessment.quality is DataQuality.VALID
    assert assessment.diagnostics == ()


def test_insufficient_frame_count_remains_valid() -> None:
    store = InMemoryObservationStore(
        [
            make_observation(second=0, luminance=0.005),
        ]
    )

    assessment = make_rule(store).assess(
        make_observation(second=1, luminance=0.008)
    )

    assert assessment.quality is DataQuality.VALID


def test_other_camera_is_ignored() -> None:
    store = InMemoryObservationStore(
        [
            make_observation(
                second=0,
                luminance=0.005,
                source="camera-02",
            ),
            make_observation(
                second=1,
                luminance=0.005,
                source="camera-02",
            ),
        ]
    )

    assessment = make_rule(store).assess(
        make_observation(
            second=2,
            luminance=0.005,
            source="camera-01",
        )
    )

    assert assessment.quality is DataQuality.VALID


def test_luminance_outside_normalized_range_is_invalid() -> None:
    assessment = make_rule(
        InMemoryObservationStore()
    ).assess(
        make_observation(second=0, luminance=1.50)
    )

    assert assessment.quality is DataQuality.INVALID
    assert assessment.score == pytest.approx(0.0)
    assert assessment.diagnostics == (
        DiagnosticCode.IMPOSSIBLE_VALUE,
    )


def test_boolean_luminance_is_invalid() -> None:
    observation = Observation(
        source="camera-01",
        variable=make_variable(),
        value=True,
        acquisition_method=AcquisitionMethod.CAMERA,
        observed_at=START_TIME,
    )

    assessment = make_rule(
        InMemoryObservationStore()
    ).assess(observation)

    assert assessment.quality is DataQuality.INVALID


def test_other_variable_is_ignored() -> None:
    variable = ScientificVariable(
        identifier="weather.ambient_light",
        name="Ambient light",
        description="Ambient light measured independently.",
        unit="lux",
        display_unit="lux",
        category="weather",
    )

    observation = Observation(
        source="light-sensor-01",
        variable=variable,
        value=500.0,
        acquisition_method=AcquisitionMethod.SENSOR,
        observed_at=START_TIME,
    )

    assessment = make_rule(
        InMemoryObservationStore()
    ).assess(observation)

    assert assessment.quality is DataQuality.VALID


def test_rule_integrates_with_quality_engine() -> None:
    store = InMemoryObservationStore(
        [
            make_observation(second=0, luminance=0.0),
            make_observation(second=1, luminance=0.0),
        ]
    )

    report = ObservationQualityEngine(
        [make_rule(store)]
    ).evaluate(
        make_observation(second=2, luminance=0.0)
    )

    assert report.assessment.quality is DataQuality.SUSPECT
    assert report.assessment.is_usable_for_reasoning is True
    assert report.failed_rule_count == 0


def test_invalid_configuration_is_rejected() -> None:
    store = InMemoryObservationStore()

    with pytest.raises(
        ValueError,
        match="maximum_luminance must be between",
    ):
        make_rule(store, maximum_luminance=1.20)

    with pytest.raises(
        ValueError,
        match="minimum_frame_count must be at least one",
    ):
        make_rule(store, minimum_frame_count=0)
