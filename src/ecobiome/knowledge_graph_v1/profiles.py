"""Calculated N10 profiles derived from reviewed Evidence Graph state."""
from __future__ import annotations

from dataclasses import dataclass

from .graph import EvidenceGraphV1, EvidenceGraphV1Error


@dataclass(frozen=True, slots=True)
class ProfileRelationV1:
    relation_id: str
    predicate_key: str
    object_object_id: str | None
    scalar_value: str | None
    text_value: str | None
    unit_key: str | None
    applicability_scope_id: str | None
    supporting_claim_ids: tuple[str, ...]
    contradicting_claim_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class KnowledgeObjectProfileV1:
    knowledge_object_id: str
    canonical_label: str
    object_type: str
    relations: tuple[ProfileRelationV1, ...]
    image_asset_ids: tuple[str, ...]


def build_knowledge_object_profile_v1(
    graph: EvidenceGraphV1,
    knowledge_object_id: str,
) -> KnowledgeObjectProfileV1:
    """Build a profile from graph edges; never persist or synthesize opaque prose."""
    knowledge_object = graph.objects.get(knowledge_object_id)
    if knowledge_object is None:
        raise EvidenceGraphV1Error(f"unknown knowledge object: {knowledge_object_id}")

    projected: list[ProfileRelationV1] = []
    for relation in sorted(graph.relations.values(), key=lambda item: item.id):
        if relation.subject_object_id != knowledge_object_id:
            continue
        links = graph.accepted_relation_links(relation.id)
        if not links:
            continue
        supporting = tuple(sorted(link.claim_id for link in links if link.stance == "supports"))
        contradicting = tuple(sorted(link.claim_id for link in links if link.stance == "contradicts"))
        projected.append(
            ProfileRelationV1(
                relation_id=relation.id,
                predicate_key=relation.predicate_key,
                object_object_id=relation.object_object_id,
                scalar_value=relation.scalar_value,
                text_value=relation.text_value,
                unit_key=relation.unit_key,
                applicability_scope_id=relation.applicability_scope_id,
                supporting_claim_ids=supporting,
                contradicting_claim_ids=contradicting,
            )
        )

    image_ids = tuple(
        link.image_asset_id
        for link in sorted(
            (item for item in graph.object_images if item.knowledge_object_id == knowledge_object_id),
            key=lambda item: (item.display_order, item.image_asset_id),
        )
    )
    return KnowledgeObjectProfileV1(
        knowledge_object_id=knowledge_object.id,
        canonical_label=knowledge_object.canonical_label,
        object_type=knowledge_object.object_type,
        relations=tuple(projected),
        image_asset_ids=image_ids,
    )
