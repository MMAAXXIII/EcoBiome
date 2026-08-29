from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

import ecobiome.knowledge_persistence.active_foundation_v1 as active
from ecobiome.knowledge_persistence.active_foundation_runtime_config_v1 import (
    PRE_ACTIVATION_RUNTIME_POLICY_DOCUMENT,
    PRE_ACTIVATION_RUNTIME_POLICY_PAYLOAD_SHA256,
    RUNTIME_POLICY_ENV,
    RUNTIME_POLICY_SHA_ENV,
    ActiveScientificFoundationRuntimeConfigV1,
    build_default_runtime_config_v1,
)
from ecobiome.knowledge_persistence.active_foundation_v1 import (
    LEGACY_PRE_ACTIVATION,
    ActiveScientificFoundationRuntimePolicyV1,
    build_runtime_policy_document,
    canonical_sha256,
    sha256_file,
)
from ecobiome.knowledge_persistence.errors import (
    PersistenceConfigurationError,
)

DESIGN_SHA = "d" * 64
POINTER_CONTRACT_SHA = "c" * 64


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
                schema_name,schema_version,design_sha256
            ) VALUES ('scientific_foundation',6,?)
            """,
            (DESIGN_SHA,),
        )
        conn.commit()
    finally:
        conn.close()


def _resolver_code_sha() -> str:
    return sha256_file(Path(active.__file__).resolve())


def test_builtin_pre_activation_policy_sha_is_content_bound() -> None:
    payload = PRE_ACTIVATION_RUNTIME_POLICY_DOCUMENT[
        "runtime_policy_payload"
    ]
    assert canonical_sha256(payload) == (
        PRE_ACTIVATION_RUNTIME_POLICY_PAYLOAD_SHA256
    )
    assert (
        PRE_ACTIVATION_RUNTIME_POLICY_DOCUMENT[
            "runtime_policy_payload_sha256"
        ]
        == PRE_ACTIVATION_RUNTIME_POLICY_PAYLOAD_SHA256
    )


def test_default_runtime_policy_env_requires_path_and_sha_together(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv(
        RUNTIME_POLICY_ENV,
        str(tmp_path / "policy.json"),
    )
    monkeypatch.delenv(
        RUNTIME_POLICY_SHA_ENV,
        raising=False,
    )
    with pytest.raises(
        PersistenceConfigurationError,
        match="must be supplied together",
    ):
        build_default_runtime_config_v1()


def test_external_policy_expected_sha_is_not_derived_from_policy_file(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            PRE_ACTIVATION_RUNTIME_POLICY_DOCUMENT,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    expected = "f" * 64
    monkeypatch.setenv(
        RUNTIME_POLICY_ENV,
        str(policy_path),
    )
    monkeypatch.setenv(
        RUNTIME_POLICY_SHA_ENV,
        expected,
    )
    config = build_default_runtime_config_v1()
    assert config.expected_runtime_policy_payload_sha256 == expected


def test_explicit_runtime_config_resolves_verified_legacy(
    tmp_path: Path,
) -> None:
    legacy = tmp_path / "legacy.sqlite3"
    _create_database(legacy)
    legacy_sha = sha256_file(legacy)

    policy = ActiveScientificFoundationRuntimePolicyV1(
        activation_decision=LEGACY_PRE_ACTIVATION,
        pointer_required=False,
        parent_database_sha256=legacy_sha,
        snapshot_database_sha256=None,
        snapshot_manifest_file_sha256=None,
        snapshot_manifest_payload_sha256=None,
        pointer_contract_payload_sha256=POINTER_CONTRACT_SHA,
        resolver_code_sha256=_resolver_code_sha(),
        consumer_migration_identity_sha256=None,
        created_at="2026-08-27T04:39:00+02:00",
    )
    document = build_runtime_policy_document(policy)

    config = ActiveScientificFoundationRuntimeConfigV1(
        pointer_path=tmp_path / "missing-active.json",
        snapshot_root=tmp_path / "snapshots",
        legacy_database_path=legacy,
        runtime_policy_document=document,
        expected_runtime_policy_payload_sha256=document[
            "runtime_policy_payload_sha256"
        ],
        expected_legacy_database_sha256=legacy_sha,
        expected_schema_version=6,
        expected_schema_design_sha256=DESIGN_SHA,
    )
    result = config.resolve()
    assert result.resolution_mode == "legacy_fallback"
    assert result.database_path == legacy.resolve()
