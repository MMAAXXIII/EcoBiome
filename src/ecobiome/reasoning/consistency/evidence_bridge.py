"""Convert consistency assessments into traceable scientific evidence."""

from dataclasses import dataclass
from uuid import UUID

from ecobiome.reasoning.consistency.consistency import (
    ConsistencyAssessment,
    ConsistencyStatus,
)
from ecobiome.reasoning.evidence import (
    Evidence,
    EvidenceRelation,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConsistencyEvidenceBridge:
    """Convert one consistency result into hypothesis evidence."""

    identifier: str
    hypothesis_id: UUID
    target_observation_id: UUID
    supporting_weight: float = 0.35
    contradicting_weight: float = 0.80

    def __post_init__(self) -> None:
        """Validate and normalize bridge configuration."""
        identifier = self.identifier.strip()

        if not identifier:
            raise ValueError(
                "A consistency evidence bridge requires an identifier."
            )

        if "." not in identifier:
            raise ValueError(
                "Bridge identifier must contain a domain prefix."
            )

        if not 0.0 <= self.supporting_weight <= 1.0:
            raise ValueError(
                "supporting_weight must be between 0 and 1."
            )

        if not 0.0 <= self.contradicting_weight <= 1.0:
            raise ValueError(
                "contradicting_weight must be between 0 and 1."
            )

        object.__setattr__(self, "identifier", identifier)

    def build(
        self,
        assessment: ConsistencyAssessment,
    ) -> tuple[Evidence, ...]:
        """Create evidence when the assessment supports a conclusion."""
        if (
            self.target_observation_id
            not in assessment.involved_observations
        ):
            raise ValueError(
                "The target observation is not involved "
                "in the consistency assessment."
            )

        if assessment.status in {
            ConsistencyStatus.UNKNOWN,
            ConsistencyStatus.INSUFFICIENT_DATA,
        }:
            return ()

        if assessment.status is ConsistencyStatus.CONSISTENT:
            relation = EvidenceRelation.SUPPORTS
            weight = self.supporting_weight
        else:
            relation = EvidenceRelation.CONTRADICTS
            weight = self.contradicting_weight

        explanation = assessment.reason.strip()

        if not explanation:
            explanation = (
                "The multi-observation consistency assessment "
                f"returned {assessment.status.value!r}."
            )

        return (
            Evidence(
                observation_id=self.target_observation_id,
                hypothesis_id=self.hypothesis_id,
                relation=relation,
                weight=weight,
                quality_score=assessment.confidence,
                explanation=explanation,
                source_rule=self.identifier,
            ),
        )
