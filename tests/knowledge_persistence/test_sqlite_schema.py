from dataclasses import fields
from pathlib import Path

from ecobiome.knowledge_persistence import PersistenceConfig
from ecobiome.knowledge_persistence.contracts import (
    AcquisitionJobsRow,
    ClaimReviewEventsRow,
    ScientificAssertionRevisionsRow,
    ScientificEntityIdentifiersRow,
    ScientificEntityNameUsagesRow,
    ScientificEntityRelationsRow,
)
from ecobiome.knowledge_persistence.sqlite_schema import (
    EXPECTED_INDEXES,
    EXPECTED_TABLES,
    RUNTIME_SCHEMA_DESIGN_SHA256,
    SCHEMA_VERSION,
)
from ecobiome.knowledge_persistence.sqlite_store import initialize_database


def test_frozen_schema_contract_constants() -> None:
    assert SCHEMA_VERSION == 5
    assert len(EXPECTED_TABLES) == 33
    assert len(EXPECTED_INDEXES) == 43
    assert "segment_review_events" in EXPECTED_TABLES
    assert "segment_review_events_segment_time_idx" in EXPECTED_INDEXES
    assert RUNTIME_SCHEMA_DESIGN_SHA256 == 'd13f146dfd6f394ebb660e420c09305a6daca6c0d34232713c9b91b21879310e'


def test_v4_collector_compatibility_row_contracts() -> None:
    acquisition_source = next(
        field for field in fields(AcquisitionJobsRow) if field.name == "source_id"
    )
    assert str(acquisition_source.type) == "str | None"

    claim_review = tuple(field.name for field in fields(ClaimReviewEventsRow))
    assert claim_review == (
        "id",
        "claim_id",
        "decision",
        "reviewer",
        "notes",
        "corrected_text",
        "corrected_text_sha256",
        "review_metadata_json",
        "reviewed_at",
    )


def test_v11_semantic_row_contracts() -> None:
    assertion = tuple(field.name for field in fields(ScientificAssertionRevisionsRow))
    assert "assertion_kind" in assertion
    assert "participants_json" in assertion
    assert "value_json" in assertion
    assert "assertion_family" not in assertion
    assert "subject_json" not in assertion
    assert "object_json" not in assertion

    identifiers = tuple(field.name for field in fields(ScientificEntityIdentifiersRow))
    assert "authority_namespace" in identifiers
    assert "authority_version" in identifiers
    assert "mapping_review_status" in identifiers

    usages = tuple(field.name for field in fields(ScientificEntityNameUsagesRow))
    for name in (
        "script",
        "source_version",
        "retrieval_id",
        "segment_id",
        "segment_char_start",
        "segment_char_end",
    ):
        assert name in usages

    relations = tuple(field.name for field in fields(ScientificEntityRelationsRow))
    assert "semantics_version" in relations
    assert "qualifiers_json" in relations


def test_initializer_is_idempotent(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    storage = tmp_path / "storage"
    config = PersistenceConfig(
        storage / "scientific.sqlite3",
        storage / "artifacts",
    )
    assert initialize_database(config, repo_root=repo) == "INITIALIZED_NEW"
    assert initialize_database(config, repo_root=repo) == "ALREADY_INITIALIZED_EXACT"
def test_v5_semantic_provider_and_candidate_schema_names() -> None:
    assert {
        "semantic_provider_runs",
        "semantic_provider_run_claim_inputs",
        "semantic_provider_run_evidence_inputs",
        "semantic_provider_run_events",
        "semantic_candidates",
        "semantic_candidate_evidence_links",
        "semantic_candidate_review_events",
        "semantic_provider_candidate_origins",
    } <= set(EXPECTED_TABLES)
    assert {
        "semantic_provider_run_events_one_validated_idx",
        "semantic_provider_run_events_one_terminal_idx",
        "semantic_candidate_review_events_candidate_time_idx",
        "semantic_candidate_review_events_replacement_idx",
    } <= set(EXPECTED_INDEXES)
