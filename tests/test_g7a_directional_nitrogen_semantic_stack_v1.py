from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition.provider_schema_v2_12 import (
    build_provider_ontology_v2_12,
)
from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1 import (
    PROJECTION_CONTRACT_SHA256 as PROJECTION_V17_SHA,
)
from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1_8 import (
    PROJECTION_CONTRACT_SHA256 as PROJECTION_V18_SHA,
)
from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1_8 import (
    ReviewedEntityArgumentV1,
    ScientificAssertionProjectionV1Error,
    candidate_argument_sha256_v1,
    project_scientific_assertion_v1_8,
)
from ecobiome.knowledge_acquisition.semantic_candidate_review_v1_1 import (
    build_semantic_candidate_review_event_v1_1,
)
from ecobiome.knowledge_acquisition.semantic_candidate_v2_11 import (
    SemanticCandidateV211Error,
    build_semantic_candidate_v2_11,
)
from ecobiome.knowledge_acquisition.semantic_candidate_v2_12 import (
    PROMOTION_REQUIRES_SEMANTIC_RESOLUTION,
    build_semantic_candidate_v2_12,
)
from ecobiome.knowledge_acquisition.semantic_contract_v2_8 import (
    apply_relation_type_contract_v2_8,
    load_relation_type_contract_v2_8,
)
from ecobiome.knowledge_acquisition.semantic_contract_v2_10 import (
    apply_relation_type_delta_v2_10,
    load_relation_type_delta_v2_10,
)
from ecobiome.knowledge_acquisition.semantic_contract_v2_12 import (
    DIRECTIONAL_NITROGEN_DESIGN_SHA256,
    DIRECTIONAL_NITROGEN_EXTENSION_V2_12_SHA256,
    apply_directional_nitrogen_contract_v2_12,
)
from ecobiome.knowledge_acquisition.semantic_grounding import (
    GROUNDING_POLICY_V1_1_SHA256,
    OPAQUE_OPEN_TEXT_ROLES_V1_2,
    OPAQUE_OPEN_TEXT_ROLES_V1_3,
    OPAQUE_OPEN_TEXT_ROLES_V1_3_ADDITIONS,
    audit_arguments,
    audit_arguments_v1_3,
)
from ecobiome.knowledge_acquisition.semantic_robustness_v2_7 import (
    validate_registry_v2_7,
)
from ecobiome.knowledge_persistence.contracts import (
    ClaimEvidenceLinksRow,
    ClaimReviewEventsRow,
    SegmentsRow,
    SourceClaimsRow,
    SourceEvidenceRow,
)

ROOT = Path(__file__).resolve().parent
V27 = ROOT / "fixtures/collector_semantic_v2_7/SEMANTIC_RELATION_REGISTRY_V2_7.json"
V28 = ROOT / "fixtures/collector_semantic_v2_8/SEMANTIC_RELATION_TYPE_CONTRACT_V2_8.json"
V210 = ROOT / "fixtures/collector_semantic_v2_10/SEMANTIC_RELATION_TYPE_DELTA_V2_10.json"

