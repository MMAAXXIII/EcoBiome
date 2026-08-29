from __future__ import annotations

import hashlib
import inspect
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from ecobiome.knowledge_persistence import active_foundation_v1 as _v1

POLICY_SCHEMA_V2 = "ecobiome-active-scientific-foundation-runtime-policy-v2"
POINTER_SCHEMA_V2 = "ecobiome-active-scientific-foundation-pointer-v2"
MANIFEST_SCHEMA_V1 = "ecobiome-scientific-foundation-snapshot-manifest-v1-reviewed"


@dataclass(frozen=True, slots=True)
class ActiveScientificFoundationResolutionV2:
    resolution_mode: str
    database_path: Path
    database_sha256: str
    snapshot_manifest_path: Path
    snapshot_manifest_file_sha256: str
    snapshot_manifest_payload_sha256: str
    policy_schema_version: str
    pointer_schema_version: str
    root_database_sha256: str
    predecessor_snapshot_database_sha256: str | None


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_hashed_document(
    path: Path,
    *,
    payload_key: str,
    payload_sha_key: str,
    trusted_payload_sha256: str | None = None,
) -> tuple[dict[str, Any], str]:
    document = cast(
        dict[str, Any], json.loads(path.read_text(encoding="utf-8"))
    )
    payload = cast(dict[str, Any], document[payload_key])
    stored_sha = cast(str, document[payload_sha_key])
    calculated = _canonical_sha256(payload)
    if stored_sha != calculated:
        raise ValueError(f"canonical payload SHA mismatch for {path}")
    if trusted_payload_sha256 is not None and calculated != trusted_payload_sha256:
        raise ValueError(f"trusted payload SHA mismatch for {path}")
    return payload, calculated


def _require_equal(label: str, left: Any, right: Any) -> None:
    if left != right:
        raise ValueError(f"{label} mismatch: {left!r} != {right!r}")


