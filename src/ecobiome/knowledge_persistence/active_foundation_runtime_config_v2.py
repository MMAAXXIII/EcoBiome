from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast

from ecobiome.knowledge_persistence.active_foundation_v2 import (
    POLICY_SCHEMA_V2,
    ActiveScientificFoundationResolutionV2,
    resolve_active_scientific_foundation_v2,
)

POLICY_ENV = "ECOBIOME_ACTIVE_SCIENTIFIC_FOUNDATION_RUNTIME_POLICY"
POLICY_SHA_ENV = "ECOBIOME_ACTIVE_SCIENTIFIC_FOUNDATION_RUNTIME_POLICY_SHA256"
LEGACY_ENV = "ECOBIOME_SCIENTIFIC_FOUNDATION_V6"


def _default_data_root() -> Path:
    return Path.home() / "Documents" / "EcoBiome-data"


def resolve_default_scientific_foundation_v2() -> ActiveScientificFoundationResolutionV2:
    if os.environ.get(LEGACY_ENV):
        raise ValueError("legacy ECOBIOME_SCIENTIFIC_FOUNDATION_V6 must remain absent")

    policy_raw = os.environ.get(POLICY_ENV)
    trusted_sha = os.environ.get(POLICY_SHA_ENV)
    if not policy_raw or not trusted_sha:
        raise ValueError("active Scientific Foundation runtime-policy environment is incomplete")

    policy_path = Path(policy_raw)
    document = cast(
        dict[str, Any], json.loads(policy_path.read_text(encoding="utf-8"))
    )
    policy_payload = cast(dict[str, Any], document["runtime_policy_payload"])
    schema = policy_payload["schema_version"]

    if schema == "ecobiome-active-scientific-foundation-runtime-policy-v1":
        from ecobiome.knowledge_persistence.active_foundation_runtime_config_v1 import (
            resolve_default_scientific_foundation_v1,
        )

        resolved = resolve_default_scientific_foundation_v1()
        manifest_path = Path(resolved.database_path).parent / "snapshot-manifest.json"
        manifest_doc = cast(
            dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8"))
        )
        manifest_payload = cast(dict[str, Any], manifest_doc["manifest_payload"])
        policy = policy_payload
        return ActiveScientificFoundationResolutionV2(
            resolution_mode=resolved.resolution_mode,
            database_path=Path(resolved.database_path).resolve(),
            database_sha256=resolved.database_sha256,
            snapshot_manifest_path=manifest_path.resolve(),
            snapshot_manifest_file_sha256=policy["snapshot_manifest_file_sha256"],
            snapshot_manifest_payload_sha256=policy["snapshot_manifest_payload_sha256"],
            policy_schema_version=schema,
            pointer_schema_version="ecobiome-active-scientific-foundation-pointer-v1",
            root_database_sha256=policy["parent_database_sha256"],
            predecessor_snapshot_database_sha256=manifest_payload["lineage"]["parent_database_sha256"],
        )

    if schema != POLICY_SCHEMA_V2:
        raise ValueError(f"unsupported runtime-policy schema: {schema}")

    data_root = _default_data_root()
    return resolve_active_scientific_foundation_v2(
        runtime_policy_path=policy_path,
        trusted_runtime_policy_payload_sha256=trusted_sha,
        active_pointer_path=data_root / "scientific-foundation-active.json",
        snapshot_root=data_root / "scientific-foundation-snapshots",
    )


# Compatibility alias for migrated consumers retaining the old symbol name.
resolve_default_scientific_foundation_v1 = resolve_default_scientific_foundation_v2
