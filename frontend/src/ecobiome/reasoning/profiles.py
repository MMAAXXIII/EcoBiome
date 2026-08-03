"""Built-in reasoning-component registry profiles."""

from ecobiome.core.observation import InMemoryObservationStore
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
from ecobiome.reasoning.rules import (
    BlackFrameRule,
    RuleDomain,
)


def build_camera_lux_registry() -> ReasoningComponentRegistry:
    """Build the standard camera/lux diagnostic registry."""
    registry = ReasoningComponentRegistry()

    registry.register_quality(
        BlackFrameRule(
            identifier="vision.camera_black_frame",
            name="Camera black frame",
            description=(
                "Detect consecutive nearly black camera frames."
            ),
            domain=RuleDomain.VISION,
            observation_store=InMemoryObservationStore(),
            minimum_frame_count=1,
            maximum_luminance=0.02,
            suspect_score=0.20,
        )
    )

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
