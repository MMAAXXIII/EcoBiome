from pathlib import Path

import pytest

from ecobiome.knowledge_persistence.artifact_store import (
    FilesystemContentAddressedArtifactStore,
)
from ecobiome.knowledge_persistence.errors import ArtifactMissingError


def test_cas_duplicate_put_is_idempotent(tmp_path: Path) -> None:
    store=FilesystemContentAddressedArtifactStore(tmp_path/"cas")
    first=store.put(b"abc"); second=store.put(b"abc")
    assert first == second
    assert store.get(first.key) == b"abc"


def test_missing_key_is_rejected(tmp_path: Path) -> None:
    store=FilesystemContentAddressedArtifactStore(tmp_path/"cas")
    with pytest.raises(ArtifactMissingError): store.get("sha256:"+"0"*64)
