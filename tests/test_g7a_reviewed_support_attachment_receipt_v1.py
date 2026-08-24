from __future__ import annotations

import json
from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest

from ecobiome.knowledge_persistence.serialization import (
    canonical_json_text,
    canonical_sha256,
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
from ecobiome.simulation.reviewed_support_attachment_receipt_v1 import (
    ReviewedSupportAttachmentReceiptV1Error,
    attach_g7a_reviewed_alignment_v2_support_with_receipt_v1,
)

_OXIDATION_SELECTION_SHA256 = (
    "0e3c0806a04eea2a626c4a0b094e857d03662269959af7fb1cbb05153c1f7cf6"
)
_ASSIMILATION_SELECTION_SHA256 = (
    "e6f186018b8e7190fa90620ae15a6918a03218f14f9b05e6ee07248a0e2a677c"
)


class _Assertions:
    def __init__(self, policy: Any) -> None:
        participants: list[dict[str, object]] = []
        for requirement in policy.base_policy_v1.required_participants:
            participant: dict[str, object] = {
                "role": requirement.role,
                "entity": {
                    "type": "entity_ref",
                    "entity_id": requirement.entity_id,
                    "entity_revision": requirement.entity_revision,
                },
            }
            if requirement.occurrence_json is not None:
                participant["occurrence"] = json.loads(
                    requirement.occurrence_json
                )
            participants.append(participant)

        self.root = SimpleNamespace(
            id=policy.assertion_ref.assertion_id,
            retired_at=None,
        )
        self.revision = SimpleNamespace(
            assertion_id=policy.assertion_ref.assertion_id,
            revision=policy.assertion_ref.assertion_revision,
            schema_version="scientific-assertion-v1.1",
            predicate=policy.predicate,
            participants_json=json.dumps(
                participants,
                sort_keys=True,
                separators=(",", ":"),
            ),
            qualifiers_json=policy.base_policy_v1.required_qualifiers_json,
            canonical_payload_sha256=(
                policy.assertion_ref.canonical_payload_sha256
            ),
        )
        self.link = SimpleNamespace(
            stance="supports",
            scope_alignment="exact",
            semantic_alignment="exact",
            reviewed_by="human",
            reviewed_at="2026-08-24T00:00:00+00:00",
        )

    def get_assertion(self, assertion_id: str) -> Any:
        return self.root if assertion_id == self.root.id else None

    def get_assertion_revision(
        self,
        assertion_id: str,
        revision: int,
    ) -> Any:
        if (
            assertion_id == self.revision.assertion_id
            and revision == self.revision.revision
        ):
            return self.revision
        return None

    def find_by_canonical_payload_sha256(
        self,
        sha256: str,
    ) -> tuple[Any, ...]:
        if sha256 == self.revision.canonical_payload_sha256:
            return (self.revision,)
        return ()

    def list_assertion_claim_links(
        self,
        assertion_id: str,
        revision: int,
    ) -> tuple[Any, ...]:
        if (
            assertion_id == self.revision.assertion_id
            and revision == self.revision.revision
        ):
            return (self.link,)
        return ()


class _Syntheses:
    def list_for_assertion(
        self,
        assertion_id: str,
        revision: int,
    ) -> tuple[Any, ...]:
        return ()


def _pending_evaluation(
    *,
    selection: Any,
    source_component_id: str,
    target_component_id: str,
) -> Any:
    basis = QuantityBasisV1(
        kind="observation",
        reference_id="g7a-mech5b-observation",
    )
    state = EcosystemStateV1(
        profile_id="g7a-mech5b-profile",
        quantities=(
            CanonicalQuantityV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                value_decimal="10",
                unit="mg N",
                basis=basis,
                zone_id="water-zone-1",
                material_component_id=source_component_id,
            ),
            CanonicalQuantityV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                value_decimal="2",
                unit="mg N",
                basis=basis,
                zone_id="water-zone-1",
                material_component_id=target_component_id,
            ),
        ),
    )
    extent_basis = QuantityBasisV1(
        kind="scenario_default",
        reference_id="g7a-mech5b-explicit-extent",
    )
    _, evaluation = evaluate_nitrogen_transformation_extent_v1(
        state,
        zone_id="water-zone-1",
        source_component_id=source_component_id,
        target_component_id=target_component_id,
        extent_decimal="1",
        extent_unit="mg N",
        extent_basis=extent_basis,
        evaluation_id="g7a-mech5b-evaluation",
        scientific_assertion_refs=(selection.policy.assertion_ref,),
    )
    return evaluation


@pytest.mark.parametrize(
    (
        "selection",
        "selection_sha256",
        "source_component_id",
        "target_component_id",
    ),
    (
        (
            G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION,
            _OXIDATION_SELECTION_SHA256,
            "reduced_inorganic_nitrogen",
            "oxidized_inorganic_nitrogen",
        ),
        (
            G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION,
            _ASSIMILATION_SELECTION_SHA256,
            "dissolved_inorganic_nitrogen",
            "biological_nitrogen",
        ),
    ),
)
def test_receipt_binds_exact_selection_support_and_evaluation(
    selection: Any,
    selection_sha256: str,
    source_component_id: str,
    target_component_id: str,
) -> None:
    pending = _pending_evaluation(
        selection=selection,
        source_component_id=source_component_id,
        target_component_id=target_component_id,
    )
    result = attach_g7a_reviewed_alignment_v2_support_with_receipt_v1(
        pending,
        receipt_id=f"receipt-{selection.selection_id}",
        selection=selection,
        expected_selection_sha256=selection_sha256,
        assertions=_Assertions(selection.policy),
        syntheses=_Syntheses(),
    )

    support = result.evaluation.scientific_supports[0]
    receipt = result.receipt
    assert receipt.evaluation_id == pending.evaluation_id
    assert receipt.pending_evaluation_sha256 == pending.canonical_sha256
    assert receipt.attached_evaluation_sha256 == result.evaluation.canonical_sha256
    assert receipt.support_sha256 == canonical_sha256(support.canonical_payload())
    assert receipt.selection_sha256 == selection_sha256
    assert receipt.selection_payload == selection.canonical_payload()
    assert receipt.selection_id == selection.selection_id
    assert receipt.alignment_policy_sha256 == selection.policy.canonical_sha256
    assert receipt.bridge_id == selection.policy.model_semantic_bridge.bridge_id
    assert receipt.bridge_sha256 == selection.policy.bridge_sha256
    assert receipt.evaluation_scope_sha256 == support.evaluation_scope_sha256
    assert receipt.assertion_ref == support.assertion_ref
    assert receipt.automatic_acceptance is False
    assert receipt.automatic_attachment is False
    assert result.evaluation.input_state_sha256 == pending.input_state_sha256
    assert result.evaluation.output_state_sha256 == pending.output_state_sha256
    assert result.evaluation.parameters_json == pending.parameters_json
    assert result.evaluation.deltas == pending.deltas


def test_receipt_rejects_tampered_human_review_payload() -> None:
    selection = G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION
    pending = _pending_evaluation(
        selection=selection,
        source_component_id="reduced_inorganic_nitrogen",
        target_component_id="oxidized_inorganic_nitrogen",
    )
    result = attach_g7a_reviewed_alignment_v2_support_with_receipt_v1(
        pending,
        receipt_id="receipt-tamper-source",
        selection=selection,
        expected_selection_sha256=_OXIDATION_SELECTION_SHA256,
        assertions=_Assertions(selection.policy),
        syntheses=_Syntheses(),
    )
    payload = result.receipt.selection_payload
    payload["reviewed_by"] = "automatic"

    with pytest.raises(
        ReviewedSupportAttachmentReceiptV1Error,
        match="reviewed_by must be human",
    ):
        replace(
            result.receipt,
            selection_sha256=canonical_sha256(payload),
            selection_payload_json=canonical_json_text(payload),
        )
