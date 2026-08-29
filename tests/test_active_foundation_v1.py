from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

import ecobiome.knowledge_persistence.active_foundation_v1 as active
from ecobiome.knowledge_persistence.active_foundation_v1 import (
    ACTIVE_POINTER_SCHEMA_V1,
    AUTHORIZE_ACTIVE_SNAPSHOT,
    LEGACY_PRE_ACTIVATION,
    ActiveScientificFoundationPointerV1,
    ActiveScientificFoundationRuntimePolicyV1,
    build_active_pointer_document,
    build_runtime_policy_document,
    canonical_sha256,
    resolve_active_scientific_foundation_v1,
    sha256_file,
)
from ecobiome.knowledge_persistence.errors import (
    PersistenceConfigurationError,
    PersistenceIntegrityError,
)

DESIGN_SHA = "d" * 64
POINTER_CONTRACT_SHA = "c" * 64
MIGRATION_IDENTITY_SHA = "a" * 64


def _create_database(
    path: Path,
    *,
    marker: str | None = None,
) -> None:
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
        conn.execute(
            """
            CREATE TABLE scientific_entities(
                id TEXT PRIMARY KEY,
                entity_kind TEXT NOT NULL
            )
            """
        )
        if marker is not None:
            conn.execute(
                """
                INSERT INTO scientific_entities(id,entity_kind)
                VALUES (?, 'test')
                """,
                (marker,),
            )
        conn.commit()
    finally:
        conn.close()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _resolver_code_sha() -> str:
    return sha256_file(Path(active.__file__).resolve())


def _make_snapshot(
    snapshot_root: Path,
    *,
    legacy_sha: str,
    marker: str | None = None,
) -> dict[str, Any]:
    temporary_db = snapshot_root.parent / (
        f"snapshot-{marker or 'default'}.sqlite3"
    )
    _create_database(temporary_db, marker=marker)
    database_sha = sha256_file(temporary_db)

    snapshot_dir = snapshot_root / database_sha
    snapshot_dir.mkdir()
    database = snapshot_dir / "scientific-foundation.sqlite3"
    database.write_bytes(temporary_db.read_bytes())

    manifest_payload = {
        "schema_version": (
            "ecobiome-scientific-foundation-"
            "snapshot-manifest-v1-reviewed"
        ),
        "snapshot": {
            "database_sha256": database_sha,
            "database_size_bytes": database.stat().st_size,
            "schema_version": 6,
            "schema_design_sha256": DESIGN_SHA,
            "immutable": True,
        },
        "lineage": {
            "parent_database_sha256": legacy_sha,
        },
        "validation": {
            "quick_check": ["ok"],
            "foreign_key_violation_count": 0,
        },
    }
    manifest_document = {
        "manifest_payload_sha256": canonical_sha256(
            manifest_payload
        ),
        "manifest_payload": manifest_payload,
    }
    manifest = snapshot_dir / "snapshot-manifest.json"
    _write_json(manifest, manifest_document)

    return {
        "snapshot_dir": snapshot_dir,
        "database": database,
        "database_sha": database_sha,
        "manifest": manifest,
        "manifest_file_sha": sha256_file(manifest),
        "manifest_payload_sha": manifest_document[
            "manifest_payload_sha256"
        ],
    }


def _base_fixture(tmp_path: Path) -> dict[str, Any]:
    legacy = tmp_path / "legacy.sqlite3"
    _create_database(legacy)
    legacy_sha = sha256_file(legacy)

    snapshot_root = tmp_path / "snapshots"
    snapshot_root.mkdir()
    snapshot = _make_snapshot(
        snapshot_root,
        legacy_sha=legacy_sha,
    )

    return {
        "legacy": legacy,
        "legacy_sha": legacy_sha,
        "snapshot_root": snapshot_root,
        **snapshot,
    }


