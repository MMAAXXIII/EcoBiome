"""End-to-end tests for the diagnostic investigation pipeline."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    InMemoryObservationStore,
    Observation,
    ObservationQualityEngine,
)
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.reasoning.abduction import (
    CameraLuxHypothesisRule,
    HypothesisGenerator,
)
from ecobiome.reasoning.consistency import ConsistencyEngine
from ecobiome.reasoning.consistency.rules import (
    CameraLuxConsistencyRule,
)
from ecobiome.reasoning.diagnostic_pipeline import (
    DiagnosticInvestigationPipeline,
)
from ecobiome.reasoning.experiment import (
    CameraLuxExperimentRule,
    ExperimentPlanner,
)
from ecobiome.reasoning.rules import (
    BlackFrameRule,
    RuleDomain,
)

OBSERVED_AT = datetime(
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
    """Create the camera-luminance variable."""
    return ScientificVariable(
        identifier="vision.frame_mean_luminance",
        name="Frame mean luminance",
        description="Normalized camera-frame luminance.",
        unit="dimensionless",
        display_unit=None,
        category="vision",
    )


def make_lux_variable() -> ScientificVariable:
    """Create the ambient-light variable."""
    return ScientificVariable(
        identifier="weather.ambient_light",
        name="Ambient light",
        description="Independent ambient-light measurement.",
        unit="lux",
        display_unit="lux",
        category="weather",
    )


def make_camera_observation(
    luminance: float = 0.01,
) -> Observation:
    """Create one almost-black camera observation."""
    return Observation(
        observation_id=CAMERA_ID,
        source="camera-01",
        variable=make_camera_variable(),
        value=luminance,
        acquisition_method=AcquisitionMethod.CAMERA,
        confidence=0.99,
        observed_at=OBSERVED_AT,
    )


def make_lux_observation(
    lux: float = 40_000.0,
) -> Observation:
    """Create one ambient-light observation."""
    return Observation(
        observation_id=LUX_ID,
        source="lux-sensor-01",
        variable=make_lux_variable(),
        value=lux,
        acquisition_method=AcquisitionMethod.SENSOR,
        confidence=0.99,
        observed_at=OBSERVED_AT,
    )


def make_pipeline() -> DiagnosticInvestigationPipeline:
    """Create the complete camera/lux diagnostic pipeline."""
    quality_engine = ObservationQualityEngine(
        [
            BlackFrameRule(
                identifier="vision.camera_black_frame",
                name="Camera black frame",
                description="Detect consecutive black camera frames.",
                domain=RuleDomain.VISION,
                observation_store=InMemoryObservationStore(),
                minimum_frame_count=1,
                maximum_luminance=0.02,
                suspect_score=0.20,
            )
        ]
    )

    return DiagnosticInvestigationPipeline(
        quality_engine=quality_engine,
        consistency_engine=ConsistencyEngine(
            [CameraLuxConsistencyRule()]
        ),
        hypothesis_generator=HypothesisGenerator(
            [CameraLuxHypothesisRule()]
        ),
        experiment_planner=ExperimentPlanner(
            [CameraLuxExperimentRule()]
        ),
    )


def test_full_pipeline_detects_contradiction() -> None:
    report = make_pipeline().run(
        (
            make_camera_observation(),
            make_lux_observation(),
        )
    )

    assert report.has_inconsistency is True
    assert len(report.usable_observations) == 2
    assert report.rejected_observations == ()
    assert report.proposal_count == 4
    assert report.experiment_count == 3
    assert report.succeeded is True


def test_full_pipeline_ranks_best_experiment() -> None:
    report = make_pipeline().run(
        (
            make_camera_observation(),
            make_lux_observation(),
        )
    )

    assert report.best_experiment is not None
    assert report.best_experiment.identifier == (
        "camera.clean_lens_and_recapture"
    )
    assert report.best_experiment.estimated_information_gain == (
        pytest.approx(0.46)
    )


def test_dark_camera_and_dark_environment_need_no_investigation() -> None:
    report = make_pipeline().run(
        (
            make_camera_observation(),
            make_lux_observation(0.5),
        )
    )

    assert report.has_inconsistency is False
    assert report.proposals == ()
    assert report.experiments == ()
    assert report.best_experiment is None


def test_pipeline_preserves_quality_assessments() -> None:
    report = make_pipeline().run(
        (
            make_camera_observation(),
            make_lux_observation(),
        )
    )

    assert len(report.quality_reports) == 2

    camera_quality = report.quality_reports[0].assessment
    lux_quality = report.quality_reports[1].assessment

    assert camera_quality.score == pytest.approx(0.20)
    assert camera_quality.is_usable_for_reasoning is True
    assert lux_quality.score == pytest.approx(1.0)


def test_empty_input_is_handled_without_crashing() -> None:
    report = make_pipeline().run(())

    assert report.usable_observations == ()
    assert report.rejected_observations == ()
    assert report.proposals == ()
    assert report.experiments == ()
    assert report.succeeded is True
