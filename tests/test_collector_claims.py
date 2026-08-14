from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ecobiome.knowledge_acquisition.claim_candidates import (
    ClaimSegment,
    build_source_statement_candidates,
)
from ecobiome.knowledge_acquisition.collector_acquire import acquire_source
from ecobiome.knowledge_acquisition.collector_cli import main as collector_main
from ecobiome.knowledge_acquisition.persistence import CollectorStore


def _representation_id(database: Path) -> str:
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT id FROM representations ORDER BY created_at LIMIT 1"
        ).fetchone()
    assert row is not None
    return str(row[0])


def _segment_ids(database: Path) -> list[str]:
    with sqlite3.connect(database) as connection:
        return [
            str(row[0])
            for row in connection.execute(
                "SELECT id FROM segments ORDER BY segment_index"
            )
        ]


def test_builder_groups_segments_and_preserves_exact_evidence() -> None:
    segments = (
        ClaimSegment(
            id="a",
            segment_index=1,
            text="Medaka live outside",
            effective_text="Medaka live outside",
            review_status="pending",
            start_seconds=1.0,
            end_seconds=3.0,
            page_number=None,
            frame_start=None,
            frame_end=None,
        ),
        ClaimSegment(
            id="b",
            segment_index=2,
            text="in summer.",
            effective_text="in summer.",
            review_status="pending",
            start_seconds=3.1,
            end_seconds=4.0,
            page_number=None,
            frame_start=None,
            frame_end=None,
        ),
    )

    candidates = build_source_statement_candidates(
        segments,
        representation_id="rep",
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.claim_kind == "source_statement"
    assert candidate.text == "Medaka live outside in summer."
    assert [item.segment_id for item in candidate.evidence] == ["a", "b"]
    assert candidate.evidence[0].evidence_text == "Medaka live outside"
    assert candidate.evidence[0].segment_char_start == 0
    assert candidate.evidence[0].segment_char_end == 19
    assert candidate.metadata["epistemic_status"] == (
        "candidate_source_statement"
    )


def test_builder_rejected_segment_withholds_unresolved_prefix() -> None:
    segments = (
        ClaimSegment(
            "a", 1, "First", "First", "pending",
            None, None, None, None, None,
        ),
        ClaimSegment(
            "bad", 2, "Wrong", "Wrong", "rejected",
            None, None, None, None, None,
        ),
        ClaimSegment(
            "b", 3, "Second.", "Second.", "pending",
            None, None, None, None, None,
        ),
    )

    candidates = build_source_statement_candidates(
        segments,
        representation_id="rep",
    )

    assert [item.text for item in candidates] == ["Second."]


def test_proposal_persists_pending_claim_and_exact_evidence(
    tmp_path: Path,
) -> None:
    source = tmp_path / "notes.txt"
    source.write_text(
        "Water stayed clear.\n\nPlants provided shade.",
        encoding="utf-8",
    )
    database = tmp_path / "collector.sqlite3"
    acquisition = acquire_source(
        source=str(source),
        database=database,
        maximum_passage_characters=40,
    )
    representation_id = acquisition.receipt.representations[0].representation_id

    store = CollectorStore(database)
    receipt = store.propose_source_statement_claims(
        representation_id=representation_id,
    )

    assert len(receipt.claims) == 2
    assert all(not item.duplicate for item in receipt.claims)
    summary = store.summary()
    assert summary["claims"] == 2
    assert summary["pending_claims"] == 2
    assert summary["evidence"] == 2

    claim = store.get_claim_with_evidence(receipt.claims[0].claim_id)
    assert claim["review_status"] == "pending"
    assert claim["claim_kind"] == "source_statement"
    assert claim["evidence"][0]["evidence_text"] == "Water stayed clear."
    assert claim["evidence"][0]["segment_char_start"] == 0
    assert claim["evidence"][0]["segment_char_end"] == 19
    assert claim["evidence"][0]["canonical_locator"] == source.as_uri()


def test_accepted_segment_does_not_auto_accept_claim(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("A source statement.", encoding="utf-8")
    database = tmp_path / "collector.sqlite3"
    run = acquire_source(source=str(source), database=database)
    representation = run.receipt.representations[0]
    segment_id = representation.segment_ids[0]

    store = CollectorStore(database)
    store.record_review_decision(
        target_type="passage",
        target_id=segment_id,
        decision="accept",
        reviewer="human",
    )
    receipt = store.propose_source_statement_claims(
        representation_id=representation.representation_id,
    )

    claim = store.get_claim_with_evidence(receipt.claims[0].claim_id)
    assert claim["review_status"] == "pending"
    assert claim["metadata"]["segment_review_statuses"] == ["accepted"]


def test_corrected_segment_changes_claim_text_not_evidence(
    tmp_path: Path,
) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("parler de nos médica.", encoding="utf-8")
    database = tmp_path / "collector.sqlite3"
    run = acquire_source(source=str(source), database=database)
    representation = run.receipt.representations[0]
    segment_id = representation.segment_ids[0]

    store = CollectorStore(database)
    store.record_review_decision(
        target_type="passage",
        target_id=segment_id,
        decision="correct",
        corrected_text="parler de nos Medaka.",
        reviewer="human",
    )
    receipt = store.propose_source_statement_claims(
        representation_id=representation.representation_id,
    )

    claim = store.get_claim_with_evidence(receipt.claims[0].claim_id)
    assert claim["text"] == "parler de nos Medaka."
    assert claim["evidence"][0]["evidence_text"] == "parler de nos médica."
    assert claim["metadata"]["uses_review_correction"] is True


def test_reproposal_deduplicates_claim_and_evidence(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("Stable observation.", encoding="utf-8")
    database = tmp_path / "collector.sqlite3"
    run = acquire_source(source=str(source), database=database)
    representation_id = run.receipt.representations[0].representation_id
    store = CollectorStore(database)

    first = store.propose_source_statement_claims(
        representation_id=representation_id,
    )
    second = store.propose_source_statement_claims(
        representation_id=representation_id,
    )

    assert first.claims[0].claim_id == second.claims[0].claim_id
    assert second.claims[0].duplicate
    assert store.summary()["claims"] == 1
    assert store.summary()["evidence"] == 1


def test_evidence_preserves_segment_time_bounds(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("Timed statement.", encoding="utf-8")
    database = tmp_path / "collector.sqlite3"
    run = acquire_source(source=str(source), database=database)
    representation = run.receipt.representations[0]
    segment_id = representation.segment_ids[0]

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            UPDATE segments
            SET start_seconds_decimal = '12.5',
                end_seconds_decimal = '14.75'
            WHERE id = ?
            """,
            (str(segment_id),),
        )

    store = CollectorStore(database)
    receipt = store.propose_source_statement_claims(
        representation_id=representation.representation_id,
    )
    claim = store.get_claim_with_evidence(receipt.claims[0].claim_id)

    assert claim["evidence"][0]["start_seconds"] == 12.5
    assert claim["evidence"][0]["end_seconds"] == 14.75


def test_claim_review_remains_append_only(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("Candidate statement.", encoding="utf-8")
    database = tmp_path / "collector.sqlite3"
    run = acquire_source(source=str(source), database=database)
    store = CollectorStore(database)
    receipt = store.propose_source_statement_claims(
        representation_id=run.receipt.representations[0].representation_id,
    )
    claim_id = receipt.claims[0].claim_id

    store.record_review_decision(
        target_type="claim",
        target_id=claim_id,
        decision="reject",
        reviewer="reviewer",
        rationale="Not a scientific fact.",
    )

    claim = store.get_claim_with_evidence(claim_id)
    assert claim["review_status"] == "rejected"
    assert claim["text"] == "Candidate statement."
    assert claim["evidence"][0]["evidence_text"] == "Candidate statement."
    assert claim["review_history"][0]["decision"] == "reject"
    assert claim["review_history"][0]["reviewer"] == "reviewer"
    assert store.summary()["review_decisions"] == 1


def test_cli_propose_claims_and_claim_show(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("CLI statement.", encoding="utf-8")
    database = tmp_path / "collector.sqlite3"
    run = acquire_source(source=str(source), database=database)
    representation_id = run.receipt.representations[0].representation_id
    output = tmp_path / "claims.json"

    assert collector_main(
        [
            "propose-claims",
            "--database",
            str(database),
            "--representation-id",
            str(representation_id),
            "--output",
            str(output),
        ]
    ) == 0
    manifest = json.loads(capsys.readouterr().out)
    assert manifest["automatic_scientific_acceptance"] is False
    assert manifest["claim_count"] == 1
    claim_id = manifest["claims"][0]["id"]
    assert json.loads(output.read_text(encoding="utf-8")) == manifest

    assert collector_main(
        [
            "claim-show",
            claim_id,
            "--database",
            str(database),
        ]
    ) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["id"] == claim_id
    assert shown["evidence"][0]["source_title"] == "notes.txt"
