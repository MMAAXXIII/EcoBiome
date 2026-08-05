"""Media-library foundation for EcoBiome projects."""

from ecobiome.media.asset import MediaAsset
from ecobiome.media.checksum import calculate_sha256
from ecobiome.media.library import (
    DuplicateMediaError,
    MediaLibrary,
)
from ecobiome.media.media_type import (
    MediaType,
    infer_media_type,
)
from ecobiome.media.metadata import MediaMetadata
from ecobiome.media.storage import LocalMediaStorage

__all__ = [
    "DuplicateMediaError",
    "LocalMediaStorage",
    "MediaAsset",
    "MediaLibrary",
    "MediaMetadata",
    "MediaType",
    "calculate_sha256",
    "infer_media_type",
]
