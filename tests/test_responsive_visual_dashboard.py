"""Tests for responsive and image-rich dashboard helpers."""

from dataclasses import dataclass
from pathlib import Path

import pytest
from PIL import Image

from ecobiome.ui.desktop import (
    DashboardViewportMetrics,
    PersistentDemoMediaStore,
    SpacingScale,
    SurfaceLevel,
    TypographyRole,
    cover_dimensions,
    geometry_dimensions,
    is_gallery_navigation_text,
    normalize_navigation_text,
    resolve_project_title,
    responsive_content_width,
    responsive_sidebar_width,
    scrollbar_fraction_for_thumb,
    scrollbar_thumb_geometry,
    spacing_scale,
    surface_profile,
    typography_font,
)
from ecobiome.ui.desktop.hero import (
    build_aquarium_fallback,
    resolve_mount_geometry_manager,
)
from ecobiome.ui.desktop.responsive import fit_content_height
from ecobiome.ui.desktop.surfaces import render_rounded_surface
from ecobiome.ui.desktop.theme import (
    ThemeIdentifier,
    get_desktop_theme,
)


@dataclass(frozen=True, slots=True)
class NamedViewModel:
    """Minimal view model carrying a project name."""

    project_name: str


def create_image(
    path: Path,
    *,
    value: int = 80,
) -> None:
    """Create one deterministic PNG image."""
    Image.new(
        "RGB",
        (64, 40),
        (
            value,
            120,
            90,
        ),
    ).save(
        path,
        format="PNG",
    )


def test_viewport_ratio_matches_reference_display() -> None:
    metrics = DashboardViewportMetrics(
        screen_width=1920,
        screen_height=1080,
    )

    assert metrics.fit_ratio == 1.0


def test_viewport_ratio_is_clamped_for_small_display() -> None:
    metrics = DashboardViewportMetrics(
        screen_width=800,
        screen_height=600,
    )

    assert metrics.fit_ratio == 0.72


def test_viewport_ratio_can_expand_for_large_displays() -> None:
    metrics = DashboardViewportMetrics(
        screen_width=2560,
        screen_height=1440,
        maximum_ratio=1.2,
    )

    assert metrics.fit_ratio == 1.2


def test_invalid_viewport_dimensions_are_rejected() -> None:
    metrics = DashboardViewportMetrics(
        screen_width=0,
        screen_height=1080,
    )

    with pytest.raises(
        ValueError,
        match="positive",
    ):
        _ = metrics.fit_ratio


def test_window_geometry_drives_non_maximized_visual_scale() -> None:
    width, height = geometry_dimensions(
        "1880x1000+-1900+16"
    )
    metrics = DashboardViewportMetrics(
        screen_width=width,
        screen_height=height,
    )

    assert (width, height) == (1880, 1000)
    assert metrics.fit_ratio == pytest.approx(
        1000 / 1080
    )

    with pytest.raises(ValueError, match="invalid"):
        geometry_dimensions("plein-écran")


def test_sidebar_width_tracks_viewport_without_crowding() -> None:
    assert responsive_sidebar_width(1200) == 204
    assert responsive_sidebar_width(2560) == 435
    assert responsive_sidebar_width(800) == 200
    assert responsive_sidebar_width(4000) == 450


def test_dashboard_content_is_capped_on_ultra_wide_viewports() -> None:
    assert responsive_content_width(1366) == 1366
    assert responsive_content_width(1920) == 1900
    assert responsive_content_width(2560) == 1900


def test_dashboard_content_width_rejects_invalid_values() -> None:
    with pytest.raises(
        ValueError,
        match="positive",
    ):
        responsive_content_width(0)

    with pytest.raises(
        ValueError,
        match="positive",
    ):
        responsive_content_width(
            1920,
            maximum=0,
        )


def test_custom_scrollbar_geometry_is_bounded_and_draggable() -> None:
    assert scrollbar_thumb_geometry(
        0.25,
        0.35,
        track_height=200,
        minimum_height=36,
    ) == (50, 86)
    assert scrollbar_thumb_geometry(
        0.95,
        1.0,
        track_height=200,
        minimum_height=36,
    ) == (164, 200)
    assert scrollbar_fraction_for_thumb(
        82,
        track_height=200,
        thumb_height=36,
    ) == 0.5

    with pytest.raises(ValueError, match="ordered"):
        scrollbar_thumb_geometry(
            0.8,
            0.2,
            track_height=200,
            minimum_height=36,
        )


def test_rounded_surface_has_clean_corners_and_fill() -> None:
    image = render_rounded_surface(
        180,
        90,
        outer_background="#01090C",
        surface="#08232A",
        border="#1C4851",
        shadow="#000508",
        radius=16,
        shadow_offset=4,
    )

    assert image.size == (180, 90)
    assert image.getpixel((0, 0)) == (1, 9, 12)
    assert image.getpixel((90, 40)) == (8, 35, 42)
    assert len(image.getcolors(maxcolors=5000) or ()) > 4


