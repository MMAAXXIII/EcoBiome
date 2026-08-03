"""Record completed diagnostic results in scientific journals."""

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
from ecobiome.reasoning.results import (
    DiagnosticResult,
    DiagnosticStatus,
)


class DiagnosticJournalBridge:
    """Transform public diagnostic results into journal entries."""

    def __init__(
        self,
        journal: ScientificJournal,
    ) -> None:
        self._journal = journal

    def record_result(
        self,
        result: DiagnosticResult,
        *,
        project_id: UUID | None = None,
    ) -> JournalEvent:
        """Record one completed diagnostic session exactly once."""
        existing = find_linked_event(
            self._journal,
            entity_type="diagnostic_session",
            entity_id=result.session_id,
            event_type=JournalEventType.DIAGNOSTIC,
        )

        if existing is not None:
            return existing

        description = self._description_for(result.status)

        return self._journal.record(
            event_type=JournalEventType.DIAGNOSTIC,
            title="Diagnostic terminé",
            description=description,
            occurred_at=result.finished_at,
            project_id=project_id,
            tags=(
                "diagnostic",
                result.status.value,
            ),
            attributes=(
                (
                    "profile_id",
                    result.profile_id,
                ),
                (
                    "status",
                    result.status.value,
                ),
                (
                    "ecobiome_version",
                    result.ecobiome_version,
                ),
            ),
            payload=(
                (
                    "session_id",
                    str(result.session_id),
                ),
                (
                    "duration_seconds",
                    result.duration_seconds,
                ),
                (
                    "observation_count",
                    result.observation_count,
                ),
                (
                    "usable_observation_count",
                    result.usable_observation_count,
                ),
                (
                    "rejected_observation_count",
                    result.rejected_observation_count,
                ),
                (
                    "proposal_count",
                    result.proposal_count,
                ),
                (
                    "experiment_count",
                    result.experiment_count,
                ),
                (
                    "has_inconsistency",
                    result.has_inconsistency,
                ),
                (
                    "best_experiment_id",
                    (
                        result.best_experiment.identifier
                        if result.best_experiment is not None
                        else None
                    ),
                ),
            ),
            references=(
                JournalReference(
                    entity_type="diagnostic_session",
                    entity_id=result.session_id,
                    relation="result",
                ),
            ),
        )

    @staticmethod
    def _description_for(
        status: DiagnosticStatus,
    ) -> str:
        """Return a concise public description for one status."""
        if status is DiagnosticStatus.HEALTHY:
            return (
                "Le diagnostic est terminé sans contradiction "
                "nécessitant une investigation."
            )

        if status is DiagnosticStatus.INVESTIGATION_REQUIRED:
            return (
                "Le diagnostic a détecté une contradiction "
                "nécessitant une investigation."
            )

        return (
            "Le diagnostic ne s'est pas terminé correctement."
        )
