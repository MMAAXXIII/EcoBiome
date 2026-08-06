"""Presentation-ready media gallery for EcoBiome interfaces."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

_SUPPORTED_IMAGE_SUFFIXES = frozenset(
    {
        ".bmp",
        ".gif",
        ".jpeg",
        ".jpg",
        ".png",
        ".ppm",
        ".tif",
        ".tiff",
        ".webp",
    }
)


_HASH_ONLY_STEM = re.compile(
    r"^[0-9a-f]{24,}$",
    re.IGNORECASE,
)
_HASH_SUFFIX = re.compile(
    r"[-_][0-9a-f]{12}$",
    re.IGNORECASE,
)


def readable_media_title(
    path: Path,
) -> str | None:
    """Return a human title, excluding storage hashes."""
    stem = _HASH_SUFFIX.sub(
        "",
        Path(path).stem,
    )
    compact_stem = re.sub(
        r"[^0-9a-f]",
        "",
        stem,
        flags=re.IGNORECASE,
    )

    if (
        _HASH_ONLY_STEM.fullmatch(stem)
        or (
            len(compact_stem) >= 24
            and compact_stem.casefold()
            == stem.casefold()
        )
    ):
        return None

    title = re.sub(
        r"[_-]+",
        " ",
        stem,
    )
    title = " ".join(
        title.split()
    ).strip()

    if not title:
        return None

    return title.title()


@dataclass(frozen=True, slots=True, kw_only=True)
class MediaGalleryItem:
    """Describe one image displayed by an EcoBiome gallery."""

    path: Path
    title: str
    captured_at: datetime
    size_bytes: int
    suffix: str

    def __post_init__(self) -> None:
        """Validate and normalize one gallery item."""
        path = Path(self.path)
        title = self.title.strip()
        suffix = self.suffix.strip().lower()

        if not path.is_file():
            raise FileNotFoundError(
                f"Gallery image does not exist: {path}."
            )

        if not title:
            raise ValueError(
                "Gallery image title cannot be empty."
            )

        if self.captured_at.tzinfo is None:
            raise ValueError(
                "Gallery timestamps must be timezone-aware."
            )

        if self.size_bytes < 0:
            raise ValueError(
                "Gallery image size cannot be negative."
            )

        if suffix not in _SUPPORTED_IMAGE_SUFFIXES:
            raise ValueError(
                f"Unsupported gallery image suffix: {suffix}."
            )

        object.__setattr__(
            self,
            "path",
            path,
        )

        object.__setattr__(
            self,
            "title",
            title,
        )

        object.__setattr__(
            self,
            "suffix",
            suffix,
        )

    @property
    def date_label(self) -> str:
        """Return a compact French date label."""
        return self.captured_at.strftime(
            "%d/%m/%Y · %H:%M"
        )

    @property
    def size_label(self) -> str:
        """Return a human-readable file size."""
        if self.size_bytes < 1024:
            return f"{self.size_bytes} o"

        kibibytes = self.size_bytes / 1024

        if kibibytes < 1024:
            return f"{kibibytes:.1f} Kio"

        mebibytes = kibibytes / 1024

        return f"{mebibytes:.1f} Mio"


def build_media_gallery(
    directory: str | Path,
    *,
    limit: int = 8,
) -> tuple[MediaGalleryItem, ...]:
    """Build a newest-first gallery from one media directory."""
    if limit < 0:
        raise ValueError(
            "Gallery item limit cannot be negative."
        )

    if limit == 0:
        return ()

    root = Path(directory)

    if not root.exists():
        return ()

    if not root.is_dir():
        raise NotADirectoryError(
            f"Gallery source is not a directory: {root}."
        )

    candidates: list[
        tuple[
            datetime,
            str,
            Path,
            int,
            str,
            str | None,
        ]
    ] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        suffix = path.suffix.lower()

        if suffix not in _SUPPORTED_IMAGE_SUFFIXES:
            continue

        statistics = path.stat()

        captured_at = datetime.fromtimestamp(
            statistics.st_mtime,
            tz=UTC,
        )

        candidates.append(
            (
                captured_at,
                path.name.casefold(),
                path,
                statistics.st_size,
                suffix,
                readable_media_title(path),
            )
        )

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
        ),
        reverse=True,
    )

    items: list[MediaGalleryItem] = []

    for index, (
        captured_at,
        _sort_name,
        path,
        size_bytes,
        suffix,
        readable_title,
    ) in enumerate(
        candidates[:limit],
        start=1,
    ):
        items.append(
            MediaGalleryItem(
                path=path,
                title=(
                    readable_title
                    or f"Image du projet {index}"
                ),
                captured_at=captured_at,
                size_bytes=size_bytes,
                suffix=suffix,
            )
        )

    return tuple(items)
