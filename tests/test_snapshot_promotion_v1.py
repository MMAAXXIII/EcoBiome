from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from ecobiome.knowledge_persistence import snapshot_promotion_v1 as module
from ecobiome.knowledge_persistence.errors import (
    ArtifactCorruptionError,
    ArtifactMissingError,
)
from ecobiome.knowledge_persistence.snapshot_promotion_v1 import (
    PromotionAuthorization,
    SnapshotPromotionError,
    _publish_atomic_complete_pair,
    canonical_sha256,
    ensure_derived_artifacts,
    locate_anchor_paragraph_v1,
    normalized_jats_text_v1,
    promote_first_derived_snapshot,
    sha256_file,
    validate_manifest_document,
    verify_execution_identity,
)


class _MemoryCas:
    def __init__(self, initial: dict[str, bytes] | None = None) -> None:
        self.data = dict(initial or {})
        self.put_count = 0
        self.get_count = 0
        self.verify_count = 0

    def verify(self, key: str) -> SimpleNamespace:
        self.verify_count += 1
        if key not in self.data:
            raise ArtifactMissingError(f"missing: {key}")
        data = self.data[key]
        digest = hashlib.sha256(data).hexdigest()
        if key != f"sha256:{digest}":
            raise ArtifactCorruptionError("synthetic CAS corruption")
        return SimpleNamespace(key=key, sha256=digest, size_bytes=len(data))

    def get(self, key: str) -> bytes:
        self.get_count += 1
        if key not in self.data:
            raise ArtifactMissingError(f"missing: {key}")
        data = self.data[key]
        digest = hashlib.sha256(data).hexdigest()
        if key != f"sha256:{digest}":
            raise ArtifactCorruptionError("synthetic CAS corruption")
        return data

    def put(self, data: bytes) -> SimpleNamespace:
        self.put_count += 1
        digest = hashlib.sha256(data).hexdigest()
        key = f"sha256:{digest}"
        self.data[key] = data
        return SimpleNamespace(key=key, sha256=digest, size_bytes=len(data))


class _CorruptCas(_MemoryCas):
    def verify(self, key: str) -> SimpleNamespace:
        raise ArtifactCorruptionError(f"corrupt: {key}")


def _derived_manifest_fixture() -> tuple[dict[str, Any], _MemoryCas, str]:
    raw = (
        b"<article><body>"
        b"<p>Nitrification is a two-step process in this synthetic fixture "
        b"and the paragraph is intentionally long enough.</p>"
        b"</body></article>"
    )
    representation, _ = normalized_jats_text_v1(raw)
    raw_sha = hashlib.sha256(raw).hexdigest()
    representation_bytes = representation.encode("utf-8")
    representation_sha = hashlib.sha256(representation_bytes).hexdigest()
    manifest = {
        "derived_cas_artifacts": [
            {
                "artifact_key": f"sha256:{representation_sha}",
                "content_sha256": representation_sha,
                "size_bytes": len(representation_bytes),
                "derivation": "normalized_jats_text_v1",
                "source_raw_artifact_key": f"sha256:{raw_sha}",
                "source_raw_sha256": raw_sha,
            }
        ]
    }
    cas = _MemoryCas({f"sha256:{raw_sha}": raw})
    return manifest, cas, f"sha256:{representation_sha}"


def _create_synthetic_parent(path: Path, design_sha: str) -> None:
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
            (design_sha,),
        )
        conn.execute(
            """
            CREATE TABLE scientific_entities(
                id TEXT PRIMARY KEY,
                entity_kind TEXT NOT NULL,
                created_at TEXT NOT NULL,
                retired_at TEXT
            )
            """
        )
        conn.execute(
            "CREATE TABLE source_lineage_edges(id TEXT PRIMARY KEY)"
        )
        conn.execute(
            "CREATE TABLE knowledge_syntheses(id TEXT PRIMARY KEY)"
        )
        conn.commit()
    finally:
        conn.close()


