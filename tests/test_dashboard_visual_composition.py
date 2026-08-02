"""Regression tests for the compact Sprint 33.3 composition."""

from __future__ import annotations

import ast
import os
import pathlib
import runpy
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from ecobiome.dashboard import build_project_dashboard
from ecobiome.ui.desktop import (
    DashboardLayoutPreferences,
    DashboardSection,
    DesktopDashboardViewModel,
    DiagnosticAnalyticsViewModel,
    EcoBiomeDesktopApp,
    HypothesisDetailViewModel,
    SurfaceLevel,
    build_media_gallery,
    readable_media_title,
    select_hero_image_path,
)
from ecobiome.ui.desktop.surfaces import RoundedSurfaceCard

_desktop_dashboard_demo = runpy.run_path(
    str(
        pathlib.Path(__file__).resolve().parents[1]
        / "examples"
        / "desktop_dashboard_demo.py"
    )
)

populate_demo_workspace = _desktop_dashboard_demo["populate_demo_workspace"]

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


def _widget_texts(
    widget: tk.Misc,
) -> tuple[str, ...]:
    texts: list[str] = []

    for child in widget.winfo_children():
        try:
            value = child.cget("text")
        except tk.TclError:
            value = ""

        if isinstance(value, str) and value:
            texts.append(value)

        texts.extend(
            _widget_texts(child)
        )

    return tuple(texts)


def _walk_widgets(
    widget: tk.Misc,
) -> tuple[tk.Misc, ...]:
    """Return every descendant widget in stable creation order."""
    descendants: list[tk.Misc] = []

    for child in widget.winfo_children():
        descendants.append(child)
        descendants.extend(_walk_widgets(child))

    return tuple(descendants)


def test_readable_media_title_removes_storage_digest() -> None:
    assert readable_media_title(
        Path(
            "naissance-guppys-a1b2c3d4e5f6.png"
        )
    ) == "Naissance Guppys"


def test_hash_only_media_receives_project_label() -> None:
    with TemporaryDirectory(
        prefix="ecobiome-readable-title-"
    ) as temporary:
        directory = Path(temporary)
        image_path = directory / (
            "a1b2c3d4e5f6"
            "00112233445566778899.png"
        )
        Image.new(
            "RGB",
            (80, 50),
            "#123A45",
        ).save(image_path)

        gallery = build_media_gallery(
            directory
        )

    assert gallery[0].title == "Image du projet 1"


def test_hero_selection_prefers_panorama() -> None:
    with TemporaryDirectory(
        prefix="ecobiome-hero-selection-"
    ) as temporary:
        directory = Path(temporary)
        square = directory / "square.png"
        panorama = directory / "panorama.png"

        Image.new(
            "RGB",
            (500, 500),
            "#173C47",
        ).save(square)
        Image.new(
            "RGB",
            (1200, 360),
            "#236051",
        ).save(panorama)

        selected = select_hero_image_path(
            (
                square,
                panorama,
            )
        )

    assert selected == panorama


def test_hero_is_built_inside_scrollable_body() -> None:
    source = Path(
        "src/ecobiome/ui/desktop/app.py"
    ).read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    application = next(
        node
        for node in tree.body
        if (
            isinstance(node, ast.ClassDef)
            and node.name == "EcoBiomeDesktopApp"
        )
    )
    main_area = next(
        node
        for node in application.body
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "_build_main_area"
        )
    )
    segment = ast.get_source_segment(
        source,
        main_area,
    )

    assert segment is not None
    assert "body = viewport.content" in segment
    assert "DashboardHeroBanner(\n            body," in segment
    assert "row=0" in segment


