from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from ecobiome.knowledge_persistence.active_foundation_v1 import (
    ACTIVE_POINTER_SCHEMA_V1,
    ActiveScientificFoundationPointerV1,
    build_active_pointer_document,
    canonical_sha256,
    resolve_active_scientific_foundation_v1,
    sha256_file,
)
from ecobiome.knowledge_persistence.errors import (
    PersistenceIntegrityError,
)

DESIGN_SHA = "d" * 64
AUTH_SHA = "a" * 64


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


def _make_snapshot_fixture(
    tmp_path: Path,
) -> dict[str, Any]:
    legacy = tmp_path / "legacy.sqlite3"
    _create_database(legacy)
    legacy_sha = sha256_file(legacy)

    snapshot_root = tmp_path / "snapshots"
    snapshot_root.mkdir()

    temporary_db = tmp_path / "snapshot.sqlite3"
    _create_database(temporary_db)
    database_sha = sha256_file(temporary_db)
    snapshot_dir = snapshot_root / database_sha
    snapshot_dir.mkdir()
    database = snapshot_dir / "scientific-foundation.sqlite3"
    database.write_bytes(temporary_db.read_bytes())

    manifest_payload = {
        "schema_version": (
            "ecobiome-scientific-foundation-snapshot-manifest-v1-reviewed"
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
        "manifest_payload_sha256": canonical_sha256(manifest_payload),
        "manifest_payload": manifest_payload,
    }
    manifest = snapshot_dir / "snapshot-manifest.json"
    _write_json(manifest, manifest_document)

    pointer = ActiveScientificFoundationPointerV1(
        snapshot_database_sha256=database_sha,
        snapshot_manifest_file_sha256=sha256_file(manifest),
        snapshot_manifest_payload_sha256=manifest_document[
            "manifest_payload_sha256"
        ],
        parent_database_sha256=legacy_sha,
        activation_authorization_payload_sha256=AUTH_SHA,
        created_at="2026-08-27T03:00:00+02:00",
    )
    pointer_path = tmp_path / "scientific-foundation-active.json"
    _write_json(pointer_path, build_active_pointer_document(pointer))

    return {
        "legacy": legacy,
        "legacy_sha": legacy_sha,
        "snapshot_root": snapshot_root,
        "snapshot_dir": snapshot_dir,
        "database": database,
        "database_sha": database_sha,
        "manifest": manifest,
        "manifest_payload": manifest_payload,
        "manifest_payload_sha": manifest_document["manifest_payload_sha256"],
        "pointer": pointer,
        "pointer_path": pointer_path,
    }


def _resolve(fixture: dict[str, Any]) -> object:
    return resolve_active_scientific_foundation_v1(
        pointer_path=fixture["pointer_path"],
        snapshot_root=fixture["snapshot_root"],
        legacy_database_path=fixture["legacy"],
        expected_legacy_database_sha256=fixture["legacy_sha"],
        expected_schema_version=6,
        expected_schema_design_sha256=DESIGN_SHA,
    )


def test_pointer_document_is_canonical_and_schema_bound() -> None:
    pointer = ActiveScientificFoundationPointerV1(
        snapshot_database_sha256="1" * 64,
        snapshot_manifest_file_sha256="2" * 64,
        snapshot_manifest_payload_sha256="3" * 64,
        parent_database_sha256="4" * 64,
        activation_authorization_payload_sha256="5" * 64,
        created_at="2026-08-27T03:00:00+02:00",
    )
    document = build_active_pointer_document(pointer)
    assert document["pointer_payload"]["schema_version"] == (
        ACTIVE_POINTER_SCHEMA_V1
    )
    assert document["pointer_payload_sha256"] == canonical_sha256(
        document["pointer_payload"]
    )


def test_missing_pointer_uses_verified_legacy_fallback(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.sqlite3"
    _create_database(legacy)
    result = resolve_active_scientific_foundation_v1(
        pointer_path=tmp_path / "missing-active.json",
        snapshot_root=tmp_path / "missing-snapshots",
        legacy_database_path=legacy,
        expected_legacy_database_sha256=sha256_file(legacy),
        expected_schema_version=6,
        expected_schema_design_sha256=DESIGN_SHA,
    )
    assert result.resolution_mode == "legacy_fallback"
    assert result.database_path == legacy.resolve()
    assert result.pointer_payload_sha256 is None


def test_valid_pointer_resolves_content_addressed_snapshot(
    tmp_path: Path,
) -> None:
    fixture = _make_snapshot_fixture(tmp_path)
    result = _resolve(fixture)
    assert result.resolution_mode == "active_snapshot"
    assert result.database_path == fixture["database"].resolve()
    assert result.database_sha256 == fixture["database_sha"]
    assert result.snapshot_manifest_payload_sha256 == fixture[
        "manifest_payload_sha"
    ]
    assert result.activation_authorization_payload_sha256 == AUTH_SHA


def test_malformed_present_pointer_fails_closed_without_legacy_fallback(
    tmp_path: Path,
) -> None:
    fixture = _make_snapshot_fixture(tmp_path)
    fixture["pointer_path"].write_text("{broken", encoding="utf-8")
    with pytest.raises(PersistenceIntegrityError):
        _resolve(fixture)


def test_pointer_canonical_sha_mismatch_fails_closed(tmp_path: Path) -> None:
    fixture = _make_snapshot_fixture(tmp_path)
    document = json.loads(
        fixture["pointer_path"].read_text(encoding="utf-8")
    )
    document["pointer_payload"]["created_at"] = (
        "2026-08-27T03:01:00+02:00"
    )
    _write_json(fixture["pointer_path"], document)
    with pytest.raises(
        PersistenceIntegrityError,
        match="pointer canonical SHA mismatch",
    ):
        _resolve(fixture)


def test_pointer_parent_identity_drift_fails_closed(tmp_path: Path) -> None:
    fixture = _make_snapshot_fixture(tmp_path)
    document = json.loads(
        fixture["pointer_path"].read_text(encoding="utf-8")
    )
    document["pointer_payload"]["parent_database_sha256"] = "f" * 64
    document["pointer_payload_sha256"] = canonical_sha256(
        document["pointer_payload"]
    )
    _write_json(fixture["pointer_path"], document)
    with pytest.raises(
        PersistenceIntegrityError,
        match="parent identity drift",
    ):
        _resolve(fixture)


def test_manifest_file_hash_drift_fails_closed(tmp_path: Path) -> None:
    fixture = _make_snapshot_fixture(tmp_path)
    fixture["manifest"].write_text(
        fixture["manifest"].read_text(encoding="utf-8") + " ",
        encoding="utf-8",
    )
    with pytest.raises(
        PersistenceIntegrityError,
        match="manifest file SHA drift",
    ):
        _resolve(fixture)


def test_manifest_payload_binding_drift_fails_closed(tmp_path: Path) -> None:
    fixture = _make_snapshot_fixture(tmp_path)
    manifest_document = json.loads(
        fixture["manifest"].read_text(encoding="utf-8")
    )
    manifest_document["manifest_payload"]["snapshot"]["immutable"] = False
    manifest_document["manifest_payload_sha256"] = canonical_sha256(
        manifest_document["manifest_payload"]
    )
    _write_json(fixture["manifest"], manifest_document)

    pointer_document = json.loads(
        fixture["pointer_path"].read_text(encoding="utf-8")
    )
    pointer_document["pointer_payload"][
        "snapshot_manifest_file_sha256"
    ] = sha256_file(fixture["manifest"])
    pointer_document["pointer_payload"][
        "snapshot_manifest_payload_sha256"
    ] = manifest_document["manifest_payload_sha256"]
    pointer_document["pointer_payload_sha256"] = canonical_sha256(
        pointer_document["pointer_payload"]
    )
    _write_json(fixture["pointer_path"], pointer_document)

    with pytest.raises(
        PersistenceIntegrityError,
        match="manifest binding drift",
    ):
        _resolve(fixture)


def test_snapshot_database_hash_drift_fails_closed(tmp_path: Path) -> None:
    fixture = _make_snapshot_fixture(tmp_path)
    with fixture["database"].open("ab") as handle:
        handle.write(b"drift")
    with pytest.raises(
        PersistenceIntegrityError,
        match="database SHA drift",
    ):
        _resolve(fixture)


def test_snapshot_directory_extra_entry_is_rejected(tmp_path: Path) -> None:
    fixture = _make_snapshot_fixture(tmp_path)
    (fixture["snapshot_dir"] / "unexpected.txt").write_text(
        "unexpected",
        encoding="utf-8",
    )
    with pytest.raises(
        PersistenceIntegrityError,
        match="unexpected entries",
    ):
        _resolve(fixture)


def test_resolver_does_not_mutate_valid_files(tmp_path: Path) -> None:
    fixture = _make_snapshot_fixture(tmp_path)
    tracked = [
        fixture["legacy"],
        fixture["database"],
        fixture["manifest"],
        fixture["pointer_path"],
    ]
    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tracked
    }
    _resolve(fixture)
    after = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tracked
    }
    assert after == before
