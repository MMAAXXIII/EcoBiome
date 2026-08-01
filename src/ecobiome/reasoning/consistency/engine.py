"""Consistency evaluation engine."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from ecobiome.core.observation import Observation
from ecobiome.reasoning.consistency.consistency import (
    ConsistencyAssessment,
    ConsistencyStatus,
)


class ConsistencyRule(Protocol):
    """Rule capable of comparing multiple observations."""

    @property
    def identifier(self) -> str:
        """Return the component identifier."""
        ...

    def evaluate(
        self,
        observations: tuple[Observation, ...],
    ) -> ConsistencyAssessment:
        """Evaluate the consistency of a group of observations."""


@dataclass(frozen=True, slots=True)
class ConsistencyRuleFailure:
    """Describe one consistency rule that failed."""

    rule_identifier: str
    exception_type: str
    message: str


@dataclass(frozen=True, slots=True)
class ConsistencyEvaluationReport:
    """Summarize one complete consistency evaluation."""

    assessments: tuple[ConsistencyAssessment, ...]
    executed_rule_ids: tuple[str, ...]
    failures: tuple[ConsistencyRuleFailure, ...]

    @property
    def failed_rule_count(self) -> int:
        """Return the number of failed rules."""
        return len(self.failures)

    @property
    def succeeded(self) -> bool:
        """Return whether every rule completed successfully."""
        return not self.failures

    @property
    def has_inconsistency(self) -> bool:
        """Return whether at least one rule found a contradiction."""
        return any(
            assessment.status is ConsistencyStatus.INCONSISTENT
            for assessment in self.assessments
        )


class ConsistencyEngine:
    """Execute independent multi-observation consistency rules."""

    def __init__(
        self,
        rules: Iterable[ConsistencyRule] = (),
    ) -> None:
        self._rules = self._prepare_rules(rules)

    @staticmethod
    def _prepare_rules(
        rules: Iterable[ConsistencyRule],
    ) -> tuple[ConsistencyRule, ...]:
        """Validate unique rule identifiers."""
        materialized = tuple(rules)
        identifiers: set[str] = set()

        for rule in materialized:
            if not callable(getattr(rule, "evaluate", None)):
                raise TypeError(
                    f"Consistency rule {rule.identifier!r} "
                    "must implement evaluate()."
                )

            if rule.identifier in identifiers:
                raise ValueError(
                    "Duplicate consistency-rule identifier: "
                    f"{rule.identifier!r}."
                )

            identifiers.add(rule.identifier)

        return materialized

    def evaluate(
        self,
        observations: Iterable[Observation],
    ) -> ConsistencyEvaluationReport:
        """Evaluate a group of observations without hiding failures."""
        materialized = tuple(observations)

        if not self._rules:
            return ConsistencyEvaluationReport(
                assessments=(
                    ConsistencyAssessment(
                        status=ConsistencyStatus.UNKNOWN,
                        confidence=0.0,
                        involved_observations=tuple(
                            observation.observation_id
                            for observation in materialized
                        ),
                        reason="No consistency rule is configured.",
                    ),
                ),
                executed_rule_ids=(),
                failures=(),
            )

        assessments: list[ConsistencyAssessment] = []
        executed_rule_ids: list[str] = []
        failures: list[ConsistencyRuleFailure] = []

        for rule in self._rules:
            executed_rule_ids.append(rule.identifier)

            try:
                assessments.append(
                    rule.evaluate(materialized)
                )
            except Exception as error:  # noqa: BLE001
                failures.append(
                    ConsistencyRuleFailure(
                        rule_identifier=rule.identifier,
                        exception_type=type(error).__name__,
                        message=str(error),
                    )
                )

        return ConsistencyEvaluationReport(
            assessments=tuple(assessments),
            executed_rule_ids=tuple(executed_rule_ids),
            failures=tuple(failures),
        )
