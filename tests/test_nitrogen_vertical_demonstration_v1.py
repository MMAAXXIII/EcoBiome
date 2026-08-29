from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

import pytest

from ecobiome.knowledge_persistence.serialization import (
    canonical_json_text,
    canonical_sha256,
)
from ecobiome.reasoning.auditable_ecosystem_explanation_v1 import (
    build_auditable_ecosystem_explanation_v1,
)
from ecobiome.reasoning.nitrogen_vertical_demonstration_v1 import (
    NitrogenVerticalDemonstrationV1Error,
    ScientificFoundationSnapshotRefV1,
    build_nitrogen_vertical_demonstration_v1,
)
from ecobiome.simulation.ecosystem_state_v1 import (
    CanonicalQuantityV1,
    EcosystemStateV1,
    QuantityBasisV1,
)
from ecobiome.simulation.g7a_alignment_instances_v2 import (
    G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION,
    G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION,
)
from ecobiome.simulation.material_balance_v1 import (
    MATERIAL_INVENTORY_VARIABLE_ID,
    evaluate_nitrogen_transformation_extent_v1,
)
from ecobiome.simulation.process_v1 import ProcessScientificSupportV1
from ecobiome.simulation.reviewed_support_attachment_receipt_v1 import (
    ReviewedSupportAttachmentReceiptV1,
)
from ecobiome.simulation.scientific_alignment_v1 import (
    attach_scientific_supports_v1,
)

_OXIDATION_SELECTION_SHA = (
    "0e3c0806a04eea2a626c4a0b094e857d03662269959af7fb1cbb05153c1f7cf6"
)
_ASSIMILATION_SELECTION_SHA = (
    "e6f186018b8e7190fa90620ae15a6918a03218f14f9b05e6ee07248a0e2a677c"
)


def _support(selection: Any) -> ProcessScientificSupportV1:
    policy = selection.policy
    base = policy.base_policy_v1
    return ProcessScientificSupportV1(
        role=base.role,
        assertion_ref=policy.assertion_ref,
        alignment_class=base.alignment_class,
        epistemic_class=base.epistemic_class,
        alignment_policy_name=policy.name,
        alignment_policy_version=policy.version,
        alignment_policy_sha256=policy.canonical_sha256,
        evaluation_scope=base.evaluation_scope,
        evaluation_scope_sha256=base.evaluation_scope.canonical_sha256,
    )


def _receipt(
    *,
    receipt_id: str,
    pending: Any,
    attached: Any,
    selection: Any,
    selection_sha: str,
) -> ReviewedSupportAttachmentReceiptV1:
    support = attached.scientific_supports[0]
    policy = selection.policy
    return ReviewedSupportAttachmentReceiptV1(
        receipt_id=receipt_id,
        evaluation_id=attached.evaluation_id,
        pending_evaluation_sha256=pending.canonical_sha256,
        attached_evaluation_sha256=attached.canonical_sha256,
        support_sha256=canonical_sha256(support.canonical_payload()),
        assertion_ref=support.assertion_ref,
        alignment_policy_sha256=support.alignment_policy_sha256,
        evaluation_scope_sha256=support.evaluation_scope_sha256,
        bridge_id=policy.model_semantic_bridge.bridge_id,
        bridge_sha256=policy.bridge_sha256,
        selection_sha256=selection_sha,
        selection_payload_json=canonical_json_text(
            selection.canonical_payload()
        ),
    )


def _fixture():
    basis = QuantityBasisV1(
        kind="observation",
        reference_id="vertical-demo-observation",
    )
    start = EcosystemStateV1(
        profile_id="vertical-demo-profile",
        quantities=(
            CanonicalQuantityV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                value_decimal="10",
                unit="mg N",
                basis=basis,
                zone_id="water-zone-1",
                material_component_id="reduced_inorganic_nitrogen",
            ),
            CanonicalQuantityV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                value_decimal="2",
                unit="mg N",
                basis=basis,
                zone_id="water-zone-1",
                material_component_id="oxidized_inorganic_nitrogen",
            ),
            CanonicalQuantityV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                value_decimal="10",
                unit="mg N",
                basis=basis,
                zone_id="water-zone-1",
                material_component_id="dissolved_inorganic_nitrogen",
            ),
            CanonicalQuantityV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                value_decimal="2",
                unit="mg N",
                basis=basis,
                zone_id="water-zone-1",
                material_component_id="biological_nitrogen",
            ),
        ),
    )
    extent_basis = QuantityBasisV1(
        kind="scenario_default",
        reference_id="vertical-demo-explicit-extent",
    )
    intermediate, oxidation_pending = (
        evaluate_nitrogen_transformation_extent_v1(
            start,
            zone_id="water-zone-1",
            source_component_id="reduced_inorganic_nitrogen",
            target_component_id="oxidized_inorganic_nitrogen",
            extent_decimal="1",
            extent_unit="mg N",
            extent_basis=extent_basis,
            evaluation_id="vertical-demo-oxidation",
            scientific_assertion_refs=(
                G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION.policy.assertion_ref,
            ),
        )
    )
    end, assimilation_pending = (
        evaluate_nitrogen_transformation_extent_v1(
            intermediate,
            zone_id="water-zone-1",
            source_component_id="dissolved_inorganic_nitrogen",
            target_component_id="biological_nitrogen",
            extent_decimal="1",
            extent_unit="mg N",
            extent_basis=extent_basis,
            evaluation_id="vertical-demo-assimilation",
            scientific_assertion_refs=(
                G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION.policy.assertion_ref,
            ),
        )
    )
    oxidation = attach_scientific_supports_v1(
        oxidation_pending,
        (_support(G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION),),
    )
    assimilation = attach_scientific_supports_v1(
        assimilation_pending,
        (_support(G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION),),
    )
    receipts = (
        _receipt(
            receipt_id="vertical-demo-receipt-oxidation",
            pending=oxidation_pending,
            attached=oxidation,
            selection=G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION,
            selection_sha=_OXIDATION_SELECTION_SHA,
        ),
        _receipt(
            receipt_id="vertical-demo-receipt-assimilation",
            pending=assimilation_pending,
            attached=assimilation,
            selection=G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION,
            selection_sha=_ASSIMILATION_SELECTION_SHA,
        ),
    )
    auditable = build_auditable_ecosystem_explanation_v1(
        start,
        end,
        (oxidation, assimilation),
        reviewed_support_attachment_receipts=receipts,
    )
    snapshot = ScientificFoundationSnapshotRefV1(
        schema_version=6,
        design_sha256="a" * 64,
        database_sha256="b" * 64,
    )
    demo = build_nitrogen_vertical_demonstration_v1(
        demo_id="vertical-demo",
        starting_state=start,
        intermediate_state=intermediate,
        ending_state=end,
        evaluations=(oxidation, assimilation),
        auditable_explanation=auditable,
        scientific_foundation_snapshot=snapshot,
    )
    return (
        start,
        intermediate,
        end,
        oxidation,
        assimilation,
        auditable,
        snapshot,
        demo,
    )


