from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

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
from ecobiome.simulation.reviewed_support_attachment_v1 import (
    ExplicitReviewedSupportAttachmentV1Error,
    attach_g7a_reviewed_alignment_v2_support_v1,
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
        return (
            self.root
            if assertion_id == self.root.id
            else None
        )

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


def _evaluation(
    *,
    selection: Any,
    source_component_id: str,
    target_component_id: str,
) -> Any:
    basis = QuantityBasisV1(
        kind="observation",
        reference_id="g7a-mech4d-observation",
    )
    state = EcosystemStateV1(
        profile_id="g7a-mech4d-profile",
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
        reference_id="g7a-mech4d-explicit-extent",
    )
    _, evaluation = evaluate_nitrogen_transformation_extent_v1(
        state,
        zone_id="water-zone-1",
        source_component_id=source_component_id,
        target_component_id=target_component_id,
        extent_decimal="1",
        extent_unit="mg N",
        extent_basis=extent_basis,
        evaluation_id="g7a-mech4d-evaluation",
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
def test_explicit_attachment_preserves_deterministic_process_semantics(
    selection: Any,
    selection_sha256: str,
    source_component_id: str,
    target_component_id: str,
) -> None:
    evaluation = _evaluation(
        selection=selection,
        source_component_id=source_component_id,
        target_component_id=target_component_id,
    )
    assert evaluation.support_status == "support_missing"
    assert evaluation.scientific_supports == ()

    attached = attach_g7a_reviewed_alignment_v2_support_v1(
        evaluation,
        selection=selection,
        expected_selection_sha256=selection_sha256,
        assertions=_Assertions(selection.policy),
        syntheses=_Syntheses(),
    )

    assert attached.support_status == "scientific_alignment_reviewed"
    assert len(attached.scientific_supports) == 1
    assert attached.scientific_supports[0].alignment_policy_sha256 == (
        selection.policy.canonical_sha256
    )
    assert attached.scientific_assertion_refs == (
        selection.policy.assertion_ref,
    )
    assert attached.input_state_sha256 == evaluation.input_state_sha256
    assert attached.output_state_sha256 == evaluation.output_state_sha256
    assert attached.parameters_json == evaluation.parameters_json
    assert attached.parameter_bases == evaluation.parameter_bases
    assert attached.deltas == evaluation.deltas
    assert attached.definition == evaluation.definition
    assert attached.profile_id == evaluation.profile_id
    assert attached.assumptions == evaluation.assumptions
    assert not any(
        "alignment is not reviewed in N4 V1" in item
        for item in attached.unknowns
    )


def test_attachment_requires_exact_human_selection_identity() -> None:
    selection = G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION
    evaluation = _evaluation(
        selection=selection,
        source_component_id="reduced_inorganic_nitrogen",
        target_component_id="oxidized_inorganic_nitrogen",
    )

    with pytest.raises(
        ExplicitReviewedSupportAttachmentV1Error,
        match="selection identity mismatch",
    ):
        attach_g7a_reviewed_alignment_v2_support_v1(
            evaluation,
            selection=selection,
            expected_selection_sha256="0" * 64,
            assertions=_Assertions(selection.policy),
            syntheses=_Syntheses(),
        )


def test_attachment_does_not_auto_route_cross_scope_selection() -> None:
    assimilation = G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION
    oxidation = G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION
    evaluation = _evaluation(
        selection=assimilation,
        source_component_id="dissolved_inorganic_nitrogen",
        target_component_id="biological_nitrogen",
    )

    with pytest.raises(
        ExplicitReviewedSupportAttachmentV1Error,
        match="cannot be attached",
    ):
        attach_g7a_reviewed_alignment_v2_support_v1(
            evaluation,
            selection=oxidation,
            expected_selection_sha256=_OXIDATION_SELECTION_SHA256,
            assertions=_Assertions(oxidation.policy),
            syntheses=_Syntheses(),
        )