def test_compact_analytics_disables_second_hypothesis_panel() -> None:
    source = Path(
        "src/ecobiome/ui/desktop/app.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "quality_only=True" in source
    assert source.count(
        '"Hypothèses principales"'
    ) == 1


def test_complete_dashboard_uses_compact_visual_rows() -> None:
    if _run_in_isolated_tk_process(
        "test_complete_dashboard_uses_compact_visual_rows"
    ):
        return

    with TemporaryDirectory(
        prefix="ecobiome-composition-"
    ) as temporary:
        workspace = populate_demo_workspace(
            Path(temporary)
            / "aquarium-guppys"
        )
        snapshot = build_project_dashboard(
            workspace,
            latest_limit=8,
            quality_score=82,
        )
        view_model = (
            DesktopDashboardViewModel.from_snapshot(
                snapshot
            )
        )
        gallery_items = build_media_gallery(
            workspace.layout.media_directory,
            limit=50,
        )
        analytics = DiagnosticAnalyticsViewModel(
            quality_score=82,
            quality_history=(
                64,
                70,
                76,
                82,
            ),
            high_quality_count=18,
            medium_quality_count=6,
            low_quality_count=2,
            rejected_count=1,
            hypotheses=(
                HypothesisDetailViewModel(
                    identifier="H1",
                    title="Capteur déréglé",
                    explanation="Dérive progressive.",
                    recommendation="Recalibrer le capteur.",
                    probability=78,
                    accent="#70D68D",
                ),
            ),
        )

        app = EcoBiomeDesktopApp(
            view_model,
            gallery_items=gallery_items,
            gallery_directory=(
                workspace.layout.media_directory
            ),
            analytics_view_model=analytics,
            layout_preferences=(
                DashboardLayoutPreferences()
            ),
        )
        root = app._root
        root.withdraw()

        try:
            root.update_idletasks()
            root.update()

            viewport = app._viewport
            hero = app._hero_banner

            assert viewport is not None
            assert hero is not None
            assert hero.master is viewport.content
            assert int(hero.cget("height")) == hero._px(132)
            assert int(
                hero.grid_info()["row"]
            ) == 0

            assert hero._window_controls is not None
            window_buttons = tuple(
                child
                for child in hero._window_controls.winfo_children()
                if isinstance(child, tk.Button)
            )
            assert tuple(
                str(button.cget("text"))
                for button in window_buttons
            ) == ("−", "□", "×")
            assert all(
                str(button.cget("takefocus")) == "1"
                for button in window_buttons
            )

            activity_info = app._section_frames[
                DashboardSection.ACTIVITY
            ].grid_info()
            analytics_info = app._section_frames[
                DashboardSection.ANALYTICS
            ].grid_info()
            memories_info = app._section_frames[
                DashboardSection.MEMORIES
            ].grid_info()
            gallery_info = app._section_frames[
                DashboardSection.GALLERY
            ].grid_info()

            assert (
                int(activity_info["row"]),
                int(activity_info["column"]),
            ) == (0, 0)
            assert (
                int(analytics_info["row"]),
                int(analytics_info["column"]),
            ) == (0, 1)
            assert (
                int(memories_info["row"]),
                int(memories_info["column"]),
            ) == (1, 0)
            assert (
                int(gallery_info["row"]),
                int(gallery_info["column"]),
            ) == (1, 1)

            texts = _widget_texts(root)
            surface_levels = {
                widget.surface_level
                for widget in _walk_widgets(root)
                if isinstance(widget, RoundedSurfaceCard)
            }

            assert surface_levels == {
                SurfaceLevel.PANEL,
                SurfaceLevel.ANALYTIC,
                SurfaceLevel.COMPACT,
            }

            assert texts.count(
                "Hypothèses principales"
            ) == 1
            assert "ESPACE SCIENTIFIQUE" in texts
            assert "COMMUNAUTÉ ET COMPTE" in texts
            assert (
                f"{view_model.metrics[0].value} observations"
                in texts
            )
            assert (
                f"Fiabilité {view_model.metrics[1].value}"
                in texts
            )
            assert "Galerie rapide" in texts
            assert "⇩  Exporter le rapport" in texts

        finally:
            root.destroy()
