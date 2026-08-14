"""Cryptographic checksums for immutable media files."""

from hashlib import sha256
from pathlib import Path

DEFAULT_CHUNK_SIZE = 1024 * 1024


def calculate_sha256(
    path: str | Path,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> str:
    """Calculate the hexadecimal SHA-256 digest of one file."""
    source = Path(path)

    if not source.is_file():
        raise FileNotFoundError(
            f"Media source file does not exist: {source}."
        )

    if chunk_size <= 0:
        raise ValueError(
            "Checksum chunk size must be positive."
        )

    digest = sha256()

    with source.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()
