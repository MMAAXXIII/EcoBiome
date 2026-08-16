"""Strict bridge from existing Collector persistence rows into N10 logical objects."""
from __future__ import annotations

import hashlib

from ecobiome.knowledge_persistence.contracts import (
    ClaimEvidenceLinksRow,
    SegmentsRow,
    SourceClaimsRow,
    SourceEvidenceRow,
)

from .models import Claim, ClaimEvidence, Evidence


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def evidence_from_collector_v1(
    *,
    claim: SourceClaimsRow,
    link: ClaimEvidenceLinksRow,
    evidence: SourceEvidenceRow,
    segment: SegmentsRow,
) -> tuple[Evidence, ClaimEvidence]:
    """Reconstruct exact Evidence text from the existing Segment span, fail-closed."""
    if link.claim_id != claim.id or link.evidence_id != evidence.id:
        raise ValueError("Collector Claim/Evidence identity mismatch")
    if evidence.segment_id != segment.id:
        raise ValueError("Collector Evidence/Segment identity mismatch")
    if segment.text_inline is None:
        raise ValueError("Collector Segment must materialize text_inline for exact N10 Evidence")
    if evidence.segment_char_start < 0 or evidence.segment_char_end > len(segment.text_inline):
        raise ValueError("Collector Evidence span lies outside Segment text")
    exact_text = segment.text_inline[evidence.segment_char_start : evidence.segment_char_end]
    if not exact_text:
        raise ValueError("Collector Evidence span is empty")
    if _sha256_text(exact_text) != evidence.evidence_text_sha256:
        raise ValueError("Collector Evidence SHA does not match exact Segment substring")
    if link.link_role != "supports_source_claim":
        raise ValueError(f"unsupported Collector Claim/Evidence role: {link.link_role!r}")
    logical_evidence = Evidence(
        id=evidence.id,
        source_id=claim.source_id,
        passage_id=segment.id,
        span_start=evidence.segment_char_start,
        span_end=evidence.segment_char_end,
        evidence_text=exact_text,
        evidence_sha256=evidence.evidence_text_sha256,
        evidence_type="primary",
    )
    logical_link = ClaimEvidence(
        claim_id=claim.id,
        evidence_id=evidence.id,
        evidence_order=link.evidence_order,
        role="primary",
        created_at=link.created_at,
    )
    return logical_evidence, logical_link


def claim_from_collector_v1(
    *,
    source_claim: SourceClaimsRow,
    passage_id: str,
    source_text: str,
    subject_surface: str,
    predicate_key: str,
    object_surface: str | None,
    subject_object_id: str | None,
    object_object_id: str | None,
    value_type: str,
    scalar_value: str | None,
    text_value: str | None,
    lower_bound: str | None,
    upper_bound: str | None,
    unit_key: str | None,
    applicability_scope_id: str | None,
    extraction_method: str,
) -> Claim:
    """Project one already-atomic Collector Claim without inventing semantic content."""
    if source_claim.claim_layer != "atomic":
        raise ValueError("N10 projection requires an atomic Collector Claim")
    expected_sha = source_claim.source_claim_effective_text_sha256 or source_claim.claim_text_sha256
    if _sha256_text(source_text) != expected_sha:
        raise ValueError("N10 source_text does not match Collector effective Claim SHA")
    return Claim(
        id=source_claim.id,
        passage_id=passage_id,
        source_text=source_text,
        subject_surface=subject_surface,
        predicate_key=predicate_key,
        object_surface=object_surface,
        subject_object_id=subject_object_id,
        object_object_id=object_object_id,
        value_type=value_type,
        scalar_value=scalar_value,
        text_value=text_value,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        unit_key=unit_key,
        applicability_scope_id=applicability_scope_id,
        extraction_method=extraction_method,
        extraction_confidence=source_claim.extraction_confidence_decimal,
        created_at=source_claim.created_at,
        review_status="pending",
    )
