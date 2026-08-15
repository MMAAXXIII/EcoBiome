"""Tests for durable EcoBiome Collector v2 persistence and review."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from ecobiome.cli.main import main as central_main
from ecobiome.knowledge_acquisition.persistence import CollectorStore
from ecobiome.knowledge_acquisition.processing import split_into_passages
from ecobiome.knowledge_acquisition.source import SourceType
from ecobiome.knowledge_acquisition.transcript import load_transcript


def _imported(
    tmp_path: Path,
    *,
    locator: str = "local:test-transcript",
):
    transcript_path = tmp_path / "transcript.txt"
    transcript_path.write_text(
        "A large volume improves thermal stability.\n\n"
        "Stable temperature can reduce biological stress.",
        encoding="utf-8",
    )
    imported = load_transcript(
        transcript_path,
        title="Thermal stability",
        locator=locator,
        author="EcoBiome test",
        language="en",
        source_type=SourceType("transcript"),
    )
    passages = split_into_passages(
        imported.text,
        maximum_characters=60,
    )
    return transcript_path, imported, passages


def test_schema_contains_v4_provenance_tables_behind_v2_compatibility(
    tmp_path: Path,
) -> None:
    store = CollectorStore(tmp_path / "collector.sqlite3")
    store.initialize()

    with sqlite3.connect(store.database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        physical = connection.execute(
            """
            SELECT schema_version, design_sha256
            FROM sf_schema_metadata
            WHERE schema_name = 'scientific_foundation'
            """
        ).fetchone()

    assert {
        "sf_schema_metadata",
        "knowledge_sources",
        "acquisition_jobs",
        "raw_artifacts",
        "retrievals",
        "representations",
        "derivations",
        "segments",
        "source_claims",
        "source_evidence",
        "claim_evidence_links",
        "claim_review_events",
        "segment_review_events",
    } <= tables
    assert {
        "schema_migrations",
        "sources",
        "job_diagnostics",
        "representation_derivations",
        "claims",
        "evidence",
        "review_decisions",
        "documents",
        "passages",
    }.isdisjoint(tables)
    assert physical == (
        5,
        "d13f146dfd6f394ebb660e420c09305a6daca6c0d34232713c9b91b21879310e",
    )
    assert store.schema_version() == 2


def test_persist_transcript_uses_raw_artifact_and_representation(
    tmp_path: Path,
) -> None:
    path, imported, passages = _imported(tmp_path)
    store = CollectorStore(tmp_path / "collector.sqlite3")

    receipt = store.persist_transcript(
        imported,
        transcript_path=path,
        passages=passages,
    )

    assert receipt.stored_document_path.is_file()
    assert receipt.stored_document_path.read_bytes() == path.read_bytes()
    assert len(receipt.passage_ids) == 2
    assert receipt.passage_review_statuses == ("pending", "pending")
    assert receipt.duplicate_document is False

    summary = store.summary()
    assert summary["sources"] == 1
    assert summary["raw_artifacts"] == 1
    assert summary["retrievals"] == 1
    assert summary["representations"] == 1
    assert summary["representation_derivations"] == 1
    assert summary["segments"] == 2
    assert summary["acquisition_jobs"] == 1
    assert summary["documents"] == 1
    assert summary["passages"] == 2
    assert summary["pending_passages"] == 2
    assert summary["failed_jobs"] == 0


def test_reimport_preserves_representation_segments_and_review_state(
    tmp_path: Path,
) -> None:
    path, first_import, passages = _imported(tmp_path)
    store = CollectorStore(tmp_path / "collector.sqlite3")

    first = store.persist_transcript(
        first_import,
        transcript_path=path,
        passages=passages,
    )
    store.record_review_decision(
        target_type="passage",
        target_id=first.passage_ids[0],
        decision="accept",
        reviewer="test",
        rationale="Preserve review state.",
    )

    _, second_import, second_passages = _imported(tmp_path)
    second = store.persist_transcript(
        second_import,
        transcript_path=path,
        passages=second_passages,
    )

    assert second.source_id == first.source_id
    assert second.document_id == first.document_id
    assert second.passage_ids == first.passage_ids
    assert second.passage_review_statuses == ("accepted", "pending")
    assert second.duplicate_document is True

    summary = store.summary()
    assert summary["sources"] == 1
    assert summary["raw_artifacts"] == 1
    assert summary["representations"] == 1
    assert summary["segments"] == 2
    assert summary["retrievals"] == 2
    assert summary["acquisition_jobs"] == 2


def test_immutable_raw_artifact_tampering_fails_and_records_job(
    tmp_path: Path,
) -> None:
    path, imported, passages = _imported(tmp_path)
    store = CollectorStore(tmp_path / "collector.sqlite3")

    first = store.persist_transcript(
        imported,
        transcript_path=path,
        passages=passages,
    )
    first.stored_document_path.write_text(
        "tampered",
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match="Existing CAS corruption",
    ):
        store.persist_transcript(
            imported,
            transcript_path=path,
            passages=passages,
        )

    summary = store.summary()
    assert summary["failed_jobs"] == 1
    assert summary["acquisition_jobs"] == 2
    assert summary["job_diagnostics"] == 1


def test_correction_is_append_only_and_preserves_original_segment(
    tmp_path: Path,
) -> None:
    path, imported, passages = _imported(tmp_path)
    store = CollectorStore(tmp_path / "collector.sqlite3")
    receipt = store.persist_transcript(
        imported,
        transcript_path=path,
        passages=passages,
    )

    passage_id = receipt.passage_ids[0]
    original = store.get_passage(passage_id)["text"]

    corrected_text = "Corrected scientific wording."
    decision_id = store.record_review_decision(
        target_type="passage",
        target_id=passage_id,
        decision="correct",
        corrected_text=corrected_text,
        reviewer="reviewer",
        rationale="Clarify the observation.",
    )

    persisted = store.get_passage(passage_id)
    assert persisted["text"] == original
    assert persisted["review_status"] == "corrected"

    with sqlite3.connect(store.database_path) as connection:
        row = connection.execute(
            """
            SELECT decision, corrected_text, corrected_text_sha256
            FROM segment_review_events
            WHERE id = ?
            """,
            (str(decision_id),),
        ).fetchone()

    assert row == (
        "correct",
        corrected_text,
        hashlib.sha256(corrected_text.encode("utf-8")).hexdigest(),
    )
    assert store.summary()["review_decisions"] == 1


def test_correction_requires_corrected_text(
    tmp_path: Path,
) -> None:
    path, imported, passages = _imported(tmp_path)
    store = CollectorStore(tmp_path / "collector.sqlite3")
    receipt = store.persist_transcript(
        imported,
        transcript_path=path,
        passages=passages,
    )

    with pytest.raises(ValueError, match="requires corrected_text"):
        store.record_review_decision(
            target_type="passage",
            target_id=receipt.passage_ids[0],
            decision="correct",
        )


def test_central_collector_cli_persists_transcript_on_v2(
    tmp_path: Path,
) -> None:
    transcript = tmp_path / "input.txt"
    transcript.write_text(
        "A large volume improves thermal stability.\n\n"
        "Stable temperature can reduce biological stress.",
        encoding="utf-8",
    )
    database = tmp_path / "collector.sqlite3"
    manifest = tmp_path / "manifest.json"

    exit_code = central_main(
        [
            "collector",
            "import-transcript",
            str(transcript),
            "--database",
            str(database),
            "--title",
            "Collector persistence smoke",
            "--locator",
            "local:collector-persistence-smoke",
            "--source-type",
            "transcript",
            "--maximum-passage-characters",
            "60",
            "--output",
            str(manifest),
        ]
    )

    assert exit_code == 0
    assert manifest.is_file()
    assert CollectorStore(database).schema_version() == 2

    summary = CollectorStore(database).summary()
    assert summary["documents"] == 1
    assert summary["passages"] == 2
    assert summary["pending_passages"] == 2


def test_reimport_manifest_preserves_persisted_review_statuses(
    tmp_path: Path,
) -> None:
    transcript = tmp_path / "input.txt"
    transcript.write_text(
        "A large volume improves thermal stability.\n\n"
        "Stable temperature can reduce biological stress.",
        encoding="utf-8",
    )
    database = tmp_path / "collector.sqlite3"
    first_manifest = tmp_path / "first-manifest.json"
    second_manifest = tmp_path / "second-manifest.json"
    arguments = [
        "collector",
        "import-transcript",
        str(transcript),
        "--database",
        str(database),
        "--title",
        "Collector reimport review state",
        "--locator",
        "local:collector-reimport-review-state",
        "--source-type",
        "transcript",
        "--maximum-passage-characters",
        "60",
    ]

    assert central_main([*arguments, "--output", str(first_manifest)]) == 0

    store = CollectorStore(database)
    pending = store.list_pending_reviews()
    first_passage_id = str(pending[0]["target_id"])
    store.record_review_decision(
        target_type="passage",
        target_id=first_passage_id,
        decision="accept",
        reviewer="test",
        rationale="Regression coverage.",
    )

    assert central_main([*arguments, "--output", str(second_manifest)]) == 0

    first_payload = json.loads(first_manifest.read_text(encoding="utf-8"))
    second_payload = json.loads(second_manifest.read_text(encoding="utf-8"))

    assert first_payload["document"]["duplicate"] is False
    assert second_payload["document"]["duplicate"] is True
    assert [
        item["id"] for item in second_payload["passages"]
    ] == [
        item["id"] for item in first_payload["passages"]
    ]
    assert [
        item["review_status"] for item in second_payload["passages"]
    ] == ["accepted", "pending"]
