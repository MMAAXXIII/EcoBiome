"""Tests for the real EcoBiome media-gallery presentation layer."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from PIL import Image

from ecobiome.ui.desktop import (
    MediaGalleryItem,
    build_media_gallery,
)

CAPTURED_AT = datetime(
    2026,
    8,
    2,
    20,
    0,
    tzinfo=UTC,
)


def create_image(
    path: Path,
    *,
    color: tuple[int, int, int],
) -> None:
    """Create one valid deterministic PNG image."""
    image = Image.new(
        "RGB",
        (160, 90),
        color,
    )

    image.save(
        path,
        format="PNG",
    )


def test_gallery_returns_supported_images_only(
    tmp_path: Path,
) -> None:
    first = tmp_path / "premiers-alevins.png"
    second = tmp_path / "aquarium-principal.jpg"
    ignored = tmp_path / "notes.txt"

    create_image(
        first,
        color=(20, 90, 70),
    )

    Image.new(
        "RGB",
        (160, 90),
        (40, 80, 120),
    ).save(
        second,
        format="JPEG",
    )

    ignored.write_text(
        "not an image",
        encoding="utf-8",
    )

    gallery = build_media_gallery(
        tmp_path
    )

    assert len(gallery) == 2

    assert {
        item.path
        for item in gallery
    } == {
        first,
        second,
    }


def test_gallery_is_sorted_newest_first(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"

    create_image(
        first,
        color=(10, 20, 30),
    )

    create_image(
        second,
        color=(30, 40, 50),
    )

    first.touch()

    second_timestamp = first.stat().st_mtime + 10

    second.touch()

    import os

    os.utime(
        second,
        (
            second_timestamp,
            second_timestamp,
        ),
    )

    gallery = build_media_gallery(
        tmp_path
    )

    assert tuple(
        item.path.name
        for item in gallery
    ) == (
        "second.png",
        "first.png",
    )


def test_gallery_limit_is_respected(
    tmp_path: Path,
) -> None:
    for index in range(5):
        create_image(
            tmp_path / f"image-{index}.png",
            color=(index, index, index),
        )

    gallery = build_media_gallery(
        tmp_path,
        limit=3,
    )

    assert len(gallery) == 3


def test_zero_gallery_limit_returns_empty(
    tmp_path: Path,
) -> None:
    create_image(
        tmp_path / "image.png",
        color=(1, 2, 3),
    )

    assert build_media_gallery(
        tmp_path,
        limit=0,
    ) == ()


def test_negative_gallery_limit_is_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        build_media_gallery(
            tmp_path,
            limit=-1,
        )


def test_missing_directory_returns_empty(
    tmp_path: Path,
) -> None:
    assert build_media_gallery(
        tmp_path / "missing"
    ) == ()


def test_gallery_item_exposes_readable_labels(
    tmp_path: Path,
) -> None:
    path = tmp_path / "naissance-guppys.png"

    create_image(
        path,
        color=(20, 120, 90),
    )

    item = MediaGalleryItem(
        path=path,
        title="Naissance des guppys",
        captured_at=CAPTURED_AT,
        size_bytes=2048,
        suffix=".png",
    )

    assert item.date_label == (
        "02/08/2026 · 20:00"
    )

    assert item.size_label == "2.0 Kio"


def test_gallery_item_rejects_unsupported_suffix(
    tmp_path: Path,
) -> None:
    path = tmp_path / "document.txt"

    path.write_text(
        "content",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported gallery image suffix",
    ):
        MediaGalleryItem(
            path=path,
            title="Document",
            captured_at=CAPTURED_AT,
            size_bytes=path.stat().st_size,
            suffix=".txt",
        )


def test_gallery_package_imports_without_window() -> None:
    from ecobiome.ui.desktop import (
        EcoBiomeDesktopApp,
        run_desktop_dashboard,
    )

    assert EcoBiomeDesktopApp is not None
    assert run_desktop_dashboard is not None
