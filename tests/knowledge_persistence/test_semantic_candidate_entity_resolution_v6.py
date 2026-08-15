from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition.semantic_candidate_entity_resolution_v1 import (
    ENTITY_RESOLUTION_POLICY_NAME,
    ENTITY_RESOLUTION_POLICY_SHA256,
    ENTITY_RESOLUTION_POLICY_VERSION,
    SemanticCandidateEntityResolutionV1Error,
    require_reviewed_entity_resolutions_v1,
)
from ecobiome.knowledge_acquisition.semantic_candidate_v2_11 import (
    build_semantic_candidate_v2_11,
)
from ecobiome.knowledge_persistence import (
    FilesystemContentAddressedArtifactStore,
    PersistenceConfig,
    SQLiteScientificFoundationUnitOfWork,
    initialize_database,
)
from ecobiome.knowledge_persistence.contracts import (
    ClaimEvidenceLinksRow,
    ClaimReviewEventsRow,
    KnowledgeSourcesRow,
    RepresentationsRow,
    ScientificEntitiesRow,
    ScientificEntityNameUsagesRow,
    ScientificEntityRevisionsRow,
    SegmentsRow,
    SemanticCandidateEntityResolutionEventsRow,
    SemanticCandidateEvidenceLinksRow,
    SemanticCandidatesRow,
    SourceClaimsRow,
    SourceEvidenceRow,
)
from ecobiome.knowledge_persistence.errors import PersistenceIntegrityError
from ecobiome.knowledge_persistence.serialization import (
    canonical_json_text,
    canonical_sha256,
)

CREATED_AT = "2026-08-15T12:00:00+00:00"
TEXT = "Ammonia adversely affects medaka."


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _registry() -> dict[str, object]:
    return {
        "relations": {
            "adversely_affects": {
                "argument_keys": ["cause", "target"],
                "epistemic_class": "explicit_causal_result",
                "semantic_type_contract_state": "historical_golden_reviewed_constrained",
                "semantic_types_allowed": ["health_effect"],
            }
        },
        "argument_role_semantics": {
            "cause": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "causal_driver_or_factor",
            },
            "target": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "target_entity_or_process",
            },
        },
    }


def _candidate() -> dict[str, object]:
    return build_semantic_candidate_v2_11(
        {
            "c": "claim-1",
            "e": ["ev-1"],
            "t": "health_effect",
            "m": {
                "r": "adversely_affects",
                "a": {"cause": "Ammonia", "target": "medaka"},
            },
        },
        {
            "source_claims": [
                {
                    "claim_id": "claim-1",
                    "effective_text": TEXT,
                    "evidence": [{"evidence_id": "ev-1", "text": TEXT}],
                }
            ]
        },
        _registry(),
    )


