"""Record imported media assets in the scientific journal."""

from ecobiome.integrations.journal.common import (
    find_linked_event,
)
from ecobiome.journal import (
    JournalEvent,
    JournalEventType,
    JournalReference,
    ScientificJournal,
)
from ecobiome.media import MediaAsset


class MediaJournalBridge:
    """Transform media-library assets into journal entries."""

    def __init__(
        self,
        journal: ScientificJournal,
    ) -> None:
        self._journal = journal

    def record_import(
        self,
        asset: MediaAsset,
    ) -> JournalEvent:
        """Record one imported asset exactly once."""
        existing = find_linked_event(
            self._journal,
            entity_type="media_asset",
            entity_id=asset.asset_id,
            event_type=JournalEventType.MEDIA,
        )

        if existing is not None:
            return existing

        occurred_at = (
            asset.metadata.captured_at
            if asset.metadata.captured_at is not None
            else asset.imported_at
        )

        return self._journal.record(
            event_type=JournalEventType.MEDIA,
            title=asset.metadata.title,
            description=asset.metadata.description,
            occurred_at=occurred_at,
            project_id=asset.project_id,
            tags=asset.metadata.tags,
            attributes=(
                (
                    "original_filename",
                    asset.original_filename,
                ),
                (
                    "media_type",
                    asset.media_type.value,
                ),
                (
                    "mime_type",
                    asset.mime_type,
                ),
            ),
            payload=(
                (
                    "asset_id",
                    str(asset.asset_id),
                ),
                (
                    "checksum_sha256",
                    asset.checksum_sha256,
                ),
                (
                    "size_bytes",
                    asset.size_bytes,
                ),
                (
                    "stored_path",
                    str(asset.stored_path),
                ),
            ),
            references=(
                JournalReference(
                    entity_type="media_asset",
                    entity_id=asset.asset_id,
                    relation="source",
                ),
            ),
        )
