from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Mapping
from pathlib import Path

from ecobiome.knowledge_persistence.active_foundation_runtime_config_v1 import (
    resolve_default_scientific_foundation_v1,
)
from ecobiome.knowledge_persistence.active_foundation_runtime_config_v2 import (
    resolve_default_scientific_foundation_v2,
)
from ecobiome.knowledge_persistence.active_foundation_v2 import (
    _require_equal,
    resolve_active_scientific_foundation_v2,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _write_hashed(
    path: Path,
    payload_key: str,
    sha_key: str,
    payload: Mapping[str, object],
) -> tuple[str, str]:
    payload_sha = _canonical(payload)
    path.write_text(
        json.dumps({payload_key: payload, sha_key: payload_sha}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload_sha, _sha(path)


def test_v2_runtime_config_is_backward_compatible_with_current_v1_control_plane() -> None:
    v1 = resolve_default_scientific_foundation_v1()
    v2 = resolve_default_scientific_foundation_v2()
    assert v2.resolution_mode == v1.resolution_mode
    assert v2.database_sha256 == v1.database_sha256
    assert Path(v2.database_path).resolve() == Path(v1.database_path).resolve()
    assert v2.policy_schema_version.endswith("runtime-policy-v1")


def test_v2_resolver_accepts_true_derived_snapshot_lineage(tmp_path: Path) -> None:
    source_db = Path(r"C:\Users\oboco\Documents\EcoBiome-data\scientific-foundation-snapshots\cc1117de65d62675ed1d6e1caed00b9fe69d1a6dd0d7043334aeacf70b633ae0\scientific-foundation.sqlite3")
    root = tmp_path / "snapshots"
    target_dir = root / "cc1117de65d62675ed1d6e1caed00b9fe69d1a6dd0d7043334aeacf70b633ae0"
    target_dir.mkdir(parents=True)
    target_db = target_dir / "scientific-foundation.sqlite3"
    shutil.copyfile(source_db, target_db)
    assert _sha(target_db) == "cc1117de65d62675ed1d6e1caed00b9fe69d1a6dd0d7043334aeacf70b633ae0"

    manifest = {
        "schema_version": "ecobiome-scientific-foundation-snapshot-manifest-v1-reviewed",
        "snapshot": {
            "created_at": "2026-08-29T00:00:00+00:00",
            "database_sha256": "cc1117de65d62675ed1d6e1caed00b9fe69d1a6dd0d7043334aeacf70b633ae0",
            "database_size_bytes": 684032,
            "immutable": True,
            "purpose": "RATE-4S synthetic V2 derived-snapshot probe",
            "schema_design_sha256": "e0c732320b8bf901de3fd285ffcc41b74db8f1e0a227df89e0428e893e4f9181",
            "schema_version": 6,
        },
        "lineage": {
            "parent_kind": "derived_snapshot",
            "parent_database_sha256": "2bc6d8524c529ebb52ce5c5a9b3b44f879dcdf9b62b5d6c8d2153443259dfde9",
            "parent_manifest_sha256": "7e0a50f571ea512ed8620c6e0fe1ae9cdc335e06ccbb9f978095dbd3a2479f20",
            "promotion_plan_sha256": "6e2837f6363bfc6d9cd5fe209e205301134482466ca50bb8ee7c28462f024c1d",
            "source_repo_head": "f55ce1d9c93978e4860d7e43ddc871b4576fc260",
        },
        "reviewed_inputs": {},
        "runtime_and_persistence_identity": {},
        "validation": {"quick_check": ["ok"], "foreign_key_violation_count": 0},
        "boundaries": {"active_pointer_updated": False, "numeric_rate_model_authorized": False},
    }
    manifest_payload_sha, manifest_file_sha = _write_hashed(
        target_dir / "snapshot-manifest.json",
        "manifest_payload",
        "manifest_payload_sha256",
        manifest,
    )

    policy = {
        "schema_version": "ecobiome-active-scientific-foundation-runtime-policy-v2",
        "activation_decision": "authorize_active_snapshot",
        "transition_kind": "derived_snapshot_successor",
        "pointer_required": True,
        "root_database_sha256": "76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f",
        "predecessor_snapshot_database_sha256": "2bc6d8524c529ebb52ce5c5a9b3b44f879dcdf9b62b5d6c8d2153443259dfde9",
        "predecessor_snapshot_manifest_payload_sha256": "7e0a50f571ea512ed8620c6e0fe1ae9cdc335e06ccbb9f978095dbd3a2479f20",
        "target_snapshot_database_sha256": "cc1117de65d62675ed1d6e1caed00b9fe69d1a6dd0d7043334aeacf70b633ae0",
        "target_snapshot_manifest_file_sha256": manifest_file_sha,
        "target_snapshot_manifest_payload_sha256": manifest_payload_sha,
        "pointer_contract_payload_sha256": _canonical({"schema": "pointer-v2-probe"}),
        "resolver_code_sha256": "513759177406ef79b239c243063bada65944d80b82cdaf9f81047c7509340a83",
        "consumer_migration_identity_sha256": "6bf9c2a2dd789321786e28f2045d0974856aa826415a428dd2b361840b89be2a",
        "created_at": "2026-08-29T00:00:00+00:00",
    }
    policy_path = tmp_path / "runtime-policy-v2.json"
    policy_sha, _ = _write_hashed(
        policy_path, "runtime_policy_payload", "runtime_policy_payload_sha256", policy
    )

    pointer = {
        "schema_version": "ecobiome-active-scientific-foundation-pointer-v2",
        "root_database_sha256": "76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f",
        "predecessor_snapshot_database_sha256": "2bc6d8524c529ebb52ce5c5a9b3b44f879dcdf9b62b5d6c8d2153443259dfde9",
        "predecessor_snapshot_manifest_payload_sha256": "7e0a50f571ea512ed8620c6e0fe1ae9cdc335e06ccbb9f978095dbd3a2479f20",
        "snapshot_database_sha256": "cc1117de65d62675ed1d6e1caed00b9fe69d1a6dd0d7043334aeacf70b633ae0",
        "snapshot_manifest_file_sha256": manifest_file_sha,
        "snapshot_manifest_payload_sha256": manifest_payload_sha,
        "activation_authorization_payload_sha256": policy_sha,
        "created_at": "2026-08-29T00:00:00+00:00",
    }
    pointer_path = tmp_path / "active-pointer-v2.json"
    _write_hashed(pointer_path, "pointer_payload", "pointer_payload_sha256", pointer)

    resolved = resolve_active_scientific_foundation_v2(
        runtime_policy_path=policy_path,
        trusted_runtime_policy_payload_sha256=policy_sha,
        active_pointer_path=pointer_path,
        snapshot_root=root,
        expected_resolver_code_sha256="513759177406ef79b239c243063bada65944d80b82cdaf9f81047c7509340a83",
    )
    assert resolved.database_sha256 == "cc1117de65d62675ed1d6e1caed00b9fe69d1a6dd0d7043334aeacf70b633ae0"
    assert resolved.predecessor_snapshot_database_sha256 == "2bc6d8524c529ebb52ce5c5a9b3b44f879dcdf9b62b5d6c8d2153443259dfde9"
    assert resolved.root_database_sha256 == "76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f"


def test_v2_lineage_distinguishes_root_from_immediate_parent() -> None:
    try:
        _require_equal("immediate parent", "76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f", "2bc6d8524c529ebb52ce5c5a9b3b44f879dcdf9b62b5d6c8d2153443259dfde9")
    except ValueError:
        pass
    else:
        raise AssertionError("root V6 must not be accepted as immediate predecessor")
