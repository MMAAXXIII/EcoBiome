"""Filesystem layout of one EcoBiome project workspace."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProjectWorkspaceLayout:
    """Expose deterministic paths inside one project workspace."""

    root: Path

    def __post_init__(self) -> None:
        """Normalize the workspace root."""
        object.__setattr__(
            self,
            "root",
            Path(self.root),
        )

    @property
    def manifest_path(self) -> Path:
        """Return the project-manifest path."""
        return self.root / "workspace.json"

    @property
    def journal_directory(self) -> Path:
        """Return the persistent-journal directory."""
        return self.root / "journal"

    @property
    def journal_path(self) -> Path:
        """Return the JSONL journal path."""
        return self.journal_directory / "events.jsonl"

    @property
    def media_directory(self) -> Path:
        """Return the immutable-media directory."""
        return self.root / "media"

    @property
    def media_index_path(self) -> Path:
        """Return the persistent media-index path."""
        return self.root / "media-index.json"

    @property
    def exports_directory(self) -> Path:
        """Return the future generated-export directory."""
        return self.root / "exports"

    @property
    def cache_directory(self) -> Path:
        """Return the local derived-data cache directory."""
        return self.root / ".cache"

    def create_directories(self) -> None:
        """Create every required workspace directory."""
        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

        for directory in (
            self.journal_directory,
            self.media_directory,
            self.exports_directory,
            self.cache_directory,
        ):
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )
