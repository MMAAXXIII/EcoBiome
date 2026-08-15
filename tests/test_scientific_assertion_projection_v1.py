from __future__ import annotations

import copy
import hashlib

import pytest

from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1 import (
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
    SegmentReviewEventsRow,
    SegmentsRow,
    SemanticCandidateReviewEventsRow,
    SourceClaimsRow,
    SourceEvidenceRow,
)
from ecobiome.knowledge_persistence.serialization import canonical_json_text


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _registry() -> dict[str, object]:
    return {
        "relations": {
            "maintained_at": {
                "argument_keys": ["variable", "value", "unit"],
                "epistemic_class": "study_context_non_result",
                "semantic_type_contract_state": (
                    "historical_golden_reviewed_constrained"
                ),
                "semantic_types_allowed": ["experimental_condition"],
            },
            "studied": {
                "argument_keys": ["life_stage", "species"],
                "epistemic_class": "study_context_non_result",
                "semantic_type_contract_state": (
                    "historical_golden_reviewed_constrained"
                ),
                "semantic_types_allowed": ["study_subject"],
            },
        },
        "argument_role_semantics": {
            "variable": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "measurable_or_described_variable",
            },
            "value": {
                "grounding_class": "exact_numeric_source_grounded",
                "semantic_domain": "numeric_value",
            },
            "unit": {
                "grounding_class": "controlled_literal_source_grounded",
                "semantic_domain": "controlled_measurement_or_time_unit",
            },
            "life_stage": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "organism_life_stage",
            },
            "species": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "species_identity",
            },
        },
    }


def _source_request(text: str) -> dict[str, object]:
    return {
        "source_claims": [
            {
                "claim_id": "claim-temperature",
                "effective_text": text,
                "evidence": [
                    {"evidence_id": "ev-2", "text": "26.5 °C"},
                    {"evidence_id": "ev-1", "text": "Temperature"},
                ],
            }
        ]
    }


def _candidate(text: str | None = None) -> dict[str, object]:
    source_text = (
        text
        or "Temperature was maintained at 26.5 °C during the trial."
    )
    survivor = {
        "c": "claim-temperature",
        "e": ["ev-2", "ev-1"],
        "t": "experimental_condition",
        "m": {
            "r": "maintained_at",
            "a": {
                "variable": "temperature",
                "value": 26.5,
                "unit": "degree celsius",
            },
        },
    }
    return build_semantic_candidate_v2_11(
        survivor,
        _source_request(source_text),
        _registry(),
    )


def _claim(
    text: str | None = None,
    *,
    layer: str = "atomic",
    effective_sha: str | None = None,
) -> SourceClaimsRow:
    claim_text = (
        text
        or "Temperature was maintained at 26.5 °C during the trial."
    )
    return SourceClaimsRow(
        id="claim-temperature",
        source_id="source-1",
        representation_id="rep-1",
        parent_claim_id="parent-1",
        claim_layer=layer,
        claim_text=claim_text,
        claim_text_sha256=_sha(claim_text),
        claim_kind="statement",
        semantic_type="experimental_condition",
        qualifiers_json="{}",
        extraction_confidence_decimal=None,
        source_claim_effective_text_sha256=effective_sha or ("f" * 64),
        notes="",
        initial_review_status="unreviewed",
        created_at="2026-08-14T20:00:00+00:00",
    )


def _accept_review() -> ClaimReviewEventsRow:
    return ClaimReviewEventsRow(
        id="review-claim-1",
        claim_id="claim-temperature",
        decision="accept",
        reviewer="human-reviewer",
        notes="",
        corrected_text=None,
        corrected_text_sha256=None,
        review_metadata_json="{}",
        reviewed_at="2026-08-14T20:10:00+00:00",
    )


def _candidate_accept_review(
    candidate: dict[str, object],
    *,
    decision: str = "accept",
    event_id: str = "candidate-review-1",
    reviewed_at: str = "2026-08-14T20:11:00+00:00",
) -> SemanticCandidateReviewEventsRow:
    if decision == "correct":
        return build_semantic_candidate_review_event_v1(
            candidate,
            event_id=event_id,
            semantic_candidate_id="candidate-1",
            decision=decision,
            reviewer="candidate-reviewer",
            reviewed_at=reviewed_at,
            replacement_candidate_id="candidate-2",
            replacement_candidate_sha256="0" * 64,
        )
    return build_semantic_candidate_review_event_v1(
        candidate,
        event_id=event_id,
        semantic_candidate_id="candidate-1",
        decision=decision,
        reviewer="candidate-reviewer",
        reviewed_at=reviewed_at,
    )


