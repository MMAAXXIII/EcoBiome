from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import uuid4

import pytest

from ecobiome.knowledge_acquisition.collector_acquire import acquire_source
from ecobiome.knowledge_acquisition.collector_cli import main as collector_main
from ecobiome.knowledge_acquisition.persistence import CollectorStore
from ecobiome.knowledge_acquisition.semantic_claims import (
    parse_atomic_claim_batch,
)
from ecobiome.knowledge_acquisition.semantic_evaluation import (
    evaluate_semantic_batch,
)
from ecobiome.knowledge_acquisition.semantic_extraction import (
    ConservativeFrenchLexicalExtractorV1,
    SemanticExtractionError,
    atomic_batch_to_payload,
    build_semantic_extraction_request,
    run_semantic_extractor,
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source_claim(
    tmp_path: Path,
    text: str,
) -> tuple[CollectorStore, dict[str, object]]:
    source = tmp_path / "source.txt"
    source.write_text(text, encoding="utf-8")
    database = tmp_path / "collector.sqlite3"
    run = acquire_source(
        source=str(source),
        database=database,
        maximum_passage_characters=1000,
    )
    representation_id = (
        run.receipt.representations[0].representation_id
    )
    store = CollectorStore(database)
    receipt = store.propose_source_statement_claims(
        representation_id=representation_id,
    )
    assert len(receipt.claims) == 1
    return (
        store,
        store.get_claim_with_evidence(receipt.claims[0].claim_id),
    )


def test_request_exports_only_persisted_evidence(tmp_path: Path) -> None:
    store, claim = _source_claim(
        tmp_path,
        "Poisson venu d'Asie, Japon principalement.",
    )

    request = build_semantic_extraction_request(
        store,
        [str(claim["id"])],
    )

    assert request["schema_version"] == 1
    assert request["task"] == "extract_atomic_source_propositions"
    assert request["rules"]["do_not_invent_evidence"] is True
    source_claims = request["source_claims"]
    assert isinstance(source_claims, list)
    assert len(source_claims) == 1
    exported = source_claims[0]
    assert exported["claim_id"] == claim["id"]
    assert exported["effective_text"] == claim["effective_text"]
    assert exported["effective_text_sha256"] == _sha256_text(
        str(claim["effective_text"])
    )
    exported_evidence = exported["evidence"]
    assert isinstance(exported_evidence, list)
    assert exported_evidence
    assert exported_evidence[0]["evidence_id"] == (
        claim["evidence"][0]["id"]
    )
    assert exported_evidence[0]["text"] == (
        claim["evidence"][0]["evidence_text"]
    )


def test_request_rejects_rejected_source_claim(tmp_path: Path) -> None:
    store, claim = _source_claim(tmp_path, "Observation source.")
    store.record_review_decision(
        target_type="claim",
        target_id=str(claim["id"]),
        decision="reject",
        reviewer="human",
    )

    with pytest.raises(
        SemanticExtractionError,
        match="Rejected source_statement",
    ):
        build_semantic_extraction_request(
            store,
            [str(claim["id"])],
        )


def test_request_rejects_duplicate_claim_ids(tmp_path: Path) -> None:
    store, claim = _source_claim(tmp_path, "Observation source.")
    claim_id = str(claim["id"])

    with pytest.raises(
        SemanticExtractionError,
        match="must not contain duplicates",
    ):
        build_semantic_extraction_request(
            store,
            [claim_id, claim_id],
        )


class _WrongIdentityExtractor:
    name = "expected-name"
    version = "1.0"

    def extract(self, request: dict[str, object]) -> object:
        claim = request["source_claims"][0]
        evidence = claim["evidence"][0]
        return {
            "schema_version": 1,
            "extractor": {
                "name": "different-name",
                "version": "1.0",
            },
            "proposals": [
                {
                    "source_claim_id": claim["claim_id"],
                    "source_claim_effective_text_sha256": (
                        claim["effective_text_sha256"]
                    ),
                    "text": "Une proposition suffisamment longue.",
                    "semantic_type": "observation",
                    "evidence_ids": [evidence["evidence_id"]],
                }
            ],
        }


def test_harness_rejects_extractor_identity_spoofing(
    tmp_path: Path,
) -> None:
    store, claim = _source_claim(tmp_path, "Observation source.")

    with pytest.raises(
        SemanticExtractionError,
        match="output name",
    ):
        run_semantic_extractor(
            store,
            _WrongIdentityExtractor(),
            [str(claim["id"])],
        )


def test_lexical_baseline_is_non_persisted_and_guard_compatible(
    tmp_path: Path,
) -> None:
    store, claim = _source_claim(
        tmp_path,
        (
            "Poisson venu d'Asie, Japon principalement, très robuste "
            "et facile avec des variations de pH."
        ),
    )
    before = store.summary()["claims"]

    run = run_semantic_extractor(
        store,
        ConservativeFrenchLexicalExtractorV1(),
        [str(claim["id"])],
    )
    payload = atomic_batch_to_payload(run.batch)

    assert payload["extractor"]["name"] == (
        "conservative-french-lexical-baseline"
    )
    assert payload["proposals"]
    assert all(
        item["qualifiers"]["benchmark_only"] is True
        for item in payload["proposals"]
    )
    assert store.summary()["claims"] == before


def _batch(
    *,
    extractor: str,
    proposals: list[dict[str, object]],
) -> object:
    return parse_atomic_claim_batch(
        {
            "schema_version": 1,
            "extractor": {
                "name": extractor,
                "version": "1.0",
            },
            "proposals": proposals,
        }
    )


def _proposal(
    *,
    source_claim_id: str,
    source_hash: str,
    text: str,
    semantic_type: str,
    evidence_ids: list[str],
) -> dict[str, object]:
    return {
        "source_claim_id": source_claim_id,
        "source_claim_effective_text_sha256": source_hash,
        "text": text,
        "semantic_type": semantic_type,
        "evidence_ids": evidence_ids,
    }


def test_evaluation_exact_match_scores_one() -> None:
    source_claim_id = str(uuid4())
    source_hash = "a" * 64
    evidence_ids = [str(uuid4()), str(uuid4())]
    proposal = _proposal(
        source_claim_id=source_claim_id,
        source_hash=source_hash,
        text="La source décrit une tolérance au froid.",
        semantic_type="temperature_tolerance",
        evidence_ids=evidence_ids,
    )
    candidate = _batch(
        extractor="candidate",
        proposals=[proposal],
    )
    reference = _batch(
        extractor="reference",
        proposals=[proposal],
    )

    report = evaluate_semantic_batch(candidate, reference)

    assert report["exact_precision"] == 1.0
    assert report["exact_recall"] == 1.0
    assert report["exact_f1"] == 1.0
    assert report["mean_aligned_evidence_jaccard"] == 1.0
    assert report["mean_aligned_text_token_jaccard"] == 1.0
    assert report["metric_definition"][
        "scientific_correctness_measured"
    ] is False


def test_evaluation_penalises_extra_and_partial_evidence() -> None:
    source_claim_id = str(uuid4())
    source_hash = "b" * 64
    evidence_a = str(uuid4())
    evidence_b = str(uuid4())
    reference = _batch(
        extractor="reference",
        proposals=[
            _proposal(
                source_claim_id=source_claim_id,
                source_hash=source_hash,
                text="La source décrit une tolérance au froid.",
                semantic_type="temperature_tolerance",
                evidence_ids=[evidence_a, evidence_b],
            )
        ],
    )
    candidate = _batch(
        extractor="candidate",
        proposals=[
            _proposal(
                source_claim_id=source_claim_id,
                source_hash=source_hash,
                text="Le poisson tolère le froid.",
                semantic_type="temperature_tolerance",
                evidence_ids=[evidence_b],
            ),
            _proposal(
                source_claim_id=source_claim_id,
                source_hash=source_hash,
                text="Une autre proposition sans référence équivalente.",
                semantic_type="other_observation",
                evidence_ids=[evidence_a],
            ),
        ],
    )

    report = evaluate_semantic_batch(candidate, reference)

    assert report["candidate_count"] == 2
    assert report["reference_count"] == 1
    assert report["aligned_count"] == 1
    assert report["exact_evidence_matches"] == 0
    assert report["exact_precision"] == 0.0
    assert report["exact_recall"] == 0.0
    assert report["mean_aligned_evidence_jaccard"] == 0.5
    assert report["unmatched_candidate_indices"] == [2]


def test_cli_exports_and_runs_baseline_without_persistence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    store, claim = _source_claim(
        tmp_path,
        "Poisson venu d'Asie, Japon principalement.",
    )
    database = store.database_path
    claim_id = str(claim["id"])
    request_path = tmp_path / "request.json"
    baseline_path = tmp_path / "baseline.json"

    assert collector_main(
        [
            "semantic-export",
            "--database",
            str(database),
            "--claim-id",
            claim_id,
            "--output",
            str(request_path),
        ]
    ) == 0
    capsys.readouterr()
    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert request["source_claims"][0]["claim_id"] == claim_id

    claims_before = store.summary()["claims"]
    assert collector_main(
        [
            "semantic-baseline",
            "--database",
            str(database),
            "--claim-id",
            claim_id,
            "--output",
            str(baseline_path),
        ]
    ) == 0
    capsys.readouterr()

    baseline = json.loads(
        baseline_path.read_text(encoding="utf-8")
    )
    assert baseline["extractor"]["name"] == (
        "conservative-french-lexical-baseline"
    )
    assert baseline["proposals"]
    assert all(
        item["qualifiers"]["benchmark_only"] is True
        for item in baseline["proposals"]
    )
    assert store.summary()["claims"] == claims_before

    batch = parse_atomic_claim_batch(baseline)
    with pytest.raises(
        ValueError,
        match="Benchmark-only semantic proposals",
    ):
        store.persist_atomic_claim_batch(batch)