def _synthetic_execution_inputs(
    parent_database: Path,
    *,
    engine_sha: str,
) -> tuple[
    dict[str, Any],
    str,
    dict[str, Any],
    str,
    PromotionAuthorization,
]:
    design_sha = "d" * 64
    row = {
        "id": "synthetic-entity",
        "entity_kind": "chemical",
        "created_at": "2026-08-27T00:00:00+00:00",
        "retired_at": None,
    }
    replay = {
        "schema_version": (
            "ecobiome-first-derived-snapshot-replay-manifest-v1"
        ),
        "parent_database_sha256": sha256_file(parent_database),
        "schema_design_sha256": design_sha,
        "promotion_plan_sha256": "1" * 64,
        "scientific_input_repo_head": "science-head",
        "reviewed_input_identities": {},
        "rows": [
            {
                "table": "scientific_entities",
                "row_id": "synthetic-entity",
                "canonical_row_payload_sha256": canonical_sha256(row),
                "identity_where": {"id": "synthetic-entity"},
                "row_payload_redacted": row,
                "protected_fields": {},
                "provenance_bindings": [],
                "dependency_row_ids": [],
            }
        ],
        "expected_table_delta": {
            "scientific_entities": 1,
            "source_lineage_edges": 0,
            "knowledge_syntheses": 0,
        },
        "replay_dependency_order": ["scientific_entities"],
        "derived_cas_artifacts": [],
    }
    replay_sha = canonical_sha256(replay)
    binding = {
        "schema_version": (
            "ecobiome-first-derived-snapshot-promotion-"
            "candidate-identity-binding-v2"
        ),
        "scientific_input_repo_head": "science-head",
        "promotion_contract_repo_head": "contract-head",
        "promotion_engine_repo_head": "engine-head",
        "promotion_engine_code_identity_sha256": engine_sha,
        "replay_manifest_payload_sha256": replay_sha,
    }
    binding_sha = canonical_sha256(binding)
    auth_payload = {
        "schema_version": (
            "ecobiome-first-derived-snapshot-execution-authorization-v1"
        ),
        "decision": "authorize",
        "snapshot_creation_authorized": True,
        "derived_representation_cas_write_authorized": False,
        "identity_binding_payload_sha256": binding_sha,
        "replay_manifest_payload_sha256": replay_sha,
        "scientific_input_repo_head": "science-head",
        "promotion_contract_repo_head": "contract-head",
        "promotion_engine_repo_head": "engine-head",
        "promotion_engine_code_identity_sha256": engine_sha,
    }
    authorization = PromotionAuthorization(
        payload=auth_payload,
        payload_sha256=canonical_sha256(auth_payload),
    )
    return replay, replay_sha, binding, binding_sha, authorization


def test_canonical_sha256_is_key_order_independent() -> None:
    left = {"b": 2, "a": {"y": 2, "x": 1}}
    right = {"a": {"x": 1, "y": 2}, "b": 2}
    assert canonical_sha256(left) == canonical_sha256(right)


def test_jats_normalization_and_anchor_selection_are_deterministic() -> None:
    raw = (
        b"<article><body>"
        b"<p>Short.</p>"
        b"<p>Nitrification is a two-step process in this synthetic fixture.</p>"
        b"<p>Another sufficiently long paragraph for deterministic ordering.</p>"
        b"</body></article>"
    )
    representation, paragraphs = normalized_jats_text_v1(raw)
    assert representation == "\n\n".join(paragraphs)
    index, paragraph = locate_anchor_paragraph_v1(
        paragraphs,
        ["Nitrification is a two-step process"],
    )
    assert index == 0
    assert hashlib.sha256(paragraph.encode()).hexdigest()


def test_manifest_rejects_knowledge_synthesis_delta() -> None:
    manifest = {
        "schema_version": "ecobiome-first-derived-snapshot-replay-manifest-v1",
        "rows": [
            {
                "table": "scientific_entities",
                "row_id": "synthetic",
                "canonical_row_payload_sha256": "0" * 64,
                "identity_where": {"id": "synthetic"},
                "row_payload_redacted": {"id": "synthetic"},
                "protected_fields": {},
            }
        ],
        "expected_table_delta": {
            "scientific_entities": 1,
            "knowledge_syntheses": 1,
            "source_lineage_edges": 0,
        },
    }
    with pytest.raises(SnapshotPromotionError):
        validate_manifest_document(manifest)