def _evidence_links() -> list[ClaimEvidenceLinksRow]:
    return [
        ClaimEvidenceLinksRow(
            claim_id="claim-temperature",
            evidence_id="ev-1",
            evidence_order=0,
            link_role="supports_source_claim",
            created_at="2026-08-14T20:00:00+00:00",
        ),
        ClaimEvidenceLinksRow(
            claim_id="claim-temperature",
            evidence_id="ev-2",
            evidence_order=1,
            link_role="supports_source_claim",
            created_at="2026-08-14T20:00:00+00:00",
        ),
    ]


def _evidence_rows() -> list[SourceEvidenceRow]:
    return [
        SourceEvidenceRow(
            id="ev-1",
            segment_id="seg-1",
            segment_char_start=0,
            segment_char_end=11,
            evidence_text_sha256=_sha("Temperature"),
            start_seconds_decimal=None,
            end_seconds_decimal=None,
            page_number=None,
            frame_start=None,
            frame_end=None,
            evidence_metadata_json="{}",
            created_at="2026-08-14T20:00:00+00:00",
        ),
        SourceEvidenceRow(
            id="ev-2",
            segment_id="seg-2",
            segment_char_start=0,
            segment_char_end=7,
            evidence_text_sha256=_sha("26.5 °C"),
            start_seconds_decimal=None,
            end_seconds_decimal=None,
            page_number=None,
            frame_start=None,
            frame_end=None,
            evidence_metadata_json="{}",
            created_at="2026-08-14T20:00:00+00:00",
        ),
    ]


def _segment(segment_id: str) -> SegmentsRow:
    return SegmentsRow(
        id=segment_id,
        representation_id="rep-1",
        segment_index=1 if segment_id == "seg-1" else 2,
        text_inline="Temperature" if segment_id == "seg-1" else "26.5 °C",
        text_sha256=_sha(
            "Temperature" if segment_id == "seg-1" else "26.5 °C"
        ),
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
        created_at="2026-08-14T20:00:00+00:00",
    )


def _segments() -> dict[str, SegmentsRow]:
    return {
        "seg-1": _segment("seg-1"),
        "seg-2": _segment("seg-2"),
    }


def _variable_argument(
    candidate: dict[str, object],
) -> dict[str, object]:
    arguments = candidate["semantic"]["arguments"]
    return next(item for item in arguments if item["role"] == "variable")


def _entity_resolution(
    candidate: dict[str, object],
    *,
    review_status: str = "reviewed_confirmed",
    argument_sha: str | None = None,
) -> ReviewedEntityArgumentV1:
    argument = _variable_argument(candidate)
    return ReviewedEntityArgumentV1(
        role="variable",
        candidate_argument_sha256=(
            argument_sha or candidate_argument_sha256_v1(argument)
        ),
        entity_id="entity-temperature",
        entity_revision=1,
        mapping_status="exact",
        mapping_review_status=review_status,
        reviewed_by="human-reviewer",
    )


def _project(
    candidate: dict[str, object] | None = None,
    *,
    claim: SourceClaimsRow | None = None,
    claim_reviews: list[ClaimReviewEventsRow] | None = None,
    candidate_reviews: list[SemanticCandidateReviewEventsRow] | None = None,
    links: list[ClaimEvidenceLinksRow] | None = None,
    evidence_rows: list[SourceEvidenceRow] | None = None,
    segments: dict[str, SegmentsRow] | None = None,
    segment_reviews: (
        dict[str, list[SegmentReviewEventsRow]] | None
    ) = None,
    entity_resolution: ReviewedEntityArgumentV1 | None = None,
) -> dict[str, object]:
    current_candidate = candidate or _candidate()
    return project_scientific_assertion_v1(
        current_candidate,
        source_claim=claim or _claim(),
        claim_reviews=(
            [_accept_review()]
            if claim_reviews is None
            else claim_reviews
        ),
        candidate_reviews=(
            [_candidate_accept_review(current_candidate)]
            if candidate_reviews is None
            else candidate_reviews
        ),
        claim_evidence_links=links or _evidence_links(),
        evidence_rows=evidence_rows or _evidence_rows(),
        segments=segments or _segments(),
        segment_reviews=segment_reviews or {},
        entity_resolutions={
            "variable": (
                entity_resolution or _entity_resolution(current_candidate)
            )
        },
    )


