from __future__ import annotations

import hashlib

import pytest

from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1 import (
    PROJECTION_CONTRACT_DESCRIPTOR_V1_6,
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

CREATED_AT = "2026-08-18T09:30:00+00:00"
TEXT = (
    "Heat-response genes were primarily associated with oxidative stress response."
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _registry() -> dict[str, object]:
    return {
        "relations": {
            "primarily_associated_with": {
                "argument_keys": ["gene_set", "process"],
                "epistemic_class": "association_only",
                "semantic_type_contract_state": (
                    "historical_golden_reviewed_constrained"
                ),
                "semantic_types_allowed": ["gene_function_association"],
            }
        },
        "argument_role_semantics": {
            "gene_set": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "gene_gene_family_or_gene_set",
            },
            "process": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": (
                    "biological_ecological_chemical_or_physical_process"
                ),
            },
        },
    }


def _candidate() -> dict[str, object]:
    return build_semantic_candidate_v2_11(
        {
            "c": "claim-gene-function",
            "e": ["ev-gene-function"],
            "t": "gene_function_association",
            "m": {
                "r": "primarily_associated_with",
                "a": {
                    "gene_set": "Heat-response genes",
                    "process": "oxidative stress response",
                },
            },
        },
        {
            "source_claims": [
                {
                    "claim_id": "claim-gene-function",
                    "effective_text": TEXT,
                    "evidence": [{"evidence_id": "ev-gene-function", "text": TEXT}],
                }
            ]
        },
        _registry(),
    )


def _argument(candidate: dict[str, object], role: str) -> dict[str, object]:
    arguments = candidate["semantic"]["arguments"]
    return next(item for item in arguments if item["role"] == role)


def _resolutions(
    candidate: dict[str, object],
    *,
    gene_set: bool = True,
    process: bool = True,
) -> dict[str, ReviewedEntityArgumentV1]:
    result: dict[str, ReviewedEntityArgumentV1] = {}
    if gene_set:
        result["gene_set"] = ReviewedEntityArgumentV1(
            role="gene_set",
            candidate_argument_sha256=candidate_argument_sha256_v1(
                _argument(candidate, "gene_set")
            ),
            entity_id="entity-heat-response-genes",
            entity_revision=1,
            mapping_status="exact",
            mapping_review_status="reviewed_confirmed",
            reviewed_by="human-reviewer",
        )
    if process:
        result["process"] = ReviewedEntityArgumentV1(
            role="process",
            candidate_argument_sha256=candidate_argument_sha256_v1(
                _argument(candidate, "process")
            ),
            entity_id="entity-oxidative-stress-response",
            entity_revision=1,
            mapping_status="exact",
            mapping_review_status="reviewed_confirmed",
            reviewed_by="human-reviewer",
        )
    return result


def _project(
    candidate: dict[str, object],
    *,
    gene_set: bool = True,
    process: bool = True,
) -> dict[str, object]:
    claim = SourceClaimsRow(
        id="claim-gene-function",
        source_id="source-1",
        representation_id="rep-1",
        parent_claim_id="parent-1",
        claim_layer="atomic",
        claim_text=TEXT,
        claim_text_sha256=_sha(TEXT),
        claim_kind="statement",
        semantic_type="gene_function_association",
        qualifiers_json="{}",
        extraction_confidence_decimal=None,
        source_claim_effective_text_sha256=_sha(TEXT),
        notes="",
        initial_review_status="unreviewed",
        created_at=CREATED_AT,
    )
    review = ClaimReviewEventsRow(
        id="claim-review-gene-function",
        claim_id="claim-gene-function",
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
        event_id="candidate-review-gene-function",
        semantic_candidate_id="candidate-gene-function",
        decision="accept",
        reviewer="candidate-reviewer",
        reviewed_at=CREATED_AT,
    )
    evidence = SourceEvidenceRow(
        id="ev-gene-function",
        segment_id="seg-gene-function",
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
        id="seg-gene-function",
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
        claim_reviews=[review],
        candidate_reviews=[candidate_review],
        claim_evidence_links=[
            ClaimEvidenceLinksRow(
                claim_id="claim-gene-function",
                evidence_id="ev-gene-function",
                evidence_order=0,
                link_role="supports_source_claim",
                created_at=CREATED_AT,
            )
        ],
        evidence_rows=[evidence],
        segments={"seg-gene-function": segment},
        segment_reviews={},
        entity_resolutions=_resolutions(
            candidate,
            gene_set=gene_set,
            process=process,
        ),
    )


def test_g6_gene_function_association_projects_reviewed_entities() -> None:
    candidate = _candidate()
    assert candidate["semantic"]["epistemic_class"] == "association_only"

    result = _project(candidate)

    assert result["contract"]["version"] == "1.6"
    assert result["contract"]["projection_spec_id"] == (
        "primarily_associated_with.gene_function_association.relational.v1"
    )
    assert result["assertion"]["payload"] == {
        "schema_version": "scientific-assertion-v1.1",
        "assertion_kind": "relational",
        "predicate": "primarily_associated_with",
        "participants": [
            {
                "role": "gene_set",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-heat-response-genes",
                    "entity_revision": 1,
                },
            },
            {
                "role": "process",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-oxidative-stress-response",
                    "entity_revision": 1,
                },
            },
        ],
        "value": {"kind": "none"},
        "qualifiers": {"semantic_type": "gene_function_association"},
    }
    assert result["automatic_persistence"] is False


def test_g6_gene_function_association_uses_spec_binary_builder() -> None:
    matching = [
        spec
        for spec in PROJECTION_CONTRACT_DESCRIPTOR_V1_6["specs"]
        if spec["relation"] == "primarily_associated_with"
        and spec["semantic_type"] == "gene_function_association"
    ]
    assert matching == [
        {
            "assertion_kind": "relational",
            "builder": "spec_binary_entity_relation_v1",
            "predicate": "primarily_associated_with",
            "relation": "primarily_associated_with",
            "role_classes": (
                ("gene_set", "ENTITY_ARGUMENT"),
                ("process", "ENTITY_ARGUMENT"),
            ),
            "semantic_type": "gene_function_association",
            "spec_id": (
                "primarily_associated_with."
                "gene_function_association.relational.v1"
            ),
        }
    ]


@pytest.mark.parametrize("missing_role", ["gene_set", "process"])
def test_g6_gene_function_association_requires_both_reviewed_entities(
    missing_role: str,
) -> None:
    candidate = _candidate()

    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match=f"human-reviewed entity mapping is required for role: {missing_role}",
    ):
        _project(
            candidate,
            gene_set=missing_role != "gene_set",
            process=missing_role != "process",
        )
