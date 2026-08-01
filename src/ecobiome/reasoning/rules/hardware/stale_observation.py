"""Hardware rules detecting stale scientific observations."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from ecobiome.core.observation import Observation
from ecobiome.reasoning.evidence import (
    Evidence,
    EvidenceRelation,
)
from ecobiome.reasoning.rules.rule import ScientificRule


@dataclass(frozen=True, slots=True, kw_only=True)
class StaleObservationRule(ScientificRule):
    """Generate contradictory evidence for stale observations."""

    hypothesis_id: UUID
    maximum_age_seconds: float
    evidence_weight: float = 0.70
    clock: Callable[[], datetime] = field(
        default=lambda: datetime.now(UTC),
        compare=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        """Validate rule metadata and configuration."""
        super().__post_init__()

        if self.maximum_age_seconds <= 0:
            raise ValueError(
                "maximum_age_seconds must be greater than zero."
            )

        if not 0.0 <= self.evidence_weight <= 1.0:
            raise ValueError(
                "evidence_weight must be between 0 and 1."
            )

    def evaluate(
        self,
        observation: Observation,
    ) -> tuple[Evidence, ...]:
        """Return negative evidence when an observation is too old."""
        evaluated_at = self.clock()

        if evaluated_at.tzinfo is None:
            raise ValueError(
                "StaleObservationRule clock must return "
                "a timezone-aware datetime."
            )

        age_seconds = (
            evaluated_at - observation.observed_at
        ).total_seconds()

        if age_seconds < 0:
            raise ValueError(
                "Observation timestamp cannot be in the future."
            )

        if age_seconds <= self.maximum_age_seconds:
            return ()

        return (
            Evidence(
                observation_id=observation.observation_id,
                hypothesis_id=self.hypothesis_id,
                relation=EvidenceRelation.CONTRADICTS,
                weight=self.evidence_weight,
                quality_score=observation.confidence,
                explanation=(
                    f"Observation {observation.observation_id} is "
                    f"{age_seconds:.1f} seconds old, exceeding the "
                    f"{self.maximum_age_seconds:.1f}-second limit."
                ),
                source_rule=self.identifier,
            ),
        )