LIU_ID = "claim-liu-2021-ammonium-to-nitrate-v1"
LIU_TEXT = (
    "In the incubation experiment, Nitrospira inopinata oxidized supplied "
    "ammonium to nitrate, the predominant measured oxidized product."
)
LEMNA_ID = "claim-monselise-1987-ammonium-n-to-glutamine-v1"
LEMNA_TEXT = (
    "In Lemna gibba exposed to labelled ammonium, ammonium-derived nitrogen "
    "was incorporated into glutamine."
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _registry_v210() -> dict[str, object]:
    v27 = validate_registry_v2_7(json.loads(V27.read_text(encoding="utf-8")))
    v28 = apply_relation_type_contract_v2_8(v27, load_relation_type_contract_v2_8(V28))
    return apply_relation_type_delta_v2_10(v28, load_relation_type_delta_v2_10(V210))


def _registry() -> dict[str, object]:
    return apply_directional_nitrogen_contract_v2_12(_registry_v210())


def _candidate(claim_id: str, text: str, relation: str) -> dict[str, object]:
    if relation == "nitrogen_oxidized_from_to":
        semantic_type = "nitrogen_oxidation"
        arguments = {
            "source_material": "ammonium",
            "target_material": "nitrate",
            "process_agent": "Nitrospira inopinata",
        }
    else:
        semantic_type = "nitrogen_assimilation"
        arguments = {
            "source_material": "ammonium",
            "target_nitrogen_pool": "glutamine",
            "process_agent": "Lemna gibba",
        }
    source = {
        "source_claims": [
            {
                "claim_id": claim_id,
                "effective_text": text,
                "evidence": [{"evidence_id": "ev", "text": text}],
            }
        ]
    }
    survivor = {
        "c": claim_id,
        "e": ["ev"],
        "t": semantic_type,
        "m": {"r": relation, "a": arguments},
    }
    return build_semantic_candidate_v2_12(survivor, source, _registry())


def _projection_rows(claim_id: str, text: str):
    digest = _sha(text)
    claim = SourceClaimsRow(
        id=claim_id,
        source_id="source",
        representation_id=None,
        parent_claim_id="parent",
        claim_layer="atomic",
        claim_text=text,
        claim_text_sha256=digest,
        claim_kind="statement",
        semantic_type=None,
        qualifiers_json="{}",
        extraction_confidence_decimal=None,
        source_claim_effective_text_sha256=digest,
        notes="",
        initial_review_status="unreviewed",
        created_at="2026-08-23T15:00:00+00:00",
    )
    review = ClaimReviewEventsRow(
        id="claim-review",
        claim_id=claim_id,
        decision="accept",
        reviewer="human",
        notes="",
        corrected_text=None,
        corrected_text_sha256=None,
        review_metadata_json="{}",
        reviewed_at="2026-08-23T15:10:00+00:00",
    )
    link = ClaimEvidenceLinksRow(
        claim_id=claim_id,
        evidence_id="ev",
        evidence_order=0,
        link_role="supports_source_claim",
        created_at="2026-08-23T15:00:00+00:00",
    )
    evidence = SourceEvidenceRow(
        id="ev",
        segment_id="seg",
        segment_char_start=0,
        segment_char_end=len(text),
        evidence_text_sha256=digest,
        start_seconds_decimal=None,
        end_seconds_decimal=None,
        page_number=None,
        frame_start=None,
        frame_end=None,
        evidence_metadata_json="{}",
        created_at="2026-08-23T15:00:00+00:00",
    )
    segment = SegmentsRow(
        id="seg",
        representation_id="rep",
        segment_index=0,
        text_inline=text,
        text_sha256=digest,
        materialization_status="inline",
        representation_char_start=0,
        representation_char_end=len(text),
        start_seconds_decimal=None,
        end_seconds_decimal=None,
        page_number=None,
        frame_start=None,
        frame_end=None,
        review_status="unreviewed",
        metadata_json="{}",
        created_at="2026-08-23T15:00:00+00:00",
    )
    return claim, review, [link], [evidence], {"seg": segment}


def _project(candidate, claim_id: str, text: str, entities: dict[str, str]):
    claim, claim_review, links, evidence, segments = _projection_rows(claim_id, text)
    candidate_review = build_semantic_candidate_review_event_v1_1(
        candidate,
        event_id="candidate-review",
        semantic_candidate_id="candidate",
        decision="accept",
        reviewer="human",
        reviewed_at="2026-08-23T15:20:00+00:00",
    )
    by_role = {
        item["role"]: item
        for item in candidate["semantic"]["arguments"]
    }
    resolutions = {
        role: ReviewedEntityArgumentV1(
            role=role,
            candidate_argument_sha256=candidate_argument_sha256_v1(by_role[role]),
            entity_id=entity_id,
            entity_revision=1,
            mapping_status="exact",
            mapping_review_status="reviewed_confirmed",
            reviewed_by="human",
        )
        for role, entity_id in entities.items()
    }
    return project_scientific_assertion_v1_8(
        candidate,
        source_claim=claim,
        claim_reviews=[claim_review],
        candidate_reviews=[candidate_review],
        claim_evidence_links=links,
        evidence_rows=evidence,
        segments=segments,
        segment_reviews={},
        entity_resolutions=resolutions,
    )


def test_contract_is_additive_and_provider_exposes_47_resolved() -> None:
    base = _registry_v210()
    before = copy.deepcopy(base)
    merged = apply_directional_nitrogen_contract_v2_12(base)
    assert base == before
    assert len(merged["relations"]) == 65
    ontology = build_provider_ontology_v2_12(merged)
    assert len(ontology["relations"]) == 47
    assert len(ontology["blocked_relation_ids"]) == 18
    assert "nitrogen_oxidized_from_to" in ontology["relations"]
    assert "nitrogen_assimilated_from_into" in ontology["relations"]
    assert DIRECTIONAL_NITROGEN_DESIGN_SHA256 == "205913037baf3e9d0fea3f2d779636cfb687618bbd0580e2d6c7c979672d2477"
    assert DIRECTIONAL_NITROGEN_EXTENSION_V2_12_SHA256 == "b5abf8b34a883f4adbca1b606e6a7bac0e9b69a6ee2f004ecd810cd43876d468"


def test_grounding_v13_is_additive_and_v11_sha_is_frozen() -> None:
    expected = {
        "source_material", "target_material",
        "target_nitrogen_pool", "process_agent",
    }
    assert OPAQUE_OPEN_TEXT_ROLES_V1_3_ADDITIONS == expected
    assert OPAQUE_OPEN_TEXT_ROLES_V1_2.isdisjoint(expected)
    assert OPAQUE_OPEN_TEXT_ROLES_V1_3 == OPAQUE_OPEN_TEXT_ROLES_V1_2 | expected
    assert GROUNDING_POLICY_V1_1_SHA256 == (
        "e7c566d78ec3eefbd30b9b424f92e35e25430933921f9a57f1c84efff232b6bf"
    )
    assert audit_arguments({"source_material": "ammonium"}, LIU_TEXT)[
        "records"
    ]["source_material"]["state"] == "unknown_role"
    assert audit_arguments_v1_3({"source_material": "ammonium"}, LIU_TEXT)[
        "records"
    ]["source_material"]["state"] == "grounded_opaque_unresolved"


def test_v212_builds_both_candidates_and_v211_stays_closed() -> None:
    ox = _candidate(LIU_ID, LIU_TEXT, "nitrogen_oxidized_from_to")
    ass = _candidate(
        LEMNA_ID, LEMNA_TEXT, "nitrogen_assimilated_from_into"
    )
    assert ox["promotion_readiness"] == PROMOTION_REQUIRES_SEMANTIC_RESOLUTION
    assert ass["promotion_readiness"] == PROMOTION_REQUIRES_SEMANTIC_RESOLUTION
    assert ox["automatic_scientific_acceptance"] is False
    assert ass["automatic_scientific_acceptance"] is False

    source = {
        "source_claims": [
            {
                "claim_id": LIU_ID,
                "effective_text": LIU_TEXT,
                "evidence": [{"evidence_id": "ev", "text": LIU_TEXT}],
            }
        ]
    }
    survivor = {
        "c": LIU_ID, "e": ["ev"], "t": "nitrogen_oxidation",
        "m": {
            "r": "nitrogen_oxidized_from_to",
            "a": {
                "source_material": "ammonium",
                "target_material": "nitrate",
                "process_agent": "Nitrospira inopinata",
            },
        },
    }
    with pytest.raises(SemanticCandidateV211Error):
        build_semantic_candidate_v2_11(survivor, source, _registry())


def test_projection_v18_fails_closed_without_entity_mappings() -> None:
    candidate = _candidate(LIU_ID, LIU_TEXT, "nitrogen_oxidized_from_to")
    claim, claim_review, links, evidence, segments = _projection_rows(LIU_ID, LIU_TEXT)
    candidate_review = build_semantic_candidate_review_event_v1_1(
        candidate,
        event_id="candidate-review",
        semantic_candidate_id="candidate",
        decision="accept",
        reviewer="human",
        reviewed_at="2026-08-23T15:20:00+00:00",
    )
    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="human-reviewed entity mapping",
    ):
        project_scientific_assertion_v1_8(
            candidate,
            source_claim=claim,
            claim_reviews=[claim_review],
            candidate_reviews=[candidate_review],
            claim_evidence_links=links,
            evidence_rows=evidence,
            segments=segments,
            segment_reviews={},
            entity_resolutions={},
        )


