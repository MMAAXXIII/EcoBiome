"""Logical timelines for completed diagnostic investigations."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class DiagnosticTimelineStage(StrEnum):
    """Stable stages exposed by the diagnostic-result API."""

    SESSION_STARTED = "session_started"
    OBSERVATIONS_EVALUATED = "observations_evaluated"
    CONSISTENCY_EVALUATED = "consistency_evaluated"
    HYPOTHESES_GENERATED = "hypotheses_generated"
    EXPERIMENTS_PLANNED = "experiments_planned"
    SESSION_FINISHED = "session_finished"


@dataclass(frozen=True, slots=True, kw_only=True)
class DiagnosticTimelineEntry:
    """Describe one ordered stage of a diagnostic session."""

    sequence: int
    stage: DiagnosticTimelineStage
    title: str
    description: str
    occurred_at: datetime | None = None
    item_count: int | None = None

    def __post_init__(self) -> None:
        """Validate and normalize a timeline entry."""
        title = self.title.strip()
        description = self.description.strip()

        if self.sequence < 0:
            raise ValueError(
                "Timeline sequence cannot be negative."
            )

        if not title:
            raise ValueError(
                "Timeline entry title cannot be empty."
            )

        if not description:
            raise ValueError(
                "Timeline entry description cannot be empty."
            )

        if (
            self.occurred_at is not None
            and self.occurred_at.tzinfo is None
        ):
            raise ValueError(
                "Timeline timestamps must be timezone-aware."
            )

        if (
            self.item_count is not None
            and self.item_count < 0
        ):
            raise ValueError(
                "Timeline item count cannot be negative."
            )

        object.__setattr__(self, "title", title)
        object.__setattr__(
            self,
            "description",
            description,
        )


def build_diagnostic_timeline(
    *,
    started_at: datetime,
    finished_at: datetime,
    observation_count: int,
    usable_observation_count: int,
    rejected_observation_count: int,
    has_inconsistency: bool,
    proposal_count: int,
    experiment_count: int,
) -> tuple[DiagnosticTimelineEntry, ...]:
    """Build a stable logical timeline from result counters."""
    consistency_description = (
        "A contradiction requiring investigation was detected."
        if has_inconsistency
        else "No contradiction requiring investigation was detected."
    )

    return (
        DiagnosticTimelineEntry(
            sequence=0,
            stage=DiagnosticTimelineStage.SESSION_STARTED,
            title="Session started",
            description="Diagnostic execution started.",
            occurred_at=started_at,
        ),
        DiagnosticTimelineEntry(
            sequence=1,
            stage=(
                DiagnosticTimelineStage.OBSERVATIONS_EVALUATED
            ),
            title="Observations evaluated",
            description=(
                f"{usable_observation_count} usable observation(s), "
                f"{rejected_observation_count} rejected."
            ),
            item_count=observation_count,
        ),
        DiagnosticTimelineEntry(
            sequence=2,
            stage=(
                DiagnosticTimelineStage.CONSISTENCY_EVALUATED
            ),
            title="Consistency evaluated",
            description=consistency_description,
            item_count=int(has_inconsistency),
        ),
        DiagnosticTimelineEntry(
            sequence=3,
            stage=(
                DiagnosticTimelineStage.HYPOTHESES_GENERATED
            ),
            title="Hypotheses generated",
            description=(
                f"{proposal_count} hypothesis proposal(s) generated."
            ),
            item_count=proposal_count,
        ),
        DiagnosticTimelineEntry(
            sequence=4,
            stage=(
                DiagnosticTimelineStage.EXPERIMENTS_PLANNED
            ),
            title="Experiments planned",
            description=(
                f"{experiment_count} experiment(s) planned."
            ),
            item_count=experiment_count,
        ),
        DiagnosticTimelineEntry(
            sequence=5,
            stage=DiagnosticTimelineStage.SESSION_FINISHED,
            title="Session finished",
            description="Diagnostic execution completed.",
            occurred_at=finished_at,
        ),
    )
