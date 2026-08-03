"""Searchable, immutable-index media library."""

from __future__ import annotations

import mimetypes
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from uuid import UUID

from ecobiome.media.asset import MediaAsset
from ecobiome.media.checksum import calculate_sha256
from ecobiome.media.media_type import (
    MediaType,
    infer_media_type,
)
from ecobiome.media.metadata import MediaMetadata
from ecobiome.media.storage import LocalMediaStorage


class DuplicateMediaError(ValueError):
    """Raised when an identical file already exists in the library."""


class MediaLibrary:
    """Manage indexed media assets and immutable source storage."""

    def __init__(
        self,
        storage: LocalMediaStorage,
        assets: Iterable[MediaAsset] = (),
    ) -> None:
        self._storage = storage
        self._assets_by_id: dict[UUID, MediaAsset] = {}
        self._asset_ids_by_checksum: dict[str, UUID] = {}

        for asset in assets:
            self.add(asset)

    @property
    def storage(self) -> LocalMediaStorage:
        """Return the configured media storage."""
        return self._storage

    def add(self, asset: MediaAsset) -> None:
        """Index one existing media asset."""
        if asset.asset_id in self._assets_by_id:
            raise ValueError(
                f"Duplicate media asset identifier: "
                f"{asset.asset_id}."
            )

        if (
            asset.checksum_sha256
            in self._asset_ids_by_checksum
        ):
            raise DuplicateMediaError(
                "An identical media file already exists "
                f"in the library: {asset.checksum_sha256}."
            )

        self._assets_by_id[asset.asset_id] = asset
        self._asset_ids_by_checksum[
            asset.checksum_sha256
        ] = asset.asset_id

    def import_file(
        self,
        source: str | Path,
        *,
        metadata: MediaMetadata,
        project_id: UUID | None = None,
        related_entity_ids: tuple[UUID, ...] = (),
        mime_type: str | None = None,
    ) -> MediaAsset:
        """Import and index one immutable media source file."""
        source_path = Path(source)

        if not source_path.is_file():
            raise FileNotFoundError(
                f"Media source file does not exist: "
                f"{source_path}."
            )

        checksum = calculate_sha256(source_path)

        if checksum in self._asset_ids_by_checksum:
            existing_id = self._asset_ids_by_checksum[
                checksum
            ]

            raise DuplicateMediaError(
                "An identical media file already exists "
                f"in the library as asset {existing_id}."
            )

        detected_mime_type = (
            mime_type.strip().lower()
            if mime_type is not None
            else (
                mimetypes.guess_type(source_path.name)[0]
                or "application/octet-stream"
            )
        )

        if not detected_mime_type:
            raise ValueError(
                "Media MIME type cannot be empty."
            )

        stored_path = self._storage.store(
            source_path,
            checksum_sha256=checksum,
        )

        asset = MediaAsset(
            original_filename=source_path.name,
            stored_path=stored_path,
            checksum_sha256=checksum,
            size_bytes=source_path.stat().st_size,
            media_type=infer_media_type(source_path),
            mime_type=detected_mime_type,
            metadata=metadata,
            project_id=project_id,
            related_entity_ids=related_entity_ids,
        )

        self.add(asset)

        return asset

    def get(self, asset_id: UUID) -> MediaAsset:
        """Return one media asset by identifier."""
        try:
            return self._assets_by_id[asset_id]
        except KeyError as error:
            raise KeyError(
                f"Unknown media asset identifier: {asset_id}."
            ) from error

    def all(self) -> tuple[MediaAsset, ...]:
        """Return all assets in deterministic import order."""
        return tuple(
            sorted(
                self._assets_by_id.values(),
                key=lambda asset: (
                    asset.imported_at,
                    str(asset.asset_id),
                ),
            )
        )

    def search(
        self,
        *,
        media_type: MediaType | None = None,
        tags: tuple[str, ...] = (),
        project_id: UUID | None = None,
        captured_from: datetime | None = None,
        captured_to: datetime | None = None,
        text: str = "",
    ) -> tuple[MediaAsset, ...]:
        """Search assets using cumulative filters."""
        if (
            captured_from is not None
            and captured_from.tzinfo is None
        ):
            raise ValueError(
                "Search start timestamp must be timezone-aware."
            )

        if (
            captured_to is not None
            and captured_to.tzinfo is None
        ):
            raise ValueError(
                "Search end timestamp must be timezone-aware."
            )

        if (
            captured_from is not None
            and captured_to is not None
            and captured_from > captured_to
        ):
            raise ValueError(
                "Search start timestamp cannot follow its end."
            )

        normalized_tags = {
            tag.strip().lower()
            for tag in tags
            if tag.strip()
        }

        normalized_text = text.strip().casefold()

        results: list[MediaAsset] = []

        for asset in self.all():
            if (
                media_type is not None
                and asset.media_type is not media_type
            ):
                continue

            if (
                project_id is not None
                and asset.project_id != project_id
            ):
                continue

            if not normalized_tags.issubset(
                set(asset.metadata.tags)
            ):
                continue

            captured_at = asset.metadata.captured_at

            if (
                captured_from is not None
                and (
                    captured_at is None
                    or captured_at < captured_from
                )
            ):
                continue

            if (
                captured_to is not None
                and (
                    captured_at is None
                    or captured_at > captured_to
                )
            ):
                continue

            if normalized_text:
                searchable_text = " ".join(
                    (
                        asset.metadata.title,
                        asset.metadata.description,
                        asset.original_filename,
                        *asset.metadata.tags,
                    )
                ).casefold()

                if normalized_text not in searchable_text:
                    continue

            results.append(asset)

        return tuple(results)

    def count(self) -> int:
        """Return the number of indexed assets."""
        return len(self._assets_by_id)
