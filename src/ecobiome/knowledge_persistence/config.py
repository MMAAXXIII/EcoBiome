"""Validated persistence configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import PersistenceConfigurationError


def _within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


@dataclass(frozen=True, slots=True)
class PersistenceConfig:
    database_path: Path
    artifact_store_root: Path
    journal_mode: str = "DELETE"
    synchronous: str = "FULL"
    foreign_keys_required: bool = True

    def validated(self, repo_root: Path) -> PersistenceConfig:
        repo=repo_root.resolve()
        db=self.database_path.resolve()
        cas=self.artifact_store_root.resolve()
        if _within(db, repo) or _within(cas, repo):
            raise PersistenceConfigurationError("DB/CAS must remain outside Git repository")
        if db == cas or _within(db, cas):
            raise PersistenceConfigurationError("DB path must not alias CAS root")
        if self.journal_mode.upper() != "DELETE" or self.synchronous.upper() != "FULL":
            raise PersistenceConfigurationError("V1 requires DELETE/FULL SQLite durability")
        if not self.foreign_keys_required:
            raise PersistenceConfigurationError("V1 requires foreign keys")
        return self
