"""First persistent Scientific Foundation activation contract V1.

RATE-3Q is design/test/dry-run only.  This module can exercise atomic
publication mechanics only outside the real EcoBiome persistent data root.
The first real persistent active-pointer write remains forbidden until a
separate human authorization gate is reviewed and accepted.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .active_foundation_runtime_config_v1 import (
    RUNTIME_POLICY_ENV,
    RUNTIME_POLICY_SHA_ENV,
)
from .active_foundation_v1 import (
    ACTIVE_POINTER_SCHEMA_V1,
    AUTHORIZE_ACTIVE_SNAPSHOT,
    RUNTIME_POLICY_SCHEMA_V1,
    ActiveScientificFoundationPointerV1,
    build_active_pointer_document,
    canonical_sha256,
)
from .errors import PersistenceConfigurationError, PersistenceIntegrityError

FIRST_ACTIVATION_CONTRACT_SCHEMA_V1 = (
    "ecobiome-first-persistent-scientific-foundation-activation-contract-v1"
)
ROLLBACK_PROTOCOL_V1 = "quiesced-reviewed-policy-atomic-pointer-archive-v1"

REAL_DATA_ROOT = Path.home() / "Documents" / "EcoBiome-data"
REAL_ACTIVE_POINTER = REAL_DATA_ROOT / "scientific-foundation-active.json"

_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
_INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
_MOVEFILE_WRITE_THROUGH = 0x00000008
_ERROR_FILE_EXISTS = 80
_ERROR_ALREADY_EXISTS = 183

FailurePoint = Literal[
    "after_temp_write",
    "before_replace",
    "after_replace_before_verify",
]


class InjectedActivationFailure(RuntimeError):
    """Raised only by explicit RATE-3Q failure injection."""


@dataclass(frozen=True, slots=True)
class ActivationIdentitySetV1:
    parent_database_sha256: str
    snapshot_database_sha256: str
    snapshot_manifest_file_sha256: str
    snapshot_manifest_payload_sha256: str
    pointer_contract_payload_sha256: str
    resolver_code_sha256: str
    consumer_migration_identity_sha256: str


@dataclass(frozen=True, slots=True)
class ActivationPathSetV1:
    persistent_pointer_path: Path
    runtime_policy_path: Path
    legacy_database_path: Path
    cas_root: Path
    snapshot_root: Path
    snapshot_directory: Path
    snapshot_database_path: Path
    snapshot_manifest_path: Path


@dataclass(frozen=True, slots=True)
class PathAuditEntryV1:
    path: str
    exists: bool
    link_like: bool


@dataclass(frozen=True, slots=True)
class PointerPublicationResultV1:
    target_path: Path
    file_sha256: str
    pointer_payload_sha256: str
    bytes_written: int


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _canonical_absolute(path: Path) -> Path:
    expanded = path.expanduser()
    return Path(os.path.abspath(os.fspath(expanded)))


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


def audit_ancestor_chain_v1(
    path: Path,
    *,
    allow_missing_leaf: bool = False,
) -> tuple[PathAuditEntryV1, ...]:
    """Reject symlink/junction/reparse points anywhere in an absolute path."""

    absolute = _canonical_absolute(path)
    parts = absolute.parts
    if not parts:
        raise PersistenceConfigurationError("Cannot audit an empty path")

    current = Path(parts[0])
    entries: list[PathAuditEntryV1] = []

    for index, part in enumerate(parts):
        if index == 0:
            current = Path(part)
        else:
            current = current / part

        exists = os.path.lexists(current)
        is_leaf = index == len(parts) - 1

        if not exists:
            if is_leaf and allow_missing_leaf:
                entries.append(
                    PathAuditEntryV1(
                        path=str(current),
                        exists=False,
                        link_like=False,
                    )
                )
                continue
            raise PersistenceConfigurationError(
                f"Audited path component is missing: {current}"
            )

        link_like = _is_link_like(current)
        entries.append(
            PathAuditEntryV1(
                path=str(current),
                exists=True,
                link_like=link_like,
            )
        )
        if link_like:
            raise PersistenceConfigurationError(
                "Audited path component must not be a "
                f"symlink/junction/reparse point: {current}"
            )

    return tuple(entries)


def _require_hex64(value: object, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise PersistenceIntegrityError(
            f"{field} must be a lowercase SHA-256"
        )
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
            f"{label} keys mismatch: "
            f"{sorted(observed)} != {sorted(expected)}"
        )


def validate_active_runtime_policy_document_v1(
    runtime_policy_document: Mapping[str, Any],
    *,
    expected_runtime_policy_payload_sha256: str,
    expected_identities: ActivationIdentitySetV1,
) -> Mapping[str, Any]:
    """Validate the independently trusted policy against exact RATE-3Q IDs."""

    _require_exact_keys(
        runtime_policy_document,
        {
            "runtime_policy_payload_sha256",
            "runtime_policy_payload",
        },
        label="runtime policy document",
    )
    expected_sha = _require_hex64(
        expected_runtime_policy_payload_sha256,
        field="expected_runtime_policy_payload_sha256",
    )
    observed_sha = _require_hex64(
        runtime_policy_document["runtime_policy_payload_sha256"],
        field="runtime_policy_payload_sha256",
    )
    payload = _require_mapping(
        runtime_policy_document["runtime_policy_payload"],
        label="runtime policy payload",
    )
    _require_exact_keys(
        payload,
        {
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
        },
        label="runtime policy payload",
    )

    if payload["schema_version"] != RUNTIME_POLICY_SCHEMA_V1:
        raise PersistenceIntegrityError(
            "Unsupported runtime policy schema"
        )
    if payload["activation_decision"] != AUTHORIZE_ACTIVE_SNAPSHOT:
        raise PersistenceIntegrityError(
            "Runtime policy does not authorize active snapshot"
        )
    if payload["pointer_required"] is not True:
        raise PersistenceIntegrityError(
            "First activation policy must require pointer"
        )

    canonical_sha = canonical_sha256(payload)
    if observed_sha != canonical_sha or expected_sha != canonical_sha:
        raise PersistenceIntegrityError(
            "Runtime policy canonical/trusted SHA mismatch"
        )

    exact = {
        "parent_database_sha256": (
            expected_identities.parent_database_sha256
        ),
        "snapshot_database_sha256": (
            expected_identities.snapshot_database_sha256
        ),
        "snapshot_manifest_file_sha256": (
            expected_identities.snapshot_manifest_file_sha256
        ),
        "snapshot_manifest_payload_sha256": (
            expected_identities.snapshot_manifest_payload_sha256
        ),
        "pointer_contract_payload_sha256": (
            expected_identities.pointer_contract_payload_sha256
        ),
        "resolver_code_sha256": expected_identities.resolver_code_sha256,
        "consumer_migration_identity_sha256": (
            expected_identities.consumer_migration_identity_sha256
        ),
    }
    for field, expected in exact.items():
        observed = _require_hex64(payload[field], field=field)
        if observed != expected:
            raise PersistenceIntegrityError(
                f"Runtime policy identity drift: {field}"
            )

    created_at = payload["created_at"]
    if not isinstance(created_at, str) or not created_at:
        raise PersistenceIntegrityError(
            "Runtime policy created_at must be non-empty"
        )

    return payload


def build_pointer_from_runtime_policy_v1(
    runtime_policy_document: Mapping[str, Any],
    *,
    expected_runtime_policy_payload_sha256: str,
    expected_identities: ActivationIdentitySetV1,
) -> dict[str, object]:
    payload = validate_active_runtime_policy_document_v1(
        runtime_policy_document,
        expected_runtime_policy_payload_sha256=(
            expected_runtime_policy_payload_sha256
        ),
        expected_identities=expected_identities,
    )

    pointer = ActiveScientificFoundationPointerV1(
        snapshot_database_sha256=expected_identities.snapshot_database_sha256,
        snapshot_manifest_file_sha256=(
            expected_identities.snapshot_manifest_file_sha256
        ),
        snapshot_manifest_payload_sha256=(
            expected_identities.snapshot_manifest_payload_sha256
        ),
        parent_database_sha256=expected_identities.parent_database_sha256,
        activation_authorization_payload_sha256=(
            expected_runtime_policy_payload_sha256
        ),
        created_at=str(payload["created_at"]),
    )
    document = build_active_pointer_document(pointer)

    pointer_payload = _require_mapping(
        document["pointer_payload"],
        label="pointer payload",
    )
    if pointer_payload["schema_version"] != ACTIVE_POINTER_SCHEMA_V1:
        raise PersistenceIntegrityError(
            "Unexpected pointer schema generated"
        )
    return document


def audit_activation_paths_v1(
    paths: ActivationPathSetV1,
) -> dict[str, tuple[PathAuditEntryV1, ...]]:
    """Audit every persistent control-plane/scientific-data path ancestry."""

    if _canonical_absolute(paths.snapshot_directory).parent != (
        _canonical_absolute(paths.snapshot_root)
    ):
        raise PersistenceConfigurationError(
            "Snapshot directory is not directly under snapshot root"
        )
    if _canonical_absolute(paths.snapshot_database_path).parent != (
        _canonical_absolute(paths.snapshot_directory)
    ):
        raise PersistenceConfigurationError(
            "Snapshot database escapes snapshot directory"
        )
    if _canonical_absolute(paths.snapshot_manifest_path).parent != (
        _canonical_absolute(paths.snapshot_directory)
    ):
        raise PersistenceConfigurationError(
            "Snapshot manifest escapes snapshot directory"
        )

    return {
        "persistent_pointer": audit_ancestor_chain_v1(
            paths.persistent_pointer_path,
            allow_missing_leaf=True,
        ),
        "runtime_policy": audit_ancestor_chain_v1(
            paths.runtime_policy_path,
        ),
        "legacy_database": audit_ancestor_chain_v1(
            paths.legacy_database_path,
        ),
        "cas_root": audit_ancestor_chain_v1(paths.cas_root),
        "snapshot_root": audit_ancestor_chain_v1(paths.snapshot_root),
        "snapshot_directory": audit_ancestor_chain_v1(
            paths.snapshot_directory
        ),
        "snapshot_database": audit_ancestor_chain_v1(
            paths.snapshot_database_path
        ),
        "snapshot_manifest": audit_ancestor_chain_v1(
            paths.snapshot_manifest_path
        ),
    }


def _assert_rate3q_dry_run_target(target_path: Path) -> Path:
    target = _canonical_absolute(target_path)
    real_root = _canonical_absolute(REAL_DATA_ROOT)

    try:
        target.relative_to(real_root)
    except ValueError:
        pass
    else:
        raise PersistenceConfigurationError(
            "RATE-3Q forbids writes under the real EcoBiome data root"
        )

    if target.exists():
        raise PersistenceConfigurationError(
            "First-activation dry-run target must not already exist"
        )
    if not target.parent.is_dir():
        raise PersistenceConfigurationError(
            "Dry-run target parent directory is missing"
        )

    audit_ancestor_chain_v1(target, allow_missing_leaf=True)
    return target



def _fsync_directory_posix_v1(directory: Path) -> None:
    """Persist directory-entry updates on POSIX filesystems."""

    if os.name == "nt":
        return
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _move_no_clobber_durable_v1(source: Path, target: Path) -> None:
    """Publish a fully written temp file without ever replacing a target.

    Windows uses MoveFileExW with MOVEFILE_WRITE_THROUGH and deliberately
    omits MOVEFILE_REPLACE_EXISTING.  POSIX uses an atomic hard-link create
    (which fails if the target exists), fsyncs the directory, then removes
    the temporary name and fsyncs the directory again.
    """

    if os.name == "nt":
        windll_factory = getattr(ctypes, "WinDLL", None)
        if windll_factory is None:
            raise PersistenceConfigurationError(
                "Win32 MoveFileExW API unavailable"
            )
        kernel32 = windll_factory("kernel32", use_last_error=True)
        move_file_ex = kernel32.MoveFileExW
        move_file_ex.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_uint32,
        ]
        move_file_ex.restype = ctypes.c_int

        moved = int(
            move_file_ex(
                str(source),
                str(target),
                _MOVEFILE_WRITE_THROUGH,
            )
        )
        if moved == 0:
            get_last_error = getattr(ctypes, "get_last_error", None)
            error_code = (
                int(get_last_error())
                if callable(get_last_error)
                else 0
            )
            if error_code in {_ERROR_FILE_EXISTS, _ERROR_ALREADY_EXISTS}:
                raise PersistenceConfigurationError(
                    "First-activation target already exists; refusing "
                    "to overwrite it"
                )
            raise PersistenceIntegrityError(
                "MoveFileExW no-clobber durable publication failed: "
                f"{error_code}"
            )
        return

    try:
        os.link(source, target)
    except FileExistsError as exc:
        raise PersistenceConfigurationError(
            "First-activation target already exists; refusing "
            "to overwrite it"
        ) from exc

    _fsync_directory_posix_v1(target.parent)
    source.unlink()
    _fsync_directory_posix_v1(target.parent)


def publish_pointer_dry_run_v1(
    target_path: Path,
    pointer_document: Mapping[str, Any],
    *,
    failure_point: FailurePoint | None = None,
) -> PointerPublicationResultV1:
    """Exercise same-directory atomic pointer publication outside real data."""

    target = _assert_rate3q_dry_run_target(target_path)

    _require_exact_keys(
        pointer_document,
        {"pointer_payload_sha256", "pointer_payload"},
        label="pointer document",
    )
    payload = _require_mapping(
        pointer_document["pointer_payload"],
        label="pointer payload",
    )
    pointer_sha = _require_hex64(
        pointer_document["pointer_payload_sha256"],
        field="pointer_payload_sha256",
    )
    if canonical_sha256(payload) != pointer_sha:
        raise PersistenceIntegrityError(
            "Pointer document canonical SHA mismatch"
        )

    encoded = _json_bytes(pointer_document)
    temporary = (
        target.parent
        / f".{target.name}.tmp-{uuid.uuid4().hex}"
    )
    descriptor: int | None = None

    try:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        descriptor = os.open(temporary, flags, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = None
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())

        if failure_point == "after_temp_write":
            raise InjectedActivationFailure("after_temp_write")

        if temporary.read_bytes() != encoded:
            raise PersistenceIntegrityError(
                "Temporary pointer readback mismatch"
            )

        if failure_point == "before_replace":
            raise InjectedActivationFailure("before_replace")

        audit_ancestor_chain_v1(target, allow_missing_leaf=True)
        _move_no_clobber_durable_v1(temporary, target)

        if failure_point == "after_replace_before_verify":
            raise InjectedActivationFailure(
                "after_replace_before_verify"
            )

        observed = target.read_bytes()
        if observed != encoded:
            raise PersistenceIntegrityError(
                "Published pointer readback mismatch"
            )
        parsed = json.loads(observed.decode("utf-8"))
        parsed_mapping = _require_mapping(
            parsed,
            label="published pointer document",
        )
        published_payload = _require_mapping(
            parsed_mapping["pointer_payload"],
            label="published pointer payload",
        )
        if canonical_sha256(published_payload) != pointer_sha:
            raise PersistenceIntegrityError(
                "Published pointer canonical SHA mismatch"
            )

        return PointerPublicationResultV1(
            target_path=target,
            file_sha256=_sha256_bytes(observed),
            pointer_payload_sha256=pointer_sha,
            bytes_written=len(observed),
        )
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary.exists():
            temporary.unlink()


def first_activation_contract_document_v1(
    *,
    expected_identities: ActivationIdentitySetV1,
) -> dict[str, object]:
    """Return the frozen RATE-3Q activation contract payload."""

    return {
        "schema_version": FIRST_ACTIVATION_CONTRACT_SCHEMA_V1,
        "status": "design_test_dry_run_only_not_activation_authority",
        "trust_source": {
            "runtime_policy_path_env": RUNTIME_POLICY_ENV,
            "expected_policy_sha_env": RUNTIME_POLICY_SHA_ENV,
            "both_required_post_activation": True,
            "expected_sha_must_not_be_derived_from_policy_file_at_runtime": True,
            "deployment_semantics": (
                "reviewed policy path and independently trusted canonical "
                "policy SHA are provisioned as separate deployment inputs"
            ),
        },
        "activation_target": {
            "parent_database_sha256": (
                expected_identities.parent_database_sha256
            ),
            "snapshot_database_sha256": (
                expected_identities.snapshot_database_sha256
            ),
            "snapshot_manifest_file_sha256": (
                expected_identities.snapshot_manifest_file_sha256
            ),
            "snapshot_manifest_payload_sha256": (
                expected_identities.snapshot_manifest_payload_sha256
            ),
            "pointer_contract_payload_sha256": (
                expected_identities.pointer_contract_payload_sha256
            ),
            "resolver_code_sha256": (
                expected_identities.resolver_code_sha256
            ),
            "consumer_migration_identity_sha256": (
                expected_identities.consumer_migration_identity_sha256
            ),
        },
        "path_security": {
            "complete_ancestor_chain_audit_required": True,
            "reject_symlink_junction_reparse_point": True,
            "paths": [
                "persistent_active_pointer",
                "runtime_policy",
                "legacy_v6_database",
                "persistent_cas_root",
                "persistent_snapshot_root",
                "content_addressed_snapshot_directory",
                "snapshot_database",
                "snapshot_manifest",
            ],
        },
        "pointer_publication": {
            "persistent_target": (
                "~/Documents/EcoBiome-data/"
                "scientific-foundation-active.json"
            ),
            "first_activation_requires_target_absent": True,
            "same_directory_temporary_file": True,
            "temporary_file_exclusive_create": True,
            "flush_and_fsync_before_publish": True,
            "atomic_no_clobber_publication": (
                "MoveFileExW(MOVEFILE_WRITE_THROUGH,no_replace)"
                if os.name == "nt"
                else "link_no_replace+directory_fsync"
            ),
            "second_ancestry_audit_immediately_before_publish": True,
            "post_publish_exact_readback_required": True,
            "overwrite_existing_active_pointer": False,
        },
        "rollback": {
            "protocol": ROLLBACK_PROTOCOL_V1,
            "separate_human_review_required": True,
            "consumers_must_be_quiesced": True,
            "silent_pointer_delete_forbidden": True,
            "archive_pointer_atomically_before_legacy_restart": True,
            "reviewed_legacy_policy_and_independent_sha_required": True,
            "scientific_snapshot_or_cas_mutation": False,
            "fail_closed_transition_window_is_acceptable": True,
        },
        "failure_injection": {
            "points": [
                "after_temp_write",
                "before_replace",
                "after_replace_before_verify",
            ],
            "pre_replace_failure_requires_pointer_absent": True,
            "post_replace_failure_requires_complete_verifiable_pointer": True,
        },
        "authorization_boundary": {
            "persistent_active_pointer_write_authorized": False,
            "persistent_runtime_policy_publication_authorized": False,
            "persistent_snapshot_mutation_authorized": False,
            "persistent_cas_mutation_authorized": False,
            "legacy_v6_write_authorized": False,
            "remote_git_write_authorized": False,
        },
    }
