"""Fail-closed in-memory Evidence Graph V1 for N10 read-model construction."""
from __future__ import annotations

from dataclasses import replace
from typing import TypeVar

from .models import (
    ApplicabilityScope,
    Claim,
    ClaimEvidence,
    ClaimRelation,
    ClaimReviewEvent,
    Evidence,
    ImageAsset,
    KnowledgeObject,
    KnowledgeObjectImage,
    KnowledgeRelation,
    RelationClaimLink,
    SourceDependency,
)

_T = TypeVar("_T")


class EvidenceGraphV1Error(ValueError):
    """Raised when an N10 graph invariant would be violated."""


_TRANSITIONS: dict[str, dict[str, str]] = {
    "pending": {"accept": "accepted", "reject": "rejected"},
    "accepted": {"reject": "rejected", "supersede": "superseded"},
    "rejected": {"reopen": "pending"},
    "superseded": {"reopen": "pending"},
}


class EvidenceGraphV1:
    """Persistence-neutral graph that never upgrades evidence to truth implicitly."""

    def __init__(self) -> None:
        self.scopes: dict[str, ApplicabilityScope] = {}
        self.evidence: dict[str, Evidence] = {}
        self.claims: dict[str, Claim] = {}
        self.claim_evidence: list[ClaimEvidence] = []
        self.claim_reviews: list[ClaimReviewEvent] = []
        self.objects: dict[str, KnowledgeObject] = {}
        self.relations: dict[str, KnowledgeRelation] = {}
        self.relation_claim_links: list[RelationClaimLink] = []
        self.claim_relations: dict[str, ClaimRelation] = {}
        self.source_dependencies: dict[str, SourceDependency] = {}
        self.images: dict[str, ImageAsset] = {}
        self.object_images: list[KnowledgeObjectImage] = []

    @staticmethod
    def _insert_unique(mapping: dict[str, _T], key: str, value: _T, label: str) -> None:
        existing = mapping.get(key)
        if existing is None:
            mapping[key] = value
            return
        if existing != value:
            raise EvidenceGraphV1Error(f"duplicate {label} id with conflicting payload: {key}")

    def add_scope(self, scope: ApplicabilityScope) -> None:
        self._insert_unique(self.scopes, scope.id, scope, "scope")

    def add_object(self, knowledge_object: KnowledgeObject) -> None:
        self._insert_unique(self.objects, knowledge_object.id, knowledge_object, "knowledge object")

    def add_evidence(self, evidence: Evidence) -> None:
        self._insert_unique(self.evidence, evidence.id, evidence, "Evidence")

    def add_claim_bundle(
        self,
        claim: Claim,
        evidence_rows: tuple[Evidence, ...],
        links: tuple[ClaimEvidence, ...],
    ) -> None:
        if claim.review_status != "pending":
            raise EvidenceGraphV1Error("new N10 Claims must start pending")
        if claim.applicability_scope_id is not None and claim.applicability_scope_id not in self.scopes:
            raise EvidenceGraphV1Error("Claim references an unknown ApplicabilityScope")
        if not evidence_rows or not links:
            raise EvidenceGraphV1Error("every Claim requires exact primary Evidence")
        evidence_by_id = {row.id: row for row in evidence_rows}
        if len(evidence_by_id) != len(evidence_rows):
            raise EvidenceGraphV1Error("duplicate Evidence rows in Claim bundle")
        linked_ids: set[str] = set()
        primary = False
        for link in links:
            if link.claim_id != claim.id:
                raise EvidenceGraphV1Error("ClaimEvidence link belongs to a different Claim")
            if link.evidence_id not in evidence_by_id:
                raise EvidenceGraphV1Error("ClaimEvidence references Evidence outside the bundle")
            if link.evidence_id in linked_ids:
                raise EvidenceGraphV1Error("ClaimEvidence contains a duplicate Evidence link")
            linked_ids.add(link.evidence_id)
            if link.role == "primary" and evidence_by_id[link.evidence_id].evidence_type == "primary":
                primary = True
        if not primary:
            raise EvidenceGraphV1Error("every Claim requires at least one exact primary Evidence")
        if linked_ids != set(evidence_by_id):
            raise EvidenceGraphV1Error("every Evidence row in a Claim bundle must be linked")
        if claim.id in self.claims and self.claims[claim.id] != claim:
            raise EvidenceGraphV1Error(f"conflicting Claim identity: {claim.id}")
        if claim.id in self.claims:
            return
        for row in evidence_rows:
            self.add_evidence(row)
        self.claims[claim.id] = claim
        self.claim_evidence.extend(sorted(links, key=lambda item: (item.evidence_order, item.evidence_id)))

    def review_claim(self, event: ClaimReviewEvent) -> Claim:
        claim = self.claims.get(event.claim_id)
        if claim is None:
            raise EvidenceGraphV1Error(f"unknown Claim: {event.claim_id}")
        if any(existing.id == event.id for existing in self.claim_reviews):
            raise EvidenceGraphV1Error(f"Claim review event is append-only and id already exists: {event.id}")
        next_status = _TRANSITIONS.get(claim.review_status, {}).get(event.decision)
        if next_status is None:
            raise EvidenceGraphV1Error(
                f"review transition {claim.review_status!r} -> {event.decision!r} is not allowed"
            )
        updated = replace(claim, review_status=next_status)
        self.claims[claim.id] = updated
        self.claim_reviews.append(event)
        return updated

    def add_relation(self, relation: KnowledgeRelation) -> None:
        if relation.subject_object_id not in self.objects:
            raise EvidenceGraphV1Error("KnowledgeRelation subject is unknown")
        if relation.object_object_id is not None and relation.object_object_id not in self.objects:
            raise EvidenceGraphV1Error("KnowledgeRelation object is unknown")
        if relation.applicability_scope_id is not None and relation.applicability_scope_id not in self.scopes:
            raise EvidenceGraphV1Error("KnowledgeRelation references an unknown ApplicabilityScope")
        self._insert_unique(self.relations, relation.id, relation, "KnowledgeRelation")

    def link_relation_claim(self, link: RelationClaimLink) -> None:
        if link.relation_id not in self.relations:
            raise EvidenceGraphV1Error("RelationClaimLink references an unknown relation")
        claim = self.claims.get(link.claim_id)
        if claim is None:
            raise EvidenceGraphV1Error("RelationClaimLink references an unknown Claim")
        if claim.review_status != "accepted":
            raise EvidenceGraphV1Error("only accepted Claims may support/contradict reusable knowledge")
        if link in self.relation_claim_links:
            return
        self.relation_claim_links.append(link)

    def add_claim_relation(self, relation: ClaimRelation) -> None:
        if relation.claim_a_id not in self.claims or relation.claim_b_id not in self.claims:
            raise EvidenceGraphV1Error("ClaimRelation references unknown Claims")
        if relation.applicability_scope_id is not None and relation.applicability_scope_id not in self.scopes:
            raise EvidenceGraphV1Error("ClaimRelation references an unknown ApplicabilityScope")
        self._insert_unique(self.claim_relations, relation.id, relation, "ClaimRelation")

    def add_source_dependency(self, dependency: SourceDependency) -> None:
        self._insert_unique(self.source_dependencies, dependency.id, dependency, "SourceDependency")

    def add_image(self, image: ImageAsset) -> None:
        self._insert_unique(self.images, image.id, image, "ImageAsset")

    def attach_image(self, link: KnowledgeObjectImage) -> None:
        if link.knowledge_object_id not in self.objects:
            raise EvidenceGraphV1Error("KnowledgeObjectImage references an unknown object")
        image = self.images.get(link.image_asset_id)
        if image is None:
            raise EvidenceGraphV1Error("KnowledgeObjectImage references an unknown image")
        if not image.attachable:
            raise EvidenceGraphV1Error("image license/use permission is not explicitly verified")
        if link not in self.object_images:
            self.object_images.append(link)

    def accepted_relation_links(self, relation_id: str) -> tuple[RelationClaimLink, ...]:
        return tuple(
            link
            for link in self.relation_claim_links
            if link.relation_id == relation_id
            and self.claims[link.claim_id].review_status == "accepted"
        )

    def independent_source_pair_count(self) -> int:
        """Count only explicitly reviewed independent pairs; unknown never counts."""
        pairs = {
            tuple(sorted((item.source_a_id, item.source_b_id)))
            for item in self.source_dependencies.values()
            if item.counts_as_independent
        }
        return len(pairs)
