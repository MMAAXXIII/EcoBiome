from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import ecobiome.knowledge_persistence.active_foundation_runtime_config_v1 as runtime_config_v1
import ecobiome.knowledge_persistence.active_foundation_v1 as active_v1
import ecobiome.knowledge_persistence.active_foundation_v2 as active_v2
from ecobiome.knowledge_persistence.active_foundation_runtime_config_v1 import (
    ActiveScientificFoundationRuntimeConfigV1,
    resolve_default_scientific_foundation_v1,
)
from ecobiome.knowledge_persistence.active_foundation_runtime_config_v2 import (
    LEGACY_ENV,
    POLICY_ENV,
    POLICY_SHA_ENV,
    resolve_default_scientific_foundation_v2,
)
from ecobiome.knowledge_persistence.active_foundation_v1 import (
    AUTHORIZE_ACTIVE_SNAPSHOT,
    ActiveScientificFoundationPointerV1,
    ActiveScientificFoundationRuntimePolicyV1,
    build_active_pointer_document,
    build_runtime_policy_document,
)
from ecobiome.knowledge_persistence.active_foundation_v2 import (
    _require_equal,
    resolve_active_scientific_foundation_v2,
)

DESIGN_SHA = "e0c732320b8bf901de3fd285ffcc41b74db8f1e0a227df89e0428e893e4f9181"
POINTER_CONTRACT_SHA = "0f97ae748e056db5ca2e88d3a0b0723c6bba7c96ed937a94165871fd5d6d67ad"
MIGRATION_IDENTITY_SHA = "6bf9c2a2dd789321786e28f2045d0974856aa826415a428dd2b361840b89be2a"
ROOT_SHA = "76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f"
PREDECESSOR_SHA = "2bc6d8524c529ebb52ce5c5a9b3b44f879dcdf9b62b5d6c8d2153443259dfde9"
PREDECESSOR_MANIFEST_SHA = (
    "7e0a50f571ea512ed8620c6e0fe1ae9cdc335e06ccbb9f978095dbd3a2479f20"
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_hashed(
    path: Path,
    payload_key: str,
    sha_key: str,
    payload: Mapping[str, object],
) -> tuple[str, str]:
    payload_sha = _canonical(payload)
    _write_json(path, {payload_key: payload, sha_key: payload_sha})
    return payload_sha, _sha(path)


def _create_database(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA user_version=6")
        conn.execute(
            """
            CREATE TABLE sf_schema_metadata(
                schema_name TEXT PRIMARY KEY,
                schema_version INTEGER NOT NULL,
                design_sha256 TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO sf_schema_metadata(
                schema_name, schema_version, design_sha256
            ) VALUES ('scientific_foundation', 6, ?)
            """,
            (DESIGN_SHA,),
        )
        conn.execute(
            """
            CREATE TABLE scientific_entities(
                id TEXT PRIMARY KEY,
                entity_kind TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _make_v1_control_plane(
    tmp_path: Path,
) -> tuple[ActiveScientificFoundationRuntimeConfigV1, Path, str]:
    legacy = tmp_path / "legacy.sqlite3"
    _create_database(legacy)
    legacy_sha = _sha(legacy)

    source_snapshot = tmp_path / "source-snapshot.sqlite3"
    _create_database(source_snapshot)
    snapshot_sha = _sha(source_snapshot)
    snapshot_root = tmp_path / "snapshots"
    snapshot_dir = snapshot_root / snapshot_sha
    snapshot_dir.mkdir(parents=True)
    snapshot_database = snapshot_dir / "scientific-foundation.sqlite3"
    snapshot_database.write_bytes(source_snapshot.read_bytes())

    manifest_payload = {
        "schema_version": "ecobiome-scientific-foundation-snapshot-manifest-v1-reviewed",
        "snapshot": {
            "database_sha256": snapshot_sha,
            "database_size_bytes": snapshot_database.stat().st_size,
            "schema_version": 6,
            "schema_design_sha256": DESIGN_SHA,
            "immutable": True,
        },
        "lineage": {"parent_database_sha256": legacy_sha},
        "validation": {
            "quick_check": ["ok"],
            "foreign_key_violation_count": 0,
        },
    }
    manifest_path = snapshot_dir / "snapshot-manifest.json"
    manifest_payload_sha, manifest_file_sha = _write_hashed(
        manifest_path,
        "manifest_payload",
        "manifest_payload_sha256",
        manifest_payload,
    )

    policy = ActiveScientificFoundationRuntimePolicyV1(
        activation_decision=AUTHORIZE_ACTIVE_SNAPSHOT,
        pointer_required=True,
        parent_database_sha256=legacy_sha,
        snapshot_database_sha256=snapshot_sha,
        snapshot_manifest_file_sha256=manifest_file_sha,
        snapshot_manifest_payload_sha256=manifest_payload_sha,
        pointer_contract_payload_sha256=POINTER_CONTRACT_SHA,
        resolver_code_sha256=_sha(Path(active_v1.__file__).resolve()),
        consumer_migration_identity_sha256=MIGRATION_IDENTITY_SHA,
        created_at="2026-08-29T00:00:00+00:00",
    )
    policy_document = build_runtime_policy_document(policy)
    policy_path = tmp_path / "runtime-policy-v1.json"
    _write_json(policy_path, policy_document)
    policy_sha = str(policy_document["runtime_policy_payload_sha256"])

    pointer = ActiveScientificFoundationPointerV1(
        snapshot_database_sha256=snapshot_sha,
        snapshot_manifest_file_sha256=manifest_file_sha,
        snapshot_manifest_payload_sha256=manifest_payload_sha,
        parent_database_sha256=legacy_sha,
        activation_authorization_payload_sha256=policy_sha,
        created_at="2026-08-29T00:00:00+00:00",
    )
    pointer_path = tmp_path / "scientific-foundation-active.json"
    _write_json(pointer_path, build_active_pointer_document(pointer))

    config = ActiveScientificFoundationRuntimeConfigV1(
        pointer_path=pointer_path,
        snapshot_root=snapshot_root,
        legacy_database_path=legacy,
        runtime_policy_document=policy_document,
        expected_runtime_policy_payload_sha256=policy_sha,
        expected_legacy_database_sha256=legacy_sha,
        expected_schema_version=6,
        expected_schema_design_sha256=DESIGN_SHA,
    )
    return config, policy_path, policy_sha


def test_v2_runtime_config_is_backward_compatible_with_current_v1_control_plane(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    config, policy_path, policy_sha = _make_v1_control_plane(tmp_path)
    monkeypatch.setattr(
        runtime_config_v1,
        "build_default_runtime_config_v1",
        lambda: config,
    )
    monkeypatch.setenv(POLICY_ENV, str(policy_path))
    monkeypatch.setenv(POLICY_SHA_ENV, policy_sha)
    monkeypatch.delenv(LEGACY_ENV, raising=False)

    v1 = resolve_default_scientific_foundation_v1()
    v2 = resolve_default_scientific_foundation_v2()
    assert v2.resolution_mode == v1.resolution_mode
    assert v2.database_sha256 == v1.database_sha256
    assert Path(v2.database_path).resolve() == Path(v1.database_path).resolve()
    assert v2.policy_schema_version.endswith("runtime-policy-v1")


def test_v2_resolver_accepts_true_derived_snapshot_lineage(
    tmp_path: Path,
) -> None:
    source_db = tmp_path / "source-successor.sqlite3"
    _create_database(source_db)
    target_sha = _sha(source_db)
    root = tmp_path / "snapshots"
    target_dir = root / target_sha
    target_dir.mkdir(parents=True)
    target_db = target_dir / "scientific-foundation.sqlite3"
    target_db.write_bytes(source_db.read_bytes())
    assert _sha(target_db) == target_sha

    manifest = {
        "schema_version": "ecobiome-scientific-foundation-snapshot-manifest-v1-reviewed",
        "snapshot": {
            "created_at": "2026-08-29T00:00:00+00:00",
            "database_sha256": target_sha,
            "database_size_bytes": target_db.stat().st_size,
            "immutable": True,
            "purpose": "RATE-4S synthetic V2 derived-snapshot probe",
            "schema_design_sha256": DESIGN_SHA,
            "schema_version": 6,
        },
        "lineage": {
            "parent_kind": "derived_snapshot",
            "parent_database_sha256": PREDECESSOR_SHA,
            "parent_manifest_sha256": PREDECESSOR_MANIFEST_SHA,
            "promotion_plan_sha256": "6e2837f6363bfc6d9cd5fe209e205301134482466ca50bb8ee7c28462f024c1d",
            "source_repo_head": "9b6dfe5dc7e39870f26aba4bb23350dd75de59d2",
        },
        "reviewed_inputs": {},
        "runtime_and_persistence_identity": {},
        "validation": {
            "quick_check": ["ok"],
            "foreign_key_violation_count": 0,
        },
        "boundaries": {
            "active_pointer_updated": False,
            "numeric_rate_model_authorized": False,
        },
    }
    manifest_payload_sha, manifest_file_sha = _write_hashed(
        target_dir / "snapshot-manifest.json",
        "manifest_payload",
        "manifest_payload_sha256",
        manifest,
    )

    resolver_sha = _sha(Path(active_v2.__file__).resolve())
    policy = {
        "schema_version": "ecobiome-active-scientific-foundation-runtime-policy-v2",
        "activation_decision": "authorize_active_snapshot",
        "transition_kind": "derived_snapshot_successor",
        "pointer_required": True,
        "root_database_sha256": ROOT_SHA,
        "predecessor_snapshot_database_sha256": PREDECESSOR_SHA,
        "predecessor_snapshot_manifest_payload_sha256": PREDECESSOR_MANIFEST_SHA,
        "target_snapshot_database_sha256": target_sha,
        "target_snapshot_manifest_file_sha256": manifest_file_sha,
        "target_snapshot_manifest_payload_sha256": manifest_payload_sha,
        "pointer_contract_payload_sha256": _canonical({"schema": "pointer-v2-probe"}),
        "resolver_code_sha256": resolver_sha,
        "consumer_migration_identity_sha256": MIGRATION_IDENTITY_SHA,
        "created_at": "2026-08-29T00:00:00+00:00",
    }
    policy_path = tmp_path / "runtime-policy-v2.json"
    policy_sha, _ = _write_hashed(
        policy_path,
        "runtime_policy_payload",
        "runtime_policy_payload_sha256",
        policy,
    )

    pointer = {
        "schema_version": "ecobiome-active-scientific-foundation-pointer-v2",
        "root_database_sha256": ROOT_SHA,
        "predecessor_snapshot_database_sha256": PREDECESSOR_SHA,
        "predecessor_snapshot_manifest_payload_sha256": PREDECESSOR_MANIFEST_SHA,
        "snapshot_database_sha256": target_sha,
        "snapshot_manifest_file_sha256": manifest_file_sha,
        "snapshot_manifest_payload_sha256": manifest_payload_sha,
        "activation_authorization_payload_sha256": policy_sha,
        "created_at": "2026-08-29T00:00:00+00:00",
    }
    pointer_path = tmp_path / "active-pointer-v2.json"
    _write_hashed(
        pointer_path,
        "pointer_payload",
        "pointer_payload_sha256",
        pointer,
    )

    resolved = resolve_active_scientific_foundation_v2(
        runtime_policy_path=policy_path,
        trusted_runtime_policy_payload_sha256=policy_sha,
        active_pointer_path=pointer_path,
        snapshot_root=root,
        expected_resolver_code_sha256=resolver_sha,
    )
    assert resolved.database_sha256 == target_sha
    assert resolved.predecessor_snapshot_database_sha256 == PREDECESSOR_SHA
    assert resolved.root_database_sha256 == ROOT_SHA


def test_v2_lineage_distinguishes_root_from_immediate_parent() -> None:
    try:
        _require_equal("immediate parent", ROOT_SHA, PREDECESSOR_SHA)
    except ValueError:
        pass
    else:
        raise AssertionError("root V6 must not be accepted as immediate predecessor")