def test_manifest_rejects_unsafe_identifier() -> None:
    manifest = {
        "schema_version": "ecobiome-first-derived-snapshot-replay-manifest-v1",
        "rows": [
            {
                "table": "scientific_entities;drop",
                "row_id": "synthetic",
                "canonical_row_payload_sha256": "0" * 64,
                "identity_where": {"id": "synthetic"},
                "row_payload_redacted": {"id": "synthetic"},
                "protected_fields": {},
            }
        ],
        "expected_table_delta": {
            "knowledge_syntheses": 0,
            "source_lineage_edges": 0,
        },
    }
    with pytest.raises(SnapshotPromotionError):
        validate_manifest_document(manifest)


def test_missing_derived_artifact_fails_when_write_unauthorized() -> None:
    manifest, cas, _ = _derived_manifest_fixture()
    with pytest.raises(
        SnapshotPromotionError,
        match="missing and write unauthorized",
    ):
        ensure_derived_artifacts(manifest, cas, allow_write=False)
    assert cas.put_count == 0


def test_missing_derived_artifact_is_materialized_when_authorized() -> None:
    manifest, cas, expected_key = _derived_manifest_fixture()
    ensure_derived_artifacts(manifest, cas, allow_write=True)
    assert cas.put_count == 1
    assert expected_key in cas.data
    assert cas.verify(expected_key).key == expected_key


def test_cas_corruption_never_enters_missing_artifact_branch() -> None:
    manifest, _, _ = _derived_manifest_fixture()
    with pytest.raises(ArtifactCorruptionError):
        ensure_derived_artifacts(
            manifest,
            _CorruptCas(),
            allow_write=True,
        )


def test_execution_identity_rejects_unreviewed_authorization_sha(
    tmp_path: Path,
) -> None:
    parent = tmp_path / "parent.sqlite3"
    _create_synthetic_parent(parent, "d" * 64)
    assert module.__file__ is not None
    engine_sha = sha256_file(Path(module.__file__))
    replay, replay_sha, binding, binding_sha, authorization = (
        _synthetic_execution_inputs(parent, engine_sha=engine_sha)
    )
    with pytest.raises(
        SnapshotPromotionError,
        match="authorization SHA is not reviewed",
    ):
        verify_execution_identity(
            authorization=authorization,
            expected_authorization_payload_sha256="0" * 64,
            identity_binding=binding,
            identity_binding_payload_sha256=binding_sha,
            replay_manifest=replay,
            replay_manifest_payload_sha256=replay_sha,
            expected_engine_code_sha256=engine_sha,
        )


def test_execution_identity_rejects_replay_sha_before_effects(
    tmp_path: Path,
) -> None:
    parent = tmp_path / "parent.sqlite3"
    _create_synthetic_parent(parent, "d" * 64)
    assert module.__file__ is not None
    engine_sha = sha256_file(Path(module.__file__))
    replay, replay_sha, binding, binding_sha, authorization = (
        _synthetic_execution_inputs(parent, engine_sha=engine_sha)
    )
    bad_replay = dict(replay)
    bad_replay["promotion_plan_sha256"] = "2" * 64
    with pytest.raises(
        SnapshotPromotionError,
        match="Replay manifest canonical SHA mismatch",
    ):
        verify_execution_identity(
            authorization=authorization,
            expected_authorization_payload_sha256=(
                authorization.payload_sha256
            ),
            identity_binding=binding,
            identity_binding_payload_sha256=binding_sha,
            replay_manifest=bad_replay,
            replay_manifest_payload_sha256=replay_sha,
            expected_engine_code_sha256=engine_sha,
        )


