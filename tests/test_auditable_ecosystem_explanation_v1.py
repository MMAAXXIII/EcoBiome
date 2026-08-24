from __future__ import annotations

from dataclasses import replace

import pytest

from ecobiome.knowledge_persistence.serialization import (
    canonical_json_text,
    canonical_sha256,
)
from ecobiome.reasoning.auditable_ecosystem_explanation_v1 import (
    AuditableEcosystemExplanationV1Error,
    build_auditable_ecosystem_explanation_v1,
)
from ecobiome.reasoning.ecosystem_explanation_v1 import (
    build_ecosystem_explanation_v1,
)
from ecobiome.simulation.ecosystem_state_v1 import (
    CanonicalQuantityV1,
    EcosystemStateV1,
    QuantityBasisV1,
)
from ecobiome.simulation.g7a_alignment_instances_v2 import (
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

_SELECTION_SHA256 = (
    "0e3c0806a04eea2a626c4a0b094e857d03662269959af7fb1cbb05153c1f7cf6"
)


def _supported_chain():
    selection = G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION
    policy = selection.policy
    basis = QuantityBasisV1(
        kind="observation",
        reference_id="auditable-explanation-observation",
    )
    start = EcosystemStateV1(
        profile_id="auditable-explanation-profile",
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
        ),
    )
    extent_basis = QuantityBasisV1(
        kind="scenario_default",
        reference_id="auditable-explanation-explicit-extent",
    )
    end, pending = evaluate_nitrogen_transformation_extent_v1(
        start,
        zone_id="water-zone-1",
        source_component_id="reduced_inorganic_nitrogen",
        target_component_id="oxidized_inorganic_nitrogen",
        extent_decimal="1",
        extent_unit="mg N",
        extent_basis=extent_basis,
        evaluation_id="auditable-explanation-evaluation",
        scientific_assertion_refs=(policy.assertion_ref,),
    )
    base_policy = policy.base_policy_v1
    support = ProcessScientificSupportV1(
        role=base_policy.role,
        assertion_ref=policy.assertion_ref,
        alignment_class=base_policy.alignment_class,
        epistemic_class=base_policy.epistemic_class,
        alignment_policy_name=policy.name,
        alignment_policy_version=policy.version,
        alignment_policy_sha256=policy.canonical_sha256,
        evaluation_scope=base_policy.evaluation_scope,
        evaluation_scope_sha256=base_policy.evaluation_scope.canonical_sha256,
    )
    attached = attach_scientific_supports_v1(
        pending,
        (support,),
    )
    receipt = ReviewedSupportAttachmentReceiptV1(
        receipt_id="receipt-auditable-explanation-oxidation",
        evaluation_id=attached.evaluation_id,
        pending_evaluation_sha256=pending.canonical_sha256,
        attached_evaluation_sha256=attached.canonical_sha256,
        support_sha256=canonical_sha256(support.canonical_payload()),
        assertion_ref=support.assertion_ref,
        alignment_policy_sha256=support.alignment_policy_sha256,
        evaluation_scope_sha256=support.evaluation_scope_sha256,
        bridge_id=policy.model_semantic_bridge.bridge_id,
        bridge_sha256=policy.bridge_sha256,
        selection_sha256=_SELECTION_SHA256,
        selection_payload_json=canonical_json_text(
            selection.canonical_payload()
        ),
    )
    return start, end, attached, receipt


def test_auditable_envelope_preserves_core_trace_and_carries_receipt() -> None:
    start, end, attached, receipt = _supported_chain()
    core = build_ecosystem_explanation_v1(
        start,
        end,
        (attached,),
    )
    auditable = build_auditable_ecosystem_explanation_v1(
        start,
        end,
        (attached,),
        reviewed_support_attachment_receipts=(receipt,),
    )

    assert auditable.explanation_trace.canonical_sha256 == core.canonical_sha256
    assert auditable.explanation_trace.canonical_payload() == core.canonical_payload()
    assert "reviewed_support_attachment_receipts" not in core.canonical_payload()
    assert auditable.process_evaluation_identities[0].canonical_sha256 == (
        attached.canonical_sha256
    )
    assert auditable.reviewed_support_attachment_receipts == (receipt,)
    payload = auditable.canonical_payload()
    assert payload["explanation_trace"] == core.canonical_payload()
    assert len(payload["reviewed_support_attachment_receipts"]) == 1
    assert auditable.canonical_sha256


def test_auditable_envelope_requires_complete_receipt_coverage() -> None:
    start, end, attached, _ = _supported_chain()
    with pytest.raises(
        AuditableEcosystemExplanationV1Error,
        match="must exactly cover trace supports",
    ):
        build_auditable_ecosystem_explanation_v1(
            start,
            end,
            (attached,),
            reviewed_support_attachment_receipts=(),
        )


def test_auditable_envelope_rejects_wrong_attached_evaluation_sha() -> None:
    start, end, attached, receipt = _supported_chain()
    tampered = replace(
        receipt,
        attached_evaluation_sha256="0" * 64,
    )
    with pytest.raises(
        AuditableEcosystemExplanationV1Error,
        match="evaluation SHA does not match trace identity",
    ):
        build_auditable_ecosystem_explanation_v1(
            start,
            end,
            (attached,),
            reviewed_support_attachment_receipts=(tampered,),
        )


def test_auditable_envelope_rejects_receipt_bound_to_wrong_support() -> None:
    start, end, attached, receipt = _supported_chain()
    tampered = replace(
        receipt,
        support_sha256="0" * 64,
    )
    with pytest.raises(
        AuditableEcosystemExplanationV1Error,
        match="support is not bound to its trace evaluation",
    ):
        build_auditable_ecosystem_explanation_v1(
            start,
            end,
            (attached,),
            reviewed_support_attachment_receipts=(tampered,),
        )
