from __future__ import annotations

import hashlib

import pytest

from ecobiome.knowledge_graph_v1 import (
    Claim,
    ClaimEvidence,
    ClaimReviewEvent,
    Evidence,
    EvidenceGraphV1,
    EvidenceGraphV1Error,
    ImageAsset,
    KnowledgeObject,
    KnowledgeObjectImage,
    KnowledgeRelation,
    LivingEntity,
    Morphotype,
    RelationClaimLink,
    build_knowledge_object_profile_v1,
)

NOW = "2026-08-16T15:00:00+00:00"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _seed_claim(graph: EvidenceGraphV1, claim_id: str, relation_id: str, stance: str) -> None:
    text = "Filamentous green algae may occur on submerged plant surfaces."
    evidence = Evidence("evidence-" + claim_id, "source-" + claim_id, "segment-" + claim_id, 0, len(text), text, _sha(text), "primary")
    claim = Claim(
        id=claim_id,
        passage_id=evidence.passage_id,
        source_text=text,
        subject_surface="filamentous green algae",
        predicate_key="grows_on",
        object_surface="submerged plant surfaces",
        subject_object_id="algae-morphotype",
        object_object_id="aquatic-plants",
        value_type="relation",
        scalar_value=None,
        text_value=None,
        lower_bound=None,
        upper_bound=None,
        unit_key=None,
        applicability_scope_id=None,
        extraction_method="human_test_fixture",
        extraction_confidence=None,
        created_at=NOW,
    )
    graph.add_claim_bundle(
        claim,
        (evidence,),
        (ClaimEvidence(claim.id, evidence.id, 0, "primary", NOW),),
    )
    graph.review_claim(ClaimReviewEvent("review-" + claim_id, claim.id, "accept", "human", "fixture review", NOW))
    graph.link_relation_claim(RelationClaimLink(relation_id, claim.id, stance))


def test_algae_morphotype_remains_distinct_from_taxonomy_and_profile_is_graph_derived() -> None:
    graph = EvidenceGraphV1()
    algae = KnowledgeObject("algae-morphotype", "morphotype", "Green filamentous algae", "green-filamentous-algae", NOW)
    plants = KnowledgeObject("aquatic-plants", "living_entity", "Aquatic plants", "aquatic-plants", NOW)
    graph.add_object(algae)
    graph.add_object(plants)
    morphotype = Morphotype(
        knowledge_object_id=algae.id,
        morphology="filamentous",
        color="green",
        texture="thread-like",
        typical_location="submerged surfaces",
        differential_features=("filaments", "green coloration"),
    )
    assert morphotype.knowledge_object_id == algae.id
    living = LivingEntity(
        knowledge_object_id="taxon-candidate",
        identification_level="unknown",
    )
    assert living.taxon_name is None
    with pytest.raises(ValueError, match="identification_level"):
        LivingEntity("bad", "morphotype")

    relation = KnowledgeRelation("relation-grow", algae.id, "grows_on", plants.id, None, None, None, None, NOW)
    graph.add_relation(relation)
    _seed_claim(graph, "claim-support", relation.id, "supports")
    _seed_claim(graph, "claim-contradict", relation.id, "contradicts")
    profile = build_knowledge_object_profile_v1(graph, algae.id)
    assert len(profile.relations) == 1
    assert profile.relations[0].supporting_claim_ids == ("claim-support",)
    assert profile.relations[0].contradicting_claim_ids == ("claim-contradict",)
    assert not hasattr(profile, "opaque_description")


def test_image_requires_explicit_license_verification_and_permission() -> None:
    graph = EvidenceGraphV1()
    graph.add_object(KnowledgeObject("algae", "morphotype", "Algae", "algae", NOW))
    asset = ImageAsset(
        id="image-a",
        source_url="https://example.org/page",
        image_url="https://example.org/image.jpg",
        creator="Example creator",
        title="Example algae",
        license="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        attribution="Example creator, CC BY 4.0",
        retrieved_at=NOW,
        sha256="a" * 64,
        usage_permission="allowed",
        verification_status="unverified",
    )
    graph.add_image(asset)
    with pytest.raises(EvidenceGraphV1Error, match="license"):
        graph.attach_image(KnowledgeObjectImage("algae", asset.id))
