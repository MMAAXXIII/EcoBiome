"""Immutable records of scientific learning and confidence revision."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class LearningOutcome(StrEnum):
    """Possible outcomes of one scientific experiment."""

    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True, slots=True, kw_only=True)
class LearningEvent:
    """Record one traceable revision of a hypothesis confidence."""

    hypothesis_id: UUID
    experiment_id: str
    outcome: LearningOutcome
    confidence_before: float
    confidence_after: float
    occurred_at: datetime
    evidence_ids: tuple[UUID, ...] = ()
    notes: str = ""
    event_id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        """Validate and normalize the learning event."""
        experiment_id = self.experiment_id.strip()
        notes = self.notes.strip()

        if not experiment_id:
            raise ValueError(
                "A learning event requires an experiment identifier."
            )

        if "." not in experiment_id:
            raise ValueError(
                "Experiment identifier must contain a domain prefix."
            )

        if self.occurred_at.tzinfo is None:
            raise ValueError(
                "Learning-event timestamp must be timezone-aware."
            )

        for name, value in (
            ("confidence_before", self.confidence_before),
            ("confidence_after", self.confidence_after),
        ):
            if isinstance(value, bool) or not isinstance(
                value,
                int | float,
            ):
                raise TypeError(f"{name} must be numeric.")

            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(
                    f"{name} must be between 0 and 1."
                )

        evidence_ids = tuple(dict.fromkeys(self.evidence_ids))

        object.__setattr__(self, "experiment_id", experiment_id)
        object.__setattr__(self, "notes", notes)
        object.__setattr__(
            self,
            "confidence_before",
            float(self.confidence_before),
        )
        object.__setattr__(
            self,
            "confidence_after",
            float(self.confidence_after),
        )
        object.__setattr__(self, "evidence_ids", evidence_ids)

    @property
    def confidence_delta(self) -> float:
        """Return the signed confidence change."""
        return self.confidence_after - self.confidence_before

    @property
    def changed_confidence(self) -> bool:
        """Return whether the event changed confidence."""
        return self.confidence_after != self.confidence_before
