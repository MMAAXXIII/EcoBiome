"""Centralized read-only Scientific Foundation runtime configuration V1.

The default pre-activation policy is code-reviewed and content-bound. Future
active operation requires a separately supplied policy document plus its
independently configured expected canonical SHA-256.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .active_foundation_v1 import (
    ResolvedScientificFoundationV1,
    resolve_active_scientific_foundation_v1,
)
from .errors import PersistenceConfigurationError, PersistenceIntegrityError

RUNTIME_POLICY_ENV = "ECOBIOME_ACTIVE_SCIENTIFIC_FOUNDATION_RUNTIME_POLICY"
RUNTIME_POLICY_SHA_ENV = (
    "ECOBIOME_ACTIVE_SCIENTIFIC_FOUNDATION_RUNTIME_POLICY_SHA256"
)

FROZEN_V6_DATABASE_SHA256 = (
    "76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f"
)
FROZEN_V6_DESIGN_SHA256 = (
    "e0c732320b8bf901de3fd285ffcc41b74db8f1e0a227df89e0428e893e4f9181"
)
PRE_ACTIVATION_RUNTIME_POLICY_PAYLOAD_SHA256 = (
    "369a8873bcf693424b2c226d1313078c7ed26ff9be3b8da5ac29baad7ca81d97"
)
PRE_ACTIVATION_RUNTIME_POLICY_DOCUMENT: dict[str, object] = {
    "runtime_policy_payload_sha256": (
        PRE_ACTIVATION_RUNTIME_POLICY_PAYLOAD_SHA256
    ),
    "runtime_policy_payload": {'schema_version': 'ecobiome-active-scientific-foundation-runtime-policy-v1', 'activation_decision': 'legacy_pre_activation', 'pointer_required': False, 'parent_database_sha256': '76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f', 'snapshot_database_sha256': None, 'snapshot_manifest_file_sha256': None, 'snapshot_manifest_payload_sha256': None, 'pointer_contract_payload_sha256': '0f97ae748e056db5ca2e88d3a0b0723c6bba7c96ed937a94165871fd5d6d67ad', 'resolver_code_sha256': '58ee76d2a163ae844b8b8c89653e65a70be475acb1a8ed3bf61aa974b56cd2e9', 'consumer_migration_identity_sha256': None, 'created_at': '2026-08-27T04:39:00+02:00'},
}


@dataclass(frozen=True, slots=True)
class ActiveScientificFoundationRuntimeConfigV1:
    pointer_path: Path
    snapshot_root: Path
    legacy_database_path: Path
    runtime_policy_document: Mapping[str, Any]
    expected_runtime_policy_payload_sha256: str
    expected_legacy_database_sha256: str = FROZEN_V6_DATABASE_SHA256
    expected_schema_version: int = 6
    expected_schema_design_sha256: str = FROZEN_V6_DESIGN_SHA256

    def resolve(self) -> ResolvedScientificFoundationV1:
        return resolve_active_scientific_foundation_v1(
            pointer_path=self.pointer_path,
            snapshot_root=self.snapshot_root,
            legacy_database_path=self.legacy_database_path,
            expected_legacy_database_sha256=(
                self.expected_legacy_database_sha256
            ),
            expected_schema_version=self.expected_schema_version,
            expected_schema_design_sha256=(
                self.expected_schema_design_sha256
            ),
            runtime_policy_document=self.runtime_policy_document,
            expected_runtime_policy_payload_sha256=(
                self.expected_runtime_policy_payload_sha256
            ),
        )


def _canonical_data_root() -> Path:
    return (
        Path.home()
        / "Documents"
        / "EcoBiome-data"
    ).resolve()


def _default_pointer_path() -> Path:
    return (
        _canonical_data_root()
        / "scientific-foundation-active.json"
    ).resolve()


def _default_snapshot_root() -> Path:
    return (
        _canonical_data_root()
        / "scientific-foundation-snapshots"
    ).resolve()


def _default_legacy_database_path() -> Path:
    return (
        _canonical_data_root()
        / "scientific-foundation-v6"
        / "scientific-foundation-v6.sqlite3"
    ).resolve()


def _read_runtime_policy_document(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise PersistenceConfigurationError(
            f"Runtime policy document not found: {path}"
        )
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PersistenceIntegrityError(
            "Runtime policy document cannot be decoded"
        ) from exc
    if not isinstance(parsed, Mapping):
        raise PersistenceIntegrityError(
            "Runtime policy document must be an object"
        )
    return parsed


def build_default_runtime_config_v1() -> (
    ActiveScientificFoundationRuntimeConfigV1
):
    policy_path_raw = os.environ.get(RUNTIME_POLICY_ENV)
    expected_sha_raw = os.environ.get(RUNTIME_POLICY_SHA_ENV)

    if policy_path_raw is None and expected_sha_raw is None:
        policy_document: Mapping[str, Any] = (
            PRE_ACTIVATION_RUNTIME_POLICY_DOCUMENT
        )
        expected_sha = PRE_ACTIVATION_RUNTIME_POLICY_PAYLOAD_SHA256
    elif policy_path_raw is None or expected_sha_raw is None:
        raise PersistenceConfigurationError(
            "Runtime policy path and independently configured expected "
            "policy SHA-256 must be supplied together"
        )
    else:
        policy_document = _read_runtime_policy_document(
            Path(policy_path_raw).expanduser().resolve()
        )
        expected_sha = expected_sha_raw.strip()

    return ActiveScientificFoundationRuntimeConfigV1(
        pointer_path=_default_pointer_path(),
        snapshot_root=_default_snapshot_root(),
        legacy_database_path=_default_legacy_database_path(),
        runtime_policy_document=policy_document,
        expected_runtime_policy_payload_sha256=expected_sha,
    )


def resolve_default_scientific_foundation_v1() -> (
    ResolvedScientificFoundationV1
):
    return build_default_runtime_config_v1().resolve()
