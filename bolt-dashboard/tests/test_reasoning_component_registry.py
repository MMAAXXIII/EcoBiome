"""Tests for the explicit reasoning-component registry."""

from datetime import UTC, datetime

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    InMemoryObservationStore,
    Observation,
)
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.reasoning.abduction import (
    CameraLuxHypothesisRule,
)
from ecobiome.reasoning.component_registry import (
    ReasoningComponentRegistry,
)
from ecobiome.reasoning.consistency.rules import (
    CameraLuxConsistencyRule,
)
from ecobiome.reasoning.experiment import (
    CameraLuxExperimentRule,
)
from ecobiome.reasoning.pipeline_factory import (
    DiagnosticPipelineFactory,
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


def make_black_frame_rule() -> BlackFrameRule:
    """Create one black-frame quality rule."""
    return BlackFrameRule(
        identifier="vision.camera_black_frame",
        name="Camera black frame",
        description="Detect consecutive black camera frames.",
        domain=RuleDomain.VISION,
        observation_store=InMemoryObservationStore(),
        minimum_frame_count=1,
    )


def make_camera_observation() -> Observation:
    """Create one black camera observation."""
    variable = ScientificVariable(
        identifier="vision.frame_mean_luminance",
        name="Frame luminance",
        description="Normalized frame luminance.",
        unit="dimensionless",
        display_unit=None,
        category="vision",
    )

    return Observation(
        source="camera-01",
        variable=variable,
        value=0.01,
        acquisition_method=AcquisitionMethod.CAMERA,
        observed_at=OBSERVED_AT,
    )


def make_lux_observation() -> Observation:
    """Create one daylight lux observation."""
    variable = ScientificVariable(
        identifier="weather.ambient_light",
        name="Ambient light",
        description="Independent ambient light.",
        unit="lux",
        display_unit="lux",
        category="weather",
    )

    return Observation(
        source="lux-sensor-01",
        variable=variable,
        value=40_000.0,
        acquisition_method=AcquisitionMethod.SENSOR,
        observed_at=OBSERVED_AT,
    )


def make_registry() -> ReasoningComponentRegistry:
    """Create a complete camera/lux component registry."""
    registry = ReasoningComponentRegistry()

    registry.register_quality(make_black_frame_rule())
    registry.register_consistency(
        CameraLuxConsistencyRule()
    )
    registry.register_hypothesis(
        CameraLuxHypothesisRule()
    )
    registry.register_experiment(
        CameraLuxExperimentRule()
    )

    return registry


def test_registry_counts_components_by_family() -> None:
    summary = make_registry().summary

    assert summary.quality_rule_count == 1
    assert summary.consistency_rule_count == 1
    assert summary.hypothesis_rule_count == 1
    assert summary.experiment_rule_count == 1
    assert summary.total_count == 4


def test_registered_components_are_exposed() -> None:
    registry = make_registry()

    assert registry.quality_rules[0].identifier == (
        "vision.camera_black_frame"
    )
    assert registry.consistency_rules[0].identifier == (
        "consistency.camera_lux"
    )
    assert registry.hypothesis_rules[0].identifier == (
        "abduction.camera_lux_contradiction"
    )
    assert registry.experiment_rules[0].identifier == (
        "experiment.camera_lux_diagnosis"
    )


def test_duplicate_identifier_in_same_family_is_rejected() -> None:
    registry = ReasoningComponentRegistry()
    registry.register_consistency(
        CameraLuxConsistencyRule()
    )

    with pytest.raises(
        ValueError,
        match="Duplicate consistency component identifier",
    ):
        registry.register_consistency(
            CameraLuxConsistencyRule()
        )


def test_same_identifier_can_exist_in_different_families() -> None:
    class QualityComponent:
        identifier = "shared.identifier"

        def assess(self, observation: Observation):
            raise NotImplementedError

    class ConsistencyComponent:
        identifier = "shared.identifier"

        def evaluate(
            self,
            observations: tuple[Observation, ...],
        ):
            raise NotImplementedError

    registry = ReasoningComponentRegistry()
    registry.register_quality(QualityComponent())
    registry.register_consistency(ConsistencyComponent())

    assert registry.summary.total_count == 2


def test_invalid_component_contract_is_rejected() -> None:
    class InvalidComponent:
        identifier = "invalid.component"

    registry = ReasoningComponentRegistry()

    with pytest.raises(
        TypeError,
        match="must implement assess",
    ):
        registry.register_quality(
            InvalidComponent()  # type: ignore[arg-type]
        )


def test_factory_builds_operational_pipeline() -> None:
    pipeline = DiagnosticPipelineFactory(
        make_registry()
    ).build()

    report = pipeline.run(
        (
            make_camera_observation(),
            make_lux_observation(),
        )
    )

    assert report.has_inconsistency is True
    assert report.proposal_count == 4
    assert report.experiment_count == 3
    assert report.succeeded is True
