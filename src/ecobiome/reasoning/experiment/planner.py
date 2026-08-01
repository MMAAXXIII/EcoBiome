"""Planning engine for uncertainty-reducing scientific experiments."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from ecobiome.reasoning.abduction import HypothesisProposal
from ecobiome.reasoning.experiment.experiment import Experiment


class ExperimentPlanningRule(Protocol):
    """Rule capable of proposing experiments for hypotheses."""

    identifier: str

    def plan(
        self,
        proposals: tuple[HypothesisProposal, ...],
    ) -> tuple[Experiment, ...]:
        """Generate experiments for the supplied proposals."""


@dataclass(frozen=True, slots=True)
class ExperimentPlanningFailure:
    """Describe one failed experiment-planning rule."""

    rule_identifier: str
    exception_type: str
    message: str


@dataclass(frozen=True, slots=True)
class ExperimentPlanningReport:
    """Summarize one complete experiment-planning cycle."""

    experiments: tuple[Experiment, ...]
    executed_rule_ids: tuple[str, ...]
    failures: tuple[ExperimentPlanningFailure, ...]

    @property
    def experiment_count(self) -> int:
        """Return the number of proposed experiments."""
        return len(self.experiments)

    @property
    def failed_rule_count(self) -> int:
        """Return the number of failed planning rules."""
        return len(self.failures)

    @property
    def succeeded(self) -> bool:
        """Return whether every planning rule succeeded."""
        return not self.failures

    @property
    def best_experiment(self) -> Experiment | None:
        """Return the highest-ranked experiment."""
        if not self.experiments:
            return None

        return self.experiments[0]


class ExperimentPlanner:
    """Generate and rank experiments from competing hypotheses."""

    def __init__(
        self,
        rules: Iterable[ExperimentPlanningRule] = (),
    ) -> None:
        self._rules = self._prepare_rules(rules)

    @staticmethod
    def _prepare_rules(
        rules: Iterable[ExperimentPlanningRule],
    ) -> tuple[ExperimentPlanningRule, ...]:
        """Validate planning-rule contracts and identifiers."""
        materialized = tuple(rules)
        identifiers: set[str] = set()

        for rule in materialized:
            if not callable(getattr(rule, "plan", None)):
                raise TypeError(
                    f"Experiment-planning rule "
                    f"{rule.identifier!r} must implement plan()."
                )

            if rule.identifier in identifiers:
                raise ValueError(
                    "Duplicate experiment-planning rule identifier: "
                    f"{rule.identifier!r}."
                )

            identifiers.add(rule.identifier)

        return materialized

    def plan(
        self,
        proposals: Iterable[HypothesisProposal],
    ) -> ExperimentPlanningReport:
        """Generate ranked experiments while isolating failures."""
        materialized = tuple(proposals)

        experiments: list[Experiment] = []
        executed_rule_ids: list[str] = []
        failures: list[ExperimentPlanningFailure] = []

        for rule in self._rules:
            executed_rule_ids.append(rule.identifier)

            try:
                experiments.extend(
                    rule.plan(materialized)
                )
            except Exception as error:  # noqa: BLE001
                failures.append(
                    ExperimentPlanningFailure(
                        rule_identifier=rule.identifier,
                        exception_type=type(error).__name__,
                        message=str(error),
                    )
                )

        deduplicated = {
            experiment.identifier: experiment
            for experiment in experiments
        }

        ranked = tuple(
            sorted(
                deduplicated.values(),
                key=lambda experiment: (
                    -experiment.estimated_information_gain,
                    experiment.estimated_duration,
                    experiment.identifier,
                ),
            )
        )

        return ExperimentPlanningReport(
            experiments=ranked,
            executed_rule_ids=tuple(executed_rule_ids),
            failures=tuple(failures),
        )
