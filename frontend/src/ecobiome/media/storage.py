"""Local immutable storage for media-library source files."""

from pathlib import Path
from shutil import copy2


class LocalMediaStorage:
    """Copy source files into checksum-addressed local storage."""

    def __init__(
        self,
        root: str | Path,
    ) -> None:
        self._root = Path(root)
        self._root.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self._root.is_dir():
            raise ValueError(
                f"Media storage root is not a directory: "
                f"{self._root}."
            )

    @property
    def root(self) -> Path:
        """Return the local media-storage root."""
        return self._root

    def destination_for(
        self,
        *,
        checksum_sha256: str,
        original_filename: str,
    ) -> Path:
        """Return the deterministic destination of one file."""
        checksum = checksum_sha256.strip().lower()

        if len(checksum) != 64:
            raise ValueError(
                "Storage checksum must contain 64 characters."
            )

        suffix = Path(original_filename).suffix.lower()
        directory = (
            self._root
            / checksum[:2]
            / checksum[2:4]
        )

        return directory / f"{checksum}{suffix}"

    def store(
        self,
        source: str | Path,
        *,
        checksum_sha256: str,
    ) -> Path:
        """Copy one source file without modifying the original."""
        source_path = Path(source)

        if not source_path.is_file():
            raise FileNotFoundError(
                f"Media source file does not exist: "
                f"{source_path}."
            )

        destination = self.destination_for(
            checksum_sha256=checksum_sha256,
            original_filename=source_path.name,
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if destination.exists():
            return destination

        copy2(source_path, destination)

        return destination
