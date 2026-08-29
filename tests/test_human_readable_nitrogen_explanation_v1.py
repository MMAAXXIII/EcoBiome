from __future__ import annotations

import copy

import pytest

from ecobiome.reasoning.human_readable_nitrogen_explanation_v1 import (
    HumanReadableNitrogenExplanationV1Error,
    build_human_readable_nitrogen_explanation_v1,
)
from ecobiome.simulation.g7a_alignment_instances_v2 import (
    G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION,
    G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION,
)
from ecobiome.simulation.model_semantic_bridge_v1 import (
    G7A_NITROGEN_ASSIMILATION_BRIDGE_V1,
    G7A_NITROGEN_OXIDATION_BRIDGE_V1,
)


def _step(
    *,
    evaluation_id: str,
    source_component_id: str,
    target_component_id: str,
    source_before: str,
    source_after: str,
    target_before: str,
    target_after: str,
    bridge: object,
    selection: object,
    receipt_id: str,
) -> dict[str, object]:
    bridge_obj = bridge
    selection_obj = selection
    assertion_ref = bridge_obj.assertion_ref
    return {
        "source_component_id": source_component_id,
        "target_component_id": target_component_id,
        "explicit_extent": {
            "value": "1",
            "unit": "mg N",
            "is_explicit_input": True,
        },
        "scientific_assertion_refs": [
            assertion_ref.canonical_payload(),
        ],
        "reviewed_attachment_receipts": [
            {
                "receipt_id": receipt_id,
                "scientific_binding": {
                    "bridge_id": bridge_obj.bridge_id,
                    "bridge_sha256": bridge_obj.canonical_sha256,
                    "support_sha256": "a" * 64,
                },
                "human_reviewed_selection": {
                    "canonical_sha256": selection_obj.canonical_sha256,
                    "payload": selection_obj.canonical_payload(),
                },
            }
        ],
        "evaluation": {
            "evaluation_id": evaluation_id,
            "support_status": "scientific_alignment_reviewed",
            "definition": {
                "process_id": "nitrogen_transformation_extent_v1",
            },
            "deltas": [
                {
                    "material_component_id": source_component_id,
                    "before": {"type": "decimal", "value": source_before},
                    "after": {"type": "decimal", "value": source_after},
                    "unit": "mg N",
                },
                {
                    "material_component_id": target_component_id,
                    "before": {"type": "decimal", "value": target_before},
                    "after": {"type": "decimal", "value": target_after},
                    "unit": "mg N",
                },
            ],
        },
    }


def _artifact() -> dict[str, object]:
    return {
        "schema_version": "ecobiome-nitrogen-vertical-demonstration-v1",
        "model_boundary": {
            "extent_is_explicit_input": True,
            "kinetic_or_rate_model_present": False,
            "dt_or_elapsed_time_prediction_present": False,
            "forecast_claim": False,
        },
        "process_steps": [
            _step(
                evaluation_id="g7a-mech5a-oxidation-evaluation",
                source_component_id="reduced_inorganic_nitrogen",
                target_component_id="oxidized_inorganic_nitrogen",
                source_before="10",
                source_after="9",
                target_before="2",
                target_after="3",
                bridge=G7A_NITROGEN_OXIDATION_BRIDGE_V1,
                selection=G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION,
                receipt_id="receipt-g7a-mech5b-oxidation-v1",
            ),
            _step(
                evaluation_id="g7a-mech5a-assimilation-evaluation",
                source_component_id="dissolved_inorganic_nitrogen",
                target_component_id="biological_nitrogen",
                source_before="10",
                source_after="9",
                target_before="2",
                target_after="3",
                bridge=G7A_NITROGEN_ASSIMILATION_BRIDGE_V1,
                selection=G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION,
                receipt_id="receipt-g7a-mech5b-assimilation-v1",
            ),
        ],
    }


def test_projection_is_deterministic_and_process_scoped() -> None:
    first = build_human_readable_nitrogen_explanation_v1(_artifact())
    second = build_human_readable_nitrogen_explanation_v1(_artifact())
    assert first.canonical_sha256 == second.canonical_sha256
    assert tuple(item.key for item in first.processes) == (
        "oxidation",
        "assimilation",
    )
    assert first.processes[0].source_before == "10"
    assert first.processes[0].source_after == "9"
    assert first.processes[0].target_before == "2"
    assert first.processes[0].target_after == "3"
    assert "ammonium" in first.processes[0].scientific_basis
    assert "nitrate" in first.processes[0].scientific_basis
    assert "L-glutamine" in first.processes[1].scientific_basis
    assert "ne doivent donc pas être additionnées" in first.abstraction_note
    assert "aucun RateModel" in first.model_limit


def test_projection_rejects_bridge_sha_drift() -> None:
    artifact = copy.deepcopy(_artifact())
    steps = artifact["process_steps"]
    assert isinstance(steps, list)
    first = steps[0]
    assert isinstance(first, dict)
    receipts = first["reviewed_attachment_receipts"]
    assert isinstance(receipts, list)
    receipt = receipts[0]
    assert isinstance(receipt, dict)
    binding = receipt["scientific_binding"]
    assert isinstance(binding, dict)
    binding["bridge_sha256"] = "0" * 64
    with pytest.raises(
        HumanReadableNitrogenExplanationV1Error,
        match="bridge SHA drift",
    ):
        build_human_readable_nitrogen_explanation_v1(artifact)


def test_projection_rejects_predictive_boundary() -> None:
    artifact = _artifact()
    boundary = artifact["model_boundary"]
    assert isinstance(boundary, dict)
    boundary["kinetic_or_rate_model_present"] = True
    with pytest.raises(
        HumanReadableNitrogenExplanationV1Error,
        match="non-predictive boundary",
    ):
        build_human_readable_nitrogen_explanation_v1(artifact)


def test_projection_rejects_non_explicit_extent() -> None:
    artifact = _artifact()
    steps = artifact["process_steps"]
    assert isinstance(steps, list)
    first = steps[0]
    assert isinstance(first, dict)
    extent = first["explicit_extent"]
    assert isinstance(extent, dict)
    extent["is_explicit_input"] = False
    with pytest.raises(
        HumanReadableNitrogenExplanationV1Error,
        match="extent must remain an explicit input",
    ):
        build_human_readable_nitrogen_explanation_v1(artifact)
