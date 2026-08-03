"""Immutable references to media managed by EcoBiome."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from ecobiome.media.media_type import MediaType
from ecobiome.media.metadata import MediaMetadata


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True, kw_only=True)
class MediaAsset:
    """Describe one immutable file managed by the media library."""

    original_filename: str
    stored_path: Path
    checksum_sha256: str
    size_bytes: int
    media_type: MediaType
    mime_type: str
    metadata: MediaMetadata
    asset_id: UUID = field(default_factory=uuid4)
    imported_at: datetime = field(default_factory=utc_now)
    project_id: UUID | None = None
    related_entity_ids: tuple[UUID, ...] = ()

    def __post_init__(self) -> None:
        """Validate and normalize one media asset."""
        original_filename = self.original_filename.strip()
        checksum = self.checksum_sha256.strip().lower()
        mime_type = self.mime_type.strip().lower()

        if not original_filename:
            raise ValueError(
                "Original media filename cannot be empty."
            )

        if len(checksum) != 64:
            raise ValueError(
                "Media SHA-256 checksum must contain 64 characters."
            )

        try:
            int(checksum, 16)
        except ValueError as error:
            raise ValueError(
                "Media SHA-256 checksum must be hexadecimal."
            ) from error

        if self.size_bytes < 0:
            raise ValueError(
                "Media file size cannot be negative."
            )

        if not mime_type:
            raise ValueError(
                "Media MIME type cannot be empty."
            )

        if self.imported_at.tzinfo is None:
            raise ValueError(
                "Media import timestamp must be timezone-aware."
            )

        related_entity_ids = tuple(
            dict.fromkeys(self.related_entity_ids)
        )

        object.__setattr__(
            self,
            "original_filename",
            original_filename,
        )
        object.__setattr__(
            self,
            "stored_path",
            Path(self.stored_path),
        )
        object.__setattr__(
            self,
            "checksum_sha256",
            checksum,
        )
        object.__setattr__(
            self,
            "mime_type",
            mime_type,
        )
        object.__setattr__(
            self,
            "related_entity_ids",
            related_entity_ids,
        )

    @property
    def extension(self) -> str:
        """Return the normalized original extension."""
        return Path(self.original_filename).suffix.lower()
