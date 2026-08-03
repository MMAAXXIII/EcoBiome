"""Presentation models for the EcoBiome desktop dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ecobiome.dashboard import ProjectDashboardSnapshot
from ecobiome.journal import JournalEventType
from ecobiome.ui.desktop.icons import DesktopIcon

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
    JournalEventType.NOTE: DesktopIcon.NOTE.value,
    JournalEventType.MEDIA: DesktopIcon.MEDIA.value,
    JournalEventType.OBSERVATION: DesktopIcon.OBSERVATION.value,
    JournalEventType.DIAGNOSTIC: DesktopIcon.DIAGNOSTIC.value,
    JournalEventType.HYPOTHESIS: DesktopIcon.HYPOTHESIS.value,
    JournalEventType.EXPERIMENT: DesktopIcon.EXPERIMENTS.value,
    JournalEventType.LEARNING: DesktopIcon.LEARNING.value,
    JournalEventType.BIOLOGICAL_EVENT: (
        DesktopIcon.BIOLOGICAL.value
    ),
    JournalEventType.INTERVENTION: "◆",
    JournalEventType.MEASUREMENT: DesktopIcon.MEASUREMENT.value,
    JournalEventType.SYSTEM: DesktopIcon.SETTINGS.value,
}

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


@dataclass(frozen=True, slots=True, kw_only=True)
class DashboardMetricViewModel:
    """Describe one summary card displayed by the interface."""

    label: str
    value: str
    symbol: str
    detail: str = ""
    accent_role: str = "accent"

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
    importance: str = "normal"


@dataclass(frozen=True, slots=True, kw_only=True)
class DashboardMemoryViewModel:
    """Describe one remembered milestone."""

    title: str
    subtitle: str
    date_label: str
    symbol: str = DesktopIcon.MEMORY.value


@dataclass(frozen=True, slots=True, kw_only=True)
class UserProgressViewModel:
    """Describe the user's progression in EcoBiome."""

    level: int
    title: str
    current_xp: int
    next_level_xp: int

    def __post_init__(self) -> None:
        """Validate progression values."""
        if self.level <= 0:
            raise ValueError(
                "User level must be positive."
            )

        if self.current_xp < 0:
            raise ValueError(
                "Current XP cannot be negative."
            )

        if self.next_level_xp <= 0:
            raise ValueError(
                "Next-level XP must be positive."
            )

        if self.current_xp > self.next_level_xp:
            raise ValueError(
                "Current XP cannot exceed next-level XP."
            )

    @property
    def progress_ratio(self) -> float:
        """Return progress toward the next level."""
        return self.current_xp / self.next_level_xp

    @property
    def progress_percent(self) -> int:
        """Return rounded progress percentage."""
        return round(self.progress_ratio * 100)


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
    memories: tuple[DashboardMemoryViewModel, ...]
    progress: UserProgressViewModel

    @classmethod
    def from_snapshot(
        cls,
        snapshot: ProjectDashboardSnapshot,
    ) -> DesktopDashboardViewModel:
        """Build a desktop presentation model from domain data."""
        quality_value = (
            f"{snapshot.quality_score}%"
            if snapshot.quality_score is not None
            else "—"
        )

        metrics = (
            DashboardMetricViewModel(
                label="Observations",
                value=str(snapshot.journal_event_count),
                symbol=DesktopIcon.OBSERVATION.value,
                detail=(
                    f"{snapshot.biological_event_count} "
                    "événement(s) biologique(s)"
                ),
                accent_role="success",
            ),
            DashboardMetricViewModel(
                label="Qualité globale",
                value=quality_value,
                symbol=DesktopIcon.QUALITY.value,
                detail=(
                    "Bonne qualité"
                    if (
                        snapshot.quality_score is not None
                        and snapshot.quality_score >= 75
                    )
                    else "Mesure à compléter"
                ),
                accent_role="quality",
            ),
            DashboardMetricViewModel(
                label="Hypothèses",
                value=str(snapshot.hypothesis_count),
                symbol=DesktopIcon.HYPOTHESIS.value,
                detail="Pistes explicatives",
                accent_role="hypothesis",
            ),
            DashboardMetricViewModel(
                label="Expériences",
                value=str(snapshot.experiment_count),
                symbol=DesktopIcon.EXPERIMENTS.value,
                detail="Protocoles évalués",
                accent_role="warning",
            ),
            DashboardMetricViewModel(
                label="Conclusions",
                value=str(snapshot.conclusion_count),
                symbol=DesktopIcon.CONCLUSION.value,
                detail="Résultats documentés",
                accent_role="conclusion",
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
                importance=(
                    "high"
                    if item.event_type
                    in {
                        JournalEventType.DIAGNOSTIC,
                        JournalEventType.BIOLOGICAL_EVENT,
                        JournalEventType.LEARNING,
                    }
                    else "normal"
                ),
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

        progress_points = min(
            4000,
            (
                snapshot.journal_event_count * 120
                + snapshot.media_file_count * 40
                + snapshot.diagnostic_count * 180
                + snapshot.learning_count * 240
            ),
        )

        progress = UserProgressViewModel(
            level=max(
                1,
                1 + progress_points // 350,
            ),
            title=_progress_title(progress_points),
            current_xp=progress_points,
            next_level_xp=4000,
        )

        memories = _build_memories(snapshot)

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
            memories=memories,
            progress=progress,
        )


def _format_datetime(value: datetime) -> str:
    """Format one timestamp without implicit timezone conversion."""
    return value.strftime(
        "%d/%m/%Y · %H:%M"
    )


def _progress_title(points: int) -> str:
    """Return a motivating progression title."""
    if points < 500:
        return "Explorateur du vivant"

    if points < 1500:
        return "Observateur confirmé"

    if points < 2800:
        return "Chercheur confirmé"

    return "Naturaliste avancé"


def _build_memories(
    snapshot: ProjectDashboardSnapshot,
) -> tuple[DashboardMemoryViewModel, ...]:
    """Build lightweight milestone memories from recent activity."""
    memories: list[DashboardMemoryViewModel] = []

    for item in reversed(snapshot.latest_activity):
        if item.event_type not in {
            JournalEventType.BIOLOGICAL_EVENT,
            JournalEventType.LEARNING,
            JournalEventType.MEDIA,
        }:
            continue

        memories.append(
            DashboardMemoryViewModel(
                title=item.title,
                subtitle=_EVENT_LABELS[item.event_type],
                date_label=item.occurred_at.strftime(
                    "%d %B %Y"
                ),
            )
        )

        if len(memories) == 3:
            break

    return tuple(memories)
