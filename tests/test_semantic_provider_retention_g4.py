from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition.collector_acquire import acquire_source
from ecobiome.knowledge_acquisition.persistence import CollectorStore
from ecobiome.knowledge_acquisition.semantic_contract_v2_8 import (
    apply_relation_type_contract_v2_8,
    load_relation_type_contract_v2_8,
)
from ecobiome.knowledge_acquisition.semantic_contract_v2_10 import (
    apply_relation_type_delta_v2_10,
    load_relation_type_delta_v2_10,
)
from ecobiome.knowledge_acquisition.semantic_extraction import (
    build_semantic_extraction_request,
)
from ecobiome.knowledge_acquisition.semantic_provider_retention_v1 import (
    ProviderRetentionError,
    retain_collector_provider_run_v1,
)
from ecobiome.knowledge_acquisition.semantic_robustness_v2_7 import (
    validate_registry_v2_7,
)
from ecobiome.knowledge_persistence import (
    ClaimEvidenceLinksRow,
    ClaimReviewEventsRow,
    FilesystemContentAddressedArtifactStore,
    KnowledgeSourcesRow,
    PersistenceConfig,
    RepresentationsRow,
    SegmentsRow,
    SourceClaimsRow,
    SourceEvidenceRow,
    SQLiteScientificFoundationUnitOfWork,
    initialize_database,
)
from ecobiome.knowledge_persistence.contracts import SegmentReviewEventsRow

ROOT = Path(__file__).resolve().parent
CREATED_AT = "2026-08-17T09:00:00Z"
V27 = (
    ROOT
    / "fixtures"
    / "collector_semantic_v2_7"
    / "SEMANTIC_RELATION_REGISTRY_V2_7.json"
)
V28 = (
    ROOT
    / "fixtures"
    / "collector_semantic_v2_8"
    / "SEMANTIC_RELATION_TYPE_CONTRACT_V2_8.json"
)
V210 = (
    ROOT
    / "fixtures"
    / "collector_semantic_v2_10"
    / "SEMANTIC_RELATION_TYPE_DELTA_V2_10.json"
)

