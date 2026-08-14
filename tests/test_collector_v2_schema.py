"""Cross-row invariant tests for Collector schema v2."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest

from ecobiome.knowledge_acquisition.collector_schema import (
    validate_derivation_graph,
    validate_evidence_anchors,
)
from ecobiome.knowledge_acquisition.persistence import CollectorStore
from ecobiome.knowledge_acquisition.processing import split_into_passages
from ecobiome.knowledge_acquisition.source import SourceType
from ecobiome.knowledge_acquisition.transcript import load_transcript


def _store(tmp_path: Path) -> tuple[CollectorStore, str, str]:
    transcript = tmp_path / "input.txt"
    transcript.write_text(
        "Water temperature remained stable at 24 C.",
        encoding="utf-8",
    )
    imported = load_transcript(
        transcript,
        title="Invariant fixture",
        locator="local:invariant-fixture",
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
    return store, str(receipt.document_id), str(receipt.passage_ids[0])


def test_derivation_cycle_is_rejected_by_application_validator(
    tmp_path: Path,
) -> None:
    store, representation_id, _segment_id = _store(tmp_path)

    with sqlite3.connect(store.database_path) as connection:
        connection.row_factory = sqlite3.Row
        second_id = str(uuid4())
        now = "2026-08-11T10:00:00+00:00"
        connection.execute(
            """
            INSERT INTO representations(
                id,
                source_id,
                origin_raw_artifact_id,
                logical_key,
                representation_kind,
                media_type,
                language,
                content_sha256,
                artifact_store_key,
                materialization_status,
                metadata_json,
                created_at
            )
            SELECT
                ?,
                source_id,
                origin_raw_artifact_id,
                'cycle-test-secondary',
                representation_kind,
                media_type,
                language,
                content_sha256,
                artifact_store_key,
                materialization_status,
                '{}',
                ?
            FROM representations
            WHERE id = ?
            """,
            (
                second_id,
                now,
                representation_id,
            ),
        )
        connection.execute(
            """
            INSERT INTO derivations(
                id,
                child_representation_id,
                parent_raw_artifact_id,
                parent_representation_id,
                derivation_method,
                tool_name,
                tool_version,
                parameters_json,
                created_at
            )
            VALUES (?, ?, NULL, ?, 'normalize', 'test', '1', '{}', ?)
            """,
            (
                str(uuid4()),
                second_id,
                representation_id,
                now,
            ),
        )
        connection.execute(
            """
            INSERT INTO derivations(
                id,
                child_representation_id,
                parent_raw_artifact_id,
                parent_representation_id,
                derivation_method,
                tool_name,
                tool_version,
                parameters_json,
                created_at
            )
            VALUES (?, ?, NULL, ?, 'invalid-cycle', 'test', '1', '{}', ?)
            """,
            (
                str(uuid4()),
                representation_id,
                second_id,
                now,
            ),
        )

        with pytest.raises(RuntimeError, match="cycle"):
            validate_derivation_graph(connection)


def test_evidence_char_anchor_must_fit_segment_and_match_text(
    tmp_path: Path,
) -> None:
    store, _representation_id, segment_id = _store(tmp_path)

    with sqlite3.connect(store.database_path) as connection:
        now = "2026-08-11T10:00:00+00:00"
        evidence_id = str(uuid4())
        connection.execute(
            """
            INSERT INTO source_evidence(
                id,
                segment_id,
                segment_char_start,
                segment_char_end,
                evidence_text_sha256,
                start_seconds_decimal,
                end_seconds_decimal,
                page_number,
                frame_start,
                frame_end,
                evidence_metadata_json,
                created_at
            )
            VALUES (?, ?, 0, 999999, ?, NULL, NULL, NULL, NULL, NULL, '{}', ?)
            """,
            (
                evidence_id,
                segment_id,
                "0" * 64,
                now,
            ),
        )

        with pytest.raises(RuntimeError, match="exceeds segment"):
            validate_evidence_anchors(connection)
