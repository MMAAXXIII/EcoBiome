"""Traceable evidence linking observations to hypotheses."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class EvidenceRelation(StrEnum):
    """Relationship between evidence and a hypothesis."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    NEUTRAL = "neutral"


@dataclass(frozen=True, slots=True, kw_only=True)
class Evidence:
    """Represent one traceable argument about a hypothesis."""

    observation_id: UUID
    hypothesis_id: UUID
    relation: EvidenceRelation
    weight: float
    explanation: str
    source_rule: str
    quality_score: float = 1.0
    evidence_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        """Validate and normalize the evidence."""
        explanation = self.explanation.strip()
        source_rule = self.source_rule.strip()

        if not explanation:
            raise ValueError("Evidence requires an explanation.")

        if not source_rule:
            raise ValueError("Evidence requires a source rule.")

        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(
                "Evidence weight must be between 0 and 1."
            )

        if not 0.0 <= self.quality_score <= 1.0:
            raise ValueError(
                "Evidence quality_score must be between 0 and 1."
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "Evidence created_at must include a timezone."
            )

        object.__setattr__(self, "explanation", explanation)
        object.__setattr__(self, "source_rule", source_rule)

    @property
    def signed_weight(self) -> float:
        """Return the evidence weight with its logical direction."""
        effective_weight = self.weight * self.quality_score

        if self.relation is EvidenceRelation.SUPPORTS:
            return effective_weight

        if self.relation is EvidenceRelation.CONTRADICTS:
            return -effective_weight

        return 0.0

    @property
    def is_supporting(self) -> bool:
        """Return whether the evidence supports its hypothesis."""
        return self.relation is EvidenceRelation.SUPPORTS

    @property
    def is_contradicting(self) -> bool:
        """Return whether the evidence contradicts its hypothesis."""
        return self.relation is EvidenceRelation.CONTRADICTS
