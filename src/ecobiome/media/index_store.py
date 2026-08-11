"""Versioned JSON persistence for media-library indexes."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from ecobiome.media.asset import MediaAsset
from ecobiome.media.media_type import MediaType
from ecobiome.media.metadata import MediaMetadata

MEDIA_INDEX_SCHEMA_VERSION = 1


def _relative_stored_path(asset: MediaAsset, storage_root: Path) -> str:
    """Return one stored path relative to its media root."""
    try:
        relative_path = asset.stored_path.resolve().relative_to(
            storage_root.resolve()
        )
    except ValueError as error:
        raise ValueError(
            "Indexed media assets must be stored under the media root."
        ) from error

    return relative_path.as_posix()


def media_asset_to_dict(
    asset: MediaAsset,
    *,
    storage_root: Path,
) -> dict[str, Any]:
    """Convert one media asset into JSON-compatible primitives."""
    metadata = asset.metadata

    return {
        "asset_id": str(asset.asset_id),
        "original_filename": asset.original_filename,
        "stored_path": _relative_stored_path(asset, storage_root),
        "checksum_sha256": asset.checksum_sha256,
        "size_bytes": asset.size_bytes,
        "media_type": asset.media_type.value,
        "mime_type": asset.mime_type,
        "metadata": {
            "title": metadata.title,
            "description": metadata.description,
            "captured_at": (
                metadata.captured_at.isoformat()
                if metadata.captured_at is not None
                else None
            ),
            "tags": list(metadata.tags),
            "attributes": [
                [key, value]
                for key, value in metadata.attributes
            ],
        },
        "imported_at": asset.imported_at.isoformat(),
        "project_id": (
            str(asset.project_id)
            if asset.project_id is not None
            else None
        ),
        "related_entity_ids": [
            str(entity_id)
            for entity_id in asset.related_entity_ids
        ],
    }


def _decode_string_list(value: object, field_name: str) -> tuple[str, ...]:
    """Decode one JSON string array."""
    if not isinstance(value, list):
        raise TypeError(f"Media index field {field_name!r} must be an array.")

    items: list[str] = []

    for item in value:
        if not isinstance(item, str):
            raise TypeError(
                f"Media index field {field_name!r} must contain only strings."
            )

        items.append(item)

    return tuple(items)


def _decode_attributes(value: object) -> tuple[tuple[str, str], ...]:
    """Decode ordered media metadata attributes."""
    if not isinstance(value, list):
        raise TypeError("Media metadata attributes must be an array.")

    attributes: list[tuple[str, str]] = []

    for item in value:
        if not isinstance(item, list) or len(item) != 2:
            raise TypeError(
                "Media metadata attributes must contain two-item arrays."
            )

        attributes.append((str(item[0]), str(item[1])))

    return tuple(attributes)


def _decode_relative_path(value: object) -> Path:
    """Decode a safe path relative to the media storage root."""
    if not isinstance(value, str) or not value.strip():
        raise TypeError("Media index stored_path must be a non-empty string.")

    relative_path = Path(value)

    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("Media index stored_path must remain inside media root.")

    return relative_path


def media_asset_from_dict(
    payload: dict[str, Any],
    *,
    storage_root: Path,
) -> MediaAsset:
    """Rebuild one media asset from a validated index record."""
    raw_metadata = payload.get("metadata")

    if not isinstance(raw_metadata, dict):
        raise TypeError("Media index metadata must be an object.")

    raw_captured_at = raw_metadata.get("captured_at")
    captured_at = (
        None
        if raw_captured_at is None
        else datetime.fromisoformat(str(raw_captured_at))
    )

    raw_project_id = payload.get("project_id")
    project_id = (
        None
        if raw_project_id is None
        else UUID(str(raw_project_id))
    )

    relative_path = _decode_relative_path(payload.get("stored_path"))
    stored_path = storage_root / relative_path

    if not stored_path.is_file():
        raise FileNotFoundError(
            f"Indexed media file does not exist: {stored_path}."
        )

    asset = MediaAsset(
        asset_id=UUID(str(payload["asset_id"])),
        original_filename=str(payload["original_filename"]),
        stored_path=stored_path,
        checksum_sha256=str(payload["checksum_sha256"]),
        size_bytes=int(payload["size_bytes"]),
        media_type=MediaType(str(payload["media_type"])),
        mime_type=str(payload["mime_type"]),
        metadata=MediaMetadata(
            title=str(raw_metadata["title"]),
            description=str(raw_metadata.get("description", "")),
            captured_at=captured_at,
            tags=_decode_string_list(raw_metadata.get("tags", []), "tags"),
            attributes=_decode_attributes(raw_metadata.get("attributes", [])),
        ),
        imported_at=datetime.fromisoformat(str(payload["imported_at"])),
        project_id=project_id,
        related_entity_ids=tuple(
            UUID(raw_id)
            for raw_id in _decode_string_list(
                payload.get("related_entity_ids", []),
                "related_entity_ids",
            )
        ),
    )

    if stored_path.stat().st_size != asset.size_bytes:
        raise ValueError(
            f"Indexed media file size differs from the index: {stored_path}."
        )

    return asset


def write_media_index(
    path: str | Path,
    assets: tuple[MediaAsset, ...],
    *,
    storage_root: Path,
) -> None:
    """Write the complete media index atomically."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")

    serialized = json.dumps(
        {
            "schema_version": MEDIA_INDEX_SCHEMA_VERSION,
            "assets": [
                media_asset_to_dict(asset, storage_root=storage_root)
                for asset in assets
            ],
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )

    temporary.write_text(serialized + "\n", encoding="utf-8")
    temporary.replace(destination)


def read_media_index(
    path: str | Path,
    *,
    storage_root: Path,
) -> tuple[MediaAsset, ...]:
    """Load and validate one persistent media index."""
    source = Path(path)

    if not source.exists():
        return ()

    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid media index JSON: {error.msg}.") from error

    if not isinstance(payload, dict):
        raise TypeError("Media index must contain a JSON object.")

    if payload.get("schema_version") != MEDIA_INDEX_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported media index schema version: "
            f"{payload.get('schema_version')!r}."
        )

    raw_assets = payload.get("assets")

    if not isinstance(raw_assets, list):
        raise TypeError("Media index assets must be an array.")

    assets: list[MediaAsset] = []

    for raw_asset in raw_assets:
        if not isinstance(raw_asset, dict):
            raise TypeError("Each media index asset must be an object.")

        try:
            assets.append(
                media_asset_from_dict(
                    cast(dict[str, Any], raw_asset),
                    storage_root=storage_root,
                )
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Invalid media index asset: {error}.") from error

    return tuple(assets)