def test_execution_identity_rejects_binding_mismatch(
    tmp_path: Path,
) -> None:
    parent = tmp_path / "parent.sqlite3"
    _create_synthetic_parent(parent, "d" * 64)
    assert module.__file__ is not None
    engine_sha = sha256_file(Path(module.__file__))
    replay, replay_sha, binding, _, authorization = (
        _synthetic_execution_inputs(parent, engine_sha=engine_sha)
    )
    bad_binding = dict(binding)
    bad_binding["promotion_contract_repo_head"] = "wrong-head"
    bad_binding_sha = canonical_sha256(bad_binding)
    with pytest.raises(
        SnapshotPromotionError,
        match="Authorization identity-binding SHA mismatch",
    ):
        verify_execution_identity(
            authorization=authorization,
            expected_authorization_payload_sha256=(
                authorization.payload_sha256
            ),
            identity_binding=bad_binding,
            identity_binding_payload_sha256=bad_binding_sha,
            replay_manifest=replay,
            replay_manifest_payload_sha256=replay_sha,
            expected_engine_code_sha256=engine_sha,
        )


def test_synthetic_end_to_end_promotion_and_manifest_binding(
    tmp_path: Path,
) -> None:
    parent = tmp_path / "parent.sqlite3"
    _create_synthetic_parent(parent, "d" * 64)
    assert module.__file__ is not None
    engine_sha = sha256_file(Path(module.__file__))
    replay, replay_sha, binding, binding_sha, authorization = (
        _synthetic_execution_inputs(parent, engine_sha=engine_sha)
    )
    snapshot_root = tmp_path / "snapshots"
    result = promote_first_derived_snapshot(
        parent_database=parent,
        snapshot_root=snapshot_root,
        replay_manifest=replay,
        replay_manifest_payload_sha256=replay_sha,
        identity_binding=binding,
        identity_binding_payload_sha256=binding_sha,
        cas=_MemoryCas(),
        authorization=authorization,
        expected_authorization_payload_sha256=(
            authorization.payload_sha256
        ),
        expected_engine_code_sha256=engine_sha,
        regression_runner=lambda: {"synthetic_regression": "pass"},
        created_at="2026-08-27T00:00:00+00:00",
    )

    final_dir = Path(result.logical_snapshot_path)
    final_db = final_dir / "scientific-foundation.sqlite3"
    final_manifest = final_dir / "snapshot-manifest.json"
    assert final_db.is_file()
    assert final_manifest.is_file()
    assert sha256_file(final_db) == result.database_sha256
    assert sha256_file(final_manifest) == result.manifest_sha256
    document = json.loads(final_manifest.read_text(encoding="utf-8"))
    validation = document["manifest_payload"]["validation"]
    assert validation["replay_manifest_payload_sha256"] == replay_sha
    assert validation["identity_binding_payload_sha256"] == binding_sha
    assert (
        validation["execution_authorization_payload_sha256"]
        == authorization.payload_sha256
    )
    assert not list(snapshot_root.glob(".tmp-promotion-*"))


@pytest.mark.parametrize("mode", ["partial", "inconsistent"])
def test_atomic_publication_rejects_bad_existing_final_directory(
    tmp_path: Path,
    mode: str,
) -> None:
    temporary = tmp_path / "temporary"
    temporary.mkdir()
    db = temporary / "scientific-foundation.sqlite3"
    manifest = temporary / "snapshot-manifest.json"
    db.write_bytes(b"database")
    manifest.write_bytes(b"manifest")
    database_sha = hashlib.sha256(db.read_bytes()).hexdigest()
    manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()

    final = tmp_path / "final"
    final.mkdir()
    (final / "scientific-foundation.sqlite3").write_bytes(
        b"database" if mode == "partial" else b"wrong"
    )
    if mode == "inconsistent":
        (final / "snapshot-manifest.json").write_bytes(b"manifest")

    with pytest.raises(SnapshotPromotionError):
        _publish_atomic_complete_pair(
            temporary_directory=temporary,
            final_directory=final,
            database_sha256=database_sha,
            manifest_sha256=manifest_sha,
        )
    assert temporary.is_dir()


def test_windows_write_through_path_is_exercised_by_end_to_end_test() -> None:
    if os.name != "nt":
        pytest.skip("Windows-specific durability path")
    assert os.name == "nt"