def _config(tmp_path: Path) -> tuple[PersistenceConfig, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    config = PersistenceConfig(
        tmp_path / "storage" / "scientific.sqlite3",
        tmp_path / "storage" / "cas",
    )
    initialize_database(config, repo_root=repo)
    return config, repo


def _argument(candidate: dict[str, object], role: str) -> dict[str, object]:
    arguments = candidate["semantic"]["arguments"]
    return next(item for item in arguments if item["role"] == role)


def _seed(config: PersistenceConfig, repo: Path) -> dict[str, object]:
    candidate = _candidate()
    candidate_json = canonical_json_text(candidate)
    contract = candidate["contract"]
    source = candidate["source"]
    semantic = candidate["semantic"]

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=FilesystemContentAddressedArtifactStore(config.artifact_store_root),
    ) as uow:
        uow.provenance.add_knowledge_source(
            KnowledgeSourcesRow(
                id="source-1",
                source_type="fixture",
                canonical_locator="urn:fixture:n3",
                title="N3 fixture",
                author=None,
                language="en",
                description="",
                imported_at=CREATED_AT,
                source_metadata_json="{}",
                logical_identity_sha256="1" * 64,
                created_at=CREATED_AT,
            )
        )
        uow.provenance.add_representation(
            RepresentationsRow(
                id="rep-1",
                source_id="source-1",
                origin_raw_artifact_id=None,
                logical_key="main",
                representation_kind="text",
                media_type="text/plain",
                language="en",
                content_sha256=_sha(TEXT),
                artifact_store_key=None,
                materialization_status="inline",
                metadata_json="{}",
                created_at=CREATED_AT,
            )
        )
        uow.provenance.add_segments([
            SegmentsRow(
                id="seg-1",
                representation_id="rep-1",
                segment_index=0,
                text_inline=TEXT,
                text_sha256=_sha(TEXT),
                materialization_status="inline",
                representation_char_start=None,
                representation_char_end=None,
                start_seconds_decimal=None,
                end_seconds_decimal=None,
                page_number=None,
                frame_start=None,
                frame_end=None,
                review_status="accepted",
                metadata_json="{}",
                created_at=CREATED_AT,
            )
        ])
        uow.provenance.add_source_evidence([
            SourceEvidenceRow(
                id="ev-1",
                segment_id="seg-1",
                segment_char_start=0,
                segment_char_end=len(TEXT),
                evidence_text_sha256=_sha(TEXT),
                start_seconds_decimal=None,
                end_seconds_decimal=None,
                page_number=None,
                frame_start=None,
                frame_end=None,
                evidence_metadata_json="{}",
                created_at=CREATED_AT,
            )
        ])
        uow.provenance.add_source_claims([
            SourceClaimsRow(
                id="claim-1",
                source_id="source-1",
                representation_id="rep-1",
                parent_claim_id=None,
                claim_layer="atomic",
                claim_text=TEXT,
                claim_text_sha256=_sha(TEXT),
                claim_kind="statement",
                semantic_type="health_effect",
                qualifiers_json="{}",
                extraction_confidence_decimal=None,
                source_claim_effective_text_sha256=_sha(TEXT),
                notes="",
                initial_review_status="unreviewed",
                created_at=CREATED_AT,
            )
        ])
        uow.provenance.add_claim_evidence_links([
            ClaimEvidenceLinksRow(
                claim_id="claim-1",
                evidence_id="ev-1",
                evidence_order=0,
                link_role="supports_source_claim",
                created_at=CREATED_AT,
            )
        ])
        uow.provenance.add_claim_review_events([
            ClaimReviewEventsRow(
                id="claim-review-1",
                claim_id="claim-1",
                decision="accept",
                reviewer="human",
                notes="",
                corrected_text=None,
                corrected_text_sha256=None,
                review_metadata_json="{}",
                reviewed_at=CREATED_AT,
            )
        ])

        for entity_id, label in (("entity-ammonia", "Ammonia"), ("entity-medaka", "medaka")):
            uow.entities.add_entity(
                ScientificEntitiesRow(
                    id=entity_id,
                    entity_kind="scientific_concept",
                    created_at=CREATED_AT,
                    retired_at=None,
                )
            )
            uow.entities.add_entity_revision(
                ScientificEntityRevisionsRow(
                    entity_id=entity_id,
                    revision=1,
                    schema_version="entity-v1",
                    canonical_label=label,
                    canonical_payload_json="{}",
                    canonical_payload_sha256=_sha(f"{entity_id}:1"),
                    review_status="reviewed_confirmed",
                    created_at=CREATED_AT,
                )
            )

        for usage_id, entity_id, name, start, end in (
            ("usage-ammonia", "entity-ammonia", "Ammonia", 0, 7),
            ("usage-medaka", "entity-medaka", "medaka", 26, 32),
        ):
            uow.entities.add_name_usage(
                ScientificEntityNameUsagesRow(
                    id=usage_id,
                    entity_id=entity_id,
                    source_id="source-1",
                    verbatim_name=name,
                    language="en",
                    script="Latn",
                    usage_status="source_usage",
                    nomenclatural_status=None,
                    mapping_review_status="reviewed_confirmed",
                    source_version=None,
                    retrieval_id=None,
                    segment_id="seg-1",
                    segment_char_start=start,
                    segment_char_end=end,
                    created_at=CREATED_AT,
                )
            )

        uow.semantic_candidates.add_candidate(
            SemanticCandidatesRow(
                id="candidate-1",
                schema_version=str(candidate["schema_version"]),
                semantic_contract_name=str(contract["name"]),
                semantic_contract_version=str(contract["version"]),
                semantic_contract_sha256=str(contract["canonical_sha256"]),
                relation_type_basis_version=str(contract["relation_type_basis_version"]),
                relation_type_registry_sha256=str(contract["relation_type_registry_sha256"]),
                grounding_policy_sha256=str(contract["grounding_policy_sha256"]),
                claim_scoped_provenance_policy_sha256=str(contract["claim_scoped_provenance_policy_sha256"]),
                source_statement_claim_id=str(source["source_statement_claim_id"]),
                source_claim_effective_text_sha256=str(source["source_claim_effective_text_sha256"]),
                semantic_type=str(semantic["semantic_type"]),
                relation=str(semantic["relation"]),
                epistemic_class=str(semantic["epistemic_class"]),
                promotion_readiness=str(candidate["promotion_readiness"]),
                automatic_scientific_acceptance=0,
                canonical_candidate_sha256=str(candidate["canonical_candidate_sha256"]),
                canonical_candidate_document_sha256=_sha(candidate_json),
                canonical_candidate_json=candidate_json,
                created_at=CREATED_AT,
            ),
            [
                SemanticCandidateEvidenceLinksRow(
                    semantic_candidate_id="candidate-1",
                    source_statement_claim_id="claim-1",
                    evidence_id="ev-1",
                    evidence_order=0,
                    created_at=CREATED_AT,
                )
            ],
        )
        uow.commit()
    return candidate


