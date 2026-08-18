from __future__ import annotations

import hashlib

from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1 import (
    PROJECTION_CONTRACT_DESCRIPTOR_V1_5,
    PROJECTION_CONTRACT_SHA256,
    PROJECTION_CONTRACT_VERSION,
    ReviewedEntityArgumentV1,
    candidate_argument_sha256_v1,
    project_scientific_assertion_v1,
)
from ecobiome.knowledge_acquisition.semantic_candidate_review_v1 import (
    build_semantic_candidate_review_event_v1,
)
from ecobiome.knowledge_acquisition.semantic_candidate_v2_11 import (
    build_semantic_candidate_v2_11,
)
from ecobiome.knowledge_persistence.contracts import (
    ClaimEvidenceLinksRow,
    ClaimReviewEventsRow,
    SegmentsRow,
    SourceClaimsRow,
    SourceEvidenceRow,
)
from ecobiome.knowledge_persistence.serialization import canonical_sha256


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _registry() -> dict[str, object]:
    return {
        "relations": {
            "poses_significant_threat_to": {
                "argument_keys": ["cause", "target"],
                "epistemic_class": "dispositional_risk",
                "semantic_type_contract_state": (
                    "historical_golden_reviewed_constrained"
                ),
                "semantic_types_allowed": [
                    "industry_impact",
                    "risk_factor",
                ],
            },
            "adversely_affects": {
                "argument_keys": ["cause", "target"],
                "epistemic_class": "explicit_causal_result",
                "semantic_type_contract_state": (
                    "historical_golden_reviewed_constrained"
                ),
                "semantic_types_allowed": [
                    "health_effect",
                    "knowledge_gap",
                ],
            },
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


def _source_request(text: str) -> dict[str, object]:
    return {
        "source_claims": [
            {
                "claim_id": "claim-impact",
                "effective_text": text,
                "evidence": [
                    {
                        "evidence_id": "ev-impact",
                        "text": text,
                    }
                ],
            }
        ]
    }


def _candidate(
    *,
    relation: str = "poses_significant_threat_to",
    semantic_type: str = "industry_impact",
) -> dict[str, object]:
    text = "Disease outbreaks pose a significant threat to aquaculture production."
    survivor = {
        "c": "claim-impact",
        "e": ["ev-impact"],
        "t": semantic_type,
        "m": {
            "r": relation,
            "a": {
                "cause": "disease outbreaks",
                "target": "aquaculture production",
            },
        },
    }
    return build_semantic_candidate_v2_11(
        survivor,
        _source_request(text),
        _registry(),
    )


def _claim() -> SourceClaimsRow:
    text = "Disease outbreaks pose a significant threat to aquaculture production."
    return SourceClaimsRow(
        id="claim-impact",
        source_id="source-1",
        representation_id="rep-1",
        parent_claim_id="parent-1",
        claim_layer="atomic",
        claim_text=text,
        claim_text_sha256=_sha(text),
        claim_kind="statement",
        semantic_type="industry_impact",
        qualifiers_json="{}",
        extraction_confidence_decimal=None,
        source_claim_effective_text_sha256=_sha(text),
        notes="",
        initial_review_status="unreviewed",
        created_at="2026-08-17T18:00:00+00:00",
    )


def _claim_review() -> ClaimReviewEventsRow:
    return ClaimReviewEventsRow(
        id="review-impact",
        claim_id="claim-impact",
        decision="accept",
        reviewer="human-reviewer",
        notes="",
        corrected_text=None,
        corrected_text_sha256=None,
        review_metadata_json="{}",
        reviewed_at="2026-08-17T18:01:00+00:00",
    )


def _candidate_review(candidate: dict[str, object]):
    return build_semantic_candidate_review_event_v1(
        candidate,
        event_id="candidate-review-impact",
        semantic_candidate_id="candidate-impact",
        decision="accept",
        reviewer="candidate-reviewer",
        reviewed_at="2026-08-17T18:02:00+00:00",
    )


def _evidence_link() -> ClaimEvidenceLinksRow:
    return ClaimEvidenceLinksRow(
        claim_id="claim-impact",
        evidence_id="ev-impact",
        evidence_order=0,
        link_role="supports_source_claim",
        created_at="2026-08-17T18:00:00+00:00",
    )


def _evidence() -> SourceEvidenceRow:
    text = "Disease outbreaks pose a significant threat to aquaculture production."
    return SourceEvidenceRow(
        id="ev-impact",
        segment_id="seg-impact",
        segment_char_start=0,
        segment_char_end=len(text),
        evidence_text_sha256=_sha(text),
        start_seconds_decimal=None,
        end_seconds_decimal=None,
        page_number=None,
        frame_start=None,
        frame_end=None,
        evidence_metadata_json="{}",
        created_at="2026-08-17T18:00:00+00:00",
    )


def _segment() -> SegmentsRow:
    text = "Disease outbreaks pose a significant threat to aquaculture production."
    return SegmentsRow(
        id="seg-impact",
        representation_id="rep-1",
        segment_index=0,
        text_inline=text,
        text_sha256=_sha(text),
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
        created_at="2026-08-17T18:00:00+00:00",
    )


def _argument(candidate: dict[str, object], role: str) -> dict[str, object]:
    arguments = candidate["semantic"]["arguments"]
    return next(item for item in arguments if item["role"] == role)


def _entity_resolutions(
    candidate: dict[str, object],
) -> dict[str, ReviewedEntityArgumentV1]:
    return {
        "cause": ReviewedEntityArgumentV1(
            role="cause",
            candidate_argument_sha256=candidate_argument_sha256_v1(
                _argument(candidate, "cause")
            ),
            entity_id="entity-disease-outbreaks",
            entity_revision=1,
            mapping_status="exact",
            mapping_review_status="reviewed_confirmed",
            reviewed_by="human-reviewer",
        ),
        "target": ReviewedEntityArgumentV1(
            role="target",
            candidate_argument_sha256=candidate_argument_sha256_v1(
                _argument(candidate, "target")
            ),
            entity_id="entity-aquaculture-production",
            entity_revision=1,
            mapping_status="exact",
            mapping_review_status="reviewed_confirmed",
            reviewed_by="human-reviewer",
        ),
    }


def _project(candidate: dict[str, object]) -> dict[str, object]:
    return project_scientific_assertion_v1(
        candidate,
        source_claim=_claim(),
        claim_reviews=[_claim_review()],
        candidate_reviews=[_candidate_review(candidate)],
        claim_evidence_links=[_evidence_link()],
        evidence_rows=[_evidence()],
        segments={"seg-impact": _segment()},
        segment_reviews={},
        entity_resolutions=_entity_resolutions(candidate),
    )


def test_g6_industry_impact_reuses_reviewed_binary_projection() -> None:
    candidate = _candidate()
    result = _project(candidate)

    assert result["contract"]["version"] == "1.5"
    assert result["contract"]["projection_spec_id"] == (
        "poses_significant_threat_to.industry_impact.relational.v1"
    )
    assert result["assertion"]["payload"] == {
        "schema_version": "scientific-assertion-v1.1",
        "assertion_kind": "relational",
        "predicate": "poses_significant_threat_to",
        "participants": [
            {
                "role": "cause",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-disease-outbreaks",
                    "entity_revision": 1,
                },
            },
            {
                "role": "target",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-aquaculture-production",
                    "entity_revision": 1,
                },
            },
        ],
        "value": {"kind": "none"},
        "qualifiers": {"semantic_type": "industry_impact"},
    }
    assert result["projection_gate_passed"] is True
    assert result["automatic_persistence"] is False
    assert result["claim_link_proposal"]["requires_persistence_review"] is True


