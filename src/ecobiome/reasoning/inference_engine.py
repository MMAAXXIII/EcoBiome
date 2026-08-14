"""Generic inference from scientific evidence."""

from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from ecobiome.reasoning.evidence import Evidence
from ecobiome.reasoning.hypothesis import (
    Hypothesis,
    HypothesisStatus,
)


@dataclass(frozen=True, slots=True)
class InferenceThresholds:
    """Confidence thresholds controlling hypothesis status."""

    rejected_below: float = 0.25
    supported_from: float = 0.70
    confirmed_from: float = 0.90

    def __post_init__(self) -> None:
        """Validate threshold ordering."""
        if not (
            0.0
            <= self.rejected_below
            <= self.supported_from
            <= self.confirmed_from
            <= 1.0
        ):
            raise ValueError(
                "Inference thresholds must be ordered between 0 and 1."
            )

    def status_for(self, confidence: float) -> HypothesisStatus:
        """Return the status associated with a confidence value."""
        if confidence < self.rejected_below:
            return HypothesisStatus.REJECTED

        if confidence >= self.confirmed_from:
            return HypothesisStatus.CONFIRMED

        if confidence >= self.supported_from:
            return HypothesisStatus.SUPPORTED

        return HypothesisStatus.PENDING


@dataclass(frozen=True, slots=True)
class InferenceResult:
    """Explain one immutable hypothesis revision."""

    previous_hypothesis: Hypothesis
    revised_hypothesis: Hypothesis
    applied_evidence_ids: tuple[UUID, ...]
    supporting_weight: float
    contradicting_weight: float
    net_weight: float

    @property
    def confidence_change(self) -> float:
        """Return the signed confidence change."""
        return (
            self.revised_hypothesis.confidence
            - self.previous_hypothesis.confidence
        )

    @property
    def changed_status(self) -> bool:
        """Return whether the hypothesis status changed."""
        return (
            self.previous_hypothesis.status
            is not self.revised_hypothesis.status
        )


class InferenceEngine:
    """Revise hypotheses from domain-independent evidence."""

    def __init__(
        self,
        thresholds: InferenceThresholds | None = None,
    ) -> None:
        self._thresholds = thresholds or InferenceThresholds()

    def revise(
        self,
        hypothesis: Hypothesis,
        evidence: Iterable[Evidence],
    ) -> InferenceResult:
        """Return a revised hypothesis and a traceable calculation."""
        relevant_evidence = self._prepare_evidence(
            hypothesis,
            evidence,
        )

        supporting_weight = sum(
            item.signed_weight
            for item in relevant_evidence
            if item.signed_weight > 0
        )
        contradicting_weight = sum(
            -item.signed_weight
            for item in relevant_evidence
            if item.signed_weight < 0
        )
        net_weight = supporting_weight - contradicting_weight

        revised_confidence = min(
            1.0,
            max(0.0, hypothesis.confidence + net_weight),
        )

        revised_status = self._thresholds.status_for(
            revised_confidence
        )

        observation_ids = tuple(
            dict.fromkeys(
                (
                    *hypothesis.supporting_observation_ids,
                    *(
                        item.observation_id
                        for item in relevant_evidence
                        if item.is_supporting
                    ),
                )
            )
        )

        revised_hypothesis = hypothesis.revise(
            confidence=revised_confidence,
            status=revised_status,
            supporting_observation_ids=observation_ids,
        )

        return InferenceResult(
            previous_hypothesis=hypothesis,
            revised_hypothesis=revised_hypothesis,
            applied_evidence_ids=tuple(
                item.evidence_id
                for item in relevant_evidence
            ),
            supporting_weight=supporting_weight,
            contradicting_weight=contradicting_weight,
            net_weight=net_weight,
        )

    @staticmethod
    def _prepare_evidence(
        hypothesis: Hypothesis,
        evidence: Iterable[Evidence],
    ) -> tuple[Evidence, ...]:
        """Validate, deduplicate, and materialize evidence."""
        unique_evidence: list[Evidence] = []
        seen_ids: set[UUID] = set()

        for item in evidence:
            if item.hypothesis_id != hypothesis.hypothesis_id:
                raise ValueError(
                    "Evidence targets a different hypothesis."
                )

            if item.evidence_id in seen_ids:
                continue

            seen_ids.add(item.evidence_id)
            unique_evidence.append(item)

        return tuple(unique_evidence)
