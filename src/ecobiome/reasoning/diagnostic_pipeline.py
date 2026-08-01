"""End-to-end orchestration of EcoBiome diagnostic reasoning."""

from collections.abc import Iterable
from dataclasses import dataclass

from ecobiome.core.observation.observation import Observation
from ecobiome.core.observation.quality_engine import (
    ObservationQualityEngine,
    QualityEvaluationReport,
)
from ecobiome.reasoning.abduction import (
    HypothesisGenerationFailure,
    HypothesisGenerator,
    HypothesisProposal,
)
from ecobiome.reasoning.consistency import (
    ConsistencyEngine,
    ConsistencyEvaluationReport,
)
from ecobiome.reasoning.experiment import (
    Experiment,
    ExperimentPlanner,
    ExperimentPlanningFailure,
)


@dataclass(frozen=True, slots=True)
class DiagnosticInvestigationReport:
    """Summarize one complete diagnostic investigation cycle."""

    quality_reports: tuple[QualityEvaluationReport, ...]
    usable_observations: tuple[Observation, ...]
    rejected_observations: tuple[Observation, ...]
    consistency_report: ConsistencyEvaluationReport
    proposals: tuple[HypothesisProposal, ...]
    experiments: tuple[Experiment, ...]
    hypothesis_failures: tuple[HypothesisGenerationFailure, ...]
    experiment_failures: tuple[ExperimentPlanningFailure, ...]

    @property
    def has_inconsistency(self) -> bool:
        """Return whether the usable observations contain a contradiction."""
        return self.consistency_report.has_inconsistency

    @property
    def proposal_count(self) -> int:
        """Return the number of generated diagnostic proposals."""
        return len(self.proposals)

    @property
    def experiment_count(self) -> int:
        """Return the number of proposed experiments."""
        return len(self.experiments)

    @property
    def best_experiment(self) -> Experiment | None:
        """Return the highest-ranked proposed experiment."""
        if not self.experiments:
            return None

        return self.experiments[0]

    @property
    def succeeded(self) -> bool:
        """Return whether every pipeline stage completed without failure."""
        return (
            all(
                report.succeeded
                for report in self.quality_reports
            )
            and self.consistency_report.succeeded
            and not self.hypothesis_failures
            and not self.experiment_failures
        )


class DiagnosticInvestigationPipeline:
    """Run quality, consistency, abduction, and experiment planning."""

    def __init__(
        self,
        *,
        quality_engine: ObservationQualityEngine,
        consistency_engine: ConsistencyEngine,
        hypothesis_generator: HypothesisGenerator,
        experiment_planner: ExperimentPlanner,
    ) -> None:
        self._quality_engine = quality_engine
        self._consistency_engine = consistency_engine
        self._hypothesis_generator = hypothesis_generator
        self._experiment_planner = experiment_planner

    def run(
        self,
        observations: Iterable[Observation],
    ) -> DiagnosticInvestigationReport:
        """Run one complete, traceable diagnostic investigation."""
        materialized = tuple(observations)

        quality_reports = tuple(
            self._quality_engine.evaluate(observation)
            for observation in materialized
        )

        usable_observations = tuple(
            observation
            for observation, report in zip(
                materialized,
                quality_reports,
                strict=True,
            )
            if report.assessment.is_usable_for_reasoning
        )

        rejected_observations = tuple(
            observation
            for observation, report in zip(
                materialized,
                quality_reports,
                strict=True,
            )
            if not report.assessment.is_usable_for_reasoning
        )

        consistency_report = self._consistency_engine.evaluate(
            usable_observations
        )

        proposals: list[HypothesisProposal] = []
        hypothesis_failures: list[HypothesisGenerationFailure] = []

        for assessment in consistency_report.assessments:
            generation_report = self._hypothesis_generator.generate(
                assessment,
                usable_observations,
            )

            proposals.extend(generation_report.proposals)
            hypothesis_failures.extend(generation_report.failures)

        ranked_proposals = self._deduplicate_proposals(proposals)

        planning_report = self._experiment_planner.plan(
            ranked_proposals
        )

        return DiagnosticInvestigationReport(
            quality_reports=quality_reports,
            usable_observations=usable_observations,
            rejected_observations=rejected_observations,
            consistency_report=consistency_report,
            proposals=ranked_proposals,
            experiments=planning_report.experiments,
            hypothesis_failures=tuple(hypothesis_failures),
            experiment_failures=planning_report.failures,
        )

    @staticmethod
    def _deduplicate_proposals(
        proposals: Iterable[HypothesisProposal],
    ) -> tuple[HypothesisProposal, ...]:
        """Keep the highest-confidence version of each proposal."""
        by_identifier: dict[str, HypothesisProposal] = {}

        for proposal in proposals:
            existing = by_identifier.get(proposal.identifier)

            if (
                existing is None
                or proposal.confidence > existing.confidence
            ):
                by_identifier[proposal.identifier] = proposal

        return tuple(
            sorted(
                by_identifier.values(),
                key=lambda proposal: (
                    -proposal.confidence,
                    proposal.identifier,
                ),
            )
        )
