"""Supported media categories and MIME-type inference."""

from enum import StrEnum
from pathlib import Path


class MediaType(StrEnum):
    """High-level categories supported by the media library."""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    OTHER = "other"


_EXTENSION_MEDIA_TYPES: dict[str, MediaType] = {
    ".avif": MediaType.IMAGE,
    ".bmp": MediaType.IMAGE,
    ".gif": MediaType.IMAGE,
    ".heic": MediaType.IMAGE,
    ".jpeg": MediaType.IMAGE,
    ".jpg": MediaType.IMAGE,
    ".png": MediaType.IMAGE,
    ".tif": MediaType.IMAGE,
    ".tiff": MediaType.IMAGE,
    ".webp": MediaType.IMAGE,
    ".avi": MediaType.VIDEO,
    ".mkv": MediaType.VIDEO,
    ".mov": MediaType.VIDEO,
    ".mp4": MediaType.VIDEO,
    ".webm": MediaType.VIDEO,
    ".flac": MediaType.AUDIO,
    ".m4a": MediaType.AUDIO,
    ".mp3": MediaType.AUDIO,
    ".ogg": MediaType.AUDIO,
    ".wav": MediaType.AUDIO,
    ".csv": MediaType.DOCUMENT,
    ".doc": MediaType.DOCUMENT,
    ".docx": MediaType.DOCUMENT,
    ".json": MediaType.DOCUMENT,
    ".md": MediaType.DOCUMENT,
    ".ods": MediaType.DOCUMENT,
    ".odt": MediaType.DOCUMENT,
    ".pdf": MediaType.DOCUMENT,
    ".ppt": MediaType.DOCUMENT,
    ".pptx": MediaType.DOCUMENT,
    ".txt": MediaType.DOCUMENT,
    ".xls": MediaType.DOCUMENT,
    ".xlsx": MediaType.DOCUMENT,
}


def infer_media_type(path: str | Path) -> MediaType:
    """Infer a media category from a filename extension."""
    suffix = Path(path).suffix.lower()

    return _EXTENSION_MEDIA_TYPES.get(
        suffix,
        MediaType.OTHER,
    )
