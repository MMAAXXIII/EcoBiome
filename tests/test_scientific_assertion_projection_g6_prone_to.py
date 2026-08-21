from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1 import (
    PROJECTION_CONTRACT_DESCRIPTOR_V1_7,
    ReviewedContextArgumentV1,
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

CREATED_AT = "2026-08-19T17:30:00+00:00"
LATER_AT = "2026-08-19T17:31:00+00:00"
TEXT = "Zebrafish are prone to oxidative stress."
REGISTRY_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "collector_semantic_v2_7"
    / "SEMANTIC_RELATION_REGISTRY_V2_7.json"
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _registry() -> dict[str, object]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _candidate() -> dict[str, object]:
    return build_semantic_candidate_v2_11(
        {
            "c": "claim-prone-to",
            "e": ["ev-prone-to"],
            "t": "risk_factor",
            "m": {
                "r": "prone_to",
                "a": {
                    "subject": "Zebrafish",
                    "outcome": "oxidative stress",
                },
            },
        },
        {
            "source_claims": [
                {
                    "claim_id": "claim-prone-to",
                    "effective_text": TEXT,
                    "evidence": [
                        {
                            "evidence_id": "ev-prone-to",
                            "text": TEXT,
                        }
                    ],
                }
            ]
        },
        _registry(),
    )


def _argument(candidate: dict[str, object], role: str) -> dict[str, object]:
    arguments = candidate["semantic"]["arguments"]
    return next(item for item in arguments if item["role"] == role)


def _reviewed_entity(
    candidate: dict[str, object],
    role: str,
    entity_id: str,
    *,
    argument_sha: str | None = None,
    mapping_review_status: str = "reviewed_confirmed",
) -> ReviewedEntityArgumentV1:
    return ReviewedEntityArgumentV1(
        role=role,
        candidate_argument_sha256=(
            argument_sha
            if argument_sha is not None
            else candidate_argument_sha256_v1(_argument(candidate, role))
        ),
        entity_id=entity_id,
        entity_revision=1,
        mapping_status="exact",
        mapping_review_status=mapping_review_status,
        reviewed_by="human-entity-reviewer",
    )


def _resolutions(
    candidate: dict[str, object],
) -> dict[str, ReviewedEntityArgumentV1]:
    return {
        "subject": _reviewed_entity(
            candidate, "subject", "entity-zebrafish"
        ),
        "outcome": _reviewed_entity(
            candidate, "outcome", "entity-oxidative-stress"
        ),
    }


def _candidate_review(
    candidate: dict[str, object],
    *,
    event_id: str,
    decision: str,
    reviewed_at: str,
):
    return build_semantic_candidate_review_event_v1(
        candidate,
        event_id=event_id,
        semantic_candidate_id="candidate-prone-to",
        decision=decision,
        reviewer="human-candidate-reviewer",
        reviewed_at=reviewed_at,
    )


def _project(
    candidate: dict[str, object],
    *,
    entity_resolutions: dict[str, ReviewedEntityArgumentV1] | None = None,
    candidate_reviews: list[object] | None = None,
    context_resolutions: dict[str, ReviewedContextArgumentV1] | None = None,
) -> dict[str, object]:
    claim = SourceClaimsRow(
        id="claim-prone-to",
        source_id="source-1",
        representation_id="rep-1",
        parent_claim_id="parent-1",
        claim_layer="atomic",
        claim_text=TEXT,
        claim_text_sha256=_sha(TEXT),
        claim_kind="statement",
        semantic_type="risk_factor",
        qualifiers_json="{}",
        extraction_confidence_decimal=None,
        source_claim_effective_text_sha256=_sha(TEXT),
        notes="",
        initial_review_status="unreviewed",
        created_at=CREATED_AT,
    )
    claim_review = ClaimReviewEventsRow(
        id="claim-review-prone-to",
        claim_id="claim-prone-to",
        decision="accept",
        reviewer="human-claim-reviewer",
        notes="",
        corrected_text=None,
        corrected_text_sha256=None,
        review_metadata_json="{}",
        reviewed_at=CREATED_AT,
    )
    accepted_review = _candidate_review(
        candidate,
        event_id="candidate-review-prone-to-accept",
        decision="accept",
        reviewed_at=CREATED_AT,
    )
    evidence = SourceEvidenceRow(
        id="ev-prone-to",
        segment_id="seg-prone-to",
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
        id="seg-prone-to",
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
        candidate_reviews=(
            [accepted_review]
            if candidate_reviews is None
            else candidate_reviews
        ),
        claim_evidence_links=[
            ClaimEvidenceLinksRow(
                claim_id="claim-prone-to",
                evidence_id="ev-prone-to",
                evidence_order=0,
                link_role="supports_source_claim",
                created_at=CREATED_AT,
            )
        ],
        evidence_rows=[evidence],
        segments={"seg-prone-to": segment},
        segment_reviews={},
        entity_resolutions=(
            _resolutions(candidate)
            if entity_resolutions is None
            else entity_resolutions
        ),
        context_resolutions=context_resolutions,
    )


def test_g6_prone_to_uses_exact_canonical_registry_semantics() -> None:
    registry = _registry()
    assert registry["relations"]["prone_to"] == {
        "argument_keys": ["subject", "outcome"],
        "description": (
            "A subject is explicitly described as prone or susceptible to an "
            "outcome; occurrence is not asserted as observed."
        ),
        "epistemic_class": "dispositional_risk",
        "semantic_types_allowed": ["risk_factor"],
    }
    assert registry["argument_role_semantics"]["subject"] == {
        "description": (
            "Entity, population, pool, system, or other subject whose state "
            "or trajectory is being described."
        ),
        "grounding_class": "open_text_source_grounded",
        "semantic_domain": "entity_or_system_being_characterized",
    }
    assert registry["argument_role_semantics"]["outcome"] == {
        "description": "Outcome, effect, or response target.",
        "grounding_class": "open_text_source_grounded",
        "semantic_domain": "outcome_or_effect_target",
    }


def test_g6_prone_to_projects_reviewed_entities_without_epistemic_upgrade() -> None:
    candidate = _candidate()
    assert candidate["semantic"]["epistemic_class"] == "dispositional_risk"
    assert candidate["automatic_scientific_acceptance"] is False

    result = _project(candidate)

    assert result["contract"]["version"] == "1.7"
    assert result["contract"]["projection_spec_id"] == (
        "prone_to.risk_factor.relational.v1"
    )
    assert result["assertion"]["payload"] == {
        "schema_version": "scientific-assertion-v1.1",
        "assertion_kind": "relational",
        "predicate": "prone_to",
        "participants": [
            {
                "role": "outcome",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-oxidative-stress",
                    "entity_revision": 1,
                },
            },
            {
                "role": "subject",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-zebrafish",
                    "entity_revision": 1,
                },
            },
        ],
        "value": {"kind": "none"},
        "qualifiers": {"semantic_type": "risk_factor"},
    }
    assert result["assertion"]["normalized_text"] == (
        'prone_to('
        'outcome=entity_ref("entity-oxidative-stress",1), '
        'subject=entity_ref("entity-zebrafish",1))'
    )
    assert result["projection_gate_passed"] is True
    assert result["automatic_persistence"] is False
    assert result["claim_link_proposal"]["requires_persistence_review"] is True


