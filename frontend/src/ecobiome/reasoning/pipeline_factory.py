"""Build diagnostic pipelines from explicit component registries."""

from dataclasses import dataclass

from ecobiome.core.observation.quality_engine import (
    ObservationQualityEngine,
)
from ecobiome.reasoning.abduction.engine import (
    HypothesisGenerator,
)
from ecobiome.reasoning.component_registry import (
    ReasoningComponentRegistry,
)
from ecobiome.reasoning.consistency.engine import (
    ConsistencyEngine,
)
from ecobiome.reasoning.diagnostic_pipeline import (
    DiagnosticInvestigationPipeline,
)
from ecobiome.reasoning.experiment.planner import (
    ExperimentPlanner,
)


@dataclass(frozen=True, slots=True)
class DiagnosticPipelineFactory:
    """Build configured diagnostic pipelines."""

    registry: ReasoningComponentRegistry

    def build(self) -> DiagnosticInvestigationPipeline:
        """Build a pipeline from registered components."""
        return DiagnosticInvestigationPipeline(
            quality_engine=ObservationQualityEngine(
                self.registry.quality_rules
            ),
            consistency_engine=ConsistencyEngine(
                self.registry.consistency_rules
            ),
            hypothesis_generator=HypothesisGenerator(
                self.registry.hypothesis_rules
            ),
            experiment_planner=ExperimentPlanner(
                self.registry.experiment_rules
            ),
        )