def test_g6_projection_contract_v1_5_identity_and_exact_scope() -> None:
    assert PROJECTION_CONTRACT_VERSION == "1.5"
    assert PROJECTION_CONTRACT_SHA256 == (
        "b6db1e8c939a78bde7e9929cd5387b2f7bb63f9a5760aa6f1f42372e50079987"
    )
    assert (
        canonical_sha256(PROJECTION_CONTRACT_DESCRIPTOR_V1_5)
        == PROJECTION_CONTRACT_SHA256
    )

    specs = PROJECTION_CONTRACT_DESCRIPTOR_V1_5["specs"]
    pairs = {
        (spec["relation"], spec["semantic_type"])
        for spec in specs
    }
    assert pairs == {
        ("maintained_at", "experimental_condition"),
        ("adversely_affects", "health_effect"),
        ("adversely_affects", "knowledge_gap"),
        ("poses_significant_threat_to", "risk_factor"),
        ("poses_significant_threat_to", "industry_impact"),
        ("caused_decrease", "biological_effect"),
        ("affected_gene_expression_in", "combined_effect"),
    }


def test_g6_knowledge_gap_reuses_reviewed_binary_projection_spec() -> None:
    specs = PROJECTION_CONTRACT_DESCRIPTOR_V1_5["specs"]
    matching = [
        spec
        for spec in specs
        if spec["relation"] == "adversely_affects"
        and spec["semantic_type"] == "knowledge_gap"
    ]

    assert matching == [
        {
            "assertion_kind": "relational",
            "builder": "binary_entity_relation_v1",
            "predicate": "adversely_affects",
            "relation": "adversely_affects",
            "role_classes": (
                ("cause", "ENTITY_ARGUMENT"),
                ("target", "ENTITY_ARGUMENT"),
            ),
            "semantic_type": "knowledge_gap",
            "spec_id": "adversely_affects.knowledge_gap.relational.v1",
        }
    ]