def test_surface_system_exposes_three_scaled_levels() -> None:
    panel = surface_profile(SurfaceLevel.PANEL)
    analytic = surface_profile(
        SurfaceLevel.ANALYTIC,
        visual_scale=1.2,
    )
    compact = surface_profile(SurfaceLevel.COMPACT)

    assert panel.radius == 14
    assert panel.shadow_offset == 3
    assert analytic.radius == 14
    assert analytic.shadow_offset == 2
    assert compact.radius == 9
    assert compact.shadow_offset == 1

    with pytest.raises(ValueError, match="positive"):
        surface_profile(
            SurfaceLevel.PANEL,
            visual_scale=0,
        )


def test_design_tokens_share_one_scaled_visual_rhythm() -> None:
    spacing = spacing_scale(1.2)

    assert spacing == SpacingScale(
        micro=5,
        compact=10,
        gutter=14,
        padding=19,
        group=29,
        major=38,
    )
    assert typography_font(
        TypographyRole.PROJECT_TITLE
    ) == ("Segoe UI Semibold", 25)
    assert typography_font(
        TypographyRole.BODY,
        visual_scale=1.2,
    ) == ("Segoe UI", 11)

    with pytest.raises(ValueError, match="positive"):
        spacing_scale(0)

    with pytest.raises(ValueError, match="positive"):
        typography_font(
            TypographyRole.BODY,
            visual_scale=0,
        )


def test_cover_dimensions_fill_target_area() -> None:
    width, height = cover_dimensions(
        400,
        200,
        1000,
        300,
    )

    assert width >= 1000
    assert height >= 300


def test_navigation_text_recognizes_gallery_entries() -> None:
    assert is_gallery_navigation_text(
        "Galerie"
    )

    assert is_gallery_navigation_text(
        "▣ Ouvrir la galerie complète →"
    )


def test_navigation_text_rejects_gallery_heading() -> None:
    assert not is_gallery_navigation_text(
        "Galerie du projet"
    )

    assert (
        normalize_navigation_text(
            "Ouvrir la galerie complète"
        )
        == "ouvrir la galerie complete"
    )


def test_project_title_is_extracted() -> None:
    view_model = NamedViewModel(
        project_name="Aquarium Guppys"
    )

    assert (
        resolve_project_title(
            view_model
        )
        == "Aquarium Guppys"
    )


def test_persistent_media_survives_store_recreation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.png"

    create_image(
        source
    )

    media_directory = (
        tmp_path
        / "persistent-media"
    )

    first_store = PersistentDemoMediaStore(
        directory=media_directory
    )

    imported = first_store.import_file(
        source
    )

    second_store = PersistentDemoMediaStore(
        directory=media_directory
    )

    assert imported.is_file()

    assert tuple(
        second_store.directory.glob(
            "*.png"
        )
    ) == (imported,)


def test_persistent_media_is_deduplicated(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.png"

    create_image(
        source
    )

    store = PersistentDemoMediaStore(
        directory=tmp_path / "media"
    )

    first = store.import_file(
        source
    )

    second = store.import_file(
        source
    )

    assert first == second

    assert len(
        tuple(
            store.directory.iterdir()
        )
    ) == 1


def test_unsupported_demo_media_is_rejected(
    tmp_path: Path,
) -> None:
    source = tmp_path / "notes.txt"

    source.write_text(
        "not an image",
        encoding="utf-8",
    )

    store = PersistentDemoMediaStore(
        directory=tmp_path / "media"
    )

    with pytest.raises(
        ValueError,
        match="Unsupported",
    ):
        store.import_file(
            source
        )

def test_mount_geometry_uses_pack_for_packed_container() -> None:
    assert (
        resolve_mount_geometry_manager(
            packed_children=2,
            gridded_children=0,
        )
        == "pack"
    )


def test_mount_geometry_uses_grid_for_gridded_container() -> None:
    assert (
        resolve_mount_geometry_manager(
            packed_children=0,
            gridded_children=3,
        )
        == "grid"
    )


def test_mount_geometry_rejects_mixed_managers() -> None:
    with pytest.raises(
        ValueError,
        match="mix",
    ):
        resolve_mount_geometry_manager(
            packed_children=1,
            gridded_children=1,
        )


def test_content_height_fills_short_viewport() -> None:
    assert fit_content_height(700, 420) == 700


def test_content_height_preserves_tall_scrollable_body() -> None:
    assert fit_content_height(700, 1280) == 1280


def test_aquarium_fallback_is_visually_non_uniform() -> None:
    image = build_aquarium_fallback(
        width=640,
        height=180,
        theme=get_desktop_theme(
            ThemeIdentifier.ECOBIOME_NIGHT
        ),
    )

    assert image.size == (640, 180)
    assert len(image.getcolors(maxcolors=640 * 180) or ()) > 20


def test_persistent_store_imports_nested_media(
    tmp_path: Path,
) -> None:
    source_directory = tmp_path / "workspace-media"
    nested_directory = source_directory / "2026" / "08"
    nested_directory.mkdir(parents=True)

    source = nested_directory / "nested.png"
    create_image(source)

    store = PersistentDemoMediaStore(
        directory=tmp_path / "persistent"
    )

    imported = store.import_directory(
        source_directory
    )

    assert len(imported) == 1
    assert imported[0].is_file()
