"""Filesystem SHA-256 content-addressed artifact store."""
from __future__ import annotations

import hashlib
import os
import re
import uuid
from pathlib import Path

from .contracts import StoredArtifact
from .errors import ArtifactCorruptionError, ArtifactMissingError

_HEX64=re.compile(r"^[0-9a-f]{64}$")
class FilesystemContentAddressedArtifactStore:
    def __init__(self, root: Path) -> None: self._root=root.resolve()
    @property
    def root(self) -> Path: return self._root
    def _digest_from_key(self,key:str)->str:
        if not key.startswith("sha256:"): raise ArtifactMissingError("Unsupported artifact key")
        digest=key[7:]
        if _HEX64.fullmatch(digest) is None: raise ArtifactMissingError("Malformed artifact key")
        return digest
    def _path(self,digest:str)->Path:
        if _HEX64.fullmatch(digest) is None: raise ArtifactMissingError("Malformed digest")
        return self._root/"sha256"/digest[:2]/digest[2:4]/f"{digest}.blob"
    def put(self,data:bytes)->StoredArtifact:
        digest=hashlib.sha256(data).hexdigest(); final=self._path(digest)
        if final.exists():
            if final.is_symlink(): raise ArtifactCorruptionError("CAS target is symlink")
            existing=final.read_bytes()
            if hashlib.sha256(existing).hexdigest()!=digest: raise ArtifactCorruptionError("Existing CAS corruption")
            return StoredArtifact(f"sha256:{digest}",digest,len(existing))
        tmp_root=self._root/".tmp"; tmp_root.mkdir(parents=True,exist_ok=True); final.parent.mkdir(parents=True,exist_ok=True)
        tmp=tmp_root/f"{uuid.uuid4()}.part"
        try:
            with tmp.open("xb") as f: f.write(data); f.flush(); os.fsync(f.fileno())
            if hashlib.sha256(tmp.read_bytes()).hexdigest()!=digest: raise ArtifactCorruptionError("Temporary CAS hash mismatch")
            os.replace(tmp,final)
        finally:
            if tmp.exists(): tmp.unlink()
        if final.is_symlink() or hashlib.sha256(final.read_bytes()).hexdigest()!=digest: raise ArtifactCorruptionError("Final CAS hash mismatch")
        return StoredArtifact(f"sha256:{digest}",digest,len(data))
    def get(self,key:str)->bytes:
        digest=self._digest_from_key(key); path=self._path(digest)
        if not path.is_file() or path.is_symlink(): raise ArtifactMissingError(f"Artifact not found: {key}")
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=digest: raise ArtifactCorruptionError("Artifact hash mismatch")
        return data
    def verify(self,key:str)->StoredArtifact:
        digest=self._digest_from_key(key); data=self.get(key)
        return StoredArtifact(key,digest,len(data))
