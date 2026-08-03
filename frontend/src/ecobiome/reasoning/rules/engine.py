"""Execution engine for independent scientific evidence rules."""

from collections.abc import Iterable
from dataclasses import dataclass
from time import perf_counter

from ecobiome.core.observation import Observation
from ecobiome.reasoning.evidence import Evidence
from ecobiome.reasoning.rules.evidence_rule import EvidenceRule
from ecobiome.reasoning.rules.rule import RuleDomain


@dataclass(frozen=True, slots=True)
class RuleFailure:
    """Describe one rule that failed during evaluation."""

    rule_identifier: str
    exception_type: str
    message: str


@dataclass(frozen=True, slots=True)
class RuleExecutionReport:
    """Summarize one complete evidence-rule evaluation."""

    evidence: tuple[Evidence, ...]
    executed_rule_ids: tuple[str, ...]
    skipped_rule_ids: tuple[str, ...]
    failures: tuple[RuleFailure, ...]
    duration_seconds: float

    @property
    def executed_rule_count(self) -> int:
        """Return the number of rules that were attempted."""
        return len(self.executed_rule_ids)

    @property
    def skipped_rule_count(self) -> int:
        """Return the number of skipped rules."""
        return len(self.skipped_rule_ids)

    @property
    def failed_rule_count(self) -> int:
        """Return the number of failed rules."""
        return len(self.failures)

    @property
    def evidence_count(self) -> int:
        """Return the number of generated evidence records."""
        return len(self.evidence)

    @property
    def succeeded(self) -> bool:
        """Return whether every executed rule completed successfully."""
        return not self.failures


class RuleEngine:
    """Evaluate observations using ordered evidence-producing rules."""

    def __init__(
        self,
        rules: Iterable[EvidenceRule] = (),
        *,
        enabled_domains: Iterable[RuleDomain] | None = None,
    ) -> None:
        self._rules = self._prepare_rules(rules)
        self._enabled_domains = (
            frozenset(enabled_domains)
            if enabled_domains is not None
            else None
        )

    @staticmethod
    def _prepare_rules(
        rules: Iterable[EvidenceRule],
    ) -> tuple[EvidenceRule, ...]:
        """Validate contracts, identifiers, and execution order."""
        materialized = tuple(rules)
        identifiers: set[str] = set()

        for rule in materialized:
            if not callable(getattr(rule, "evaluate", None)):
                raise TypeError(
                    f"Evidence rule {rule.identifier!r} "
                    "must implement evaluate()."
                )

            if rule.identifier in identifiers:
                raise ValueError(
                    f"Duplicate rule identifier: {rule.identifier!r}."
                )

            identifiers.add(rule.identifier)

        return tuple(
            sorted(
                materialized,
                key=lambda rule: (
                    -rule.priority,
                    rule.identifier,
                ),
            )
        )

    def evaluate(
        self,
        observation: Observation,
    ) -> RuleExecutionReport:
        """Evaluate one observation while isolating rule failures."""
        started_at = perf_counter()

        evidence: list[Evidence] = []
        executed_rule_ids: list[str] = []
        skipped_rule_ids: list[str] = []
        failures: list[RuleFailure] = []

        for rule in self._rules:
            if not self._should_execute(rule):
                skipped_rule_ids.append(rule.identifier)
                continue

            executed_rule_ids.append(rule.identifier)

            try:
                generated = rule.evaluate(observation)
            except Exception as error:  # noqa: BLE001
                failures.append(
                    RuleFailure(
                        rule_identifier=rule.identifier,
                        exception_type=type(error).__name__,
                        message=str(error),
                    )
                )
                continue

            evidence.extend(generated)

        return RuleExecutionReport(
            evidence=tuple(evidence),
            executed_rule_ids=tuple(executed_rule_ids),
            skipped_rule_ids=tuple(skipped_rule_ids),
            failures=tuple(failures),
            duration_seconds=perf_counter() - started_at,
        )

    def _should_execute(self, rule: EvidenceRule) -> bool:
        """Return whether one rule is enabled for this engine."""
        if not rule.enabled:
            return False

        if self._enabled_domains is None:
            return True

        return rule.domain in self._enabled_domains

    @property
    def rules(self) -> tuple[EvidenceRule, ...]:
        """Return registered rules in execution order."""
        return self._rules