_APPEND_ONLY_TABLES = (
    "semantic_provider_runs",
    "semantic_provider_run_claim_inputs",
    "semantic_provider_run_evidence_inputs",
    "semantic_provider_run_events",
    "semantic_candidates",
    "semantic_candidate_evidence_links",
    "semantic_provider_candidate_origins",
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _registry_v2_10() -> dict[str, object]:
    base = validate_registry_v2_7(
        json.loads(V27.read_text(encoding="utf-8"))
    )
    v2_8 = apply_relation_type_contract_v2_8(
        base,
        load_relation_type_contract_v2_8(V28),
    )
    return apply_relation_type_delta_v2_10(
        v2_8,
        load_relation_type_delta_v2_10(V210),
    )


def _collector_fixture(
    tmp_path: Path,
) -> tuple[CollectorStore, str, dict[str, object]]:
    source = tmp_path / "source.txt"
    source.write_text(
        "juvenile zebrafish were studied.",
        encoding="utf-8",
    )
    database = tmp_path / "collector.sqlite3"
    run = acquire_source(
        source=str(source),
        database=database,
        maximum_passage_characters=1000,
    )
    representation_id = run.receipt.representations[0].representation_id
    store = CollectorStore(database)
    receipt = store.propose_source_statement_claims(
        representation_id=representation_id,
    )
    assert len(receipt.claims) == 1
    claim_id = str(receipt.claims[0].claim_id)
    store.record_review_decision(
        target_type="claim",
        target_id=claim_id,
        decision="accept",
        reviewer="g4-fixture",
        rationale="reviewed before provider retention",
    )
    request = build_semantic_extraction_request(store, [claim_id])
    return store, claim_id, request


def _scientific_foundation_fixture(
    tmp_path: Path,
    source_request: dict[str, object],
) -> tuple[
    PersistenceConfig,
    FilesystemContentAddressedArtifactStore,
    Path,
]:
    repo = tmp_path / "repo"
    repo.mkdir()
    storage = tmp_path / "scientific"
    config = PersistenceConfig(
        storage / "scientific.sqlite3",
        storage / "artifacts",
    )
    initialize_database(config, repo_root=repo)
    artifacts = FilesystemContentAddressedArtifactStore(
        config.artifact_store_root
    )

    raw_claims = source_request["source_claims"]
    assert isinstance(raw_claims, list)
    claim = raw_claims[0]
    assert isinstance(claim, dict)
    raw_evidence = claim["evidence"]
    assert isinstance(raw_evidence, list)
    evidence = raw_evidence[0]
    assert isinstance(evidence, dict)
    raw_source = evidence["source"]
    assert isinstance(raw_source, dict)

    source_id = str(raw_source["source_id"])
    claim_id = str(claim["claim_id"])
    evidence_id = str(evidence["evidence_id"])
    segment_id = str(evidence["segment_id"])
    evidence_text = str(evidence["text"])
    evidence_sha = str(evidence["sha256"])
    effective_text = str(claim["effective_text"])
    effective_sha = str(claim["effective_text_sha256"])

    source_row = KnowledgeSourcesRow(
        id=source_id,
        source_type=str(raw_source["source_type"]),
        canonical_locator=str(raw_source["canonical_locator"]),
        title=str(raw_source.get("title") or "G4 fixture"),
        author=(
            None
            if raw_source.get("author") is None
            else str(raw_source["author"])
        ),
        language="en",
        description="",
        imported_at=CREATED_AT,
        source_metadata_json="{}",
        logical_identity_sha256=_sha(
            f"{raw_source['source_type']}:{raw_source['canonical_locator']}"
        ),
        created_at=CREATED_AT,
    )
    representation_row = RepresentationsRow(
        id="g4-representation",
        source_id=source_id,
        origin_raw_artifact_id=None,
        logical_key="main",
        representation_kind="text",
        media_type="text/plain",
        language="en",
        content_sha256=evidence_sha,
        artifact_store_key=None,
        materialization_status="inline",
        metadata_json="{}",
        created_at=CREATED_AT,
    )
    segment_row = SegmentsRow(
        id=segment_id,
        representation_id=representation_row.id,
        segment_index=int(evidence["segment_index"]),
        text_inline=evidence_text,
        text_sha256=evidence_sha,
        materialization_status="inline",
        representation_char_start=0,
        representation_char_end=len(evidence_text),
        start_seconds_decimal=None,
        end_seconds_decimal=None,
        page_number=None,
        frame_start=None,
        frame_end=None,
        review_status="pending",
        metadata_json="{}",
        created_at=CREATED_AT,
    )
    evidence_row = SourceEvidenceRow(
        id=evidence_id,
        segment_id=segment_id,
        segment_char_start=0,
        segment_char_end=len(evidence_text),
        evidence_text_sha256=evidence_sha,
        start_seconds_decimal=None,
        end_seconds_decimal=None,
        page_number=None,
        frame_start=None,
        frame_end=None,
        evidence_metadata_json="{}",
        created_at=CREATED_AT,
    )
    claim_row = SourceClaimsRow(
        id=claim_id,
        source_id=source_id,
        representation_id=representation_row.id,
        parent_claim_id=None,
        claim_layer="extracted",
        claim_text=effective_text,
        claim_text_sha256=effective_sha,
        claim_kind="source_statement",
        semantic_type=None,
        qualifiers_json="{}",
        extraction_confidence_decimal=None,
        source_claim_effective_text_sha256=effective_sha,
        notes="",
        initial_review_status="pending",
        created_at=CREATED_AT,
    )
    link_row = ClaimEvidenceLinksRow(
        claim_id=claim_id,
        evidence_id=evidence_id,
        evidence_order=0,
        link_role="supports_source_claim",
        created_at=CREATED_AT,
    )
    claim_review = ClaimReviewEventsRow(
        id="g4-claim-review-accept",
        claim_id=claim_id,
        decision="accept",
        reviewer="g4-fixture",
        notes="reviewed before provider retention",
        corrected_text=None,
        corrected_text_sha256=None,
        review_metadata_json="{}",
        reviewed_at="2026-08-17T09:00:01Z",
    )
    segment_review = SegmentReviewEventsRow(
        id="g4-segment-review-accept",
        segment_id=segment_id,
        decision="accept",
        reviewer="g4-fixture",
        rationale="usable provider Evidence",
        corrected_text=None,
        corrected_text_sha256=None,
        review_metadata_json="{}",
        reviewed_at="2026-08-17T09:00:01Z",
    )

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow:
        assert uow.provenance.add_knowledge_source(source_row) is True
        assert uow.provenance.add_representation(representation_row) is True
        assert uow.provenance.add_segments([segment_row]) == 1
        assert uow.provenance.add_source_evidence([evidence_row]) == 1
        assert uow.provenance.add_source_claims([claim_row]) == 1
        assert uow.provenance.add_claim_evidence_links([link_row]) == 1
        assert uow.provenance.record_claim_review_event(claim_review) is True
        assert (
            uow.provenance.record_segment_review_event(segment_review) is True
        )
        uow.commit()

    return config, artifacts, repo


def _install_append_only_guards(config: PersistenceConfig) -> None:
    with sqlite3.connect(config.database_path) as connection:
        for table in _APPEND_ONLY_TABLES:
            connection.execute(
                f"CREATE TRIGGER guard_{table}_update "
                f"BEFORE UPDATE ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'append-only UPDATE blocked'); END"
            )
            connection.execute(
                f"CREATE TRIGGER guard_{table}_delete "
                f"BEFORE DELETE ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'append-only DELETE blocked'); END"
            )


def _compact_output(
    source_request: dict[str, object],
    *,
    duplicate: bool = True,
) -> dict[str, object]:
    claims = source_request["source_claims"]
    assert isinstance(claims, list)
    claim = claims[0]
    assert isinstance(claim, dict)
    evidence = claim["evidence"]
    assert isinstance(evidence, list)
    evidence_id = str(evidence[0]["evidence_id"])

    proposal = {
        "s": {
            "c": str(claim["claim_id"]),
            "e": [evidence_id],
        },
        "x": {
            "t": "study_subject",
            "m": {
                "r": "studied",
                "a": {
                    "life_stage": "juvenile",
                    "species": "zebrafish",
                },
            },
        },
    }
    return {"p": [proposal, proposal] if duplicate else [proposal]}


def _retention_kwargs(
    source_request: dict[str, object],
) -> dict[str, object]:
    compact = _compact_output(source_request)
    request_body = json.dumps(
        {
            "model": "fixture-model",
            "source_request": source_request,
        },
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    response_body = json.dumps(
        {
            "id": "response-1",
            "status": "completed",
            "output": compact,
        },
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    return {
        "compact_output": compact,
        "registry_v2_10": _registry_v2_10(),
        "run_id": "g4-provider-run-1",
        "provider_name": "fixture-provider",
        "provider_adapter_name": "fixture-provider-adapter",
        "provider_adapter_version": "1.0",
        "endpoint": "https://provider.invalid/v1",
        "model_requested": "fixture-model",
        "instruction_sha256": _sha("fixture instruction"),
        "request_body": request_body,
        "response_body": response_body,
        "safe_configuration": {
            "store": False,
            "tools": [],
        },
        "created_at": CREATED_AT,
        "started_at": "2026-08-17T08:59:59Z",
        "model_returned": "fixture-model",
        "provider_request_id": "request-1",
        "provider_response_id": "response-1",
        "http_status_code": 200,
        "response_status": "completed",
        "content_type": "application/json",
        "usage": {
            "input_tokens": 12,
            "output_tokens": 8,
        },
        "diagnostics": {
            "fixture": True,
        },
    }


def _count(config: PersistenceConfig, table: str) -> int:
    with sqlite3.connect(config.database_path) as connection:
        row = connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()
    assert row is not None
    return int(row[0])


def test_g4_collector_to_v6_provider_retention_is_append_only_and_idempotent(
    tmp_path: Path,
) -> None:
    store, claim_id, source_request = _collector_fixture(tmp_path)
    config, artifacts, repo = _scientific_foundation_fixture(
        tmp_path,
        source_request,
    )
    _install_append_only_guards(config)
    kwargs = _retention_kwargs(source_request)

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow:
        receipt = retain_collector_provider_run_v1(
            store,
            [claim_id],
            uow,
            **kwargs,
        )
        uow.commit()

    assert receipt.run_inserted is True
    assert receipt.claim_input_inserted_count == 1
    assert receipt.evidence_input_inserted_count == 1
    assert receipt.provider_event_inserted_count == 3
    assert receipt.candidate_inserted_count == 1
    assert receipt.candidate_count == 1
    assert receipt.origin_inserted_count == 2
    assert receipt.origin_count == 2
    assert receipt.automatic_scientific_acceptance is False

    assert _count(config, "semantic_provider_runs") == 1
    assert _count(config, "semantic_provider_run_claim_inputs") == 1
    assert _count(config, "semantic_provider_run_evidence_inputs") == 1
    assert _count(config, "semantic_provider_run_events") == 3
    assert _count(config, "semantic_candidates") == 1
    assert _count(config, "semantic_candidate_evidence_links") == 1
    assert _count(config, "semantic_provider_candidate_origins") == 2

    with sqlite3.connect(config.database_path) as connection:
        events = connection.execute(
            "SELECT event_index,event_type "
            "FROM semantic_provider_run_events "
            "ORDER BY event_index"
        ).fetchall()
        origins = connection.execute(
            "SELECT proposal_index,semantic_candidate_id "
            "FROM semantic_provider_candidate_origins "
            "ORDER BY proposal_index"
        ).fetchall()
        automatic = connection.execute(
            "SELECT automatic_scientific_acceptance "
            "FROM semantic_candidates"
        ).fetchone()

    assert events == [
        (0, "provider_response_received"),
        (1, "validated"),
        (2, "completed"),
    ]
    assert [row[0] for row in origins] == [0, 1]
    assert origins[0][1] == origins[1][1]
    assert automatic == (0,)

    assert artifacts.verify(
        receipt.request_artifact_store_key
    ).sha256 == hashlib.sha256(
        kwargs["request_body"]
    ).hexdigest()
    assert artifacts.verify(
        receipt.response_artifact_store_key
    ).sha256 == hashlib.sha256(
        kwargs["response_body"]
    ).hexdigest()
    assert artifacts.verify(
        receipt.validated_output_artifact_store_key
    ).size_bytes > 0

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow:
        replay = retain_collector_provider_run_v1(
            store,
            [claim_id],
            uow,
            **kwargs,
        )
        uow.commit()

    assert replay.run_inserted is False
    assert replay.claim_input_inserted_count == 0
    assert replay.evidence_input_inserted_count == 0
    assert replay.provider_event_inserted_count == 0
    assert replay.candidate_inserted_count == 0
    assert replay.origin_inserted_count == 0
    assert _count(config, "semantic_provider_runs") == 1
    assert _count(config, "semantic_provider_run_events") == 3
    assert _count(config, "semantic_candidates") == 1
    assert _count(config, "semantic_provider_candidate_origins") == 2


def test_g4_rejects_collector_v6_claim_snapshot_drift_before_cas_write(
    tmp_path: Path,
) -> None:
    store, claim_id, source_request = _collector_fixture(tmp_path)
    config, artifacts, repo = _scientific_foundation_fixture(
        tmp_path,
        source_request,
    )

    corrected_text = "adult zebrafish were studied"
    correction = ClaimReviewEventsRow(
        id="g4-claim-review-correct",
        claim_id=claim_id,
        decision="correct",
        reviewer="g4-fixture",
        notes="scientific correction after Collector snapshot",
        corrected_text=corrected_text,
        corrected_text_sha256=_sha(corrected_text),
        review_metadata_json="{}",
        reviewed_at="2026-08-17T09:00:02Z",
    )
    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow:
        assert uow.provenance.record_claim_review_event(correction) is True
        uow.commit()

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow, pytest.raises(
        ProviderRetentionError,
        match="Collector/V6 Claim snapshot drift",
    ):
        retain_collector_provider_run_v1(
            store,
            [claim_id],
            uow,
            **_retention_kwargs(source_request),
        )

    assert _count(config, "semantic_provider_runs") == 0
    assert _count(config, "semantic_candidates") == 0
    assert not list(config.artifact_store_root.rglob("*.blob"))


def test_g4_zero_proposal_abstention_retains_audited_run_without_candidate(
    tmp_path: Path,
) -> None:
    store, claim_id, source_request = _collector_fixture(tmp_path)
    config, artifacts, repo = _scientific_foundation_fixture(
        tmp_path,
        source_request,
    )
    kwargs = _retention_kwargs(source_request)
    kwargs["compact_output"] = {"p": []}
    kwargs["response_body"] = b'{"status":"completed","output":{"p":[]}}'
    kwargs["run_id"] = "g4-provider-run-abstention"

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow:
        receipt = retain_collector_provider_run_v1(
            store,
            [claim_id],
            uow,
            **kwargs,
        )
        uow.commit()

    assert receipt.candidate_count == 0
    assert receipt.origin_count == 0
    assert receipt.automatic_scientific_acceptance is False
    assert _count(config, "semantic_provider_runs") == 1
    assert _count(config, "semantic_provider_run_events") == 3
    assert _count(config, "semantic_candidates") == 0
    assert _count(config, "semantic_provider_candidate_origins") == 0
