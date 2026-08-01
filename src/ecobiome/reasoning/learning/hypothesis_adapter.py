"""Apply accumulated scientific learning to hypothesis proposals."""

from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from ecobiome.reasoning.abduction.proposal import (
    HypothesisProposal,
)
from ecobiome.reasoning.learning.engine import (
    LearningEngine,
)
from ecobiome.reasoning.learning.event import (
    LearningEvent,
    LearningOutcome,
)
from ecobiome.reasoning.learning.identity import (
    hypothesis_uuid,
)
from ecobiome.reasoning.learning.store import (
    LearningEventStore,
)


class HypothesisLearningAdapter:
    """Connect abductive proposals with persistent learning history."""

    def __init__(
        self,
        store: LearningEventStore,
    ) -> None:
        self._engine = LearningEngine(store)

    def record_outcome(
        self,
        *,
        proposal: HypothesisProposal,
        experiment_id: str,
        outcome: LearningOutcome,
        strength: float,
        occurred_at: datetime,
        evidence_ids: tuple[UUID, ...] = (),
        notes: str = "",
    ) -> LearningEvent:
        """Record an experimental outcome for one proposal."""
        hypothesis_id = hypothesis_uuid(
            proposal.identifier
        )

        summary = self._engine.summarize(
            hypothesis_id
        )

        confidence_before = (
            summary.current_confidence
            if summary.current_confidence is not None
            else proposal.confidence
        )

        return self._engine.record(
            hypothesis_id=hypothesis_id,
            experiment_id=experiment_id,
            outcome=outcome,
            confidence_before=confidence_before,
            strength=strength,
            occurred_at=occurred_at,
            evidence_ids=evidence_ids,
            notes=notes,
        )

    def adjust(
        self,
        proposals: Iterable[HypothesisProposal],
    ) -> tuple[HypothesisProposal, ...]:
        """Apply learned confidence and return ranked proposals."""
        adjusted = tuple(
            self._adjust_one(proposal)
            for proposal in proposals
        )

        return tuple(
            sorted(
                adjusted,
                key=lambda proposal: (
                    -proposal.confidence,
                    proposal.identifier,
                ),
            )
        )

    def _adjust_one(
        self,
        proposal: HypothesisProposal,
    ) -> HypothesisProposal:
        """Apply learning history to one proposal."""
        summary = self._engine.summarize(
            hypothesis_uuid(proposal.identifier)
        )

        if summary.current_confidence is None:
            return proposal

        return HypothesisProposal(
            identifier=proposal.identifier,
            title=proposal.title,
            statement=proposal.statement,
            confidence=summary.current_confidence,
            source_rule=proposal.source_rule,
            supporting_observation_ids=(
                proposal.supporting_observation_ids
            ),
            rationale=proposal.rationale,
        )