def _preactivation_policy(
    fixture: dict[str, Any],
    *,
    resolver_code_sha: str | None = None,
) -> dict[str, object]:
    policy = ActiveScientificFoundationRuntimePolicyV1(
        activation_decision=LEGACY_PRE_ACTIVATION,
        pointer_required=False,
        parent_database_sha256=fixture["legacy_sha"],
        snapshot_database_sha256=None,
        snapshot_manifest_file_sha256=None,
        snapshot_manifest_payload_sha256=None,
        pointer_contract_payload_sha256=POINTER_CONTRACT_SHA,
        resolver_code_sha256=(
            resolver_code_sha or _resolver_code_sha()
        ),
        consumer_migration_identity_sha256=None,
        created_at="2026-08-27T04:00:00+02:00",
    )
    return build_runtime_policy_document(policy)


def _active_policy(
    fixture: dict[str, Any],
    *,
    snapshot: dict[str, Any] | None = None,
    resolver_code_sha: str | None = None,
) -> dict[str, object]:
    selected = snapshot or fixture
    policy = ActiveScientificFoundationRuntimePolicyV1(
        activation_decision=AUTHORIZE_ACTIVE_SNAPSHOT,
        pointer_required=True,
        parent_database_sha256=fixture["legacy_sha"],
        snapshot_database_sha256=selected["database_sha"],
        snapshot_manifest_file_sha256=selected[
            "manifest_file_sha"
        ],
        snapshot_manifest_payload_sha256=selected[
            "manifest_payload_sha"
        ],
        pointer_contract_payload_sha256=POINTER_CONTRACT_SHA,
        resolver_code_sha256=(
            resolver_code_sha or _resolver_code_sha()
        ),
        consumer_migration_identity_sha256=(
            MIGRATION_IDENTITY_SHA
        ),
        created_at="2026-08-27T04:00:00+02:00",
    )
    return build_runtime_policy_document(policy)


def _write_pointer_for_policy(
    fixture: dict[str, Any],
    policy_document: dict[str, object],
    *,
    target: dict[str, Any] | None = None,
    authorization_sha: str | None = None,
) -> Path:
    selected = target or fixture
    policy_payload = policy_document["runtime_policy_payload"]
    assert isinstance(policy_payload, dict)
    policy_sha = policy_document["runtime_policy_payload_sha256"]
    assert isinstance(policy_sha, str)

    pointer = ActiveScientificFoundationPointerV1(
        snapshot_database_sha256=selected["database_sha"],
        snapshot_manifest_file_sha256=selected[
            "manifest_file_sha"
        ],
        snapshot_manifest_payload_sha256=selected[
            "manifest_payload_sha"
        ],
        parent_database_sha256=fixture["legacy_sha"],
        activation_authorization_payload_sha256=(
            authorization_sha or policy_sha
        ),
        created_at=str(policy_payload["created_at"]),
    )
    pointer_path = (
        fixture["snapshot_root"].parent
        / "scientific-foundation-active.json"
    )
    _write_json(
        pointer_path,
        build_active_pointer_document(pointer),
    )
    fixture["pointer_path"] = pointer_path
    return pointer_path


def _resolve(
    fixture: dict[str, Any],
    policy_document: dict[str, object],
    *,
    pointer_path: Path | None = None,
) -> object:
    policy_sha = policy_document["runtime_policy_payload_sha256"]
    assert isinstance(policy_sha, str)
    return resolve_active_scientific_foundation_v1(
        pointer_path=(
            pointer_path
            or fixture.get(
                "pointer_path",
                fixture["snapshot_root"].parent
                / "scientific-foundation-active.json",
            )
        ),
        snapshot_root=fixture["snapshot_root"],
        legacy_database_path=fixture["legacy"],
        expected_legacy_database_sha256=fixture["legacy_sha"],
        expected_schema_version=6,
        expected_schema_design_sha256=DESIGN_SHA,
        runtime_policy_document=policy_document,
        expected_runtime_policy_payload_sha256=policy_sha,
    )