def _resolve_active_scientific_foundation_v2_strict(
    *,
    runtime_policy_path: Path,
    trusted_runtime_policy_payload_sha256: str,
    active_pointer_path: Path,
    snapshot_root: Path,
    expected_resolver_code_sha256: str | None = None,
) -> ActiveScientificFoundationResolutionV2:
    policy, policy_sha = _read_hashed_document(
        runtime_policy_path,
        payload_key="runtime_policy_payload",
        payload_sha_key="runtime_policy_payload_sha256",
        trusted_payload_sha256=trusted_runtime_policy_payload_sha256,
    )
    _require_equal("runtime policy schema", policy["schema_version"], POLICY_SCHEMA_V2)
    _require_equal("activation decision", policy["activation_decision"], "authorize_active_snapshot")
    _require_equal("transition kind", policy["transition_kind"], "derived_snapshot_successor")
    _require_equal("pointer required", policy["pointer_required"], True)
    if expected_resolver_code_sha256 is not None:
        _require_equal("resolver code SHA", policy["resolver_code_sha256"], expected_resolver_code_sha256)

    pointer, _ = _read_hashed_document(
        active_pointer_path,
        payload_key="pointer_payload",
        payload_sha_key="pointer_payload_sha256",
    )
    _require_equal("pointer schema", pointer["schema_version"], POINTER_SCHEMA_V2)

    for label, policy_key, pointer_key in (
        ("root database", "root_database_sha256", "root_database_sha256"),
        ("predecessor database", "predecessor_snapshot_database_sha256", "predecessor_snapshot_database_sha256"),
        ("predecessor manifest", "predecessor_snapshot_manifest_payload_sha256", "predecessor_snapshot_manifest_payload_sha256"),
        ("target database", "target_snapshot_database_sha256", "snapshot_database_sha256"),
        ("target manifest file", "target_snapshot_manifest_file_sha256", "snapshot_manifest_file_sha256"),
        ("target manifest payload", "target_snapshot_manifest_payload_sha256", "snapshot_manifest_payload_sha256"),
    ):
        _require_equal(label, policy[policy_key], pointer[pointer_key])
    _require_equal(
        "activation authorization",
        pointer["activation_authorization_payload_sha256"],
        policy_sha,
    )

    target_sha = policy["target_snapshot_database_sha256"]
    target_dir = snapshot_root / target_sha
    database_path = target_dir / "scientific-foundation.sqlite3"
    manifest_path = target_dir / "snapshot-manifest.json"
    if not database_path.is_file() or not manifest_path.is_file():
        raise ValueError("target snapshot database/manifest missing")

    manifest_file_sha = _file_sha256(manifest_path)
    _require_equal("manifest file SHA", manifest_file_sha, policy["target_snapshot_manifest_file_sha256"])
    manifest, manifest_payload_sha = _read_hashed_document(
        manifest_path,
        payload_key="manifest_payload",
        payload_sha_key="manifest_payload_sha256",
        trusted_payload_sha256=policy["target_snapshot_manifest_payload_sha256"],
    )
    _require_equal("manifest schema", manifest["schema_version"], MANIFEST_SCHEMA_V1)
    _require_equal("manifest target database", manifest["snapshot"]["database_sha256"], target_sha)
    _require_equal(
        "manifest immediate parent",
        manifest["lineage"]["parent_database_sha256"],
        policy["predecessor_snapshot_database_sha256"],
    )
    _require_equal(
        "manifest parent manifest",
        manifest["lineage"]["parent_manifest_sha256"],
        policy["predecessor_snapshot_manifest_payload_sha256"],
    )
    _require_equal("manifest parent kind", manifest["lineage"]["parent_kind"], "derived_snapshot")

    db_sha = _file_sha256(database_path)
    _require_equal("database SHA", db_sha, target_sha)
    _require_equal(
        "database size",
        database_path.stat().st_size,
        manifest["snapshot"]["database_size_bytes"],
    )

    uri = f"file:{database_path.as_posix()}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        quick = [row[0] for row in conn.execute("PRAGMA quick_check")]
        if quick != ["ok"]:
            raise ValueError(f"snapshot quick_check failed: {quick!r}")
        fk = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk:
            raise ValueError(f"snapshot foreign_key_check failed: {fk[:10]!r}")
        _require_equal(
            "snapshot schema version",
            conn.execute("PRAGMA user_version").fetchone()[0],
            manifest["snapshot"]["schema_version"],
        )
    finally:
        conn.close()

    return ActiveScientificFoundationResolutionV2(
        resolution_mode="active_snapshot",
        database_path=database_path.resolve(),
        database_sha256=db_sha,
        snapshot_manifest_path=manifest_path.resolve(),
        snapshot_manifest_file_sha256=manifest_file_sha,
        snapshot_manifest_payload_sha256=manifest_payload_sha,
        policy_schema_version=POLICY_SCHEMA_V2,
        pointer_schema_version=POINTER_SCHEMA_V2,
        root_database_sha256=policy["root_database_sha256"],
        predecessor_snapshot_database_sha256=policy["predecessor_snapshot_database_sha256"],
    )


# The strict V2 implementation is private; the public name below is the
# compatibility dispatcher for low-level consumers migrated by module path only.


