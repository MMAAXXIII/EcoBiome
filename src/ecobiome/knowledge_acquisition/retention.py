"""Retention policy and dry-run CAS garbage-collection planning."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path


class GcPolicyError(RuntimeError):
    """Retention / garbage-collection safety policy violation."""


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    """Minimum safe Collector retention policy for Sprint A."""

    gc_enabled: bool = False
    minimum_orphan_age_seconds: int = 0


@dataclass(frozen=True, slots=True)
class GcCandidate:
    """One unreferenced content-addressed file eligible for review."""

    storage_relpath: str
    sha256: str
    size_bytes: int
    reason: str


@dataclass(frozen=True, slots=True)
class GcPlan:
    """Dry-run garbage-collection plan."""

    candidates: tuple[GcCandidate, ...]
    protected_artifact_count: int
    orphan_file_count: int
    total_candidate_bytes: int


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _cas_inventory(root: Path) -> dict[str, tuple[str, int]]:
    if not root.exists():
        return {}

    return {
        str(path.relative_to(root)).replace("\\", "/"): (
            _sha256_file(path),
            path.stat().st_size,
        )
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _table_columns(
    connection: sqlite3.Connection,
    table: str,
) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM pragma_table_info(?)",
            (table,),
        )
    }


def _cas_relpath_from_store_key(store_key: object) -> str:
    key = str(store_key)
    prefix = "sha256:"
    if not key.startswith(prefix):
        raise GcPolicyError(f"Unsupported CAS artifact_store_key: {key}")
    digest = key[len(prefix) :]
    if len(digest) != 64 or any(
        character not in "0123456789abcdef"
        for character in digest
    ):
        raise GcPolicyError(f"Malformed SHA-256 CAS key: {key}")
    return f"sha256/{digest[:2]}/{digest[2:4]}/{digest}.blob"


def _database_referenced_artifacts(
    connection: sqlite3.Connection,
) -> set[str]:
    raw_columns = _table_columns(connection, "raw_artifacts")
    if "storage_relpath" in raw_columns:
        return {
            str(row[0]).replace("\\", "/")
            for row in connection.execute(
                "SELECT storage_relpath FROM raw_artifacts"
            )
        }

    if "artifact_store_key" not in raw_columns:
        raise GcPolicyError(
            "Unsupported Collector raw_artifacts storage contract."
        )

    store_keys = {
        str(row[0])
        for row in connection.execute(
            """
            SELECT artifact_store_key
            FROM raw_artifacts
            WHERE artifact_store_key IS NOT NULL
            """
        )
    }
    representation_columns = _table_columns(connection, "representations")
    if "artifact_store_key" not in representation_columns:
        raise GcPolicyError(
            "Schema V4 raw artifacts detected without representation CAS keys."
        )
    store_keys |= {
        str(row[0])
        for row in connection.execute(
            """
            SELECT artifact_store_key
            FROM representations
            WHERE artifact_store_key IS NOT NULL
            """
        )
    }
    return {
        _cas_relpath_from_store_key(store_key)
        for store_key in store_keys
    }


def build_gc_plan(
    *,
    database_path: str | Path,
    artifact_directory: str | Path,
    policy: RetentionPolicy | None = None,
) -> GcPlan:
    """Return a dry-run plan; every database-referenced artifact is protected."""
    active_policy = policy or RetentionPolicy()
    database = Path(database_path).expanduser().resolve()
    artifacts = Path(artifact_directory).expanduser().resolve()

    if not database.is_file():
        raise FileNotFoundError(database)

    inventory = _cas_inventory(artifacts)

    with sqlite3.connect(database) as connection:
        referenced = _database_referenced_artifacts(connection)

    candidates: list[GcCandidate] = []
    orphan_count = 0

    for relpath, (sha256, size_bytes) in sorted(inventory.items()):
        if relpath in referenced:
            continue

        orphan_count += 1
        path = artifacts / relpath
        if active_policy.minimum_orphan_age_seconds > 0:
            import time

            age_seconds = max(0.0, time.time() - path.stat().st_mtime)
            if age_seconds < active_policy.minimum_orphan_age_seconds:
                continue

        candidates.append(
            GcCandidate(
                storage_relpath=relpath,
                sha256=sha256,
                size_bytes=size_bytes,
                reason="unreferenced_cas_object",
            )
        )

    return GcPlan(
        candidates=tuple(candidates),
        protected_artifact_count=len(referenced),
        orphan_file_count=orphan_count,
        total_candidate_bytes=sum(
            candidate.size_bytes for candidate in candidates
        ),
    )


def write_gc_plan(
    path: str | Path,
    plan: GcPlan,
) -> None:
    """Atomically write an auditable dry-run GC plan."""
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    payload = {
        "mode": "dry-run",
        "deletion_performed": False,
        "candidates": [asdict(candidate) for candidate in plan.candidates],
        "protected_artifact_count": plan.protected_artifact_count,
        "orphan_file_count": plan.orphan_file_count,
        "total_candidate_bytes": plan.total_candidate_bytes,
    }
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(destination)


def execute_gc(*, policy: RetentionPolicy | None = None) -> None:
    """Refuse production deletion during Sprint A."""
    active_policy = policy or RetentionPolicy()
    if not active_policy.gc_enabled:
        raise GcPolicyError("Collector GC is disabled by default.")
    raise GcPolicyError(
        "Collector production GC execution is not implemented in Sprint A; "
        "use build_gc_plan() dry-run only."
    )