def test_pointer_document_remains_canonical_and_schema_bound() -> None:
    pointer = ActiveScientificFoundationPointerV1(
        snapshot_database_sha256="1" * 64,
        snapshot_manifest_file_sha256="2" * 64,
        snapshot_manifest_payload_sha256="3" * 64,
        parent_database_sha256="4" * 64,
        activation_authorization_payload_sha256="5" * 64,
        created_at="2026-08-27T04:00:00+02:00",
    )
    document = build_active_pointer_document(pointer)
    assert document["pointer_payload"]["schema_version"] == (
        ACTIVE_POINTER_SCHEMA_V1
    )
    assert document["pointer_payload_sha256"] == canonical_sha256(
        document["pointer_payload"]
    )


def test_runtime_policy_document_is_canonical() -> None:
    policy = ActiveScientificFoundationRuntimePolicyV1(
        activation_decision=LEGACY_PRE_ACTIVATION,
        pointer_required=False,
        parent_database_sha256="1" * 64,
        snapshot_database_sha256=None,
        snapshot_manifest_file_sha256=None,
        snapshot_manifest_payload_sha256=None,
        pointer_contract_payload_sha256="2" * 64,
        resolver_code_sha256="3" * 64,
        consumer_migration_identity_sha256=None,
        created_at="2026-08-27T04:00:00+02:00",
    )
    document = build_runtime_policy_document(policy)
    assert document["runtime_policy_payload_sha256"] == (
        canonical_sha256(document["runtime_policy_payload"])
    )


def test_missing_pointer_pre_activation_uses_verified_legacy(
    tmp_path: Path,
) -> None:
    fixture = _base_fixture(tmp_path)
    policy = _preactivation_policy(fixture)
    result = _resolve(fixture, policy)
    assert result.resolution_mode == "legacy_fallback"
    assert result.database_path == fixture["legacy"].resolve()
    assert result.runtime_policy_payload_sha256 == (
        policy["runtime_policy_payload_sha256"]
    )


def test_missing_pointer_post_activation_fails_closed(
    tmp_path: Path,
) -> None:
    fixture = _base_fixture(tmp_path)
    policy = _active_policy(fixture)
    with pytest.raises(
        PersistenceIntegrityError,
        match="pointer is required",
    ):
        _resolve(fixture, policy)


def test_present_pointer_is_rejected_by_pre_activation_policy(
    tmp_path: Path,
) -> None:
    fixture = _base_fixture(tmp_path)
    policy = _preactivation_policy(fixture)
    _write_pointer_for_policy(fixture, policy)
    with pytest.raises(
        PersistenceIntegrityError,
        match="not authorized by runtime policy",
    ):
        _resolve(fixture, policy)


def test_valid_pointer_requires_matching_trusted_policy(
    tmp_path: Path,
) -> None:
    fixture = _base_fixture(tmp_path)
    policy = _active_policy(fixture)
    _write_pointer_for_policy(fixture, policy)
    result = _resolve(fixture, policy)
    assert result.resolution_mode == "active_snapshot"
    assert result.database_sha256 == fixture["database_sha"]
    assert result.activation_authorization_payload_sha256 == (
        policy["runtime_policy_payload_sha256"]
    )
    assert result.runtime_policy_payload_sha256 == (
        policy["runtime_policy_payload_sha256"]
    )


def test_self_consistent_pointer_retarget_cannot_escape_policy(
    tmp_path: Path,
) -> None:
    fixture = _base_fixture(tmp_path)
    policy = _active_policy(fixture)
    second = _make_snapshot(
        fixture["snapshot_root"],
        legacy_sha=fixture["legacy_sha"],
        marker="second",
    )
    _write_pointer_for_policy(
        fixture,
        policy,
        target=second,
    )
    with pytest.raises(
        PersistenceIntegrityError,
        match="outside trusted policy",
    ):
        _resolve(fixture, policy)


