from __future__ import annotations

import hashlib

import pytest

from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1 import (
    PROJECTION_CONTRACT_DESCRIPTOR_V1_7,
    ReviewedEntityArgumentV1,
    ScientificAssertionProjectionV1Error,
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

CREATED_AT = "2026-08-17T21:00:00+00:00"
TEXT = "Heat exposure caused a decrease in growth."


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _registry() -> dict[str, object]:
    return {
        "relations": {
            "caused_decrease": {
                "argument_keys": ["exposure", "variable"],
                "epistemic_class": "explicit_causal_result",
                "semantic_type_contract_state": (
                    "historical_golden_reviewed_constrained"
                ),
                "semantic_types_allowed": ["biological_effect"],
            },
        },
        "argument_role_semantics": {
            "exposure": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "exposure_intervention_or_stressor",
            },
            "variable": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "measurable_or_described_variable",
            },
        },
    }


def _candidate() -> dict[str, object]:
    return build_semantic_candidate_v2_11(
        {
            "c": "claim-decrease",
            "e": ["ev-decrease"],
            "t": "biological_effect",
            "m": {
                "r": "caused_decrease",
                "a": {
                    "exposure": "Heat exposure",
                    "variable": "growth",
                },
            },
        },
        {
            "source_claims": [
                {
                    "claim_id": "claim-decrease",
                    "effective_text": TEXT,
                    "evidence": [
                        {
                            "evidence_id": "ev-decrease",
                            "text": TEXT,
                        }
                    ],
                }
            ]
        },
        _registry(),
    )


def _argument(
    candidate: dict[str, object],
    role: str,
) -> dict[str, object]:
    arguments = candidate["semantic"]["arguments"]
    return next(item for item in arguments if item["role"] == role)


def _entity_resolutions(
    candidate: dict[str, object],
    *,
    include_exposure: bool = True,
) -> dict[str, ReviewedEntityArgumentV1]:
    rows = {
        "variable": ReviewedEntityArgumentV1(
            role="variable",
            candidate_argument_sha256=candidate_argument_sha256_v1(
                _argument(candidate, "variable")
            ),
            entity_id="entity-growth",
            entity_revision=1,
            mapping_status="exact",
            mapping_review_status="reviewed_confirmed",
            reviewed_by="human-reviewer",
        ),
    }
    if include_exposure:
        rows["exposure"] = ReviewedEntityArgumentV1(
            role="exposure",
            candidate_argument_sha256=candidate_argument_sha256_v1(
                _argument(candidate, "exposure")
            ),
            entity_id="entity-heat-exposure",
            entity_revision=1,
            mapping_status="exact",
            mapping_review_status="reviewed_confirmed",
            reviewed_by="human-reviewer",
        )
    return rows


def _project(
    candidate: dict[str, object],
    *,
    include_exposure: bool = True,
) -> dict[str, object]:
    claim = SourceClaimsRow(
        id="claim-decrease",
        source_id="source-1",
        representation_id="rep-1",
        parent_claim_id="parent-1",
        claim_layer="atomic",
        claim_text=TEXT,
        claim_text_sha256=_sha(TEXT),
        claim_kind="statement",
        semantic_type="biological_effect",
        qualifiers_json="{}",
        extraction_confidence_decimal=None,
        source_claim_effective_text_sha256=_sha(TEXT),
        notes="",
        initial_review_status="unreviewed",
        created_at=CREATED_AT,
    )
    claim_review = ClaimReviewEventsRow(
        id="claim-review-decrease",
        claim_id="claim-decrease",
        decision="accept",
        reviewer="human-reviewer",
        notes="",
        corrected_text=None,
        corrected_text_sha256=None,
        review_metadata_json="{}",
        reviewed_at=CREATED_AT,
    )
    candidate_review = build_semantic_candidate_review_event_v1(
        candidate,
        event_id="candidate-review-decrease",
        semantic_candidate_id="candidate-decrease",
        decision="accept",
        reviewer="candidate-reviewer",
        reviewed_at=CREATED_AT,
    )
    evidence = SourceEvidenceRow(
        id="ev-decrease",
        segment_id="seg-decrease",
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
    segment = SegmentsRow(
        id="seg-decrease",
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
    return project_scientific_assertion_v1(
        candidate,
        source_claim=claim,
        claim_reviews=[claim_review],
        candidate_reviews=[candidate_review],
        claim_evidence_links=[
            ClaimEvidenceLinksRow(
                claim_id="claim-decrease",
                evidence_id="ev-decrease",
                evidence_order=0,
                link_role="supports_source_claim",
                created_at=CREATED_AT,
            )
        ],
        evidence_rows=[evidence],
        segments={"seg-decrease": segment},
        segment_reviews={},
        entity_resolutions=_entity_resolutions(
            candidate,
            include_exposure=include_exposure,
        ),
    )


def test_g6_caused_decrease_projects_two_reviewed_entities() -> None:
    candidate = _candidate()
    result = _project(candidate)

    assert result["contract"]["version"] == "1.7"
    assert result["contract"]["projection_spec_id"] == (
        "caused_decrease.biological_effect.relational.v1"
    )
    assert result["assertion"]["payload"] == {
        "schema_version": "scientific-assertion-v1.1",
        "assertion_kind": "relational",
        "predicate": "caused_decrease",
        "participants": [
            {
                "role": "exposure",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-heat-exposure",
                    "entity_revision": 1,
                },
            },
            {
                "role": "variable",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-growth",
                    "entity_revision": 1,
                },
            },
        ],
        "value": {"kind": "none"},
        "qualifiers": {"semantic_type": "biological_effect"},
    }
    assert result["assertion"]["normalized_text"] == (
        'caused_decrease('
        'exposure=entity_ref("entity-heat-exposure",1), '
        'variable=entity_ref("entity-growth",1))'
    )
    assert result["projection_gate_passed"] is True
    assert result["automatic_persistence"] is False
    assert result["claim_link_proposal"]["requires_persistence_review"] is True


def test_g6_caused_decrease_uses_spec_binary_builder() -> None:
    matching = [
        spec
        for spec in PROJECTION_CONTRACT_DESCRIPTOR_V1_7["specs"]
        if spec["relation"] == "caused_decrease"
        and spec["semantic_type"] == "biological_effect"
    ]

    assert matching == [
        {
            "assertion_kind": "relational",
            "builder": "spec_binary_entity_relation_v1",
            "predicate": "caused_decrease",
            "relation": "caused_decrease",
            "role_classes": (
                ("exposure", "ENTITY_ARGUMENT"),
                ("variable", "ENTITY_ARGUMENT"),
            ),
            "semantic_type": "biological_effect",
            "spec_id": "caused_decrease.biological_effect.relational.v1",
        }
    ]


def test_g6_caused_decrease_requires_reviewed_exposure_entity() -> None:
    candidate = _candidate()

    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="human-reviewed entity mapping is required for role: exposure",
    ):
        _project(candidate, include_exposure=False)
