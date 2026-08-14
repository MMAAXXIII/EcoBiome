from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition.collector_acquire import acquire_source
from ecobiome.knowledge_acquisition.collector_cli import main as collector_main
from ecobiome.knowledge_acquisition.persistence import CollectorStore
from ecobiome.knowledge_acquisition.semantic_claims import (
    SemanticClaimValidationError,
    load_atomic_claim_batch,
    parse_atomic_claim_batch,
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source_claims(
    tmp_path: Path,
    text: str = "Medaka tolerate pH variations.",
) -> tuple[CollectorStore, list[dict[str, object]]]:
    source = tmp_path / "notes.txt"
    source.write_text(text, encoding="utf-8")
    database = tmp_path / "collector.sqlite3"
    run = acquire_source(
        source=str(source),
        database=database,
        maximum_passage_characters=20,
    )
    store = CollectorStore(database)
    receipt = store.propose_source_statement_claims(
        representation_id=(
            run.receipt.representations[0].representation_id
        ),
    )
    claims = [
        store.get_claim_with_evidence(item.claim_id)
        for item in receipt.claims
    ]
    return store, claims


def _proposal(
    claim: dict[str, object],
    *,
    text: str = "Medaka are described as tolerant of pH variations.",
    semantic_type: str = "tolerance",
    evidence_ids: list[str] | None = None,
) -> dict[str, object]:
    evidence = claim["evidence"]
    assert isinstance(evidence, list)
    effective_text = str(claim["effective_text"])
    selected = (
        evidence_ids
        if evidence_ids is not None
        else [str(item["id"]) for item in evidence]
    )
    return {
        "source_claim_id": str(claim["id"]),
        "source_claim_effective_text_sha256": _sha256_text(
            effective_text
        ),
        "text": text,
        "semantic_type": semantic_type,
        "evidence_ids": selected,
        "qualifiers": {
            "scope": "source_attribution",
        },
    }


def _batch(*proposals: dict[str, object]) -> object:
    return parse_atomic_claim_batch(
        {
            "schema_version": 1,
            "extractor": {
                "name": "fixture-semantic",
                "version": "1.0",
            },
            "proposals": list(proposals),
        }
    )


def test_contract_allows_empty_proposal_batch() -> None:
    batch = parse_atomic_claim_batch(
        {
            "schema_version": 1,
            "extractor": {
                "name": "conservative-extractor",
                "version": "1.0",
            },
            "proposals": [],
        }
    )

    assert batch.proposals == ()


def test_contract_accepts_strict_atomic_proposal(tmp_path: Path) -> None:
    store, claims = _source_claims(tmp_path)
    batch = _batch(_proposal(claims[0]))

    assert batch.schema_version == 1
    assert batch.extractor.name == "fixture-semantic"
    assert len(batch.proposals) == 1
    assert batch.proposals[0].semantic_type == "tolerance"
    assert store.summary()["claims"] >= 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("confidence", 0.99),
        ("accepted", True),
        ("evidence_text", "fabricated"),
    ],
)
def test_contract_rejects_model_authority_and_fabricated_evidence_fields(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    _store, claims = _source_claims(tmp_path)
    proposal = _proposal(claims[0])
    proposal[field] = value

    with pytest.raises(
        SemanticClaimValidationError,
        match="unsupported keys",
    ):
        _batch(proposal)



def test_contract_rejects_noncanonical_uppercase_uuid(tmp_path: Path) -> None:
    _store, claims = _source_claims(tmp_path)
    proposal = _proposal(claims[0])
    proposal["source_claim_id"] = str(claims[0]["id"]).upper()

    with pytest.raises(
        SemanticClaimValidationError,
        match="canonical lowercase UUID",
    ):
        _batch(proposal)

def test_contract_rejects_duplicate_evidence_ids(tmp_path: Path) -> None:
    _store, claims = _source_claims(tmp_path)
    evidence = claims[0]["evidence"]
    assert isinstance(evidence, list)
    evidence_id = str(evidence[0]["id"])
    proposal = _proposal(
        claims[0],
        evidence_ids=[evidence_id, evidence_id],
    )

    with pytest.raises(
        SemanticClaimValidationError,
        match="contains duplicates",
    ):
        _batch(proposal)


def test_json_loader_rejects_duplicate_object_keys(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        (
            '{"schema_version":1,"schema_version":1,'
            '"extractor":{"name":"x","version":"1"},'
            '"proposals":[]}'
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        SemanticClaimValidationError,
        match="Duplicate JSON object key",
    ):
        load_atomic_claim_batch(path)



def test_contract_rejects_nonfinite_qualifier_from_python_object(
    tmp_path: Path,
) -> None:
    _store, claims = _source_claims(tmp_path)
    proposal = _proposal(claims[0])
    proposal["qualifiers"] = {"measurement": float("nan")}

    with pytest.raises(
        SemanticClaimValidationError,
        match="must be finite",
    ):
        _batch(proposal)


def test_json_loader_rejects_oversized_input(tmp_path: Path) -> None:
    path = tmp_path / "too-large.json"
    path.write_text(" " * (2 * 1024 * 1024 + 1), encoding="utf-8")

    with pytest.raises(
        SemanticClaimValidationError,
        match="input exceeds",
    ):
        load_atomic_claim_batch(path)

def test_atomic_persistence_reuses_exact_parent_evidence(
    tmp_path: Path,
) -> None:
    store, claims = _source_claims(tmp_path)
    parent = claims[0]
    batch = _batch(_proposal(parent))

    receipt = store.persist_atomic_claim_batch(batch)
    assert len(receipt) == 1
    assert receipt[0].duplicate is False

    atomic = store.get_claim_with_evidence(receipt[0].claim_id)
    assert atomic["claim_kind"] == "atomic_source_proposition"
    assert atomic["review_status"] == "pending"
    assert atomic["effective_text"] == atomic["text"]
    assert atomic["metadata"]["epistemic_status"] == (
        "candidate_atomic_source_proposition"
    )
    assert atomic["metadata"]["automatic_scientific_acceptance"] is False
    assert atomic["metadata"]["source_claim_id"] == parent["id"]

    parent_evidence = parent["evidence"]
    atomic_evidence = atomic["evidence"]
    assert isinstance(parent_evidence, list)
    assert len(atomic_evidence) == len(parent_evidence)
    assert atomic["metadata"]["selected_parent_evidence_ids"] == [
        str(item["id"])
        for item in parent_evidence
    ]
    for original, reused in zip(
        parent_evidence,
        atomic_evidence,
        strict=True,
    ):
        assert reused["id"] == original["id"]
        assert reused["evidence_text"] == original["evidence_text"]
        assert reused["evidence_sha256"] == original["evidence_sha256"]
        assert reused["segment_id"] == original["segment_id"]
        assert reused["start_seconds"] == original["start_seconds"]
        assert reused["end_seconds"] == original["end_seconds"]


def test_atomic_persistence_rejects_evidence_from_another_claim(
    tmp_path: Path,
) -> None:
    store, claims = _source_claims(
        tmp_path,
        "First statement.\n\nSecond statement.",
    )
    assert len(claims) == 2
    second_evidence = claims[1]["evidence"]
    assert isinstance(second_evidence, list)
    proposal = _proposal(
        claims[0],
        evidence_ids=[str(second_evidence[0]["id"])],
    )

    with pytest.raises(
        ValueError,
        match="does not belong",
    ):
        store.persist_atomic_claim_batch(_batch(proposal))


def test_atomic_persistence_rejects_stale_parent_text(
    tmp_path: Path,
) -> None:
    store, claims = _source_claims(tmp_path)
    parent = claims[0]
    batch = _batch(_proposal(parent))

    store.record_review_decision(
        target_type="claim",
        target_id=str(parent["id"]),
        decision="correct",
        corrected_text="Medaka tolerate some pH variation.",
        reviewer="human",
    )

    with pytest.raises(ValueError, match="stale"):
        store.persist_atomic_claim_batch(batch)

    refreshed = store.get_claim_with_evidence(parent["id"])
    assert refreshed["effective_text"] == (
        "Medaka tolerate some pH variation."
    )
    assert refreshed["text_was_corrected"] is True


def test_atomic_persistence_rejects_rejected_parent(
    tmp_path: Path,
) -> None:
    store, claims = _source_claims(tmp_path)
    parent = claims[0]
    store.record_review_decision(
        target_type="claim",
        target_id=str(parent["id"]),
        decision="reject",
        reviewer="human",
    )

    with pytest.raises(ValueError, match="Rejected source_statement"):
        store.persist_atomic_claim_batch(_batch(_proposal(parent)))


def test_atomic_persistence_rejects_rejected_evidence_segment(
    tmp_path: Path,
) -> None:
    store, claims = _source_claims(tmp_path)
    parent = claims[0]
    evidence = parent["evidence"]
    assert isinstance(evidence, list)
    store.record_review_decision(
        target_type="passage",
        target_id=str(evidence[0]["segment_id"]),
        decision="reject",
        reviewer="human",
    )

    with pytest.raises(ValueError, match="rejected Segment"):
        store.persist_atomic_claim_batch(_batch(_proposal(parent)))



def test_atomic_batch_rolls_back_if_later_proposal_is_invalid(
    tmp_path: Path,
) -> None:
    store, claims = _source_claims(
        tmp_path,
        "First statement.\n\nSecond statement.",
    )
    assert len(claims) == 2
    second_evidence = claims[1]["evidence"]
    assert isinstance(second_evidence, list)

    valid = _proposal(
        claims[0],
        text="The source makes a first atomic statement.",
    )
    invalid = _proposal(
        claims[1],
        text="The source makes a second atomic statement.",
        evidence_ids=[str(claims[0]["evidence"][0]["id"])],
    )
    before = store.summary()

    with pytest.raises(ValueError, match="does not belong"):
        store.persist_atomic_claim_batch(_batch(valid, invalid))

    assert store.summary() == before

def test_exact_atomic_reingestion_deduplicates_claim_and_evidence(
    tmp_path: Path,
) -> None:
    store, claims = _source_claims(tmp_path)
    batch = _batch(_proposal(claims[0]))

    first = store.persist_atomic_claim_batch(batch)
    summary_after_first = store.summary()
    second = store.persist_atomic_claim_batch(batch)

    assert first[0].claim_id == second[0].claim_id
    assert second[0].duplicate is True
    assert store.summary() == summary_after_first


def test_accepted_source_claim_never_auto_accepts_atomic_claim(
    tmp_path: Path,
) -> None:
    store, claims = _source_claims(tmp_path)
    parent = claims[0]
    store.record_review_decision(
        target_type="claim",
        target_id=str(parent["id"]),
        decision="accept",
        reviewer="human",
    )
    refreshed = store.get_claim_with_evidence(parent["id"])

    receipt = store.persist_atomic_claim_batch(
        _batch(_proposal(refreshed))
    )
    atomic = store.get_claim_with_evidence(receipt[0].claim_id)

    assert atomic["review_status"] == "pending"
    assert atomic["review_history"] == []
    assert atomic["metadata"]["source_claim_review_status"] == "accepted"


def test_cli_ingest_atomic_claims_writes_reviewable_manifest(
    tmp_path: Path,
    capsys,
) -> None:
    store, claims = _source_claims(tmp_path)
    database = store.database_path
    payload = {
        "schema_version": 1,
        "extractor": {
            "name": "fixture-semantic",
            "version": "1.0",
        },
        "proposals": [_proposal(claims[0])],
    }
    input_path = tmp_path / "atomic-input.json"
    output_path = tmp_path / "atomic-output.json"
    input_path.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )

    assert collector_main(
        [
            "ingest-atomic-claims",
            str(input_path),
            "--database",
            str(database),
            "--output",
            str(output_path),
        ]
    ) == 0

    manifest = json.loads(capsys.readouterr().out)
    assert manifest["semantic_contract_version"] == 1
    assert manifest["automatic_scientific_acceptance"] is False
    assert manifest["claim_count"] == 1
    assert manifest["claims"][0]["claim_kind"] == (
        "atomic_source_proposition"
    )
    assert manifest["claims"][0]["review_status"] == "pending"
    assert json.loads(output_path.read_text(encoding="utf-8")) == manifest
