"""Tests for Collector v2 retention and dry-run GC policy."""

from __future__ import annotations

from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition.persistence import CollectorStore
from ecobiome.knowledge_acquisition.processing import split_into_passages
from ecobiome.knowledge_acquisition.retention import (
    GcPolicyError,
    RetentionPolicy,
    build_gc_plan,
    execute_gc,
    write_gc_plan,
)
from ecobiome.knowledge_acquisition.source import SourceType
from ecobiome.knowledge_acquisition.transcript import load_transcript


def _persist_one_transcript(tmp_path: Path) -> CollectorStore:
    transcript = tmp_path / "input.txt"
    transcript.write_text(
        "Accepted evidence source text.",
        encoding="utf-8",
    )
    imported = load_transcript(
        transcript,
        title="Retention fixture",
        locator="local:retention-fixture",
        author="EcoBiome test",
        language="en",
        source_type=SourceType("transcript"),
    )
    passages = split_into_passages(
        imported.text,
        maximum_characters=100,
    )
    store = CollectorStore(tmp_path / "collector.sqlite3")
    receipt = store.persist_transcript(
        imported,
        transcript_path=transcript,
        passages=passages,
    )
    store.record_review_decision(
        target_type="passage",
        target_id=receipt.passage_ids[0],
        decision="accept",
        reviewer="test",
        rationale="Protect reviewed provenance.",
    )
    return store


def test_gc_plan_protects_all_db_artifacts_and_lists_only_orphans(
    tmp_path: Path,
) -> None:
    store = _persist_one_transcript(tmp_path)

    orphan = store.artifact_directory / "raw" / "ff" / "orphan-fixture"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_bytes(b"orphan fixture")

    plan = build_gc_plan(
        database_path=store.database_path,
        artifact_directory=store.artifact_directory,
    )

    assert plan.protected_artifact_count == 1
    assert plan.orphan_file_count == 1
    assert len(plan.candidates) == 1
    assert plan.candidates[0].storage_relpath == "raw/ff/orphan-fixture"
    assert plan.candidates[0].reason == "unreferenced_cas_object"

    # Planning is dry-run only.
    assert orphan.is_file()
    assert next(
        path
        for path in store.artifact_directory.rglob("*")
        if path.is_file() and path != orphan
    ).is_file()


def test_gc_plan_is_auditable_and_execution_is_disabled(
    tmp_path: Path,
) -> None:
    store = _persist_one_transcript(tmp_path)
    orphan = store.artifact_directory / "raw" / "ee" / "orphan-fixture"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_bytes(b"orphan fixture")

    plan = build_gc_plan(
        database_path=store.database_path,
        artifact_directory=store.artifact_directory,
        policy=RetentionPolicy(gc_enabled=False),
    )
    output = tmp_path / "gc-plan.json"
    write_gc_plan(output, plan)

    payload = output.read_text(encoding="utf-8")
    assert '"mode": "dry-run"' in payload
    assert '"deletion_performed": false' in payload
    assert "unreferenced_cas_object" in payload
    assert orphan.is_file()

    with pytest.raises(GcPolicyError, match="disabled"):
        execute_gc(policy=RetentionPolicy(gc_enabled=False))

    with pytest.raises(GcPolicyError, match="not implemented"):
        execute_gc(policy=RetentionPolicy(gc_enabled=True))

    assert orphan.is_file()
