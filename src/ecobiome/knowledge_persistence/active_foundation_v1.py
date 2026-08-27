"""Read-only active Scientific Foundation trust policy and resolver V1.

RATE-3M contains no persistent active-pointer writer and performs no runtime
consumer migration.  A mutable pointer is never its own trust anchor: active
resolution requires a separately reviewed runtime-policy document whose
canonical SHA is supplied by the caller as trusted configuration.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .errors import PersistenceConfigurationError, PersistenceIntegrityError

ACTIVE_POINTER_SCHEMA_V1 = "ecobiome-active-scientific-foundation-pointer-v1"
RUNTIME_POLICY_SCHEMA_V1 = (
    "ecobiome-active-scientific-foundation-runtime-policy-v1"
)
SNAPSHOT_MANIFEST_SCHEMA_V1 = (
    "ecobiome-scientific-foundation-snapshot-manifest-v1-reviewed"
)

LEGACY_PRE_ACTIVATION = "legacy_pre_activation"
AUTHORIZE_ACTIVE_SNAPSHOT = "authorize_active_snapshot"

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
_INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF


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
        raise PersistenceIntegrityError(
            f"{field} must be a lowercase SHA-256"
        )
    return value


def _require_optional_hex64(
    value: object,
    *,
    field: str,
) -> str | None:
    if value is None:
        return None
    return _require_hex64(value, field=field)


def _require_aware_timestamp(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise PersistenceIntegrityError(
            f"{field} must be a non-empty timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise PersistenceIntegrityError(
            f"{field} is not ISO-8601"
        ) from exc
    if parsed.tzinfo is None:
        raise PersistenceIntegrityError(
            f"{field} must be timezone-aware"
        )
    return value


def _require_mapping(
    value: object,
    *,
    label: str,
) -> Mapping[str, Any]:
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
            f"{label} keys mismatch: "
            f"{sorted(observed)} != {sorted(expected)}"
        )


def _windows_is_reparse_point(path: Path) -> bool:
    if os.name != "nt":
        return False

    windll_factory = getattr(ctypes, "WinDLL", None)
    if windll_factory is None:
        raise PersistenceConfigurationError(
            "Win32 file-attribute API unavailable"
        )

    kernel32 = windll_factory("kernel32", use_last_error=True)
    get_attributes = kernel32.GetFileAttributesW
    get_attributes.argtypes = [ctypes.c_wchar_p]
    get_attributes.restype = ctypes.c_uint32

    attributes = int(get_attributes(str(path)))
    if attributes == _INVALID_FILE_ATTRIBUTES:
        get_last_error = getattr(ctypes, "get_last_error", None)
        error_code = int(get_last_error()) if callable(get_last_error) else 0
        raise PersistenceConfigurationError(
            f"GetFileAttributesW failed for {path}: {error_code}"
        )
    return bool(attributes & _FILE_ATTRIBUTE_REPARSE_POINT)


def _is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    if callable(is_junction) and is_junction():
        return True
    return _windows_is_reparse_point(path)


def _reject_link_like(path: Path, *, label: str) -> None:
    if _is_link_like(path):
        raise PersistenceConfigurationError(
            f"{label} must not be a symlink/junction/reparse point"
        )


def _read_json_object(
    path: Path,
    *,
    label: str,
) -> Mapping[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PersistenceIntegrityError(
            f"{label} cannot be decoded"
        ) from exc
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
            "snapshot_manifest_file_sha256": (
                self.snapshot_manifest_file_sha256
            ),
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
class ActiveScientificFoundationRuntimePolicyV1:
    activation_decision: str
    pointer_required: bool
    parent_database_sha256: str
    snapshot_database_sha256: str | None
    snapshot_manifest_file_sha256: str | None
    snapshot_manifest_payload_sha256: str | None
    pointer_contract_payload_sha256: str
    resolver_code_sha256: str
    consumer_migration_identity_sha256: str | None
    created_at: str

    def payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": RUNTIME_POLICY_SCHEMA_V1,
            "activation_decision": self.activation_decision,
            "pointer_required": self.pointer_required,
            "parent_database_sha256": self.parent_database_sha256,
            "snapshot_database_sha256": self.snapshot_database_sha256,
            "snapshot_manifest_file_sha256": (
                self.snapshot_manifest_file_sha256
            ),
            "snapshot_manifest_payload_sha256": (
                self.snapshot_manifest_payload_sha256
            ),
            "pointer_contract_payload_sha256": (
                self.pointer_contract_payload_sha256
            ),
            "resolver_code_sha256": self.resolver_code_sha256,
            "consumer_migration_identity_sha256": (
                self.consumer_migration_identity_sha256
            ),
            "created_at": self.created_at,
        }
        _validate_runtime_policy_payload(payload)
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
    runtime_policy_payload_sha256: str


def build_active_pointer_document(
    pointer: ActiveScientificFoundationPointerV1,
) -> dict[str, object]:
    payload = pointer.payload()
    return {
        "pointer_payload_sha256": canonical_sha256(payload),
        "pointer_payload": payload,
    }


def build_runtime_policy_document(
    policy: ActiveScientificFoundationRuntimePolicyV1,
) -> dict[str, object]:
    payload = policy.payload()
    return {
        "runtime_policy_payload_sha256": canonical_sha256(payload),
        "runtime_policy_payload": payload,
    }


def _validate_pointer_payload(
    payload: Mapping[str, Any],
) -> None:
    expected = {
        "schema_version",
        "snapshot_database_sha256",
        "snapshot_manifest_file_sha256",
        "snapshot_manifest_payload_sha256",
        "parent_database_sha256",
        "activation_authorization_payload_sha256",
        "created_at",
    }
    _require_exact_keys(
        payload,
        expected,
        label="active pointer payload",
    )
    if payload["schema_version"] != ACTIVE_POINTER_SCHEMA_V1:
        raise PersistenceIntegrityError(
            "Unsupported active pointer schema"
        )
    for field in (
        "snapshot_database_sha256",
        "snapshot_manifest_file_sha256",
        "snapshot_manifest_payload_sha256",
        "parent_database_sha256",
        "activation_authorization_payload_sha256",
    ):
        _require_hex64(payload[field], field=field)
    _require_aware_timestamp(
        payload["created_at"],
        field="created_at",
    )


def _validate_runtime_policy_payload(
    payload: Mapping[str, Any],
) -> None:
    expected = {
        "schema_version",
        "activation_decision",
        "pointer_required",
        "parent_database_sha256",
        "snapshot_database_sha256",
        "snapshot_manifest_file_sha256",
        "snapshot_manifest_payload_sha256",
        "pointer_contract_payload_sha256",
        "resolver_code_sha256",
        "consumer_migration_identity_sha256",
        "created_at",
    }
    _require_exact_keys(
        payload,
        expected,
        label="runtime policy payload",
    )
    if payload["schema_version"] != RUNTIME_POLICY_SCHEMA_V1:
        raise PersistenceIntegrityError(
            "Unsupported runtime policy schema"
        )

    decision = payload["activation_decision"]
    pointer_required = payload["pointer_required"]
    if not isinstance(pointer_required, bool):
        raise PersistenceIntegrityError(
            "pointer_required must be boolean"
        )

    _require_hex64(
        payload["parent_database_sha256"],
        field="parent_database_sha256",
    )
    _require_hex64(
        payload["pointer_contract_payload_sha256"],
        field="pointer_contract_payload_sha256",
    )
    _require_hex64(
        payload["resolver_code_sha256"],
        field="resolver_code_sha256",
    )
    _require_aware_timestamp(
        payload["created_at"],
        field="created_at",
    )

    snapshot_fields = (
        "snapshot_database_sha256",
        "snapshot_manifest_file_sha256",
        "snapshot_manifest_payload_sha256",
    )

    if decision == LEGACY_PRE_ACTIVATION:
        if pointer_required:
            raise PersistenceIntegrityError(
                "legacy pre-activation policy cannot require pointer"
            )
        if any(payload[field] is not None for field in snapshot_fields):
            raise PersistenceIntegrityError(
                "legacy pre-activation policy cannot authorize snapshot"
            )
        if payload["consumer_migration_identity_sha256"] is not None:
            raise PersistenceIntegrityError(
                "legacy pre-activation policy cannot bind migration identity"
            )
        return

    if decision == AUTHORIZE_ACTIVE_SNAPSHOT:
        if not pointer_required:
            raise PersistenceIntegrityError(
                "active snapshot authorization requires pointer"
            )
        for field in snapshot_fields:
            _require_hex64(payload[field], field=field)
        _require_hex64(
            payload["consumer_migration_identity_sha256"],
            field="consumer_migration_identity_sha256",
        )
        return

    raise PersistenceIntegrityError(
        "Unsupported activation_decision"
    )


def _parse_runtime_policy_document(
    document: Mapping[str, Any],
    *,
    expected_payload_sha256: str,
) -> tuple[Mapping[str, Any], str]:
    _require_exact_keys(
        document,
        {
            "runtime_policy_payload_sha256",
            "runtime_policy_payload",
        },
        label="runtime policy document",
    )
    expected = _require_hex64(
        expected_payload_sha256,
        field="expected_runtime_policy_payload_sha256",
    )
    observed = _require_hex64(
        document["runtime_policy_payload_sha256"],
        field="runtime_policy_payload_sha256",
    )
    payload = _require_mapping(
        document["runtime_policy_payload"],
        label="runtime policy payload",
    )
    _validate_runtime_policy_payload(payload)
    canonical = canonical_sha256(payload)
    if observed != canonical or expected != canonical:
        raise PersistenceIntegrityError(
            "Runtime policy canonical/trusted SHA mismatch"
        )
    return payload, canonical


def _verify_resolver_code_identity(
    policy: Mapping[str, Any],
) -> None:
    expected = _require_hex64(
        policy["resolver_code_sha256"],
        field="resolver_code_sha256",
    )
    observed = sha256_file(Path(__file__).resolve())
    if observed != expected:
        raise PersistenceIntegrityError(
            "Runtime policy resolver-code identity mismatch"
        )


def _verify_database(
    path: Path,
    *,
    expected_sha256: str,
    expected_schema_version: int,
    expected_schema_design_sha256: str,
) -> None:
    if not path.is_file():
        raise PersistenceIntegrityError(
            f"Scientific Foundation DB missing: {path}"
        )
    _reject_link_like(
        path,
        label="Scientific Foundation database",
    )
    if sha256_file(path) != expected_sha256:
        raise PersistenceIntegrityError(
            "Scientific Foundation database SHA drift"
        )

    try:
        conn = sqlite3.connect(
            path.resolve().as_uri() + "?mode=ro",
            uri=True,
        )
        try:
            conn.execute("PRAGMA query_only=ON")
            quick = [
                row[0]
                for row in conn.execute("PRAGMA quick_check")
            ]
            foreign_keys = conn.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()
            user_version = conn.execute(
                "PRAGMA user_version"
            ).fetchone()[0]
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
        raise PersistenceIntegrityError(
            "Scientific Foundation integrity failure"
        )
    if user_version != expected_schema_version:
        raise PersistenceIntegrityError(
            "Scientific Foundation schema-version drift"
        )
    if metadata != (
        expected_schema_version,
        expected_schema_design_sha256,
    ):
        raise PersistenceIntegrityError(
            "Scientific Foundation schema-design drift"
        )


def _resolve_legacy(
    *,
    legacy_database_path: Path,
    expected_legacy_database_sha256: str,
    expected_schema_version: int,
    expected_schema_design_sha256: str,
    runtime_policy_payload_sha256: str,
) -> ResolvedScientificFoundationV1:
    _verify_database(
        legacy_database_path,
        expected_sha256=expected_legacy_database_sha256,
        expected_schema_version=expected_schema_version,
        expected_schema_design_sha256=(
            expected_schema_design_sha256
        ),
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
        runtime_policy_payload_sha256=(
            runtime_policy_payload_sha256
        ),
    )


def resolve_active_scientific_foundation_v1(
    *,
    pointer_path: Path,
    snapshot_root: Path,
    legacy_database_path: Path,
    expected_legacy_database_sha256: str,
    expected_schema_version: int,
    expected_schema_design_sha256: str,
    runtime_policy_document: Mapping[str, Any],
    expected_runtime_policy_payload_sha256: str,
) -> ResolvedScientificFoundationV1:
    """Resolve only what a separately trusted runtime policy authorizes.

    Pre-activation:
        pointer_required=False and pointer absent -> verified legacy fallback.

    Post-activation:
        pointer_required=True and pointer absent -> fail closed.

    Any present pointer must exactly match the trusted runtime-policy target.
    """

    expected_legacy_database_sha256 = _require_hex64(
        expected_legacy_database_sha256,
        field="expected_legacy_database_sha256",
    )
    expected_schema_design_sha256 = _require_hex64(
        expected_schema_design_sha256,
        field="expected_schema_design_sha256",
    )

    policy, policy_sha = _parse_runtime_policy_document(
        runtime_policy_document,
        expected_payload_sha256=(
            expected_runtime_policy_payload_sha256
        ),
    )
    _verify_resolver_code_identity(policy)

    policy_parent = _require_hex64(
        policy["parent_database_sha256"],
        field="parent_database_sha256",
    )
    if policy_parent != expected_legacy_database_sha256:
        raise PersistenceIntegrityError(
            "Runtime policy parent identity drift"
        )

    if not pointer_path.exists():
        if policy["pointer_required"]:
            raise PersistenceIntegrityError(
                "Active pointer is required by runtime policy"
            )
        if policy["activation_decision"] != LEGACY_PRE_ACTIVATION:
            raise PersistenceIntegrityError(
                "Runtime policy does not authorize legacy fallback"
            )
        return _resolve_legacy(
            legacy_database_path=legacy_database_path,
            expected_legacy_database_sha256=(
                expected_legacy_database_sha256
            ),
            expected_schema_version=expected_schema_version,
            expected_schema_design_sha256=(
                expected_schema_design_sha256
            ),
            runtime_policy_payload_sha256=policy_sha,
        )

    if (
        policy["activation_decision"] != AUTHORIZE_ACTIVE_SNAPSHOT
        or policy["pointer_required"] is not True
    ):
        raise PersistenceIntegrityError(
            "Present active pointer is not authorized by runtime policy"
        )

    if not pointer_path.is_file():
        raise PersistenceIntegrityError(
            "Active pointer is not a regular file"
        )
    _reject_link_like(pointer_path, label="Active pointer")

    document = _read_json_object(
        pointer_path,
        label="active pointer document",
    )
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
        raise PersistenceIntegrityError(
            "Active pointer canonical SHA mismatch"
        )

    expected_pointer_values = {
        "snapshot_database_sha256": policy[
            "snapshot_database_sha256"
        ],
        "snapshot_manifest_file_sha256": policy[
            "snapshot_manifest_file_sha256"
        ],
        "snapshot_manifest_payload_sha256": policy[
            "snapshot_manifest_payload_sha256"
        ],
        "parent_database_sha256": policy[
            "parent_database_sha256"
        ],
        "activation_authorization_payload_sha256": policy_sha,
        "created_at": policy["created_at"],
    }
    for field, expected in expected_pointer_values.items():
        if payload[field] != expected:
            raise PersistenceIntegrityError(
                f"Active pointer is outside trusted policy: {field}"
            )

    parent_sha = _require_hex64(
        payload["parent_database_sha256"],
        field="parent_database_sha256",
    )

    if not snapshot_root.is_dir():
        raise PersistenceIntegrityError(
            "Snapshot root is missing"
        )
    _reject_link_like(snapshot_root, label="Snapshot root")

    database_sha = _require_hex64(
        payload["snapshot_database_sha256"],
        field="snapshot_database_sha256",
    )
    snapshot_directory = snapshot_root / database_sha
    if not snapshot_directory.is_dir():
        raise PersistenceIntegrityError(
            "Content-addressed snapshot is missing"
        )
    _reject_link_like(
        snapshot_directory,
        label="Snapshot directory",
    )
    if (
        snapshot_directory.resolve().parent
        != snapshot_root.resolve()
    ):
        raise PersistenceConfigurationError(
            "Snapshot directory escapes snapshot root"
        )

    database_path = (
        snapshot_directory / "scientific-foundation.sqlite3"
    )
    manifest_path = (
        snapshot_directory / "snapshot-manifest.json"
    )
    for path, label in (
        (database_path, "Snapshot database"),
        (manifest_path, "Snapshot manifest"),
    ):
        if not path.is_file():
            raise PersistenceIntegrityError(
                f"{label} is missing"
            )
        _reject_link_like(path, label=label)

    observed_names = {
        path.name
        for path in snapshot_directory.iterdir()
    }
    if observed_names != {
        "scientific-foundation.sqlite3",
        "snapshot-manifest.json",
    }:
        raise PersistenceIntegrityError(
            "Snapshot directory contains unexpected entries"
        )

    expected_manifest_file_sha = _require_hex64(
        payload["snapshot_manifest_file_sha256"],
        field="snapshot_manifest_file_sha256",
    )
    if sha256_file(manifest_path) != expected_manifest_file_sha:
        raise PersistenceIntegrityError(
            "Snapshot manifest file SHA drift"
        )

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
        raise PersistenceIntegrityError(
            "Snapshot manifest canonical SHA mismatch"
        )
    if (
        manifest_payload_sha
        != payload["snapshot_manifest_payload_sha256"]
    ):
        raise PersistenceIntegrityError(
            "Pointer/manifest payload identity mismatch"
        )

    if (
        manifest_payload.get("schema_version")
        != SNAPSHOT_MANIFEST_SCHEMA_V1
    ):
        raise PersistenceIntegrityError(
            "Unsupported snapshot manifest schema"
        )

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
        or snapshot.get("schema_version")
        != expected_schema_version
        or snapshot.get("schema_design_sha256")
        != expected_schema_design_sha256
        or snapshot.get("immutable") is not True
        or lineage.get("parent_database_sha256")
        != parent_sha
        or validation.get("quick_check") != ["ok"]
        or validation.get("foreign_key_violation_count") != 0
    ):
        raise PersistenceIntegrityError(
            "Snapshot manifest binding drift"
        )

    _verify_database(
        database_path,
        expected_sha256=database_sha,
        expected_schema_version=expected_schema_version,
        expected_schema_design_sha256=(
            expected_schema_design_sha256
        ),
    )

    return ResolvedScientificFoundationV1(
        resolution_mode="active_snapshot",
        database_path=database_path.resolve(),
        database_sha256=database_sha,
        schema_version=expected_schema_version,
        schema_design_sha256=expected_schema_design_sha256,
        snapshot_manifest_path=manifest_path.resolve(),
        snapshot_manifest_file_sha256=(
            expected_manifest_file_sha
        ),
        snapshot_manifest_payload_sha256=manifest_payload_sha,
        pointer_payload_sha256=pointer_sha,
        activation_authorization_payload_sha256=policy_sha,
        runtime_policy_payload_sha256=policy_sha,
    )
