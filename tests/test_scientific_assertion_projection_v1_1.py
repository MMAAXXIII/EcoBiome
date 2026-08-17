from __future__ import annotations

import hashlib

import pytest

from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1 import (
    ScientificAssertionProjectionV1Error,
    candidate_argument_sha256_v1,
    project_scientific_assertion_v1,
)
from ecobiome.knowledge_acquisition.semantic_candidate_entity_resolution_v1 import (
    ENTITY_RESOLUTION_POLICY_NAME,
    ENTITY_RESOLUTION_POLICY_SHA256,
    ENTITY_RESOLUTION_POLICY_VERSION,
    require_reviewed_entity_resolutions_v1,
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
    SemanticCandidateEntityResolutionEventsRow,
    SourceClaimsRow,
    SourceEvidenceRow,
)

CREATED_AT = "2026-08-15T12:00:00+00:00"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _registry() -> dict[str, object]:
    return {
        "relations": {
            "adversely_affects": {
                "argument_keys": ["cause", "target"],
                "epistemic_class": "explicit_causal_result",
                "semantic_type_contract_state": "historical_golden_reviewed_constrained",
                "semantic_types_allowed": ["health_effect", "knowledge_gap"],
            },
            "poses_significant_threat_to": {
                "argument_keys": ["cause", "target"],
                "epistemic_class": "dispositional_risk",
                "semantic_type_contract_state": "historical_golden_reviewed_constrained",
                "semantic_types_allowed": ["risk_factor", "industry_impact"],
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


def _candidate(relation: str, semantic_type: str) -> tuple[dict[str, object], str]:
    text = (
        "Ammonia adversely affects medaka."
        if relation == "adversely_affects"
        else "Ammonia poses significant threat to medaka."
    )
    candidate = build_semantic_candidate_v2_11(
        {
            "c": "claim-1",
            "e": ["ev-1"],
            "t": semantic_type,
            "m": {
                "r": relation,
                "a": {"cause": "Ammonia", "target": "medaka"},
            },
        },
        {
            "source_claims": [
                {
                    "claim_id": "claim-1",
                    "effective_text": text,
                    "evidence": [{"evidence_id": "ev-1", "text": text}],
                }
            ]
        },
        _registry(),
    )
    return candidate, text


def _resolution_events(candidate: dict[str, object]) -> list[SemanticCandidateEntityResolutionEventsRow]:
    arguments = {item["role"]: item for item in candidate["semantic"]["arguments"]}
    rows = []
    for role, entity_id, usage in (
        ("cause", "entity-ammonia", "usage-ammonia"),
        ("target", "entity-medaka", "usage-medaka"),
    ):
        rows.append(
            SemanticCandidateEntityResolutionEventsRow(
                id=f"resolution-{role}",
                semantic_candidate_id="candidate-1",
                semantic_candidate_sha256=str(candidate["canonical_candidate_sha256"]),
                role=role,
                candidate_argument_sha256=candidate_argument_sha256_v1(arguments[role]),
                entity_name_usage_id=usage,
                entity_id=entity_id,
                entity_revision=1,
                mapping_status="exact",
                decision="accept",
                reviewer="human-entity-reviewer",
                rationale="fixture",
                review_policy_name=ENTITY_RESOLUTION_POLICY_NAME,
                review_policy_version=ENTITY_RESOLUTION_POLICY_VERSION,
                review_policy_sha256=ENTITY_RESOLUTION_POLICY_SHA256,
                reviewed_at=CREATED_AT,
            )
        )
    return rows


def _project(relation: str, semantic_type: str) -> dict[str, object]:
    candidate, text = _candidate(relation, semantic_type)
    resolutions = require_reviewed_entity_resolutions_v1(
        candidate,
        semantic_candidate_id="candidate-1",
        events=_resolution_events(candidate),
        required_roles=("cause", "target"),
    )
    claim = SourceClaimsRow(
        id="claim-1",
        source_id="source-1",
        representation_id="rep-1",
        parent_claim_id=None,
        claim_layer="atomic",
        claim_text=text,
        claim_text_sha256=_sha(text),
        claim_kind="statement",
        semantic_type=semantic_type,
        qualifiers_json="{}",
        extraction_confidence_decimal=None,
        source_claim_effective_text_sha256=_sha(text),
        notes="",
        initial_review_status="unreviewed",
        created_at=CREATED_AT,
    )
    claim_review = ClaimReviewEventsRow(
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
    candidate_review = build_semantic_candidate_review_event_v1(
        candidate,
        event_id="candidate-review-1",
        semantic_candidate_id="candidate-1",
        decision="accept",
        reviewer="candidate-reviewer",
        reviewed_at=CREATED_AT,
    )
    evidence = SourceEvidenceRow(
        id="ev-1",
        segment_id="seg-1",
        segment_char_start=0,
        segment_char_end=len(text),
        evidence_text_sha256=_sha(text),
        start_seconds_decimal=None,
        end_seconds_decimal=None,
        page_number=None,
        frame_start=None,
        frame_end=None,
        evidence_metadata_json="{}",
        created_at=CREATED_AT,
    )
    segment = SegmentsRow(
        id="seg-1",
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
        created_at=CREATED_AT,
    )
    return project_scientific_assertion_v1(
        candidate,
        source_claim=claim,
        claim_reviews=[claim_review],
        candidate_reviews=[candidate_review],
        claim_evidence_links=[
            ClaimEvidenceLinksRow(
                claim_id="claim-1",
                evidence_id="ev-1",
                evidence_order=0,
                link_role="supports_source_claim",
                created_at=CREATED_AT,
            )
        ],
        evidence_rows=[evidence],
        segments={"seg-1": segment},
        segment_reviews={},
        entity_resolutions=resolutions,
    )


@pytest.mark.parametrize(
    ("relation", "semantic_type"),
    [
        ("adversely_affects", "health_effect"),
        ("poses_significant_threat_to", "risk_factor"),
        ("poses_significant_threat_to", "industry_impact"),
    ],
)
def test_projection_v1_2_builds_reviewed_binary_entity_relation(
    relation: str,
    semantic_type: str,
) -> None:
    result = _project(relation, semantic_type)
    assert result["contract"]["version"] == "1.2"
    assert result["contract"]["canonical_sha256"] == (
        "628dacf8a2a21c94d62d0374e9f0872ea9e1d547272fcb2600bc037786316526"
    )
    payload = result["assertion"]["payload"]
    assert payload["assertion_kind"] == "relational"
    assert payload["predicate"] == relation
    assert payload["value"] == {"kind": "none"}
    assert payload["qualifiers"] == {"semantic_type": semantic_type}
    assert payload["participants"] == [
        {
            "role": "cause",
            "entity": {
                "type": "entity_ref",
                "entity_id": "entity-ammonia",
                "entity_revision": 1,
            },
        },
        {
            "role": "target",
            "entity": {
                "type": "entity_ref",
                "entity_id": "entity-medaka",
                "entity_revision": 1,
            },
        },
    ]
    assert result["projection_gate_passed"] is True
    assert result["automatic_persistence"] is False


@pytest.mark.parametrize(
    ("relation", "semantic_type"),
    [
        ("adversely_affects", "knowledge_gap"),
    ],
)
def test_projection_v1_2_keeps_other_relation_type_pairs_fail_closed(
    relation: str,
    semantic_type: str,
) -> None:
    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="no exact Scientific Assertion Projection V1 mapping",
    ):
        _project(relation, semantic_type)