def test_projection_v18_builds_two_process_assertions() -> None:
    ox = _project(
        _candidate(LIU_ID, LIU_TEXT, "nitrogen_oxidized_from_to"),
        LIU_ID,
        LIU_TEXT,
        {
            "source_material": "entity-pubchem-cid-223",
            "target_material": "entity-pubchem-cid-943",
            "process_agent": "entity-ncbitaxon-1715989",
        },
    )
    ass = _project(
        _candidate(LEMNA_ID, LEMNA_TEXT, "nitrogen_assimilated_from_into"),
        LEMNA_ID,
        LEMNA_TEXT,
        {
            "source_material": "entity-pubchem-cid-223",
            "target_nitrogen_pool": "entity-pubchem-cid-5961",
            "process_agent": "entity-ipni-526178-1",
        },
    )
    assert ox["assertion"]["payload"]["assertion_kind"] == "process"
    assert ox["assertion"]["payload"]["predicate"] == "nitrogen_oxidized_from_to"
    assert ass["assertion"]["payload"]["assertion_kind"] == "process"
    assert ass["assertion"]["payload"]["predicate"] == "nitrogen_assimilated_from_into"
    assert len(ox["assertion"]["payload"]["participants"]) == 3
    assert len(ass["assertion"]["payload"]["participants"]) == 3
    assert ox["automatic_persistence"] is False
    assert ass["automatic_persistence"] is False


def test_projection_v17_identity_is_unchanged() -> None:
    assert PROJECTION_V17_SHA == (
        "11c72c4411c98191413c5288d0a1ad76655c92c8bd731c317591a5c5bdd87c75"
    )
    assert PROJECTION_V18_SHA == "006458c7163d275217ae584064b3e72adc3cdc3a36c5fe8a97b40088bcccd6e5"
    assert PROJECTION_V18_SHA != PROJECTION_V17_SHA