def test_g6_prone_to_uses_spec_binary_builder_with_logical_role_order() -> None:
    matching = [
        spec
        for spec in PROJECTION_CONTRACT_DESCRIPTOR_V1_7["specs"]
        if spec["relation"] == "prone_to"
        and spec["semantic_type"] == "risk_factor"
    ]
    assert matching == [
        {
            "assertion_kind": "relational",
            "builder": "spec_binary_entity_relation_v1",
            "predicate": "prone_to",
            "relation": "prone_to",
            "role_classes": (
                ("subject", "ENTITY_ARGUMENT"),
                ("outcome", "ENTITY_ARGUMENT"),
            ),
            "semantic_type": "risk_factor",
            "spec_id": "prone_to.risk_factor.relational.v1",
        }
    ]


@pytest.mark.parametrize("missing_role", ["subject", "outcome"])
def test_g6_prone_to_requires_both_reviewed_entities(
    missing_role: str,
) -> None:
    candidate = _candidate()
    resolutions = _resolutions(candidate)
    resolutions.pop(missing_role)

    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match=(
            "human-reviewed entity mapping is required for role: "
            f"{missing_role}"
        ),
    ):
        _project(candidate, entity_resolutions=resolutions)


def test_g6_prone_to_rejects_stale_argument_sha() -> None:
    candidate = _candidate()
    resolutions = _resolutions(candidate)
    resolutions["subject"] = _reviewed_entity(
        candidate,
        "subject",
        "entity-zebrafish",
        argument_sha="0" * 64,
    )
    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="entity mapping is stale for candidate role: subject",
    ):
        _project(candidate, entity_resolutions=resolutions)


def test_g6_prone_to_requires_human_confirmed_entity_mapping() -> None:
    candidate = _candidate()
    resolutions = _resolutions(candidate)
    resolutions["subject"] = _reviewed_entity(
        candidate,
        "subject",
        "entity-zebrafish",
        mapping_review_status="rejected",
    )
    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="entity mapping is not human-reviewed for role: subject",
    ):
        _project(candidate, entity_resolutions=resolutions)


def test_g6_prone_to_forbids_extra_entity_reconstruction() -> None:
    candidate = _candidate()
    resolutions = _resolutions(candidate)
    resolutions["foreign"] = ReviewedEntityArgumentV1(
        role="foreign",
        candidate_argument_sha256="0" * 64,
        entity_id="entity-foreign",
        entity_revision=1,
        mapping_status="exact",
        mapping_review_status="reviewed_confirmed",
        reviewed_by="human-entity-reviewer",
    )
    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="cross-Claim or extra entity reconstruction is forbidden",
    ):
        _project(candidate, entity_resolutions=resolutions)


def test_g6_prone_to_forbids_extra_context_reconstruction() -> None:
    candidate = _candidate()
    context = {
        "context": ReviewedContextArgumentV1(
            role="context",
            candidate_argument_sha256="0" * 64,
            canonical_value="heat exposure",
            mapping_review_status="reviewed_confirmed",
            reviewed_by="human-context-reviewer",
        )
    }
    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="cross-Claim or extra context reconstruction is forbidden",
    ):
        _project(candidate, context_resolutions=context)


def test_g6_prone_to_latest_candidate_reject_blocks_projection() -> None:
    candidate = _candidate()
    accepted = _candidate_review(
        candidate,
        event_id="candidate-review-prone-to-accept",
        decision="accept",
        reviewed_at=CREATED_AT,
    )
    rejected = _candidate_review(
        candidate,
        event_id="candidate-review-prone-to-reject",
        decision="reject",
        reviewed_at=LATER_AT,
    )
    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="latest semantic Candidate review is 'reject', not 'accept'",
    ):
        _project(candidate, candidate_reviews=[accepted, rejected])
