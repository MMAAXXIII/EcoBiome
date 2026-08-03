"""Tests for the functional desktop media gallery."""

from datetime import UTC, datetime
from inspect import signature
from pathlib import Path

import pytest
from PIL import Image

from ecobiome.ui.desktop import (
    EcoBiomeDesktopApp,
    GalleryNavigator,
    GalleryViewerDialog,
    MediaGalleryItem,
    run_desktop_dashboard,
)

CAPTURED_AT = datetime(
    2026,
    8,
    2,
    20,
    0,
    tzinfo=UTC,
)


def create_item(
    tmp_path: Path,
    *,
    name: str,
) -> MediaGalleryItem:
    """Create one deterministic gallery item."""
    path = tmp_path / name

    Image.new(
        "RGB",
        (100, 60),
        (20, 80, 60),
    ).save(
        path,
        format="PNG",
    )

    return MediaGalleryItem(
        path=path,
        title=path.stem,
        captured_at=CAPTURED_AT,
        size_bytes=path.stat().st_size,
        suffix=".png",
    )


def test_empty_navigator_has_no_current_item() -> None:
    navigator = GalleryNavigator(
        items=()
    )

    assert navigator.current is None
    assert navigator.position_label == "0 / 0"
    assert navigator.next() is navigator
    assert navigator.previous() is navigator


def test_empty_navigator_rejects_nonzero_index() -> None:
    with pytest.raises(
        ValueError,
        match="must use index zero",
    ):
        GalleryNavigator(
            items=(),
            index=1,
        )


def test_navigator_exposes_current_item(
    tmp_path: Path,
) -> None:
    first = create_item(
        tmp_path,
        name="first.png",
    )

    second = create_item(
        tmp_path,
        name="second.png",
    )

    navigator = GalleryNavigator(
        items=(
            first,
            second,
        )
    )

    assert navigator.current == first
    assert navigator.position_label == "1 / 2"


def test_next_navigation_wraps(
    tmp_path: Path,
) -> None:
    first = create_item(
        tmp_path,
        name="first.png",
    )

    second = create_item(
        tmp_path,
        name="second.png",
    )

    navigator = GalleryNavigator(
        items=(
            first,
            second,
        ),
        index=1,
    )

    assert navigator.next().current == first


def test_previous_navigation_wraps(
    tmp_path: Path,
) -> None:
    first = create_item(
        tmp_path,
        name="first.png",
    )

    second = create_item(
        tmp_path,
        name="second.png",
    )

    navigator = GalleryNavigator(
        items=(
            first,
            second,
        )
    )

    assert navigator.previous().current == second


def test_explicit_selection_changes_position(
    tmp_path: Path,
) -> None:
    first = create_item(
        tmp_path,
        name="first.png",
    )

    second = create_item(
        tmp_path,
        name="second.png",
    )

    navigator = GalleryNavigator(
        items=(
            first,
            second,
        )
    ).select(1)

    assert navigator.current == second
    assert navigator.position_label == "2 / 2"


def test_invalid_selection_is_rejected(
    tmp_path: Path,
) -> None:
    item = create_item(
        tmp_path,
        name="image.png",
    )

    navigator = GalleryNavigator(
        items=(item,)
    )

    with pytest.raises(
        IndexError,
        match="outside",
    ):
        navigator.select(4)


def test_desktop_app_accepts_gallery_actions() -> None:
    parameters = signature(
        EcoBiomeDesktopApp.__init__
    ).parameters

    assert "gallery_directory" in parameters

    assert (
        "on_import_gallery_files"
        in parameters
    )


def test_gallery_api_imports_without_window() -> None:
    parameters = signature(
        run_desktop_dashboard
    ).parameters

    assert GalleryViewerDialog is not None
    assert "gallery_directory" in parameters

    assert (
        "on_import_gallery_files"
        in parameters
    )