def test_pointer_authorization_sha_must_equal_policy_sha(
    tmp_path: Path,
) -> None:
    fixture = _base_fixture(tmp_path)
    policy = _active_policy(fixture)
    _write_pointer_for_policy(
        fixture,
        policy,
        authorization_sha="f" * 64,
    )
    with pytest.raises(
        PersistenceIntegrityError,
        match="outside trusted policy",
    ):
        _resolve(fixture, policy)


def test_runtime_policy_expected_sha_is_external_trust_anchor(
    tmp_path: Path,
) -> None:
    fixture = _base_fixture(tmp_path)
    policy = _preactivation_policy(fixture)
    with pytest.raises(
        PersistenceIntegrityError,
        match="canonical/trusted SHA mismatch",
    ):
        resolve_active_scientific_foundation_v1(
            pointer_path=tmp_path / "missing.json",
            snapshot_root=fixture["snapshot_root"],
            legacy_database_path=fixture["legacy"],
            expected_legacy_database_sha256=fixture[
                "legacy_sha"
            ],
            expected_schema_version=6,
            expected_schema_design_sha256=DESIGN_SHA,
            runtime_policy_document=policy,
            expected_runtime_policy_payload_sha256="f" * 64,
        )


def test_runtime_policy_binds_exact_resolver_code(
    tmp_path: Path,
) -> None:
    fixture = _base_fixture(tmp_path)
    policy = _preactivation_policy(
        fixture,
        resolver_code_sha="f" * 64,
    )
    with pytest.raises(
        PersistenceIntegrityError,
        match="resolver-code identity mismatch",
    ):
        _resolve(fixture, policy)


def test_malformed_present_pointer_fails_closed(
    tmp_path: Path,
) -> None:
    fixture = _base_fixture(tmp_path)
    policy = _active_policy(fixture)
    pointer = tmp_path / "scientific-foundation-active.json"
    pointer.write_text("{broken", encoding="utf-8")
    with pytest.raises(PersistenceIntegrityError):
        _resolve(
            fixture,
            policy,
            pointer_path=pointer,
        )


def test_manifest_file_hash_drift_fails_closed(
    tmp_path: Path,
) -> None:
    fixture = _base_fixture(tmp_path)
    policy = _active_policy(fixture)
    _write_pointer_for_policy(fixture, policy)
    fixture["manifest"].write_text(
        fixture["manifest"].read_text(encoding="utf-8") + " ",
        encoding="utf-8",
    )
    with pytest.raises(
        PersistenceIntegrityError,
        match="manifest file SHA drift",
    ):
        _resolve(fixture, policy)


def test_snapshot_database_hash_drift_fails_closed(
    tmp_path: Path,
) -> None:
    fixture = _base_fixture(tmp_path)
    policy = _active_policy(fixture)
    _write_pointer_for_policy(fixture, policy)
    with fixture["database"].open("ab") as handle:
        handle.write(b"drift")
    with pytest.raises(
        PersistenceIntegrityError,
        match="database SHA drift",
    ):
        _resolve(fixture, policy)


def test_generic_windows_reparse_signal_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "ordinary-file"
    path.write_text("x", encoding="utf-8")
    monkeypatch.setattr(
        active,
        "_windows_is_reparse_point",
        lambda _path: True,
    )
    with pytest.raises(
        PersistenceConfigurationError,
        match="reparse point",
    ):
        active._reject_link_like(path, label="test path")


def test_resolver_does_not_mutate_valid_files(
    tmp_path: Path,
) -> None:
    fixture = _base_fixture(tmp_path)
    policy = _active_policy(fixture)
    pointer = _write_pointer_for_policy(fixture, policy)

    tracked = [
        fixture["legacy"],
        fixture["database"],
        fixture["manifest"],
        pointer,
    ]
    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tracked
    }
    _resolve(fixture, policy)
    after = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tracked
    }
    assert after == before