def _event(
    candidate: dict[str, object],
    role: str,
    *,
    event_id: str,
    decision: str = "accept",
    usage_id: str | None = None,
) -> SemanticCandidateEntityResolutionEventsRow:
    entity_id = "entity-ammonia" if role == "cause" else "entity-medaka"
    return SemanticCandidateEntityResolutionEventsRow(
        id=event_id,
        semantic_candidate_id="candidate-1",
        semantic_candidate_sha256=str(candidate["canonical_candidate_sha256"]),
        role=role,
        candidate_argument_sha256=canonical_sha256(_argument(candidate, role)),
        entity_name_usage_id=usage_id or ("usage-ammonia" if role == "cause" else "usage-medaka"),
        entity_id=entity_id,
        entity_revision=1,
        mapping_status="exact",
        decision=decision,
        reviewer="human-entity-reviewer",
        rationale="fixture",
        review_policy_name=ENTITY_RESOLUTION_POLICY_NAME,
        review_policy_version=ENTITY_RESOLUTION_POLICY_VERSION,
        review_policy_sha256=ENTITY_RESOLUTION_POLICY_SHA256,
        reviewed_at=CREATED_AT,
    )


def test_persisted_resolution_reconstructs_exact_entity_arguments(tmp_path: Path) -> None:
    config, repo = _config(tmp_path)
    candidate = _seed(config, repo)
    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=FilesystemContentAddressedArtifactStore(config.artifact_store_root),
    ) as uow:
        assert uow.entities.add_candidate_entity_resolution_event(
            _event(candidate, "cause", event_id="resolution-1")
        )
        assert uow.entities.add_candidate_entity_resolution_event(
            _event(candidate, "target", event_id="resolution-2")
        )
        events = uow.entities.list_candidate_entity_resolution_events("candidate-1")
        uow.commit()

    resolved = require_reviewed_entity_resolutions_v1(
        candidate,
        semantic_candidate_id="candidate-1",
        events=events,
        required_roles=("cause", "target"),
    )
    assert resolved["cause"].entity_id == "entity-ammonia"
    assert resolved["target"].entity_id == "entity-medaka"
    assert resolved["cause"].entity_revision == 1


def test_persistence_rejects_name_usage_bound_to_wrong_entity(tmp_path: Path) -> None:
    config, repo = _config(tmp_path)
    candidate = _seed(config, repo)
    wrong = _event(
        candidate,
        "cause",
        event_id="resolution-wrong",
        usage_id="usage-medaka",
    )
    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=FilesystemContentAddressedArtifactStore(config.artifact_store_root),
    ) as uow, pytest.raises(
        PersistenceIntegrityError,
        match="name usage entity does not match event",
    ):
        uow.entities.add_candidate_entity_resolution_event(wrong)


def test_latest_rejected_resolution_blocks_reconstruction(tmp_path: Path) -> None:
    config, repo = _config(tmp_path)
    candidate = _seed(config, repo)
    accepted = _event(candidate, "cause", event_id="resolution-a")
    rejected = replace(
        accepted,
        id="resolution-z",
        decision="reject",
        reviewed_at="2026-08-15T12:00:01+00:00",
    )
    with pytest.raises(
        SemanticCandidateEntityResolutionV1Error,
        match="latest entity-resolution review is rejected",
    ):
        require_reviewed_entity_resolutions_v1(
            candidate,
            semantic_candidate_id="candidate-1",
            events=[accepted, rejected],
            required_roles=("cause",),
        )
