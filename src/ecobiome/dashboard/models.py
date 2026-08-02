"""Interface-ready models for EcoBiome project dashboards."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ecobiome.journal import JournalEventType
from ecobiome.workspace import ProjectType


@dataclass(frozen=True, slots=True, kw_only=True)
class DashboardEventCount:
    """Count journal events belonging to one category."""

    event_type: JournalEventType
    count: int

    def __post_init__(self) -> None:
        """Validate one event-category counter."""
        if self.count < 0:
            raise ValueError(
                "Dashboard event count cannot be negative."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class DashboardActivityItem:
    """Describe one recent item displayed by a dashboard."""

    event_id: UUID
    event_type: JournalEventType
    title: str
    description: str
    occurred_at: datetime
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate and normalize one activity item."""
        title = self.title.strip()
        description = self.description.strip()

        if not title:
            raise ValueError(
                "Dashboard activity title cannot be empty."
            )

        if self.occurred_at.tzinfo is None:
            raise ValueError(
                "Dashboard activity timestamps must be "
                "timezone-aware."
            )

        tags = tuple(
            dict.fromkeys(
                tag.strip().lower()
                for tag in self.tags
                if tag.strip()
            )
        )

        object.__setattr__(self, "title", title)
        object.__setattr__(
            self,
            "description",
            description,
        )
        object.__setattr__(self, "tags", tags)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectDashboardSnapshot:
    """Contain an immutable, interface-ready project overview."""

    project_id: UUID
    project_name: str
    project_type: ProjectType
    description: str
    updated_at: datetime
    tags: tuple[str, ...]
    journal_event_count: int
    media_file_count: int
    diagnostic_count: int
    learning_count: int
    biological_event_count: int
    event_counts: tuple[DashboardEventCount, ...]
    latest_activity: tuple[DashboardActivityItem, ...]

    def __post_init__(self) -> None:
        """Validate and normalize one dashboard snapshot."""
        project_name = self.project_name.strip()
        description = self.description.strip()

        if not project_name:
            raise ValueError(
                "Dashboard project name cannot be empty."
            )

        if self.updated_at.tzinfo is None:
            raise ValueError(
                "Dashboard project timestamp must be "
                "timezone-aware."
            )

        counters = (
            self.journal_event_count,
            self.media_file_count,
            self.diagnostic_count,
            self.learning_count,
            self.biological_event_count,
        )

        if any(counter < 0 for counter in counters):
            raise ValueError(
                "Dashboard counters cannot be negative."
            )

        if sum(
            counter.count
            for counter in self.event_counts
        ) != self.journal_event_count:
            raise ValueError(
                "Dashboard event-category counts must equal "
                "the total journal-event count."
            )

        if len(self.latest_activity) > self.journal_event_count:
            raise ValueError(
                "Dashboard recent activity cannot exceed "
                "the total journal-event count."
            )

        tags = tuple(
            dict.fromkeys(
                tag.strip().lower()
                for tag in self.tags
                if tag.strip()
            )
        )

        object.__setattr__(
            self,
            "project_name",
            project_name,
        )
        object.__setattr__(
            self,
            "description",
            description,
        )
        object.__setattr__(self, "tags", tags)

    @property
    def has_activity(self) -> bool:
        """Return whether the project contains journal activity."""
        return self.journal_event_count > 0

    @property
    def has_media(self) -> bool:
        """Return whether the workspace contains media files."""
        return self.media_file_count > 0

    def event_count_for(
        self,
        event_type: JournalEventType,
    ) -> int:
        """Return the count associated with one event category."""
        for event_count in self.event_counts:
            if event_count.event_type is event_type:
                return event_count.count

        return 0
