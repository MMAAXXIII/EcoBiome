"""Tests for the EcoBiome desktop-dashboard prototype."""

import os
import subprocess
import sys
import time
import tkinter as tk
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch as mock_patch
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
    EcoBiomeDesktopApp,
    NavigationIdentifier,
    NavigationStatus,
    ThemeIdentifier,
    available_desktop_themes,
    get_desktop_theme,
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

_TK_SCENARIO_ENVIRONMENT_VARIABLE = (
    "ECOBIOME_TK_TEST_SCENARIO"
)


def _run_in_isolated_tk_process(
    scenario_name: str,
) -> bool:
    """Run one native Tk scenario in its own Python process."""
    if (
        os.environ.get(
            _TK_SCENARIO_ENVIRONMENT_VARIABLE
        )
        == scenario_name
    ):
        return False

    environment = os.environ.copy()
    environment[
        _TK_SCENARIO_ENVIRONMENT_VARIABLE
    ] = scenario_name
    node_identifier = (
        f"{Path(__file__).resolve()}::{scenario_name}"
    )
    result = subprocess.run(
        (
            sys.executable,
            "-m",
            "pytest",
            node_identifier,
            "-q",
        ),
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert result.returncode == 0, (
        "Isolated Tk scenario failed:\n"
        f"{result.stdout}\n{result.stderr}"
    )
    return True


def _relative_luminance(color: str) -> float:
    """Return WCAG relative luminance for one hexadecimal color."""
    channels = (
        int(color[index : index + 2], 16) / 255
        for index in (1, 3, 5)
    )
    linear = tuple(
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    )
    return (
        0.2126 * linear[0]
        + 0.7152 * linear[1]
        + 0.0722 * linear[2]
    )


def _contrast_ratio(
    foreground: str,
    background: str,
) -> float:
    """Return the WCAG contrast ratio between two colors."""
    lighter, darker = sorted(
        (
            _relative_luminance(foreground),
            _relative_luminance(background),
        ),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


def _walk_widgets(widget: tk.Misc) -> tuple[tk.Misc, ...]:
    """Return every descendant widget in stable creation order."""
    descendants: list[tk.Misc] = []

    for child in widget.winfo_children():
        descendants.append(child)
        descendants.extend(_walk_widgets(child))

    return tuple(descendants)


def _tcl_commands(root: tk.Tk) -> tuple[str, ...]:
    """Return the live Tcl command names for one interpreter."""
    commands = root.tk.call("info", "commands")

    if isinstance(commands, tuple):
        return tuple(str(command) for command in commands)

    return tuple(root.tk.splitlist(commands))


def _settle_tk_redraws(root: tk.Tk) -> None:
    """Let short visual debounce timers complete before measuring Tcl."""
    time.sleep(0.08)
    root.update_idletasks()
    root.update()


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
        conclusion_count=(
            1 if with_activity else 0
        ),
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


def test_corrected_semantic_text_colors_have_contrast_margin() -> None:
    laboratory = get_desktop_theme(
        ThemeIdentifier.LABORATORY_LIGHT
    )
    forest = get_desktop_theme(
        ThemeIdentifier.FOREST
    )

    assert (
        _contrast_ratio(
            laboratory.success,
            laboratory.surface,
        )
        >= 4.7
    )
    assert (
        _contrast_ratio(
            forest.danger,
            forest.surface,
        )
        >= 4.7
    )


def test_root_bindings_are_installed_idempotently() -> None:
    app = EcoBiomeDesktopApp.__new__(EcoBiomeDesktopApp)
    root = Mock()
    root.bind.side_effect = (
        "wheel-id",
        "scroll-up-id",
        "scroll-down-id",
        "home-id",
        "end-id",
    )
    app._root = root
    app._root_binding_ids = {}

    app._install_root_bindings()
    app._install_root_bindings()

    assert root.bind.call_count == 5
    assert app._root_binding_ids == {
        "<MouseWheel>": "wheel-id",
        "<Button-4>": "scroll-up-id",
        "<Button-5>": "scroll-down-id",
        "<Home>": "home-id",
        "<End>": "end-id",
    }


def test_theme_change_waits_for_current_tk_callback() -> None:
    app = EcoBiomeDesktopApp.__new__(
        EcoBiomeDesktopApp
    )
    root = Mock()
    app._root = root
    app._theme_name_by_display = {
        "Laboratory Light": (
            ThemeIdentifier.LABORATORY_LIGHT
        ),
    }
    app._pending_theme_identifier = None
    app._theme_change_after_id = None
    root.after_idle.return_value = "theme-change-id"

    app._change_theme("Laboratory Light")

    root.after_idle.assert_called_once_with(
        app._apply_pending_theme,
    )
    assert app._theme_change_after_id == "theme-change-id"
    assert app._pending_theme_identifier is (
        ThemeIdentifier.LABORATORY_LIGHT
    )
    root.winfo_children.assert_not_called()


def test_rapid_theme_requests_are_coalesced() -> None:
    app = EcoBiomeDesktopApp.__new__(EcoBiomeDesktopApp)
    root = Mock()
    root.after_idle.return_value = "theme-change-id"
    app._root = root
    app._theme_name_by_display = {
        "EcoBiome Night": ThemeIdentifier.ECOBIOME_NIGHT,
        "Laboratory Light": ThemeIdentifier.LABORATORY_LIGHT,
        "Forest": ThemeIdentifier.FOREST,
    }
    app._pending_theme_identifier = None
    app._theme_change_after_id = None
    app._apply_theme = Mock()

    app._change_theme("EcoBiome Night")
    app._change_theme("Laboratory Light")
    app._change_theme("Forest")

    root.after_idle.assert_called_once_with(
        app._apply_pending_theme,
    )
    assert app._pending_theme_identifier is ThemeIdentifier.FOREST

    app._apply_pending_theme()

    app._apply_theme.assert_called_once_with(
        ThemeIdentifier.FOREST
    )
    assert app._theme_change_after_id is None
    assert app._pending_theme_identifier is None


def test_deferred_theme_change_rebuilds_live_dashboard() -> None:
    if _run_in_isolated_tk_process(
        "test_deferred_theme_change_rebuilds_live_dashboard"
    ):
        return

    view_model = DesktopDashboardViewModel.from_snapshot(
        make_snapshot()
    )
    app = EcoBiomeDesktopApp(view_model)
    root = app._root
    root.withdraw()

    try:
        root.update_idletasks()
        root.update()

        for theme in available_desktop_themes():
            app._change_theme(theme.display_name)

            root.update_idletasks()
            root.update()

            assert app._theme.identifier is theme.identifier
            assert root.winfo_children()

    finally:
        root.destroy()


def test_theme_rebuilds_do_not_grow_tcl_commands_linearly() -> None:
    if _run_in_isolated_tk_process(
        "test_theme_rebuilds_do_not_grow_tcl_commands_linearly"
    ):
        return

    view_model = DesktopDashboardViewModel.from_snapshot(
        make_snapshot()
    )
    app = EcoBiomeDesktopApp(view_model)
    root = app._root
    root.withdraw()
    themes = available_desktop_themes()

    try:
        for index in range(8):
            app._change_theme(
                themes[index % len(themes)].display_name
            )
            root.update_idletasks()
            root.update()

        _settle_tk_redraws(root)
        command_count_after_warmup = len(
            _tcl_commands(root)
        )

        for index in range(100):
            app._change_theme(
                themes[index % len(themes)].display_name
            )
            root.update_idletasks()
            root.update()

        _settle_tk_redraws(root)
        command_count_after_stress = len(
            _tcl_commands(root)
        )

        assert (
            command_count_after_stress
            == command_count_after_warmup
        )
        assert len(app._root_binding_ids) == 5

    finally:
        root.destroy()


def test_primary_navigation_is_explicit_and_keyboard_accessible() -> None:
    if _run_in_isolated_tk_process(
        "test_primary_navigation_is_explicit_and_keyboard_accessible"
    ):
        return

    view_model = DesktopDashboardViewModel.from_snapshot(
        make_snapshot()
    )
    app = EcoBiomeDesktopApp(view_model)
    root = app._root
    root.withdraw()

    try:
        items = app._navigation_items
        assert len(items) == 13
        assert {
            item.identifier
            for item in items
        } >= {
            NavigationIdentifier.DASHBOARD,
            NavigationIdentifier.GALLERY,
            NavigationIdentifier.EXPERIMENTS,
            NavigationIdentifier.LEARNING,
        }
        assert sum(
            item.status is NavigationStatus.AVAILABLE
            for item in items
        ) == 2

        assert app._sidebar is not None
        assert app._sidebar_navigation_canvas is not None
        assert app._sidebar_navigation_content is not None
        assert isinstance(
            app._sidebar_navigation_scrollbar,
            tk.Canvas,
        )
        expected_texts = {
            icon_text(item.icon, item.label)
            for item in items
        }
        buttons = tuple(
            widget
            for widget in _walk_widgets(app._sidebar)
            if (
                isinstance(widget, tk.Button)
                and str(widget.cget("text"))
                in expected_texts
            )
        )
        assert not any(
            isinstance(widget, tk.Scrollbar)
            for widget in _walk_widgets(app._sidebar)
        )

        assert len(buttons) == len(items)
        assert all(
            str(button.cget("takefocus")) == "1"
            for button in buttons
        )
        assert all(
            int(button.cget("highlightthickness")) == 2
            for button in buttons
        )
        assert all(
            button.bind("<Return>")
            and button.bind("<space>")
            for button in buttons
        )

        selected_button = next(
            button
            for button in buttons
            if str(button.cget("text"))
            == icon_text(
                items[0].icon,
                items[0].label,
            )
        )
        assert str(selected_button.cget("relief")) == "sunken"

        invocation = Mock()
        selected_button.configure(command=invocation)

        result = app._invoke_navigation_button(
            selected_button,
            Mock(),
        )
        assert result == "break"
        invocation.assert_called_once_with()

        invocation.reset_mock()
        result = app._invoke_navigation_button(
            selected_button,
            Mock(),
        )
        assert result == "break"
        invocation.assert_called_once_with()

        entry = tk.Entry(root)
        event = Mock(widget=entry)
        assert app._on_root_home(event) is None
        assert app._on_root_end(event) is None
        entry.destroy()

        experiments = next(
            item
            for item in items
            if item.identifier
            is NavigationIdentifier.EXPERIMENTS
        )

        with mock_patch(
            "ecobiome.ui.desktop.app.messagebox.showinfo"
        ) as showinfo:
            experiments.command()

        showinfo.assert_called_once()
        assert "Expériences" in showinfo.call_args.args[1]

        root.geometry("1366x768")
        root.update_idletasks()
        root.update()

        sidebar_height = app._sidebar.winfo_height()
        bottom_widget = app._sidebar.winfo_children()[-1]
        assert (
            bottom_widget.winfo_y()
            + bottom_widget.winfo_height()
            <= sidebar_height
        )

        last_button = buttons[-1]
        last_button.focus_set()
        app._reveal_sidebar_navigation_item(
            Mock(widget=last_button)
        )
        canvas = app._sidebar_navigation_canvas
        assert canvas is not None
        assert canvas.yview()[1] > 0.0

    finally:
        root.destroy()


def test_hero_without_asset_uses_fallback_and_releases_callbacks(
    tmp_path: Path,
) -> None:
    if _run_in_isolated_tk_process(
        "test_hero_without_asset_uses_fallback_and_releases_callbacks"
    ):
        return

    view_model = DesktopDashboardViewModel.from_snapshot(
        make_snapshot()
    )
    app = EcoBiomeDesktopApp(view_model)
    root = app._root
    root.withdraw()
    banner = app._hero_banner

    assert banner is not None
    missing_path = tmp_path / "missing-hero.png"
    assert not missing_path.exists()
    assert not banner.has_source_image

    banner.set_image_path(missing_path)
    assert not banner.has_source_image

    corrupt_path = tmp_path / "corrupt-hero.png"
    corrupt_path.write_bytes(b"not an image")
    banner.set_image_path(corrupt_path)
    assert not banner.has_source_image

    theme_variable = banner._theme_variable
    trace_id = banner._theme_trace_id
    assert theme_variable is not None
    assert trace_id is not None
    assert any(
        trace_id == callback_name
        for _mode, callback_name in theme_variable.trace_info()
    )

    rendered = banner._render_background(
        width=640,
        height=180,
    )
    assert rendered.size == (640, 180)

    banner._schedule_redraw()
    assert banner._redraw_after_id is not None

    banner.destroy()
    banner.destroy()

    assert banner._theme_trace_id is None
    assert banner._redraw_after_id is None
    assert banner._initial_redraw_after_id is None
    assert not theme_variable.trace_info()

    root.update_idletasks()
    root.update()
    root.destroy()


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
        "Observations": "2",
        "Qualité globale": "—",
        "Hypothèses": "0",
        "Expériences": "0",
        "Conclusions": "1",
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
