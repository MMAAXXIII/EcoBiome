"""Tests for dashboard profiles and resilient persistence."""

from pathlib import Path

from ecobiome.ui.desktop import (
    DashboardLayoutPreferences,
    DashboardLayoutPreset,
    DashboardLayoutStore,
    DashboardSection,
    dashboard_layout_for_preset,
    identify_dashboard_layout_preset,
)


def test_complete_profile_matches_default() -> None:
    preferences = dashboard_layout_for_preset(
        DashboardLayoutPreset.COMPLETE
    )

    assert preferences == (
        DashboardLayoutPreferences()
    )


def test_analytics_profile_prioritizes_analysis() -> None:
    preferences = dashboard_layout_for_preset(
        DashboardLayoutPreset.ANALYTICS_FIRST
    )

    assert preferences.order[:2] == (
        DashboardSection.ANALYTICS,
        DashboardSection.MEMORIES,
    )

    assert preferences.hidden_sections == frozenset()


def test_focus_profile_hides_secondary_sections() -> None:
    preferences = dashboard_layout_for_preset(
        DashboardLayoutPreset.FOCUS
    )

    assert preferences.visible_sections == (
        DashboardSection.ANALYTICS,
        DashboardSection.ACTIVITY,
    )


def test_matching_profile_is_identified() -> None:
    preferences = dashboard_layout_for_preset(
        DashboardLayoutPreset.MEDIA_REVIEW
    )

    assert identify_dashboard_layout_preset(
        preferences
    ) is DashboardLayoutPreset.MEDIA_REVIEW


def test_custom_layout_has_no_matching_profile() -> None:
    preferences = DashboardLayoutPreferences(
        order=(
            DashboardSection.GALLERY,
            DashboardSection.ANALYTICS,
            DashboardSection.ACTIVITY,
            DashboardSection.MEMORIES,
        ),
        hidden_sections=frozenset(
            {
                DashboardSection.MEMORIES,
            }
        ),
    )

    assert (
        identify_dashboard_layout_preset(
            preferences
        )
        is None
    )


def test_section_can_move_to_absolute_position() -> None:
    preferences = DashboardLayoutPreferences()

    moved = preferences.move_to(
        DashboardSection.MEMORIES,
        0,
    )

    assert moved.order == (
        DashboardSection.MEMORIES,
        DashboardSection.ANALYTICS,
        DashboardSection.ACTIVITY,
        DashboardSection.GALLERY,
    )


def test_absolute_position_is_clamped() -> None:
    preferences = DashboardLayoutPreferences()

    moved = preferences.move_to(
        DashboardSection.ANALYTICS,
        999,
    )

    assert moved.order == (
        DashboardSection.ACTIVITY,
        DashboardSection.GALLERY,
        DashboardSection.MEMORIES,
        DashboardSection.ANALYTICS,
    )


def test_missing_store_returns_default(
    tmp_path: Path,
) -> None:
    store = DashboardLayoutStore(
        path=tmp_path / "missing.json"
    )

    assert store.load_or_default() == (
        DashboardLayoutPreferences()
    )


def test_invalid_store_is_backed_up(
    tmp_path: Path,
) -> None:
    store = DashboardLayoutStore(
        path=tmp_path / "dashboard-layout.json"
    )

    store.path.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    recovered = store.load_or_default()

    assert recovered == (
        DashboardLayoutPreferences()
    )

    assert not store.path.exists()
    assert store.invalid_backup_path.is_file()

    assert (
        store.invalid_backup_path.read_text(
            encoding="utf-8"
        )
        == "{invalid json"
    )


def test_profile_survives_store_round_trip(
    tmp_path: Path,
) -> None:
    store = DashboardLayoutStore(
        path=tmp_path / "exported-layout.json"
    )

    original = dashboard_layout_for_preset(
        DashboardLayoutPreset.FOCUS
    )

    store.save(original)

    assert store.load() == original


def test_profile_api_imports_without_window() -> None:
    from ecobiome.ui.desktop import (
        DashboardLayoutDialog,
    )

    assert DashboardLayoutDialog is not None

    assert (
        DashboardLayoutPreset.COMPLETE.display_name
        == "Vue complète"
    )
