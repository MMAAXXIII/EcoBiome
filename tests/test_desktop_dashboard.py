"""Tests for the EcoBiome desktop-dashboard prototype."""

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
    ThemeIdentifier,
    available_desktop_themes,
    get_desktop_theme,
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


def make_snapshot(
    *,
    with_activity: bool = True,
) -> ProjectDashboardSnapshot:
    """Create one deterministic dashboard snapshot."""
    if with_activity:
        event_counts = (
            DashboardEventCount(
                event_type=(
                    JournalEventType.BIOLOGICAL_EVENT
                ),
                count=1,
            ),
            DashboardEventCount(
                event_type=JournalEventType.DIAGNOSTIC,
                count=1,
            ),
        )

        latest_activity = (
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
        )

        event_count = 2
    else:
        event_counts = ()
        latest_activity = ()
        event_count = 0

    return ProjectDashboardSnapshot(
        project_id=PROJECT_ID,
        project_name="Aquarium guppys",
        project_type=ProjectType.AQUARIUM,
        description="Suivi des guppys.",
        updated_at=UPDATED_AT,
        tags=("guppy", "aquarium"),
        journal_event_count=event_count,
        media_file_count=3,
        diagnostic_count=(
            1 if with_activity else 0
        ),
        learning_count=0,
        biological_event_count=(
            1 if with_activity else 0
        ),
        event_counts=event_counts,
        latest_activity=latest_activity,
    )


def test_four_desktop_themes_are_available() -> None:
    themes = available_desktop_themes()

    assert tuple(
        theme.identifier
        for theme in themes
    ) == tuple(ThemeIdentifier)

    assert len(themes) == 4


def test_theme_can_be_resolved_from_string() -> None:
    theme = get_desktop_theme(
        "ecobiome-night"
    )

    assert theme.identifier is (
        ThemeIdentifier.ECOBIOME_NIGHT
    )

    assert theme.display_name == "EcoBiome Night"
    assert theme.background.startswith("#")


def test_unknown_theme_is_rejected() -> None:
    with pytest.raises(
        KeyError,
        match="Unknown desktop theme identifier",
    ):
        get_desktop_theme("unknown-theme")


def test_all_theme_colors_use_hexadecimal_notation() -> None:
    for theme in available_desktop_themes():
        colors = (
            theme.background,
            theme.surface,
            theme.surface_elevated,
            theme.text_primary,
            theme.text_secondary,
            theme.border,
            theme.accent,
            theme.success,
            theme.warning,
            theme.danger,
            theme.hypothesis,
        )

        assert all(
            len(color) == 7
            and color.startswith("#")
            for color in colors
        )


def test_view_model_exposes_project_identity() -> None:
    view_model = (
        DesktopDashboardViewModel.from_snapshot(
            make_snapshot()
        )
    )

    assert view_model.project_name == "Aquarium guppys"
    assert view_model.project_type == "Aquarium"
    assert view_model.description == "Suivi des guppys."
    assert view_model.tags == "guppy · aquarium"
    assert view_model.updated_at == (
        "02/08/2026 · 20:00"
    )


def test_view_model_builds_summary_metrics() -> None:
    view_model = (
        DesktopDashboardViewModel.from_snapshot(
            make_snapshot()
        )
    )

    values = {
        metric.label: metric.value
        for metric in view_model.metrics
    }

    assert values == {
        "Événements": "2",
        "Médias": "3",
        "Diagnostics": "1",
        "Apprentissages": "0",
        "Événements biologiques": "1",
    }


def test_active_project_receives_activity_status() -> None:
    view_model = (
        DesktopDashboardViewModel.from_snapshot(
            make_snapshot()
        )
    )

    assert view_model.status_title == "Projet actif"
    assert "2 événement(s)" in (
        view_model.status_message
    )


def test_empty_project_receives_ready_status() -> None:
    view_model = (
        DesktopDashboardViewModel.from_snapshot(
            make_snapshot(with_activity=False)
        )
    )

    assert view_model.status_title == "Projet prêt"
    assert "commencer votre journal" in (
        view_model.status_message
    )


def test_activity_is_converted_to_french_view_model() -> None:
    view_model = (
        DesktopDashboardViewModel.from_snapshot(
            make_snapshot()
        )
    )

    activity = view_model.latest_activity[0]

    assert activity.category == (
        "Événements biologiques"
    )
    assert activity.title == (
        "Naissance de mes premiers guppys"
    )
    assert activity.occurred_at == (
        "02/08/2026 · 20:00"
    )
    assert activity.tags == "guppy · alevins"


def test_event_distribution_is_human_readable() -> None:
    view_model = (
        DesktopDashboardViewModel.from_snapshot(
            make_snapshot()
        )
    )

    assert view_model.event_distribution == (
        ("Diagnostics", 1),
        ("Événements biologiques", 1),
    )


def test_desktop_package_imports_without_opening_window() -> None:
    from ecobiome.ui.desktop import (
        EcoBiomeDesktopApp,
        run_desktop_dashboard,
    )

    assert EcoBiomeDesktopApp is not None
    assert run_desktop_dashboard is not None
