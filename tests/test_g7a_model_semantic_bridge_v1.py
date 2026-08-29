from __future__ import annotations

from dataclasses import replace

import pytest

from ecobiome.simulation.model_semantic_bridge_v1 import (
    G7A_NITROGEN_ASSIMILATION_BRIDGE_V1,
    G7A_NITROGEN_OXIDATION_BRIDGE_V1,
    REVIEWED_MODEL_SEMANTIC_BRIDGE_DESIGN_SHA256,
    ModelSemanticParticipantBindingV1,
    ReviewedModelSemanticBridgeV1Error,
)


def test_adopted_bridge_design_identity_and_exact_bridge_shas() -> None:
    assert REVIEWED_MODEL_SEMANTIC_BRIDGE_DESIGN_SHA256 == (
        "5d6ea5088bb7b1b22b44ee56e8644f1860cbe6556b1e4139d5c2989ea8515157"
    )
    assert G7A_NITROGEN_OXIDATION_BRIDGE_V1.canonical_sha256 == (
        "82f4ae564dacf41b57172febd09aa1bc7db9ad6cfaa0bb7899bb1b7a5d359b6c"
    )
    assert G7A_NITROGEN_ASSIMILATION_BRIDGE_V1.canonical_sha256 == (
        "a0a9813dbdb2c54d888a9f33c7789823bcfc8054579b7d5193d99cf8a80dafcd"
    )


def test_ammonium_is_contextually_abstracted_not_globally_identified() -> None:
    oxidation = next(
        item
        for item in G7A_NITROGEN_OXIDATION_BRIDGE_V1.participant_bindings
        if item.entity_id == "entity-pubchem-cid-223"
    )
    assimilation = next(
        item
        for item in G7A_NITROGEN_ASSIMILATION_BRIDGE_V1.participant_bindings
        if item.entity_id == "entity-pubchem-cid-223"
    )

    assert oxidation.model_component_id == "reduced_inorganic_nitrogen"
    assert assimilation.model_component_id == "dissolved_inorganic_nitrogen"
    assert oxidation.mapping_kind == "model_abstraction_membership"
    assert assimilation.mapping_kind == "model_abstraction_membership"

    semantics = G7A_NITROGEN_OXIDATION_BRIDGE_V1.canonical_payload()["semantics"]
    assert semantics["identity"] is False
    assert semantics["equivalence"] is False
    assert semantics["global_taxonomy"] is False


def test_assimilation_bridge_retains_biological_compartment_context() -> None:
    target = next(
        item
        for item in G7A_NITROGEN_ASSIMILATION_BRIDGE_V1.participant_bindings
        if item.assertion_role == "target_nitrogen_pool"
    )
    agent = G7A_NITROGEN_ASSIMILATION_BRIDGE_V1.context_participants[0]

    assert target.entity_id == "entity-pubchem-cid-5961"
    assert target.model_component_id == "biological_nitrogen"
    assert "Lemna gibba biological material" in target.context
    assert "excludes dissolved or extracellular glutamine" in target.context
    assert agent.entity_id == "entity-ipni-526178-1"
    assert agent.assertion_role == "process_agent"


def test_bridge_rejects_identity_or_equivalence_mapping_kind() -> None:
    with pytest.raises(
        ReviewedModelSemanticBridgeV1Error,
        match="identity/equivalence mappings are forbidden",
    ):
        ModelSemanticParticipantBindingV1(
            assertion_role="source_material",
            entity_id="entity-pubchem-cid-223",
            entity_revision=1,
            model_component_id="reduced_inorganic_nitrogen",
            mapping_kind="identity",
            context="invalid global identity",
        )


def test_bridge_rejects_evaluation_outside_exact_source_target_scope() -> None:
    bridge = G7A_NITROGEN_OXIDATION_BRIDGE_V1
    with pytest.raises(
        ReviewedModelSemanticBridgeV1Error,
        match="target_component_id",
    ):
        bridge.require_evaluation_match(
            process_id="nitrogen_transformation_extent_v1",
            process_version="1",
            role="mechanism",
            parameters={
                "source_component_id": "reduced_inorganic_nitrogen",
                "target_component_id": "biological_nitrogen",
            },
        )


def test_bridge_rejects_role_that_is_both_material_and_context() -> None:
    bridge = G7A_NITROGEN_OXIDATION_BRIDGE_V1
    context = replace(
        bridge.context_participants[0],
        assertion_role="source_material",
    )
    with pytest.raises(
        ReviewedModelSemanticBridgeV1Error,
        match="both material-mapped and context-only",
    ):
        replace(bridge, context_participants=(context,))
