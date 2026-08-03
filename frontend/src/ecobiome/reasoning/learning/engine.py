"""Explainable confidence revision from scientific experiments."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ecobiome.reasoning.learning.event import (
    LearningEvent,
    LearningOutcome,
)
from ecobiome.reasoning.learning.store import LearningEventStore


@dataclass(frozen=True, slots=True)
class LearningSummary:
    """Summarize learning history for one hypothesis."""

    hypothesis_id: UUID
    event_count: int
    confirmed_count: int
    refuted_count: int
    inconclusive_count: int
    current_confidence: float | None
    event_ids: tuple[UUID, ...]

    @property
    def has_history(self) -> bool:
        """Return whether the hypothesis has learning history."""
        return self.event_count > 0


class LearningEngine:
    """Create, persist, and summarize confidence revisions."""

    def __init__(
        self,
        store: LearningEventStore,
    ) -> None:
        self._store = store

    def record(
        self,
        *,
        hypothesis_id: UUID,
        experiment_id: str,
        outcome: LearningOutcome,
        confidence_before: float,
        strength: float,
        occurred_at: datetime,
        evidence_ids: tuple[UUID, ...] = (),
        notes: str = "",
    ) -> LearningEvent:
        """Calculate and persist one explainable learning event."""
        confidence_before = self._validate_probability(
            confidence_before,
            name="confidence_before",
        )
        strength = self._validate_probability(
            strength,
            name="strength",
        )

        confidence_after = self._revise_confidence(
            confidence_before=confidence_before,
            outcome=outcome,
            strength=strength,
        )

        event = LearningEvent(
            hypothesis_id=hypothesis_id,
            experiment_id=experiment_id,
            outcome=outcome,
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            occurred_at=occurred_at,
            evidence_ids=evidence_ids,
            notes=notes,
        )

        self._store.append(event)
        return event

    @staticmethod
    def _revise_confidence(
        *,
        confidence_before: float,
        outcome: LearningOutcome,
        strength: float,
    ) -> float:
        """Apply a bounded, deterministic confidence revision."""
        if outcome is LearningOutcome.CONFIRMED:
            revised = confidence_before + (
                1.0 - confidence_before
            ) * strength
        elif outcome is LearningOutcome.REFUTED:
            revised = confidence_before * (1.0 - strength)
        else:
            revised = confidence_before

        return min(1.0, max(0.0, revised))

    @staticmethod
    def _validate_probability(
        value: float,
        *,
        name: str,
    ) -> float:
        """Validate one probability-like numerical value."""
        if isinstance(value, bool) or not isinstance(
            value,
            int | float,
        ):
            raise TypeError(f"{name} must be numeric.")

        normalized = float(value)

        if not 0.0 <= normalized <= 1.0:
            raise ValueError(
                f"{name} must be between 0 and 1."
            )

        return normalized

    def summarize(
        self,
        hypothesis_id: UUID,
    ) -> LearningSummary:
        """Summarize the complete history of one hypothesis."""
        events = self._store.load_for_hypothesis(
            hypothesis_id
        )

        current_confidence = (
            events[-1].confidence_after
            if events
            else None
        )

        return LearningSummary(
            hypothesis_id=hypothesis_id,
            event_count=len(events),
            confirmed_count=sum(
                event.outcome is LearningOutcome.CONFIRMED
                for event in events
            ),
            refuted_count=sum(
                event.outcome is LearningOutcome.REFUTED
                for event in events
            ),
            inconclusive_count=sum(
                event.outcome is LearningOutcome.INCONCLUSIVE
                for event in events
            ),
            current_confidence=current_confidence,
            event_ids=tuple(
                event.event_id
                for event in events
            ),
        )