def test_projection_builds_exact_measurement_assertion() -> None:
    result = _project()

    assertion = result["assertion"]
    assert assertion["payload"] == {
        "schema_version": "scientific-assertion-v1.1",
        "assertion_kind": "measurement",
        "predicate": "maintained_at",
        "participants": [
            {
                "role": "variable",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-temperature",
                    "entity_revision": 1,
                },
            }
        ],
        "value": {
            "kind": "measurement",
            "amount": {"type": "decimal", "value": "26.5"},
            "unit": "celsius",
        },
        "qualifiers": {
            "semantic_type": "experimental_condition",
        },
    }
    assert result["projection_gate_passed"] is True
    assert result["automatic_persistence"] is False
    assert result["claim_link_proposal"]["requires_persistence_review"] is True


def test_projection_is_deterministic_and_float_free() -> None:
    first = _project()
    second = _project()

    assert first == second
    serialized = canonical_json_text(first)
    assert '"value":"26.5"' in serialized
    assert "26.5" in first["assertion"]["normalized_text"]


def test_projection_requires_human_claim_review() -> None:
    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="at least one human review",
    ):
        _project(claim_reviews=[])


def test_projection_rejects_latest_rejected_claim() -> None:
    rejected = copy.copy(_accept_review())
    rejected = ClaimReviewEventsRow(
        id="review-claim-2",
        claim_id=rejected.claim_id,
        decision="reject",
        reviewer="human-reviewer",
        notes="",
        corrected_text=None,
        corrected_text_sha256=None,
        review_metadata_json="{}",
        reviewed_at="2026-08-14T20:20:00+00:00",
    )

    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="latest source Claim review is rejected",
    ):
        _project(claim_reviews=[_accept_review(), rejected])


def test_projection_allows_reviewed_correction_when_candidate_was_rebuilt() -> None:
    original = "Temperature was 25 °C during the trial."
    corrected = "Temperature was maintained at 26.5 °C during the trial."
    candidate = _candidate(corrected)
    correction = ClaimReviewEventsRow(
        id="review-correction",
        claim_id="claim-temperature",
        decision="correct",
        reviewer="human-reviewer",
        notes="",
        corrected_text=corrected,
        corrected_text_sha256=_sha(corrected),
        review_metadata_json="{}",
        reviewed_at="2026-08-14T20:10:00+00:00",
    )
    claim = _claim(
        original,
        effective_sha=_sha(corrected),
    )

    result = _project(
        candidate,
        claim=claim,
        claim_reviews=[correction],
        entity_resolution=_entity_resolution(candidate),
    )

    assert (
        result["source"]["source_claim_effective_text_sha256"]
        == _sha(corrected)
    )


def test_projection_rejects_stale_candidate_after_correction() -> None:
    candidate = _candidate()
    corrected = (
        "Temperature was maintained at 27.0 °C during the corrected trial."
    )
    correction = ClaimReviewEventsRow(
        id="review-correction",
        claim_id="claim-temperature",
        decision="correct",
        reviewer="human-reviewer",
        notes="",
        corrected_text=corrected,
        corrected_text_sha256=_sha(corrected),
        review_metadata_json="{}",
        reviewed_at="2026-08-14T20:10:00+00:00",
    )
    claim = _claim(
        effective_sha=_sha(corrected),
    )

    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="candidate is stale",
    ):
        _project(
            candidate,
            claim=claim,
            claim_reviews=[correction],
        )


def test_projection_requires_atomic_claim() -> None:
    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="atomic source Claim",
    ):
        _project(claim=_claim(layer="extracted"))


def test_projection_rejects_missing_claim_evidence_link() -> None:
    links = _evidence_links()
    links.pop()

    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="not linked to the atomic Claim",
    ):
        _project(links=links)


def test_projection_rejects_missing_evidence_segment_reports_exact_segment() -> None:
    segments = {"seg-2": _segment("seg-2")}

    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match=r"Evidence segment is missing: seg-1$",
    ):
        _project(segments=segments)


def test_projection_rejects_rejected_evidence_segment() -> None:
    review = SegmentReviewEventsRow(
        id="segment-review-1",
        segment_id="seg-2",
        decision="reject",
        reviewer="human-reviewer",
        rationale="bad evidence",
        corrected_text=None,
        corrected_text_sha256=None,
        review_metadata_json="{}",
        reviewed_at="2026-08-14T20:15:00+00:00",
    )

    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="latest Evidence segment review is rejected",
    ):
        _project(segment_reviews={"seg-2": [review]})


def test_projection_requires_reviewed_entity_mapping() -> None:
    candidate = _candidate()
    resolution = _entity_resolution(
        candidate,
        review_status="unreviewed",
    )

    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="not human-reviewed",
    ):
        _project(
            candidate,
            entity_resolution=resolution,
        )


def test_projection_rejects_stale_entity_mapping() -> None:
    candidate = _candidate()
    resolution = _entity_resolution(
        candidate,
        argument_sha="0" * 64,
    )

    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="entity mapping is stale",
    ):
        _project(
            candidate,
            entity_resolution=resolution,
        )


