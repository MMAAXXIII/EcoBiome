from __future__ import annotations

from dataclasses import replace

import pytest

from ecobiome.reasoning.ecosystem_explanation_v1 import (
    build_ecosystem_explanation_v1,
)
from ecobiome.simulation.ecosystem_state_v1 import (
    CanonicalQuantityV1,
    EcosystemStateV1,
    QuantityBasisV1,
)
from ecobiome.simulation.intervention_v1 import (
    ReplacementCompositionV1,
    WaterExchangeInterventionV1,
)
from ecobiome.simulation.material_balance_v1 import (
    MATERIAL_INVENTORY_VARIABLE_ID,
    WATER_VOLUME_VARIABLE_ID,
    evaluate_nitrogen_transformation_extent_v1,
    evaluate_well_mixed_water_exchange_v1,
)
from ecobiome.simulation.process_v1 import ScientificAssertionRefV1


def _basis(kind: str, ref: str) -> QuantityBasisV1:
    return QuantityBasisV1(kind=kind, reference_id=ref)


def _starting_state() -> EcosystemStateV1:
    basis = _basis("observation", "obs-initial")
    return EcosystemStateV1(
        profile_id="profile-aquarium-v1",
        quantities=(
            CanonicalQuantityV1(
                variable_id=WATER_VOLUME_VARIABLE_ID,
                value_decimal="250",
                unit="L",
                basis=basis,
                zone_id="water",
            ),
            CanonicalQuantityV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                value_decimal="50",
                unit="mg N",
                basis=basis,
                zone_id="water",
                material_component_id="reduced_inorganic_nitrogen",
            ),
            CanonicalQuantityV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                value_decimal="100",
                unit="mg N",
                basis=basis,
                zone_id="water",
                material_component_id="oxidized_inorganic_nitrogen",
            ),
        ),
    )


def _chain():
    start = _starting_state()
    assertion = ScientificAssertionRefV1(
        assertion_id="assertion-nitrification",
        assertion_revision=1,
        canonical_payload_sha256="b" * 64,
    )
    transformed, transform_eval = evaluate_nitrogen_transformation_extent_v1(
        start,
        zone_id="water",
        source_component_id="reduced_inorganic_nitrogen",
        target_component_id="oxidized_inorganic_nitrogen",
        extent_decimal="20",
        extent_unit="mg N",
        extent_basis=_basis("user_assumption", "extent-assumption"),
        evaluation_id="eval-transform",
        scientific_assertion_refs=(assertion,),
    )
    exchange = WaterExchangeInterventionV1(
        id="exchange-1",
        water_zone_id="water",
        removed_volume_decimal="50",
        removed_volume_unit="L",
        replacement_volume_decimal="50",
        replacement_volume_unit="L",
        replacement_composition=(
            ReplacementCompositionV1(
                material_component_id="reduced_inorganic_nitrogen",
                concentration_decimal="0",
                unit="mg N/L",
                basis=_basis("scenario_default", "replacement-reduced"),
            ),
            ReplacementCompositionV1(
                material_component_id="oxidized_inorganic_nitrogen",
                concentration_decimal="0",
                unit="mg N/L",
                basis=_basis("scenario_default", "replacement-oxidized"),
            ),
        ),
        basis=_basis("observation", "exchange-observation"),
    )
    end, exchange_eval = evaluate_well_mixed_water_exchange_v1(
        transformed,
        exchange,
        evaluation_id="eval-exchange",
    )
    return start, end, transform_eval, exchange_eval


