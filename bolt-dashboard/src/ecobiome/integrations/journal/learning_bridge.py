"""Record scientific-learning outcomes in project journals."""

from uuid import UUID

from ecobiome.integrations.journal.common import (
    find_linked_event,
)
from ecobiome.journal import (
    JournalEvent,
    JournalEventType,
    JournalReference,
    ScientificJournal,
)
from ecobiome.reasoning.learning import LearningEvent


class LearningJournalBridge:
    """Transform learning events into journal entries."""

    def __init__(
        self,
        journal: ScientificJournal,
    ) -> None:
        self._journal = journal

    def record_learning(
        self,
        learning_event: LearningEvent,
        *,
        project_id: UUID | None = None,
    ) -> JournalEvent:
        """Record one scientific-learning event exactly once."""
        existing = find_linked_event(
            self._journal,
            entity_type="learning_event",
            entity_id=learning_event.event_id,
            event_type=JournalEventType.LEARNING,
        )

        if existing is not None:
            return existing

        outcome = learning_event.outcome.value

        return self._journal.record(
            event_type=JournalEventType.LEARNING,
            title=f"Apprentissage scientifique : {outcome}",
            description=learning_event.notes,
            occurred_at=learning_event.occurred_at,
            project_id=project_id,
            tags=(
                "learning",
                outcome,
            ),
            attributes=(
                (
                    "outcome",
                    outcome,
                ),
                (
                    "experiment_id",
                    learning_event.experiment_id,
                ),
            ),
            payload=(
                (
                    "learning_event_id",
                    str(learning_event.event_id),
                ),
                (
                    "hypothesis_id",
                    str(learning_event.hypothesis_id),
                ),
                (
                    "confidence_before",
                    learning_event.confidence_before,
                ),
                (
                    "confidence_after",
                    learning_event.confidence_after,
                ),
                (
                    "evidence_ids",
                    tuple(
                        str(evidence_id)
                        for evidence_id
                        in learning_event.evidence_ids
                    ),
                ),
            ),
            references=(
                JournalReference(
                    entity_type="learning_event",
                    entity_id=learning_event.event_id,
                    relation="source",
                ),
                JournalReference(
                    entity_type="hypothesis",
                    entity_id=learning_event.hypothesis_id,
                    relation="updates",
                ),
            ),
        )
