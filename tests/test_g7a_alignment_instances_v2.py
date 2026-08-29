from __future__ import annotations

from dataclasses import replace

import pytest

from ecobiome.simulation.g7a_alignment_instances_v2 import (
    G7A_ALIGNMENT_V2_SELECTIONS,
    G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2,
    G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION,
    G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SHA256,
    G7A_NITROGEN_OXIDATION_ALIGNMENT_V2,
    G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION,
    G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SHA256,
    HumanReviewedAlignmentV2SelectionError,
)


def test_human_review_freezes_exact_queue_policy_identities() -> None:
    oxidation = G7A_NITROGEN_OXIDATION_ALIGNMENT_V2
    assimilation = G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2

    assert oxidation.canonical_sha256 == G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SHA256
    assert oxidation.canonical_sha256 == (
        "d20e41bac0fafa83e34a7f564e2952be75758e487ebce53ab75661fc0a940115"
    )
    assert oxidation.base_policy_v1.canonical_sha256 == (
        "85ff14d808c2526b7422f523c500fd7bb8026bfee9b2663429752484d98a64c9"
    )
    assert oxidation.evaluation_scope_sha256 == (
        "f673fb12a5234af0bc2857660624555c9b5340255047aca71333c91877f6de2b"
    )

    assert assimilation.canonical_sha256 == (
        G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SHA256
    )
    assert assimilation.canonical_sha256 == (
        "3b516cb2dd8968c2f714f979678da4ee64d79608fe33524287ace5f99a8ab14f"
    )
    assert assimilation.base_policy_v1.canonical_sha256 == (
        "046e5cfff4d59756b8c391b073932f112b46f913b390aa39e41e8629c6067221"
    )
    assert assimilation.evaluation_scope_sha256 == (
        "00d4df977ea146ed1208bec93d73ea20b76c26b5276458bb6ef748a3f905484b"
    )


def test_human_review_accepts_both_without_automatic_attachment() -> None:
    assert len(G7A_ALIGNMENT_V2_SELECTIONS) == 2
    assert {item.policy.name for item in G7A_ALIGNMENT_V2_SELECTIONS} == {
        "g7a-nitrogen-oxidation-mechanism-alignment-v2",
        "g7a-nitrogen-assimilation-mechanism-alignment-v2",
    }

    for selection in G7A_ALIGNMENT_V2_SELECTIONS:
        payload = selection.canonical_payload()
        assert selection.decision == "accept"
        assert selection.review_status == "reviewed_confirmed"
        assert selection.reviewed_by == "human"
        assert selection.automatic_attachment is False
        assert payload["automatic_attachment"] is False
        assert selection.policy.canonical_payload()["automatic_acceptance"] is False
        assert selection.policy.canonical_payload()["automatic_attachment"] is False


def test_accepted_instances_preserve_contextual_ammonium_abstraction() -> None:
    oxidation = G7A_NITROGEN_OXIDATION_ALIGNMENT_V2.model_semantic_bridge
    assimilation = G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2.model_semantic_bridge

    assert oxidation.source_component_id == "reduced_inorganic_nitrogen"
    assert oxidation.target_component_id == "oxidized_inorganic_nitrogen"
    assert assimilation.source_component_id == "dissolved_inorganic_nitrogen"
    assert assimilation.target_component_id == "biological_nitrogen"
    assert oxidation.assertion_ref != assimilation.assertion_ref


def test_assimilation_acceptance_preserves_biological_compartment_guard() -> None:
    bridge = G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2.model_semantic_bridge
    target = next(
        item
        for item in bridge.participant_bindings
        if item.assertion_role == "target_nitrogen_pool"
    )

    assert target.entity_id == "entity-pubchem-cid-5961"
    assert "Lemna gibba biological material" in target.context
    assert "excludes dissolved or extracellular glutamine" in target.context


def test_selection_rejects_automatic_attachment() -> None:
    with pytest.raises(
        HumanReviewedAlignmentV2SelectionError,
        match="automatic_attachment must remain false",
    ):
        replace(
            G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION,
            automatic_attachment=True,
        )


def test_two_selections_are_distinct_and_transitively_bound() -> None:
    oxidation = G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION
    assimilation = G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION

    assert oxidation.canonical_sha256 != assimilation.canonical_sha256
    assert oxidation.policy.bridge_sha256 != assimilation.policy.bridge_sha256
    assert oxidation.policy.assertion_ref != assimilation.policy.assertion_ref