def test_explanation_trace_preserves_epistemic_categories_and_scientific_refs() -> None:
    start, end, transform_eval, exchange_eval = _chain()
    trace = build_ecosystem_explanation_v1(
        start,
        end,
        (transform_eval, exchange_eval),
        observation_refs=("obs-initial", "exchange-observation"),
        intervention_refs=("exchange-1",),
    )

    assert trace.process_evaluation_refs == ("eval-transform", "eval-exchange")
    assert len(trace.scientific_assertion_refs) == 1
    assert trace.causal_steps[0].support_status == "support_missing"
    assert any(step.support_status == "deterministic_identity" for step in trace.causal_steps)
    assert any("user_assumption" in step.epistemic_basis_kinds for step in trace.causal_steps)
    assert any("scenario_default" in step.epistemic_basis_kinds for step in trace.causal_steps)
    assert "observation" in trace.causal_steps[0].epistemic_basis_kinds
    text = trace.render_text()
    assert "Pourquoi cet état évolue-t-il ainsi ?" in text
    assert "support_missing" in text
    assert "deterministic_identity" in text


def test_explanation_trace_sha_is_deterministic() -> None:
    start, end, transform_eval, exchange_eval = _chain()
    first = build_ecosystem_explanation_v1(
        start,
        end,
        (transform_eval, exchange_eval),
    )
    second = build_ecosystem_explanation_v1(
        start,
        end,
        (transform_eval, exchange_eval),
    )
    assert first.canonical_sha256 == second.canonical_sha256


def test_explanation_rejects_noncontiguous_process_chain() -> None:
    start, end, transform_eval, exchange_eval = _chain()
    broken = replace(
        exchange_eval,
        input_state_sha256="f" * 64,
    )
    with pytest.raises(ValueError, match="contiguous"):
        build_ecosystem_explanation_v1(
            start,
            end,
            (transform_eval, broken),
        )


def test_explanation_derives_bound_observation_and_intervention_refs() -> None:
    start, end, transform_eval, exchange_eval = _chain()
    trace = build_ecosystem_explanation_v1(
        start,
        end,
        (transform_eval, exchange_eval),
    )
    assert trace.observation_refs == ("exchange-observation", "obs-initial")
    assert trace.intervention_refs == ("exchange-1",)


def test_explanation_rejects_free_floating_intervention_ref() -> None:
    start, end, transform_eval, exchange_eval = _chain()
    with pytest.raises(ValueError, match="exactly match interventions"):
        build_ecosystem_explanation_v1(
            start,
            end,
            (transform_eval, exchange_eval),
            intervention_refs=("not-bound-to-an-evaluation",),
        )


def test_explanation_rejects_tampered_intervention_sha() -> None:
    start, end, transform_eval, exchange_eval = _chain()
    tampered = replace(
        exchange_eval,
        parameters_json=exchange_eval.parameters_json.replace(
            exchange_eval.parameters_payload["intervention_sha256"],
            "0" * 64,
        ),
    )
    with pytest.raises(ValueError, match="does not match its payload"):
        build_ecosystem_explanation_v1(
            start,
            end,
            (transform_eval, tampered),
        )


def test_explanation_rejects_free_floating_observation_ref() -> None:
    start, end, transform_eval, exchange_eval = _chain()
    with pytest.raises(ValueError, match="exactly match observation"):
        build_ecosystem_explanation_v1(
            start,
            end,
            (transform_eval, exchange_eval),
            observation_refs=("not-used",),
        )



def test_direct_trace_rejects_mismatched_process_evaluation_refs() -> None:
    start, end, transform_eval, exchange_eval = _chain()
    trace = build_ecosystem_explanation_v1(
        start,
        end,
        (transform_eval, exchange_eval),
    )
    with pytest.raises(ValueError, match="exactly match causal-step"):
        replace(
            trace,
            process_evaluation_refs=("forged-evaluation",),
        )


def test_direct_trace_rejects_scientific_refs_not_present_in_steps() -> None:
    start, end, transform_eval, exchange_eval = _chain()
    trace = build_ecosystem_explanation_v1(
        start,
        end,
        (transform_eval, exchange_eval),
    )
    with pytest.raises(ValueError, match="exactly match causal-step refs"):
        replace(
            trace,
            scientific_assertion_refs=(),
        )
