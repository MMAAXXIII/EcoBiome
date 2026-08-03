"""Tests for the EcoBiome media-library foundation."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from ecobiome.media import (
    DuplicateMediaError,
    LocalMediaStorage,
    MediaLibrary,
    MediaMetadata,
    MediaType,
    calculate_sha256,
    infer_media_type,
)

CAPTURED_AT = datetime(
    2026,
    8,
    2,
    18,
    42,
    tzinfo=UTC,
)

PROJECT_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)

RELATED_ENTITY_ID = UUID(
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
)


def make_source(
    tmp_path: Path,
    *,
    name: str = "premiers-guppys.jpg",
    content: bytes = b"fake-image-content",
) -> Path:
    """Create one deterministic source file."""
    path = tmp_path / name
    path.write_bytes(content)
    return path


def make_metadata(
    *,
    title: str = "Naissance de mes premiers guppys",
    captured_at: datetime = CAPTURED_AT,
    tags: tuple[str, ...] = (
        "Guppy",
        "Reproduction",
        "Alevins",
    ),
) -> MediaMetadata:
    """Create deterministic media metadata."""
    return MediaMetadata(
        title=title,
        description=(
            "Premiers alevins observés près "
            "des plantes flottantes."
        ),
        captured_at=captured_at,
        tags=tags,
        attributes=(
            ("aquarium", "principal"),
            ("species", "Poecilia reticulata"),
        ),
    )


def test_media_type_is_inferred_from_extension() -> None:
    assert infer_media_type("photo.JPG") is MediaType.IMAGE
    assert infer_media_type("observation.mp4") is MediaType.VIDEO
    assert infer_media_type("notes.pdf") is MediaType.DOCUMENT
    assert infer_media_type("unknown.bin") is MediaType.OTHER


def test_checksum_is_deterministic(
    tmp_path: Path,
) -> None:
    source = make_source(tmp_path)

    assert calculate_sha256(source) == calculate_sha256(source)
    assert len(calculate_sha256(source)) == 64


def test_import_preserves_original_file(
    tmp_path: Path,
) -> None:
    source = make_source(tmp_path)
    original_content = source.read_bytes()

    library = MediaLibrary(
        LocalMediaStorage(tmp_path / "library")
    )

    asset = library.import_file(
        source,
        metadata=make_metadata(),
        project_id=PROJECT_ID,
        related_entity_ids=(RELATED_ENTITY_ID,),
    )

    assert source.is_file()
    assert source.read_bytes() == original_content

    assert asset.stored_path.is_file()
    assert asset.stored_path.read_bytes() == original_content
    assert asset.stored_path != source


def test_import_creates_traceable_asset(
    tmp_path: Path,
) -> None:
    source = make_source(tmp_path)

    library = MediaLibrary(
        LocalMediaStorage(tmp_path / "library")
    )

    asset = library.import_file(
        source,
        metadata=make_metadata(),
        project_id=PROJECT_ID,
        related_entity_ids=(
            RELATED_ENTITY_ID,
            RELATED_ENTITY_ID,
        ),
    )

    assert asset.original_filename == "premiers-guppys.jpg"
    assert asset.extension == ".jpg"
    assert asset.media_type is MediaType.IMAGE
    assert asset.mime_type == "image/jpeg"
    assert asset.size_bytes == source.stat().st_size
    assert asset.project_id == PROJECT_ID
    assert asset.related_entity_ids == (
        RELATED_ENTITY_ID,
    )

    assert asset.metadata.title == (
        "Naissance de mes premiers guppys"
    )

    assert asset.metadata.tags == (
        "guppy",
        "reproduction",
        "alevins",
    )


def test_storage_path_is_checksum_addressed(
    tmp_path: Path,
) -> None:
    source = make_source(tmp_path)

    storage = LocalMediaStorage(
        tmp_path / "library"
    )

    library = MediaLibrary(storage)
    asset = library.import_file(
        source,
        metadata=make_metadata(),
    )

    checksum = asset.checksum_sha256

    assert asset.stored_path == (
        storage.root
        / checksum[:2]
        / checksum[2:4]
        / f"{checksum}.jpg"
    )


def test_duplicate_content_is_rejected(
    tmp_path: Path,
) -> None:
    first = make_source(
        tmp_path,
        name="first.jpg",
    )

    second = make_source(
        tmp_path,
        name="second.jpg",
    )

    library = MediaLibrary(
        LocalMediaStorage(tmp_path / "library")
    )

    library.import_file(
        first,
        metadata=make_metadata(),
    )

    with pytest.raises(
        DuplicateMediaError,
        match="identical media file",
    ):
        library.import_file(
            second,
            metadata=make_metadata(
                title="Duplicate image"
            ),
        )


def test_library_returns_asset_by_identifier(
    tmp_path: Path,
) -> None:
    source = make_source(tmp_path)

    library = MediaLibrary(
        LocalMediaStorage(tmp_path / "library")
    )

    asset = library.import_file(
        source,
        metadata=make_metadata(),
    )

    assert library.get(asset.asset_id) == asset
    assert library.all() == (asset,)
    assert library.count() == 1


def test_search_filters_by_media_type_and_tags(
    tmp_path: Path,
) -> None:
    image = make_source(
        tmp_path,
        name="guppys.jpg",
        content=b"image-content",
    )

    document = make_source(
        tmp_path,
        name="parameters.pdf",
        content=b"document-content",
    )

    library = MediaLibrary(
        LocalMediaStorage(tmp_path / "library")
    )

    image_asset = library.import_file(
        image,
        metadata=make_metadata(),
        project_id=PROJECT_ID,
    )

    library.import_file(
        document,
        metadata=MediaMetadata(
            title="Water parameters",
            captured_at=CAPTURED_AT,
            tags=("analysis", "water"),
        ),
        project_id=PROJECT_ID,
    )

    assert library.search(
        media_type=MediaType.IMAGE,
        tags=("guppy", "alevins"),
    ) == (image_asset,)


def test_search_filters_by_project_and_period(
    tmp_path: Path,
) -> None:
    source = make_source(tmp_path)

    library = MediaLibrary(
        LocalMediaStorage(tmp_path / "library")
    )

    asset = library.import_file(
        source,
        metadata=make_metadata(),
        project_id=PROJECT_ID,
    )

    assert library.search(
        project_id=PROJECT_ID,
        captured_from=CAPTURED_AT - timedelta(days=1),
        captured_to=CAPTURED_AT + timedelta(days=1),
    ) == (asset,)

    assert library.search(
        captured_from=CAPTURED_AT + timedelta(days=1),
    ) == ()


def test_search_matches_descriptive_text(
    tmp_path: Path,
) -> None:
    source = make_source(tmp_path)

    library = MediaLibrary(
        LocalMediaStorage(tmp_path / "library")
    )

    asset = library.import_file(
        source,
        metadata=make_metadata(),
    )

    assert library.search(text="alevins observés") == (asset,)
    assert library.search(text="guppys") == (asset,)
    assert library.search(text="tomates") == ()


def test_metadata_normalizes_tags_and_attributes() -> None:
    metadata = MediaMetadata(
        title="  Guppy birth  ",
        tags=(
            " Guppy ",
            "guppy",
            "",
            " Alevins ",
        ),
        attributes=(
            (" aquarium ", " principal "),
            ("aquarium", "nursery"),
        ),
    )

    assert metadata.title == "Guppy birth"
    assert metadata.tags == (
        "guppy",
        "alevins",
    )

    assert metadata.attributes == (
        ("aquarium", "nursery"),
    )


def test_naive_capture_timestamp_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        MediaMetadata(
            title="Invalid timestamp",
            captured_at=CAPTURED_AT.replace(
                tzinfo=None
            ),
        )


def test_invalid_search_period_is_rejected(
    tmp_path: Path,
) -> None:
    library = MediaLibrary(
        LocalMediaStorage(tmp_path / "library")
    )

    with pytest.raises(
        ValueError,
        match="cannot follow",
    ):
        library.search(
            captured_from=CAPTURED_AT,
            captured_to=CAPTURED_AT - timedelta(days=1),
        )


def test_unknown_asset_identifier_is_rejected(
    tmp_path: Path,
) -> None:
    library = MediaLibrary(
        LocalMediaStorage(tmp_path / "library")
    )

    unknown_id = UUID(
        "cccccccc-cccc-cccc-cccc-cccccccccccc"
    )

    with pytest.raises(
        KeyError,
        match="Unknown media asset identifier",
    ):
        library.get(unknown_id)
