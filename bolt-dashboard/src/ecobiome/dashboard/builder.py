"""Build project-dashboard snapshots from durable workspaces."""

from collections import Counter
from pathlib import Path

from ecobiome.dashboard.models import (
    DashboardActivityItem,
    DashboardEventCount,
    ProjectDashboardSnapshot,
)
from ecobiome.journal import (
    JournalEvent,
    JournalEventType,
)
from ecobiome.workspace import ProjectWorkspace


def count_stored_media_files(
    directory: Path,
) -> int:
    """Count immutable media files stored inside one workspace."""
    if not directory.exists():
        return 0

    return sum(
        1
        for path in directory.rglob("*")
        if path.is_file()
    )


def build_project_dashboard(
    workspace: ProjectWorkspace,
    *,
    latest_limit: int = 10,
    quality_score: int | None = None,
) -> ProjectDashboardSnapshot:
    """Build an immutable dashboard snapshot for one project."""
    if latest_limit < 0:
        raise ValueError(
            "Dashboard latest-activity limit cannot be negative."
        )

    if (
        quality_score is not None
        and not 0 <= quality_score <= 100
    ):
        raise ValueError(
            "Dashboard quality score must be between "
            "zero and one hundred."
        )

    events = workspace.journal.timeline()

    counts = Counter(
        event.event_type
        for event in events
    )

    event_counts = tuple(
        DashboardEventCount(
            event_type=event_type,
            count=counts[event_type],
        )
        for event_type in JournalEventType
        if counts[event_type] > 0
    )

    latest_events = workspace.journal.latest(
        limit=latest_limit
    )

    latest_activity = tuple(
        _activity_item_from_event(event)
        for event in latest_events
    )

    manifest = workspace.manifest

    return ProjectDashboardSnapshot(
        project_id=manifest.project_id,
        project_name=manifest.name,
        project_type=manifest.project_type,
        description=manifest.description,
        updated_at=manifest.updated_at,
        tags=manifest.tags,
        journal_event_count=len(events),
        media_file_count=count_stored_media_files(
            workspace.layout.media_directory
        ),
        diagnostic_count=counts[
            JournalEventType.DIAGNOSTIC
        ],
        learning_count=counts[
            JournalEventType.LEARNING
        ],
        biological_event_count=counts[
            JournalEventType.BIOLOGICAL_EVENT
        ],
        event_counts=event_counts,
        latest_activity=latest_activity,
        quality_score=quality_score,
        hypothesis_count=counts[
            JournalEventType.HYPOTHESIS
        ],
        experiment_count=counts[
            JournalEventType.EXPERIMENT
        ],
        conclusion_count=(
            counts[JournalEventType.LEARNING]
            + counts[JournalEventType.BIOLOGICAL_EVENT]
        ),
    )


def _activity_item_from_event(
    event: JournalEvent,
) -> DashboardActivityItem:
    """Convert one journal event to a dashboard activity item."""
    return DashboardActivityItem(
        event_id=event.event_id,
        event_type=event.event_type,
        title=event.title,
        description=event.description,
        occurred_at=event.occurred_at,
        tags=event.tags,
    )
