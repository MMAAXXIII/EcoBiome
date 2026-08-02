"""Tests for the EcoBiome visual-identity layer."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from ecobiome.dashboard import (
    DashboardActivityItem,
    DashboardEventCount,
    ProjectDashboardSnapshot,
)
from ecobiome.journal import JournalEventType
from ecobiome.ui.desktop import (
    DesktopDashboardViewModel,
    DesktopIcon,
    UserProgressViewModel,
    icon_text,
)
from ecobiome.workspace import ProjectType

UPDATED_AT = datetime(
    2026,
    8,
    2,
    20,
    0,
    tzinfo=UTC,
)

PROJECT_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)

EVENT_ID = UUID(
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
)


def make_snapshot() -> ProjectDashboardSnapshot:
    """Create one populated dashboard snapshot."""
    return ProjectDashboardSnapshot(
        project_id=PROJECT_ID,
        project_name="Aquarium guppys",
        project_type=ProjectType.AQUARIUM,
        description="Suivi scientifique des guppys.",
        updated_at=UPDATED_AT,
        tags=("guppy", "aquarium"),
        journal_event_count=4,
        media_file_count=3,
        diagnostic_count=1,
        learning_count=1,
        biological_event_count=1,
        event_counts=(
            DashboardEventCount(
                event_type=JournalEventType.DIAGNOSTIC,
                count=1,
            ),
            DashboardEventCount(
                event_type=JournalEventType.LEARNING,
                count=1,
            ),
            DashboardEventCount(
                event_type=(
                    JournalEventType.BIOLOGICAL_EVENT
                ),
                count=1,
            ),
            DashboardEventCount(
                event_type=JournalEventType.NOTE,
                count=1,
            ),
        ),
        latest_activity=(
            DashboardActivityItem(
                event_id=EVENT_ID,
                event_type=(
                    JournalEventType.BIOLOGICAL_EVENT
                ),
                title="Naissance de mes premiers guppys",
                description="Premiers alevins observés.",
                occurred_at=UPDATED_AT,
                tags=("guppy", "alevins"),
            ),
        ),
    )


def test_icon_text_combines_symbol_and_label() -> None:
    assert icon_text(
        DesktopIcon.DASHBOARD,
        "Tableau de bord",
    ) == (
        f"{DesktopIcon.DASHBOARD.value}  "
        "Tableau de bord"
    )


def test_empty_icon_label_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        icon_text(
            DesktopIcon.DASHBOARD,
            " ",
        )


def test_progress_ratio_and_percent_are_consistent() -> None:
    progress = UserProgressViewModel(
        level=12,
        title="Chercheur confirmé",
        current_xp=2480,
        next_level_xp=4000,
    )

    assert progress.progress_ratio == pytest.approx(0.62)
    assert progress.progress_percent == 62


def test_progress_rejects_invalid_xp() -> None:
    with pytest.raises(
        ValueError,
        match="cannot exceed",
    ):
        UserProgressViewModel(
            level=1,
            title="Explorateur",
            current_xp=5000,
            next_level_xp=4000,
        )


def test_view_model_contains_five_visual_metrics() -> None:
    view_model = (
        DesktopDashboardViewModel.from_snapshot(
            make_snapshot()
        )
    )

    assert len(view_model.metrics) == 5

    assert tuple(
        metric.label
        for metric in view_model.metrics
    ) == (
        "Observations",
        "Qualité globale",
        "Hypothèses",
        "Expériences",
        "Conclusions",
    )


def test_view_model_builds_progression() -> None:
    view_model = (
        DesktopDashboardViewModel.from_snapshot(
            make_snapshot()
        )
    )

    assert view_model.progress.level >= 1
    assert view_model.progress.current_xp > 0
    assert view_model.progress.next_level_xp == 4000


def test_view_model_marks_key_activity_as_high() -> None:
    view_model = (
        DesktopDashboardViewModel.from_snapshot(
            make_snapshot()
        )
    )

    assert view_model.latest_activity[0].importance == "high"


def test_view_model_builds_milestone_memory() -> None:
    view_model = (
        DesktopDashboardViewModel.from_snapshot(
            make_snapshot()
        )
    )

    assert len(view_model.memories) == 1
    assert view_model.memories[0].title == (
        "Naissance de mes premiers guppys"
    )


def test_display_distribution_has_stable_priority() -> None:
    view_model = (
        DesktopDashboardViewModel.from_snapshot(
            make_snapshot()
        )
    )

    assert tuple(
        label
        for label, _count
        in view_model.event_distribution
    ) == (
        "Diagnostics",
        "Apprentissages",
        "Événements biologiques",
        "Notes",
    )


def test_visual_package_imports_without_window() -> None:
    from ecobiome.ui.desktop import (
        EcoBiomeDesktopApp,
        run_desktop_dashboard,
    )

    assert EcoBiomeDesktopApp is not None
    assert run_desktop_dashboard is not None
