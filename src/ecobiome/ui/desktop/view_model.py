"""Presentation models for the EcoBiome desktop dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ecobiome.dashboard import ProjectDashboardSnapshot
from ecobiome.journal import JournalEventType

_EVENT_DISPLAY_PRIORITY: dict[JournalEventType, int] = {
    JournalEventType.DIAGNOSTIC: 10,
    JournalEventType.LEARNING: 20,
    JournalEventType.HYPOTHESIS: 30,
    JournalEventType.EXPERIMENT: 40,
    JournalEventType.BIOLOGICAL_EVENT: 50,
    JournalEventType.OBSERVATION: 60,
    JournalEventType.MEASUREMENT: 70,
    JournalEventType.INTERVENTION: 80,
    JournalEventType.MEDIA: 90,
    JournalEventType.NOTE: 100,
    JournalEventType.SYSTEM: 110,
}


_EVENT_LABELS: dict[JournalEventType, str] = {
    JournalEventType.NOTE: "Notes",
    JournalEventType.MEDIA: "Médias",
    JournalEventType.OBSERVATION: "Observations",
    JournalEventType.DIAGNOSTIC: "Diagnostics",
    JournalEventType.HYPOTHESIS: "Hypothèses",
    JournalEventType.EXPERIMENT: "Expériences",
    JournalEventType.LEARNING: "Apprentissages",
    JournalEventType.BIOLOGICAL_EVENT: "Événements biologiques",
    JournalEventType.INTERVENTION: "Interventions",
    JournalEventType.MEASUREMENT: "Mesures",
    JournalEventType.SYSTEM: "Système",
}

_EVENT_SYMBOLS: dict[JournalEventType, str] = {
    JournalEventType.NOTE: "✎",
    JournalEventType.MEDIA: "▣",
    JournalEventType.OBSERVATION: "◉",
    JournalEventType.DIAGNOSTIC: "⌁",
    JournalEventType.HYPOTHESIS: "◇",
    JournalEventType.EXPERIMENT: "⚗",
    JournalEventType.LEARNING: "↗",
    JournalEventType.BIOLOGICAL_EVENT: "✦",
    JournalEventType.INTERVENTION: "◆",
    JournalEventType.MEASUREMENT: "∿",
    JournalEventType.SYSTEM: "⚙",
}


@dataclass(frozen=True, slots=True, kw_only=True)
class DashboardMetricViewModel:
    """Describe one summary card displayed by the interface."""

    label: str
    value: str
    symbol: str

    def __post_init__(self) -> None:
        """Validate one metric presentation model."""
        if not self.label.strip():
            raise ValueError(
                "Dashboard metric label cannot be empty."
            )

        if not self.value.strip():
            raise ValueError(
                "Dashboard metric value cannot be empty."
            )

        if not self.symbol.strip():
            raise ValueError(
                "Dashboard metric symbol cannot be empty."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class DashboardActivityViewModel:
    """Describe one chronological activity row."""

    symbol: str
    category: str
    title: str
    description: str
    occurred_at: str
    tags: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DesktopDashboardViewModel:
    """Contain all text displayed by the desktop dashboard."""

    project_name: str
    project_type: str
    description: str
    updated_at: str
    tags: str
    status_title: str
    status_message: str
    metrics: tuple[DashboardMetricViewModel, ...]
    event_distribution: tuple[tuple[str, int], ...]
    latest_activity: tuple[DashboardActivityViewModel, ...]

    @classmethod
    def from_snapshot(
        cls,
        snapshot: ProjectDashboardSnapshot,
    ) -> DesktopDashboardViewModel:
        """Build a desktop presentation model from domain data."""
        metrics = (
            DashboardMetricViewModel(
                label="Événements",
                value=str(snapshot.journal_event_count),
                symbol="◫",
            ),
            DashboardMetricViewModel(
                label="Médias",
                value=str(snapshot.media_file_count),
                symbol="▣",
            ),
            DashboardMetricViewModel(
                label="Diagnostics",
                value=str(snapshot.diagnostic_count),
                symbol="⌁",
            ),
            DashboardMetricViewModel(
                label="Apprentissages",
                value=str(snapshot.learning_count),
                symbol="↗",
            ),
            DashboardMetricViewModel(
                label="Événements biologiques",
                value=str(snapshot.biological_event_count),
                symbol="✦",
            ),
        )

        event_distribution = tuple(
            (
                _EVENT_LABELS[counter.event_type],
                counter.count,
            )
            for counter in sorted(
                snapshot.event_counts,
                key=lambda counter: (
                    _EVENT_DISPLAY_PRIORITY[
                        counter.event_type
                    ],
                    counter.event_type.value,
                ),
            )
        )

        latest_activity = tuple(
            DashboardActivityViewModel(
                symbol=_EVENT_SYMBOLS[item.event_type],
                category=_EVENT_LABELS[item.event_type],
                title=item.title,
                description=item.description,
                occurred_at=_format_datetime(
                    item.occurred_at
                ),
                tags=" · ".join(item.tags),
            )
            for item in snapshot.latest_activity
        )

        if snapshot.has_activity:
            status_title = "Projet actif"
            status_message = (
                f"{snapshot.journal_event_count} événement(s) "
                "documenté(s) dans le journal scientifique."
            )
        else:
            status_title = "Projet prêt"
            status_message = (
                "Ajoutez une observation, une photo ou une note "
                "pour commencer votre journal."
            )

        return cls(
            project_name=snapshot.project_name,
            project_type=snapshot.project_type.value.replace(
                "_",
                " ",
            ).title(),
            description=snapshot.description,
            updated_at=_format_datetime(
                snapshot.updated_at
            ),
            tags=" · ".join(snapshot.tags),
            status_title=status_title,
            status_message=status_message,
            metrics=metrics,
            event_distribution=event_distribution,
            latest_activity=latest_activity,
        )


def _format_datetime(value: datetime) -> str:
    """Format one timestamp for the French desktop interface."""
    return value.strftime(
        "%d/%m/%Y · %H:%M"
    )