def test_projection_rejects_extra_cross_claim_entity_reconstruction() -> None:
    candidate = _candidate()
    resolution = _entity_resolution(candidate)

    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="extra entity reconstruction",
    ):
        project_scientific_assertion_v1(
            candidate,
            source_claim=_claim(),
            claim_reviews=[_accept_review()],
            candidate_reviews=[_candidate_accept_review(candidate)],
            claim_evidence_links=_evidence_links(),
            evidence_rows=_evidence_rows(),
            segments=_segments(),
            segment_reviews={},
            entity_resolutions={
                "variable": resolution,
                "species": ReviewedEntityArgumentV1(
                    role="species",
                    candidate_argument_sha256="0" * 64,
                    entity_id="entity-zebrafish",
                    entity_revision=1,
                    mapping_status="exact",
                    mapping_review_status="reviewed_confirmed",
                    reviewed_by="human-reviewer",
                ),
            },
        )


def test_projection_fails_closed_without_exact_projection_mapping() -> None:
    source = {
        "source_claims": [
            {
                "claim_id": "claim-study",
                "effective_text": "Juvenile zebrafish were studied.",
                "evidence": [
                    {
                        "evidence_id": "ev-study",
                        "text": "Juvenile zebrafish were studied.",
                    }
                ],
            }
        ]
    }
    survivor = {
        "c": "claim-study",
        "e": ["ev-study"],
        "t": "study_subject",
        "m": {
            "r": "studied",
            "a": {
                "life_stage": "juvenile",
                "species": "zebrafish",
            },
        },
    }
    candidate = build_semantic_candidate_v2_11(
        survivor,
        source,
        _registry(),
    )
    claim_text = "Juvenile zebrafish were studied."
    claim = SourceClaimsRow(
        id="claim-study",
        source_id="source-1",
        representation_id="rep-1",
        parent_claim_id="parent-1",
        claim_layer="atomic",
        claim_text=claim_text,
        claim_text_sha256=_sha(claim_text),
        claim_kind="statement",
        semantic_type="study_subject",
        qualifiers_json="{}",
        extraction_confidence_decimal=None,
        source_claim_effective_text_sha256=_sha(claim_text),
        notes="",
        initial_review_status="unreviewed",
        created_at="2026-08-14T20:00:00+00:00",
    )
    review = ClaimReviewEventsRow(
        id="review-study",
        claim_id="claim-study",
        decision="accept",
        reviewer="human-reviewer",
        notes="",
        corrected_text=None,
        corrected_text_sha256=None,
        review_metadata_json="{}",
        reviewed_at="2026-08-14T20:10:00+00:00",
    )
    link = ClaimEvidenceLinksRow(
        claim_id="claim-study",
        evidence_id="ev-study",
        evidence_order=0,
        link_role="supports_source_claim",
        created_at="2026-08-14T20:00:00+00:00",
    )
    evidence = SourceEvidenceRow(
        id="ev-study",
        segment_id="seg-study",
        segment_char_start=0,
        segment_char_end=len(claim_text),
        evidence_text_sha256=_sha(claim_text),
        start_seconds_decimal=None,
        end_seconds_decimal=None,
        page_number=None,
        frame_start=None,
        frame_end=None,
        evidence_metadata_json="{}",
        created_at="2026-08-14T20:00:00+00:00",
    )
    segment = SegmentsRow(
        id="seg-study",
        representation_id="rep-1",
        segment_index=0,
        text_inline=claim_text,
        text_sha256=_sha(claim_text),
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
        created_at="2026-08-14T20:00:00+00:00",
    )

    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="no exact Scientific Assertion Projection V1 mapping",
    ):
        project_scientific_assertion_v1(
            candidate,
            source_claim=claim,
            claim_reviews=[review],
            candidate_reviews=[_candidate_accept_review(candidate)],
            claim_evidence_links=[link],
            evidence_rows=[evidence],
            segments={"seg-study": segment},
            segment_reviews={},
            entity_resolutions={},
        )
def test_projection_requires_human_candidate_acceptance() -> None:
    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="Candidate requires at least one human review",
    ):
        _project(candidate_reviews=[])


def test_projection_rejects_latest_rejected_candidate() -> None:
    candidate = _candidate()
    rejected = _candidate_accept_review(
        candidate,
        decision="reject",
        event_id="candidate-review-reject",
        reviewed_at="2026-08-14T20:12:00+00:00",
    )
    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="latest semantic Candidate review is 'reject'",
    ):
        _project(candidate, candidate_reviews=[rejected])
