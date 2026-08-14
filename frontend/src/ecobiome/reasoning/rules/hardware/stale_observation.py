"""Hardware rules detecting stale scientific observations."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from ecobiome.core.observation import (
    DataQuality,
    DiagnosticCode,
    Observation,
    QualityAssessment,
)
from ecobiome.reasoning.evidence import (
    Evidence,
    EvidenceRelation,
)
from ecobiome.reasoning.rules.rule import ScientificRule


@dataclass(frozen=True, slots=True, kw_only=True)
class StaleObservationRule(ScientificRule):
    """Detect observations that are too old to remain trustworthy."""

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

    def _age_seconds(
        self,
        observation: Observation,
    ) -> float:
        """Return the age of an observation."""
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

        return age_seconds

    def assess(
        self,
        observation: Observation,
    ) -> QualityAssessment:
        """Classify the observation as valid or stale."""
        age_seconds = self._age_seconds(observation)

        if age_seconds <= self.maximum_age_seconds:
            return QualityAssessment.valid(
                observation.observation_id
            )

        return QualityAssessment(
            observation_id=observation.observation_id,
            quality=DataQuality.STALE,
            score=0.0,
            diagnostics=(DiagnosticCode.STALE_OBSERVATION,),
            reasons=(
                (
                    f"Observation is {age_seconds:.1f} seconds old, "
                    f"exceeding the {self.maximum_age_seconds:.1f}-second "
                    "limit."
                ),
            ),
        )

    def evaluate(
        self,
        observation: Observation,
    ) -> tuple[Evidence, ...]:
        """Generate contradictory evidence for stale data."""
        assessment = self.assess(observation)

        if assessment.quality is DataQuality.VALID:
            return ()

        return (
            Evidence(
                observation_id=observation.observation_id,
                hypothesis_id=self.hypothesis_id,
                relation=EvidenceRelation.CONTRADICTS,
                weight=self.evidence_weight,
                quality_score=observation.confidence,
                explanation=assessment.reasons[0],
                source_rule=self.identifier,
            ),
        )
