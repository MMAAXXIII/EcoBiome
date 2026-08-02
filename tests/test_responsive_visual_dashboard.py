"""Tests for responsive and image-rich dashboard helpers."""

from dataclasses import dataclass
from pathlib import Path

import pytest
from PIL import Image

from ecobiome.ui.desktop import (
    DashboardViewportMetrics,
    PersistentDemoMediaStore,
    cover_dimensions,
    is_gallery_navigation_text,
    normalize_navigation_text,
    resolve_project_title,
)
from ecobiome.ui.desktop.hero import (
    build_aquarium_fallback,
    resolve_mount_geometry_manager,
)
from ecobiome.ui.desktop.responsive import fit_content_height
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
