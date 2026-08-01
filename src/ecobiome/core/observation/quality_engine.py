"""Aggregate independent quality assessments for observations."""

from collections.abc import Iterable
from dataclasses import dataclass

from ecobiome.core.observation.observation import Observation
from ecobiome.core.observation.quality import (
    DataQuality,
    DiagnosticCode,
    QualityAssessment,
)
from ecobiome.reasoning.rules.quality_rule import QualityRule

ObservationQualityRule = QualityRule



@dataclass(frozen=True, slots=True)
class QualityRuleFailure:
    """Describe one quality rule that failed."""

    rule_identifier: str
    exception_type: str
    message: str


@dataclass(frozen=True, slots=True)
class QualityEvaluationReport:
    """Summarize a complete observation-quality evaluation."""

    assessment: QualityAssessment
    executed_rule_ids: tuple[str, ...]
    failures: tuple[QualityRuleFailure, ...]

    @property
    def failed_rule_count(self) -> int:
        """Return the number of failed quality rules."""
        return len(self.failures)

    @property
    def succeeded(self) -> bool:
        """Return whether every rule completed successfully."""
        return not self.failures


_QUALITY_RANK = {
    DataQuality.VALID: 0,
    DataQuality.SUSPECT: 1,
    DataQuality.STALE: 2,
    DataQuality.INVALID: 3,
    DataQuality.MISSING: 4,
}


def merge_quality_assessments(
    assessments: Iterable[QualityAssessment],
) -> QualityAssessment:
    """Merge assessments using the most conservative result."""
    materialized = tuple(assessments)

    if not materialized:
        raise ValueError(
            "At least one quality assessment is required."
        )

    observation_id = materialized[0].observation_id

    if any(
        item.observation_id != observation_id
        for item in materialized
    ):
        raise ValueError(
            "Quality assessments must target the same observation."
        )

    worst_quality = max(
        (item.quality for item in materialized),
        key=_QUALITY_RANK.__getitem__,
    )
    score = min(item.score for item in materialized)

    diagnostics = tuple(
        dict.fromkeys(
            diagnostic
            for item in materialized
            for diagnostic in item.diagnostics
        )
    )
    reasons = tuple(
        dict.fromkeys(
            reason
            for item in materialized
            for reason in item.reasons
        )
    )

    if worst_quality is DataQuality.VALID:
        return QualityAssessment.valid(
            observation_id,
            score=score,
        )

    if worst_quality in {
        DataQuality.INVALID,
        DataQuality.MISSING,
    }:
        score = 0.0

    return QualityAssessment(
        observation_id=observation_id,
        quality=worst_quality,
        score=score,
        diagnostics=diagnostics,
        reasons=reasons,
    )


class ObservationQualityEngine:
    """Execute and aggregate independent quality rules."""

    def __init__(
        self,
        rules: Iterable[QualityRule] = (),
    ) -> None:
        self._rules = self._prepare_rules(rules)

    @staticmethod
    def _prepare_rules(
        rules: Iterable[QualityRule],
    ) -> tuple[QualityRule, ...]:
        """Validate unique quality-rule identifiers."""
        materialized = tuple(rules)
        identifiers: set[str] = set()

        for rule in materialized:
            if not callable(getattr(rule, "assess", None)):
                raise TypeError(
                    f"Quality rule {rule.identifier!r} "
                    "must implement assess()."
                )

            if rule.identifier in identifiers:
                raise ValueError(
                    "Duplicate quality-rule identifier: "
                    f"{rule.identifier!r}."
                )

            identifiers.add(rule.identifier)

        return materialized

    def evaluate(
        self,
        observation: Observation,
    ) -> QualityEvaluationReport:
        """Assess an observation without hiding rule failures."""
        assessments: list[QualityAssessment] = []
        executed_rule_ids: list[str] = []
        failures: list[QualityRuleFailure] = []

        for rule in self._rules:
            executed_rule_ids.append(rule.identifier)

            try:
                assessments.append(rule.assess(observation))
            except Exception as error:  # noqa: BLE001
                failures.append(
                    QualityRuleFailure(
                        rule_identifier=rule.identifier,
                        exception_type=type(error).__name__,
                        message=str(error),
                    )
                )

        if failures:
            assessments.append(
                QualityAssessment(
                    observation_id=observation.observation_id,
                    quality=DataQuality.SUSPECT,
                    score=0.50,
                    diagnostics=(DiagnosticCode.UNKNOWN,),
                    reasons=(
                        (
                            "One or more quality rules failed "
                            "during evaluation."
                        ),
                    ),
                )
            )

        if not assessments:
            assessments.append(
                QualityAssessment.valid(
                    observation.observation_id
                )
            )

        return QualityEvaluationReport(
            assessment=merge_quality_assessments(assessments),
            executed_rule_ids=tuple(executed_rule_ids),
            failures=tuple(failures),
        )