def test_vertical_demo_is_deterministic_and_self_contained() -> None:
    *_, demo = _fixture()
    second = replace(demo)
    assert demo.canonical_sha256 == second.canonical_sha256
    payload = demo.canonical_payload()
    assert len(payload["process_steps"]) == 2
    assert payload["model_boundary"]["extent_is_explicit_input"] is True
    assert payload["model_boundary"]["kinetic_or_rate_model_present"] is False
    assert payload["model_boundary"]["forecast_claim"] is False
    assert all(
        step["explicit_extent"]["value"] == "1"
        for step in payload["process_steps"]
    )
    assert all(
        len(step["reviewed_attachment_receipts"]) == 1
        for step in payload["process_steps"]
    )


def test_vertical_demo_rejects_rate_parameter_key() -> None:
    (
        start,
        intermediate,
        end,
        oxidation,
        assimilation,
        auditable,
        snapshot,
        _,
    ) = _fixture()
    params = json.loads(oxidation.parameters_json)
    params["rate"] = {"value": "1", "unit": "mg N/h"}
    mutated = replace(
        oxidation,
        parameters_json=canonical_json_text(params),
    )
    with pytest.raises(
        NitrogenVerticalDemonstrationV1Error,
        match="rate/dt/kinetic parameters are forbidden",
    ):
        build_nitrogen_vertical_demonstration_v1(
            demo_id="rate-rejected",
            starting_state=start,
            intermediate_state=intermediate,
            ending_state=end,
            evaluations=(mutated, assimilation),
            auditable_explanation=auditable,
            scientific_foundation_snapshot=snapshot,
        )


def test_vertical_demo_rejects_wrong_transformation_order() -> None:
    (
        start,
        intermediate,
        end,
        oxidation,
        assimilation,
        auditable,
        snapshot,
        _,
    ) = _fixture()
    with pytest.raises(
        NitrogenVerticalDemonstrationV1Error,
        match="state identities are not contiguous|outside the frozen vertical scope",
    ):
        build_nitrogen_vertical_demonstration_v1(
            demo_id="wrong-order",
            starting_state=start,
            intermediate_state=intermediate,
            ending_state=end,
            evaluations=(assimilation, oxidation),
            auditable_explanation=auditable,
            scientific_foundation_snapshot=snapshot,
        )


def test_vertical_demo_rejects_derived_extent_basis() -> None:
    (
        start,
        intermediate,
        end,
        oxidation,
        assimilation,
        auditable,
        snapshot,
        _,
    ) = _fixture()
    params = json.loads(oxidation.parameters_json)
    params["extent_basis"]["kind"] = "derived"
    mutated = replace(
        oxidation,
        parameters_json=canonical_json_text(params),
    )
    with pytest.raises(
        NitrogenVerticalDemonstrationV1Error,
        match="explicit input, not derived",
    ):
        build_nitrogen_vertical_demonstration_v1(
            demo_id="derived-extent-rejected",
            starting_state=start,
            intermediate_state=intermediate,
            ending_state=end,
            evaluations=(mutated, assimilation),
            auditable_explanation=auditable,
            scientific_foundation_snapshot=snapshot,
        )


def test_vertical_demo_markdown_states_non_predictive_boundary() -> None:
    *_, demo = _fixture()
    rendered = demo.render_markdown()
    assert "pas une prediction cinetique" in rendered
    assert "1 mg N" in rendered
    assert "scientific_alignment_reviewed" in rendered
    assert "Aucune vitesse" in rendered
