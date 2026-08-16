from __future__ import annotations

import hashlib

import pytest

from ecobiome.knowledge_graph_v1 import (
    claim_from_collector_v1,
    evidence_from_collector_v1,
)
from ecobiome.knowledge_persistence.contracts import (
    ClaimEvidenceLinksRow,
    SegmentsRow,
    SourceClaimsRow,
    SourceEvidenceRow,
)

NOW = "2026-08-16T15:00:00+00:00"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_bridge_preserves_exact_collector_evidence_span_and_hash() -> None:
    segment_text = "prefix algae grows on plants suffix"
    exact = "algae grows on plants"
    start = segment_text.index(exact)
    end = start + len(exact)
    claim = SourceClaimsRow(
        id="claim-a",
        source_id="source-a",
        representation_id="representation-a",
        parent_claim_id=None,
        claim_layer="atomic",
        claim_text=exact,
        claim_text_sha256=_sha(exact),
        claim_kind=None,
        semantic_type=None,
        qualifiers_json="{}",
        extraction_confidence_decimal="0.8",
        source_claim_effective_text_sha256=_sha(exact),
        notes="",
        initial_review_status="pending",
        created_at=NOW,
    )
    evidence = SourceEvidenceRow(
        id="evidence-a",
        segment_id="segment-a",
        segment_char_start=start,
        segment_char_end=end,
        evidence_text_sha256=_sha(exact),
        start_seconds_decimal=None,
        end_seconds_decimal=None,
        page_number=None,
        frame_start=None,
        frame_end=None,
        evidence_metadata_json="{}",
        created_at=NOW,
    )
    segment = SegmentsRow(
        id="segment-a",
        representation_id="representation-a",
        segment_index=0,
        text_inline=segment_text,
        text_sha256=_sha(segment_text),
        materialization_status="inline",
        representation_char_start=0,
        representation_char_end=len(segment_text),
        start_seconds_decimal=None,
        end_seconds_decimal=None,
        page_number=None,
        frame_start=None,
        frame_end=None,
        review_status="accepted",
        metadata_json="{}",
        created_at=NOW,
    )
    link = ClaimEvidenceLinksRow("claim-a", "evidence-a", 0, "supports_source_claim", NOW)
    logical_evidence, logical_link = evidence_from_collector_v1(
        claim=claim,
        link=link,
        evidence=evidence,
        segment=segment,
    )
    assert logical_evidence.evidence_text == exact
    assert logical_evidence.span_start == start
    assert logical_link.role == "primary"

    logical_claim = claim_from_collector_v1(
        source_claim=claim,
        passage_id=segment.id,
        source_text=exact,
        subject_surface="algae",
        predicate_key="grows_on",
        object_surface="plants",
        subject_object_id=None,
        object_object_id=None,
        value_type="relation",
        scalar_value=None,
        text_value=None,
        lower_bound=None,
        upper_bound=None,
        unit_key=None,
        applicability_scope_id=None,
        extraction_method="semantic_candidate",
    )
    assert logical_claim.review_status == "pending"
    assert logical_claim.source_text == exact


def test_bridge_rejects_non_atomic_collector_claim() -> None:
    text = "broad statement"
    claim = SourceClaimsRow(
        id="claim-broad",
        source_id="source-a",
        representation_id=None,
        parent_claim_id=None,
        claim_layer="extracted",
        claim_text=text,
        claim_text_sha256=_sha(text),
        claim_kind=None,
        semantic_type=None,
        qualifiers_json="{}",
        extraction_confidence_decimal=None,
        source_claim_effective_text_sha256=_sha(text),
        notes="",
        initial_review_status="pending",
        created_at=NOW,
    )
    with pytest.raises(ValueError, match="atomic"):
        claim_from_collector_v1(
            source_claim=claim,
            passage_id="segment",
            source_text=text,
            subject_surface="subject",
            predicate_key="associated_with",
            object_surface="object",
            subject_object_id=None,
            object_object_id=None,
            value_type="relation",
            scalar_value=None,
            text_value=None,
            lower_bound=None,
            upper_bound=None,
            unit_key=None,
            applicability_scope_id=None,
            extraction_method="semantic_candidate",
        )
