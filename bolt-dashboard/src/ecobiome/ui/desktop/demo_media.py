"""Persistent media storage used by the desktop demonstration."""

from __future__ import annotations

import hashlib
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_DEMO_IMAGE_SUFFIXES = frozenset(
    {
        ".bmp",
        ".gif",
        ".jpeg",
        ".jpg",
        ".png",
        ".tif",
        ".tiff",
        ".webp",
    }
)


def is_supported_demo_image(
    path: Path,
) -> bool:
    """Return whether one path uses a supported image suffix."""
    return (
        Path(path).suffix.casefold()
        in SUPPORTED_DEMO_IMAGE_SUFFIXES
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class PersistentDemoMediaStore:
    """Copy demonstration images to a stable per-user directory."""

    directory: Path

    def __post_init__(self) -> None:
        """Normalize and create the destination directory."""
        normalized_directory = Path(
            self.directory
        )

        normalized_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        object.__setattr__(
            self,
            "directory",
            normalized_directory,
        )

    def import_files(
        self,
        source_paths: Iterable[Path],
    ) -> tuple[Path, ...]:
        """Import supported images with content-based deduplication."""
        imported_paths: list[Path] = []

        for source_path in source_paths:
            imported_paths.append(
                self.import_file(
                    Path(source_path)
                )
            )

        return tuple(imported_paths)

    def import_directory(
        self,
        source_directory: Path,
    ) -> tuple[Path, ...]:
        """Import supported images found directly in one directory."""
        directory = Path(
            source_directory
        )

        if not directory.is_dir():
            return ()

        source_paths = tuple(
            candidate
            for candidate in sorted(
                directory.rglob("*"),
                key=lambda path: (
                    str(
                        path.relative_to(
                            directory
                        )
                    ).casefold()
                ),
            )
            if (
                candidate.is_file()
                and is_supported_demo_image(candidate)
            )
        )

        return self.import_files(
            source_paths
        )

    def import_file(
        self,
        source_path: Path,
    ) -> Path:
        """Import one image atomically and return its stable path."""
        source = Path(
            source_path
        )

        if not source.is_file():
            raise FileNotFoundError(
                f"Image source not found: {source}"
            )

        if not is_supported_demo_image(source):
            raise ValueError(
                f"Unsupported image format: {source.suffix}"
            )

        digest = self._sha256(
            source
        )

        safe_stem = self._safe_stem(
            source.stem
        )

        destination = self.directory / (
            f"{safe_stem}-{digest[:12]}"
            f"{source.suffix.casefold()}"
        )

        if destination.is_file():
            return destination

        temporary_path = destination.with_name(
            f"{destination.name}.tmp"
        )

        try:
            shutil.copy2(
                source,
                temporary_path,
            )

            temporary_path.replace(
                destination
            )

        finally:
            if temporary_path.exists():
                temporary_path.unlink()

        return destination

    @staticmethod
    def _sha256(
        path: Path,
    ) -> str:
        """Return the SHA-256 digest of one file."""
        digest = hashlib.sha256()

        with path.open("rb") as stream:
            for block in iter(
                lambda: stream.read(1024 * 1024),
                b"",
            ):
                digest.update(block)

        return digest.hexdigest()

    @staticmethod
    def _safe_stem(
        stem: str,
    ) -> str:
        """Return a filesystem-friendly deterministic filename stem."""
        normalized = "".join(
            character
            if (
                character.isalnum()
                or character in {"-", "_"}
            )
            else "-"
            for character in stem.strip()
        )

        compact = "-".join(
            part
            for part in normalized.split("-")
            if part
        )

        return (
            compact[:80]
            if compact
            else "image"
        )
