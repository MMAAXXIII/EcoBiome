from __future__ import annotations

import hashlib

import pytest

from ecobiome.knowledge_graph_v1 import (
    ApplicabilityScope,
    Claim,
    ClaimEvidence,
    ClaimRelation,
    ClaimReviewEvent,
    Evidence,
    EvidenceGraphV1,
    EvidenceGraphV1Error,
    KnowledgeObject,
    KnowledgeRelation,
    RelationClaimLink,
    SourceDependency,
)

NOW = "2026-08-16T15:00:00+00:00"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _evidence(evidence_id: str, text: str = "Green filamentous algae were observed on plants.") -> Evidence:
    return Evidence(
        id=evidence_id,
        source_id="source-a",
        passage_id="segment-a",
        span_start=0,
        span_end=len(text),
        evidence_text=text,
        evidence_sha256=_sha(text),
        evidence_type="primary",
    )


def _claim(claim_id: str, scope_id: str | None = None) -> Claim:
    return Claim(
        id=claim_id,
        passage_id="segment-a",
        source_text="Green filamentous algae were observed on plants.",
        subject_surface="green filamentous algae",
        predicate_key="grows_on",
        object_surface="plants",
        subject_object_id="algae",
        object_object_id="plants",
        value_type="relation",
        scalar_value=None,
        text_value=None,
        lower_bound=None,
        upper_bound=None,
        unit_key=None,
        applicability_scope_id=scope_id,
        extraction_method="collector_semantic_candidate",
        extraction_confidence="0.84",
        created_at=NOW,
    )


def _add_claim(graph: EvidenceGraphV1, claim: Claim, evidence_id: str) -> None:
    evidence = _evidence(evidence_id)
    graph.add_claim_bundle(
        claim,
        (evidence,),
        (
            ClaimEvidence(
                claim_id=claim.id,
                evidence_id=evidence.id,
                evidence_order=0,
                role="primary",
                created_at=NOW,
            ),
        ),
    )


def test_claim_requires_exact_primary_evidence_and_starts_pending() -> None:
    graph = EvidenceGraphV1()
    claim = _claim("claim-a")
    with pytest.raises(EvidenceGraphV1Error, match="primary Evidence"):
        graph.add_claim_bundle(claim, (), ())
    _add_claim(graph, claim, "evidence-a")
    assert graph.claims[claim.id].review_status == "pending"


def test_evidence_hash_and_span_fail_closed() -> None:
    text = "exact passage"
    with pytest.raises(ValueError, match="SHA-256"):
        Evidence(
            id="evidence",
            source_id="source",
            passage_id="segment",
            span_start=0,
            span_end=len(text),
            evidence_text=text,
            evidence_sha256="0" * 64,
            evidence_type="primary",
        )


def test_claim_review_is_append_only_and_reopen_is_controlled() -> None:
    graph = EvidenceGraphV1()
    claim = _claim("claim-a")
    _add_claim(graph, claim, "evidence-a")
    rejected = ClaimReviewEvent(
        id="review-1",
        claim_id=claim.id,
        decision="reject",
        reviewer="human",
        rationale="scope not established",
        reviewed_at=NOW,
    )
    assert graph.review_claim(rejected).review_status == "rejected"
    with pytest.raises(EvidenceGraphV1Error, match="already exists"):
        graph.review_claim(rejected)
    reopened = ClaimReviewEvent(
        id="review-2",
        claim_id=claim.id,
        decision="reopen",
        reviewer="human",
        rationale="new exact evidence will be reviewed",
        reviewed_at="2026-08-16T15:01:00+00:00",
    )
    assert graph.review_claim(reopened).review_status == "pending"


def test_unspecified_scope_means_unknown_not_universal() -> None:
    scope = ApplicabilityScope(id="scope-unknown")
    assert scope.is_unspecified is True
    assert scope.canonical_payload()["missing_dimensions_mean_unknown"] is True


def test_numeric_claim_cannot_self_declare_threshold() -> None:
    base = _claim("claim-threshold")
    payload = {field: getattr(base, field) for field in base.__dataclass_fields__}
    payload["value_type"] = "threshold"
    payload["scalar_value"] = "5"
    with pytest.raises(ValueError, match="threshold"):
        Claim(**payload)


def test_contradiction_is_retained_and_unknown_source_dependency_is_not_independent() -> None:
    graph = EvidenceGraphV1()
    graph.add_object(KnowledgeObject("algae", "living_entity", "Green algae", "green-algae", NOW))
    graph.add_object(KnowledgeObject("plants", "living_entity", "Aquatic plants", "aquatic-plants", NOW))
    for claim_id, evidence_id in (("claim-support", "evidence-support"), ("claim-contradict", "evidence-contradict")):
        claim = _claim(claim_id)
        _add_claim(graph, claim, evidence_id)
        graph.review_claim(
            ClaimReviewEvent(
                id=f"review-{claim_id}",
                claim_id=claim_id,
                decision="accept",
                reviewer="human",
                rationale="exact source reviewed",
                reviewed_at=NOW,
            )
        )
    relation = KnowledgeRelation(
        id="relation-a",
        subject_object_id="algae",
        predicate_key="grows_on",
        object_object_id="plants",
        scalar_value=None,
        text_value=None,
        unit_key=None,
        applicability_scope_id=None,
        created_at=NOW,
    )
    graph.add_relation(relation)
    graph.link_relation_claim(RelationClaimLink("relation-a", "claim-support", "supports"))
    graph.link_relation_claim(RelationClaimLink("relation-a", "claim-contradict", "contradicts"))
    links = graph.accepted_relation_links("relation-a")
    assert {link.stance for link in links} == {"supports", "contradicts"}

    graph.add_claim_relation(
        ClaimRelation(
            id="claim-relation",
            claim_a_id="claim-support",
            claim_b_id="claim-contradict",
            relation_type="contradicts",
            scope_overlap="partial",
            applicability_scope_id=None,
            review_status="accepted",
            created_at=NOW,
        )
    )
    assert graph.claim_relations["claim-relation"].scope_overlap == "partial"

    graph.add_source_dependency(
        SourceDependency(
            id="dependency-unknown",
            source_a_id="source-a",
            source_b_id="source-b",
            dependency_type="unknown",
            review_status="accepted",
            detection_method="not_established",
            detection_confidence=None,
            created_at=NOW,
        )
    )
    assert graph.independent_source_pair_count() == 0
