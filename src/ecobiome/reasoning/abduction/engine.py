"""Execution engine for abductive hypothesis-generation rules."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from ecobiome.core.observation import Observation
from ecobiome.reasoning.abduction.proposal import (
    HypothesisProposal,
)
from ecobiome.reasoning.consistency import (
    ConsistencyAssessment,
)


class HypothesisGenerationRule(Protocol):
    """Rule capable of proposing explanations for an assessment."""

    identifier: str

    def generate(
        self,
        assessment: ConsistencyAssessment,
        observations: tuple[Observation, ...],
    ) -> tuple[HypothesisProposal, ...]:
        """Generate provisional explanations."""


@dataclass(frozen=True, slots=True)
class HypothesisGenerationFailure:
    """Describe one hypothesis-generation rule failure."""

    rule_identifier: str
    exception_type: str
    message: str


@dataclass(frozen=True, slots=True)
class HypothesisGenerationReport:
    """Summarize one abductive generation cycle."""

    proposals: tuple[HypothesisProposal, ...]
    executed_rule_ids: tuple[str, ...]
    failures: tuple[HypothesisGenerationFailure, ...]

    @property
    def proposal_count(self) -> int:
        """Return the number of generated proposals."""
        return len(self.proposals)

    @property
    def failed_rule_count(self) -> int:
        """Return the number of failed rules."""
        return len(self.failures)

    @property
    def succeeded(self) -> bool:
        """Return whether every rule completed successfully."""
        return not self.failures


class HypothesisGenerator:
    """Generate and rank concurrent explanatory hypotheses."""

    def __init__(
        self,
        rules: Iterable[HypothesisGenerationRule] = (),
    ) -> None:
        self._rules = self._prepare_rules(rules)

    @staticmethod
    def _prepare_rules(
        rules: Iterable[HypothesisGenerationRule],
    ) -> tuple[HypothesisGenerationRule, ...]:
        """Validate unique rule identifiers."""
        materialized = tuple(rules)
        identifiers: set[str] = set()

        for rule in materialized:
            if not callable(getattr(rule, "generate", None)):
                raise TypeError(
                    f"Hypothesis-generation rule "
                    f"{rule.identifier!r} must implement generate()."
                )

            if rule.identifier in identifiers:
                raise ValueError(
                    "Duplicate hypothesis-generation rule identifier: "
                    f"{rule.identifier!r}."
                )

            identifiers.add(rule.identifier)

        return materialized

    def generate(
        self,
        assessment: ConsistencyAssessment,
        observations: Iterable[Observation],
    ) -> HypothesisGenerationReport:
        """Generate ranked proposals while isolating rule failures."""
        materialized = tuple(observations)

        proposals: list[HypothesisProposal] = []
        executed_rule_ids: list[str] = []
        failures: list[HypothesisGenerationFailure] = []

        for rule in self._rules:
            executed_rule_ids.append(rule.identifier)

            try:
                proposals.extend(
                    rule.generate(assessment, materialized)
                )
            except Exception as error:  # noqa: BLE001
                failures.append(
                    HypothesisGenerationFailure(
                        rule_identifier=rule.identifier,
                        exception_type=type(error).__name__,
                        message=str(error),
                    )
                )

        ranked = tuple(
            sorted(
                proposals,
                key=lambda proposal: (
                    -proposal.confidence,
                    proposal.identifier,
                ),
            )
        )

        return HypothesisGenerationReport(
            proposals=ranked,
            executed_rule_ids=tuple(executed_rule_ids),
            failures=tuple(failures),
        )