def _legacy_bound_arguments(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    signature = inspect.signature(
        _v1.resolve_active_scientific_foundation_v1
    )
    bound = signature.bind_partial(*args, **kwargs)
    return dict(bound.arguments)


def _path_from_bound(
    bound: dict[str, Any],
    *fragments: str,
) -> Path | None:
    for name, value in bound.items():
        lowered = name.lower()
        if all(fragment in lowered for fragment in fragments):
            if isinstance(value, Path):
                return value
            if isinstance(value, str):
                return Path(value)
    return None


def _str_from_bound(
    bound: dict[str, Any],
    *fragments: str,
) -> str | None:
    for name, value in bound.items():
        lowered = name.lower()
        if all(fragment in lowered for fragment in fragments) and isinstance(value, str):
            return value
    return None


def _policy_path_from_call(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    raw = kwargs.get("runtime_policy_path")
    if isinstance(raw, Path):
        try:
            return raw, _legacy_bound_arguments(args, kwargs)
        except TypeError:
            return raw, {}
    if isinstance(raw, str):
        try:
            return Path(raw), _legacy_bound_arguments(args, kwargs)
        except TypeError:
            return Path(raw), {}
    bound = _legacy_bound_arguments(args, kwargs)
    path = _path_from_bound(bound, "runtime", "policy")
    if path is None:
        raise ValueError("runtime policy path could not be resolved")
    return path, bound


def resolve_active_scientific_foundation_v2(
    *args: Any,
    **kwargs: Any,
) -> Any:
    runtime_policy_path, bound = _policy_path_from_call(args, kwargs)
    document = cast(
        dict[str, Any],
        json.loads(runtime_policy_path.read_text(encoding="utf-8")),
    )
    payload = cast(dict[str, Any], document["runtime_policy_payload"])
    schema = cast(str, payload["schema_version"])

    if schema == "ecobiome-active-scientific-foundation-runtime-policy-v1":
        return _v1.resolve_active_scientific_foundation_v1(
            *args,
            **kwargs,
        )

    if schema != POLICY_SCHEMA_V2:
        raise ValueError(f"unsupported runtime-policy schema: {schema}")

    # Native V2 callers use the strict V2 keyword interface directly.
    native_keys = {
        "runtime_policy_path",
        "trusted_runtime_policy_payload_sha256",
        "active_pointer_path",
        "snapshot_root",
    }
    if native_keys.issubset(kwargs):
        return _resolve_active_scientific_foundation_v2_strict(
            runtime_policy_path=Path(kwargs["runtime_policy_path"]),
            trusted_runtime_policy_payload_sha256=cast(
                str,
                kwargs["trusted_runtime_policy_payload_sha256"],
            ),
            active_pointer_path=Path(kwargs["active_pointer_path"]),
            snapshot_root=Path(kwargs["snapshot_root"]),
            expected_resolver_code_sha256=cast(
                str | None,
                kwargs.get("expected_resolver_code_sha256"),
            ),
        )

    # Migrated low-level consumers retain their old V1 call shape.
    if not bound:
        bound = _legacy_bound_arguments(args, kwargs)
    trusted_sha = (
        _str_from_bound(bound, "trusted", "policy", "sha")
        or _str_from_bound(bound, "runtime", "policy", "sha")
    )
    pointer_path = _path_from_bound(bound, "pointer")
    snapshot_root = _path_from_bound(bound, "snapshot", "root")
    if trusted_sha is None or pointer_path is None or snapshot_root is None:
        raise ValueError(
            "derived V2 resolution could not map the legacy low-level call "
            "to trusted policy SHA, active pointer path, and snapshot root"
        )
    return _resolve_active_scientific_foundation_v2_strict(
        runtime_policy_path=runtime_policy_path,
        trusted_runtime_policy_payload_sha256=trusted_sha,
        active_pointer_path=pointer_path,
        snapshot_root=snapshot_root,
        expected_resolver_code_sha256=_file_sha256(Path(__file__)),
    )


# Compatibility names used by migrated V1 consumers.
resolve_active_scientific_foundation_v1 = (
    resolve_active_scientific_foundation_v2
)
ActiveScientificFoundationResolutionV1 = (
    ActiveScientificFoundationResolutionV2
)


def __getattr__(name: str) -> Any:
    # Preserve any other low-level V1 constants/types imported by historical
    # consumers while routing the resolver itself through the dispatcher above.
    if hasattr(_v1, name):
        return getattr(_v1, name)
    raise AttributeError(name)
