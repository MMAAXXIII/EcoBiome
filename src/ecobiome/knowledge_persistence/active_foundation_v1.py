"""Read-only active Scientific Foundation pointer and resolver V1.

RATE-3K intentionally contains no persistent pointer writer.  The module can
construct canonical pointer documents in memory and resolve either the frozen
legacy root or an already-published immutable snapshot.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .errors import PersistenceConfigurationError, PersistenceIntegrityError

ACTIVE_POINTER_SCHEMA_V1 = "ecobiome-active-scientific-foundation-pointer-v1"
SNAPSHOT_MANIFEST_SCHEMA_V1 = (
    "ecobiome-scientific-foundation-snapshot-manifest-v1-reviewed"
)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_hex64(value: object, *, field: str) -> str:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise PersistenceIntegrityError(f"{field} must be a lowercase SHA-256")
    return value


def _require_aware_timestamp(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise PersistenceIntegrityError(f"{field} must be a non-empty timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise PersistenceIntegrityError(f"{field} is not ISO-8601") from exc
    if parsed.tzinfo is None:
        raise PersistenceIntegrityError(f"{field} must be timezone-aware")
    return value


def _require_mapping(value: object, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PersistenceIntegrityError(f"{label} must be an object")
    return value


def _require_exact_keys(
    value: Mapping[str, Any],
    expected: set[str],
    *,
    label: str,
) -> None:
    observed = set(value)
    if observed != expected:
        raise PersistenceIntegrityError(
            f"{label} keys mismatch: {sorted(observed)} != {sorted(expected)}"
        )


def _is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(callable(is_junction) and is_junction())


def _reject_link_like(path: Path, *, label: str) -> None:
    if _is_link_like(path):
        raise PersistenceConfigurationError(f"{label} must not be a link/junction")


def _read_json_object(path: Path, *, label: str) -> Mapping[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PersistenceIntegrityError(f"{label} cannot be decoded") from exc
    return _require_mapping(parsed, label=label)


@dataclass(frozen=True, slots=True)
class ActiveScientificFoundationPointerV1:
    snapshot_database_sha256: str
    snapshot_manifest_file_sha256: str
    snapshot_manifest_payload_sha256: str
    parent_database_sha256: str
    activation_authorization_payload_sha256: str
    created_at: str

    def payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": ACTIVE_POINTER_SCHEMA_V1,
            "snapshot_database_sha256": self.snapshot_database_sha256,
            "snapshot_manifest_file_sha256": self.snapshot_manifest_file_sha256,
            "snapshot_manifest_payload_sha256": (
                self.snapshot_manifest_payload_sha256
            ),
            "parent_database_sha256": self.parent_database_sha256,
            "activation_authorization_payload_sha256": (
                self.activation_authorization_payload_sha256
            ),
            "created_at": self.created_at,
        }
        _validate_pointer_payload(payload)
        return payload


@dataclass(frozen=True, slots=True)
class ResolvedScientificFoundationV1:
    resolution_mode: str
    database_path: Path
    database_sha256: str
    schema_version: int
    schema_design_sha256: str
    snapshot_manifest_path: Path | None
    snapshot_manifest_file_sha256: str | None
    snapshot_manifest_payload_sha256: str | None
    pointer_payload_sha256: str | None
    activation_authorization_payload_sha256: str | None


def build_active_pointer_document(
    pointer: ActiveScientificFoundationPointerV1,
) -> dict[str, object]:
    payload = pointer.payload()
    return {
        "pointer_payload_sha256": canonical_sha256(payload),
        "pointer_payload": payload,
    }


def _validate_pointer_payload(payload: Mapping[str, Any]) -> None:
    expected = {
        "schema_version",
        "snapshot_database_sha256",
        "snapshot_manifest_file_sha256",
        "snapshot_manifest_payload_sha256",
        "parent_database_sha256",
        "activation_authorization_payload_sha256",
        "created_at",
    }
    _require_exact_keys(payload, expected, label="active pointer payload")
    if payload["schema_version"] != ACTIVE_POINTER_SCHEMA_V1:
        raise PersistenceIntegrityError("Unsupported active pointer schema")
    for field in (
        "snapshot_database_sha256",
        "snapshot_manifest_file_sha256",
        "snapshot_manifest_payload_sha256",
        "parent_database_sha256",
        "activation_authorization_payload_sha256",
    ):
        _require_hex64(payload[field], field=field)
    _require_aware_timestamp(payload["created_at"], field="created_at")


def _verify_database(
    path: Path,
    *,
    expected_sha256: str,
    expected_schema_version: int,
    expected_schema_design_sha256: str,
) -> None:
    if not path.is_file():
        raise PersistenceIntegrityError(f"Scientific Foundation DB missing: {path}")
    _reject_link_like(path, label="Scientific Foundation database")
    if sha256_file(path) != expected_sha256:
        raise PersistenceIntegrityError("Scientific Foundation database SHA drift")

    try:
        conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            conn.execute("PRAGMA query_only=ON")
            quick = [row[0] for row in conn.execute("PRAGMA quick_check")]
            foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
            user_version = conn.execute("PRAGMA user_version").fetchone()[0]
            metadata = conn.execute(
                """
                SELECT schema_version,design_sha256
                FROM sf_schema_metadata
                WHERE schema_name='scientific_foundation'
                """
            ).fetchone()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        raise PersistenceIntegrityError(
            "Scientific Foundation SQLite verification failed"
        ) from exc

    if quick != ["ok"] or foreign_keys:
        raise PersistenceIntegrityError("Scientific Foundation integrity failure")
    if user_version != expected_schema_version:
        raise PersistenceIntegrityError("Scientific Foundation schema-version drift")
    if metadata != (
        expected_schema_version,
        expected_schema_design_sha256,
    ):
        raise PersistenceIntegrityError("Scientific Foundation schema-design drift")


def _resolve_legacy(
    *,
    legacy_database_path: Path,
    expected_legacy_database_sha256: str,
    expected_schema_version: int,
    expected_schema_design_sha256: str,
) -> ResolvedScientificFoundationV1:
    _verify_database(
        legacy_database_path,
        expected_sha256=expected_legacy_database_sha256,
        expected_schema_version=expected_schema_version,
        expected_schema_design_sha256=expected_schema_design_sha256,
    )
    return ResolvedScientificFoundationV1(
        resolution_mode="legacy_fallback",
        database_path=legacy_database_path.resolve(),
        database_sha256=expected_legacy_database_sha256,
        schema_version=expected_schema_version,
        schema_design_sha256=expected_schema_design_sha256,
        snapshot_manifest_path=None,
        snapshot_manifest_file_sha256=None,
        snapshot_manifest_payload_sha256=None,
        pointer_payload_sha256=None,
        activation_authorization_payload_sha256=None,
    )


def resolve_active_scientific_foundation_v1(
    *,
    pointer_path: Path,
    snapshot_root: Path,
    legacy_database_path: Path,
    expected_legacy_database_sha256: str,
    expected_schema_version: int,
    expected_schema_design_sha256: str,
) -> ResolvedScientificFoundationV1:
    """Resolve a reviewed immutable snapshot or the frozen legacy root.

    Missing pointer -> verified legacy fallback.
    Present but malformed/corrupt pointer -> fail closed, never fallback.
    """

    expected_legacy_database_sha256 = _require_hex64(
        expected_legacy_database_sha256,
        field="expected_legacy_database_sha256",
    )
    expected_schema_design_sha256 = _require_hex64(
        expected_schema_design_sha256,
        field="expected_schema_design_sha256",
    )

    if not pointer_path.exists():
        return _resolve_legacy(
            legacy_database_path=legacy_database_path,
            expected_legacy_database_sha256=expected_legacy_database_sha256,
            expected_schema_version=expected_schema_version,
            expected_schema_design_sha256=expected_schema_design_sha256,
        )

    if not pointer_path.is_file():
        raise PersistenceIntegrityError("Active pointer is not a regular file")
    _reject_link_like(pointer_path, label="Active pointer")

    document = _read_json_object(pointer_path, label="active pointer document")
    _require_exact_keys(
        document,
        {"pointer_payload_sha256", "pointer_payload"},
        label="active pointer document",
    )
    pointer_sha = _require_hex64(
        document["pointer_payload_sha256"],
        field="pointer_payload_sha256",
    )
    payload = _require_mapping(
        document["pointer_payload"],
        label="active pointer payload",
    )
    _validate_pointer_payload(payload)
    if canonical_sha256(payload) != pointer_sha:
        raise PersistenceIntegrityError("Active pointer canonical SHA mismatch")

    parent_sha = _require_hex64(
        payload["parent_database_sha256"],
        field="parent_database_sha256",
    )
    if parent_sha != expected_legacy_database_sha256:
        raise PersistenceIntegrityError("Active pointer parent identity drift")

    if not snapshot_root.is_dir():
        raise PersistenceIntegrityError("Snapshot root is missing")
    _reject_link_like(snapshot_root, label="Snapshot root")

    database_sha = _require_hex64(
        payload["snapshot_database_sha256"],
        field="snapshot_database_sha256",
    )
    snapshot_directory = snapshot_root / database_sha
    if not snapshot_directory.is_dir():
        raise PersistenceIntegrityError("Content-addressed snapshot is missing")
    _reject_link_like(snapshot_directory, label="Snapshot directory")
    if snapshot_directory.resolve().parent != snapshot_root.resolve():
        raise PersistenceConfigurationError("Snapshot directory escapes snapshot root")

    database_path = snapshot_directory / "scientific-foundation.sqlite3"
    manifest_path = snapshot_directory / "snapshot-manifest.json"
    for path, label in (
        (database_path, "Snapshot database"),
        (manifest_path, "Snapshot manifest"),
    ):
        if not path.is_file():
            raise PersistenceIntegrityError(f"{label} is missing")
        _reject_link_like(path, label=label)

    observed_names = {path.name for path in snapshot_directory.iterdir()}
    if observed_names != {
        "scientific-foundation.sqlite3",
        "snapshot-manifest.json",
    }:
        raise PersistenceIntegrityError("Snapshot directory contains unexpected entries")

    expected_manifest_file_sha = _require_hex64(
        payload["snapshot_manifest_file_sha256"],
        field="snapshot_manifest_file_sha256",
    )
    if sha256_file(manifest_path) != expected_manifest_file_sha:
        raise PersistenceIntegrityError("Snapshot manifest file SHA drift")

    manifest_document = _read_json_object(
        manifest_path,
        label="snapshot manifest document",
    )
    _require_exact_keys(
        manifest_document,
        {"manifest_payload_sha256", "manifest_payload"},
        label="snapshot manifest document",
    )
    manifest_payload_sha = _require_hex64(
        manifest_document["manifest_payload_sha256"],
        field="manifest_payload_sha256",
    )
    manifest_payload = _require_mapping(
        manifest_document["manifest_payload"],
        label="snapshot manifest payload",
    )
    if canonical_sha256(manifest_payload) != manifest_payload_sha:
        raise PersistenceIntegrityError("Snapshot manifest canonical SHA mismatch")
    if manifest_payload_sha != payload["snapshot_manifest_payload_sha256"]:
        raise PersistenceIntegrityError("Pointer/manifest payload identity mismatch")

    if manifest_payload.get("schema_version") != SNAPSHOT_MANIFEST_SCHEMA_V1:
        raise PersistenceIntegrityError("Unsupported snapshot manifest schema")
    snapshot = _require_mapping(
        manifest_payload.get("snapshot"),
        label="snapshot manifest snapshot",
    )
    lineage = _require_mapping(
        manifest_payload.get("lineage"),
        label="snapshot manifest lineage",
    )
    validation = _require_mapping(
        manifest_payload.get("validation"),
        label="snapshot manifest validation",
    )

    if (
        snapshot.get("database_sha256") != database_sha
        or snapshot.get("schema_version") != expected_schema_version
        or snapshot.get("schema_design_sha256")
        != expected_schema_design_sha256
        or snapshot.get("immutable") is not True
        or lineage.get("parent_database_sha256") != parent_sha
        or validation.get("quick_check") != ["ok"]
        or validation.get("foreign_key_violation_count") != 0
    ):
        raise PersistenceIntegrityError("Snapshot manifest binding drift")

    _verify_database(
        database_path,
        expected_sha256=database_sha,
        expected_schema_version=expected_schema_version,
        expected_schema_design_sha256=expected_schema_design_sha256,
    )

    return ResolvedScientificFoundationV1(
        resolution_mode="active_snapshot",
        database_path=database_path.resolve(),
        database_sha256=database_sha,
        schema_version=expected_schema_version,
        schema_design_sha256=expected_schema_design_sha256,
        snapshot_manifest_path=manifest_path.resolve(),
        snapshot_manifest_file_sha256=expected_manifest_file_sha,
        snapshot_manifest_payload_sha256=manifest_payload_sha,
        pointer_payload_sha256=pointer_sha,
        activation_authorization_payload_sha256=_require_hex64(
            payload["activation_authorization_payload_sha256"],
            field="activation_authorization_payload_sha256",
        ),
    )
