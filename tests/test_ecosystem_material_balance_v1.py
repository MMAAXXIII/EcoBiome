from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import pytest

from ecobiome.core.observation.measurement import ScientificMeasurement
from ecobiome.core.observation.observation import AcquisitionMethod, Observation
from ecobiome.core.units import Measurement
from ecobiome.knowledge.variable import ScientificVariable
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
from ecobiome.simulation.observation_adapter_v1 import canonicalize_observation_v1
from ecobiome.simulation.process_v1 import (
    ProcessEvaluationV1,
    ScientificAssertionRefV1,
)
from ecobiome.world.ecosystem_profile_v1 import ecosystem_profile_from_mapping_v1


def _basis(kind: str = "user_assumption", ref: str = "basis-1") -> QuantityBasisV1:
    return QuantityBasisV1(kind=kind, reference_id=ref)


def _state() -> EcosystemStateV1:
    basis = _basis()
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


def _zero_replacement(component_id: str) -> ReplacementCompositionV1:
    return ReplacementCompositionV1(
        material_component_id=component_id,
        concentration_decimal="0",
        unit="mg N/L",
        basis=_basis("scenario_default", f"replacement-{component_id}"),
    )


def test_canonical_quantity_rejects_native_float() -> None:
    with pytest.raises(TypeError, match="never native float"):
        CanonicalQuantityV1(
            variable_id="water.test",
            value_decimal=0.1,
            unit="mg/L",
            basis=_basis(),
        )


def test_state_hash_is_independent_of_quantity_order() -> None:
    first = _state()
    second = EcosystemStateV1(
        profile_id=first.profile_id,
        quantities=tuple(reversed(first.quantities)),
    )
    assert first.canonical_sha256 == second.canonical_sha256


def test_nitrogen_transformation_conserves_elemental_n() -> None:
    initial = _state()
    assertion = ScientificAssertionRefV1(
        assertion_id="assertion-nitrification",
        assertion_revision=1,
        canonical_payload_sha256="a" * 64,
    )
    output, evaluation = evaluate_nitrogen_transformation_extent_v1(
        initial,
        zone_id="water",
        source_component_id="reduced_inorganic_nitrogen",
        target_component_id="oxidized_inorganic_nitrogen",
        extent_decimal="20",
        extent_unit="mg N",
        extent_basis=_basis("observation", "extent-observation"),
        evaluation_id="eval-nitrogen",
        scientific_assertion_refs=(assertion,),
    )

    reduced = output.get_quantity(
        MATERIAL_INVENTORY_VARIABLE_ID,
        zone_id="water",
        material_component_id="reduced_inorganic_nitrogen",
    )
    oxidized = output.get_quantity(
        MATERIAL_INVENTORY_VARIABLE_ID,
        zone_id="water",
        material_component_id="oxidized_inorganic_nitrogen",
    )
    assert reduced.value_decimal == "30"
    assert oxidized.value_decimal == "120"
    assert reduced.decimal + oxidized.decimal == initial.get_quantity(
        MATERIAL_INVENTORY_VARIABLE_ID,
        zone_id="water",
        material_component_id="reduced_inorganic_nitrogen",
    ).decimal + initial.get_quantity(
        MATERIAL_INVENTORY_VARIABLE_ID,
        zone_id="water",
        material_component_id="oxidized_inorganic_nitrogen",
    ).decimal
    assert evaluation.support_status == "support_missing"
    assert evaluation.scientific_assertion_refs == (assertion,)
    assert "alignment is not reviewed" in evaluation.unknowns[0]
    assert evaluation.parameters_payload["extent"] == {
        "unit": "mg N",
        "value": {"type": "decimal", "value": "20"},
    }
    assert evaluation.parameters_payload["extent_base"] == {
        "unit": "mg N",
        "value": {"type": "decimal", "value": "20"},
    }


def test_nitrogen_extent_without_assertion_remains_scenario_hypothesis() -> None:
    _, evaluation = evaluate_nitrogen_transformation_extent_v1(
        _state(),
        zone_id="water",
        source_component_id="reduced_inorganic_nitrogen",
        target_component_id="oxidized_inorganic_nitrogen",
        extent_decimal="5",
        extent_unit="mg N",
        extent_basis=_basis("user_assumption", "assumption-extent"),
        evaluation_id="eval-assumed",
    )
    assert evaluation.support_status == "scenario_hypothesis"
    assert evaluation.unknowns == ("scientific mechanism assertion not supplied",)


def test_nitrogen_extent_cannot_exceed_available_inventory() -> None:
    with pytest.raises(ValueError, match="exceeds source inventory"):
        evaluate_nitrogen_transformation_extent_v1(
            _state(),
            zone_id="water",
            source_component_id="reduced_inorganic_nitrogen",
            target_component_id="oxidized_inorganic_nitrogen",
            extent_decimal="51",
            extent_unit="mg N",
            extent_basis=_basis(),
            evaluation_id="eval-too-large",
        )


def test_water_exchange_exactly_conserves_retained_fraction_with_zero_replacement() -> None:
    transformed, _ = evaluate_nitrogen_transformation_extent_v1(
        _state(),
        zone_id="water",
        source_component_id="reduced_inorganic_nitrogen",
        target_component_id="oxidized_inorganic_nitrogen",
        extent_decimal="20",
        extent_unit="mg N",
        extent_basis=_basis(),
        evaluation_id="eval-transform",
    )
    intervention = WaterExchangeInterventionV1(
        id="exchange-1",
        water_zone_id="water",
        removed_volume_decimal="50",
        removed_volume_unit="L",
        replacement_volume_decimal="50",
        replacement_volume_unit="L",
        replacement_composition=(
            _zero_replacement("reduced_inorganic_nitrogen"),
            _zero_replacement("oxidized_inorganic_nitrogen"),
        ),
        basis=_basis("user_assumption", "exchange-basis"),
    )
    output, evaluation = evaluate_well_mixed_water_exchange_v1(
        transformed,
        intervention,
        evaluation_id="eval-exchange",
    )

    assert output.get_quantity(
        WATER_VOLUME_VARIABLE_ID,
        zone_id="water",
    ).value_decimal == "250"
    assert output.get_quantity(
        MATERIAL_INVENTORY_VARIABLE_ID,
        zone_id="water",
        material_component_id="reduced_inorganic_nitrogen",
    ).value_decimal == "24"
    assert output.get_quantity(
        MATERIAL_INVENTORY_VARIABLE_ID,
        zone_id="water",
        material_component_id="oxidized_inorganic_nitrogen",
    ).value_decimal == "96"
    assert evaluation.support_status == "deterministic_identity"


def test_water_exchange_requires_explicit_replacement_composition() -> None:
    intervention = WaterExchangeInterventionV1(
        id="exchange-missing",
        water_zone_id="water",
        removed_volume_decimal="50",
        removed_volume_unit="L",
        replacement_volume_decimal="50",
        replacement_volume_unit="L",
        replacement_composition=(
            _zero_replacement("reduced_inorganic_nitrogen"),
        ),
        basis=_basis(),
    )
    with pytest.raises(ValueError, match="replacement composition is unknown"):
        evaluate_well_mixed_water_exchange_v1(
            _state(),
            intervention,
            evaluation_id="eval-missing",
        )


def test_legacy_observation_adapter_marks_native_float_canonicalization() -> None:
    variable = ScientificVariable(
        identifier="water.temperature",
        name="Temperature",
        description="Water temperature",
        unit="degree_Celsius",
    )
    observation = Observation(
        source="manual thermometer",
        variable=variable,
        value=ScientificMeasurement(
            quantity=Measurement(value=21.5, unit="degree_Celsius"),
            uncertainty=0.1,
        ),
        acquisition_method=AcquisitionMethod.HUMAN,
        observation_id=UUID("00000000-0000-0000-0000-000000000001"),
    )
    result = canonicalize_observation_v1(observation, zone_id="water")

    assert result.quantity.value_decimal == "21.5"
    assert result.quantity.basis.kind == "observation"
    assert result.warnings == ("legacy_native_float_canonicalized",)


def test_process_output_hash_changes_if_extent_changes() -> None:
    first, _ = evaluate_nitrogen_transformation_extent_v1(
        _state(),
        zone_id="water",
        source_component_id="reduced_inorganic_nitrogen",
        target_component_id="oxidized_inorganic_nitrogen",
        extent_decimal="5",
        extent_unit="mg N",
        extent_basis=_basis(),
        evaluation_id="eval-1",
    )
    second, _ = evaluate_nitrogen_transformation_extent_v1(
        _state(),
        zone_id="water",
        source_component_id="reduced_inorganic_nitrogen",
        target_component_id="oxidized_inorganic_nitrogen",
        extent_decimal="6",
        extent_unit="mg N",
        extent_basis=_basis(),
        evaluation_id="eval-2",
    )
    assert first.canonical_sha256 != second.canonical_sha256


def test_scientific_assertion_basis_requires_exact_revision() -> None:
    with pytest.raises(ValueError, match="exact reference_revision"):
        QuantityBasisV1(
            kind="scientific_assertion",
            reference_id="assertion-1",
        )


def test_water_exchange_records_exact_intervention_parameters_and_sha() -> None:
    intervention = WaterExchangeInterventionV1(
        id="exchange-audit",
        water_zone_id="water",
        removed_volume_decimal="25",
        removed_volume_unit="L",
        replacement_volume_decimal="20",
        replacement_volume_unit="L",
        replacement_composition=(
            _zero_replacement("reduced_inorganic_nitrogen"),
            _zero_replacement("oxidized_inorganic_nitrogen"),
        ),
        basis=_basis("observation", "exchange-observation"),
    )
    _, evaluation = evaluate_well_mixed_water_exchange_v1(
        _state(),
        intervention,
        evaluation_id="eval-exchange-audit",
    )

    params = evaluation.parameters_payload
    assert params["intervention"] == intervention.canonical_payload()
    assert params["intervention_sha256"] == intervention.canonical_sha256
    removed = params["intervention"]["removed_volume"]
    assert removed == {
        "unit": "L",
        "value": {"type": "decimal", "value": "25"},
    }


def test_water_exchange_rejects_nonpositive_current_volume() -> None:
    state = _state().replace_quantities(
        (
            CanonicalQuantityV1(
                variable_id=WATER_VOLUME_VARIABLE_ID,
                value_decimal="0",
                unit="L",
                basis=_basis(),
                zone_id="water",
            ),
        )
    )
    intervention = WaterExchangeInterventionV1(
        id="exchange-zero-volume",
        water_zone_id="water",
        removed_volume_decimal="0",
        removed_volume_unit="L",
        replacement_volume_decimal="10",
        replacement_volume_unit="L",
        replacement_composition=(
            _zero_replacement("reduced_inorganic_nitrogen"),
            _zero_replacement("oxidized_inorganic_nitrogen"),
        ),
        basis=_basis(),
    )
    with pytest.raises(ValueError, match="positive current water volume"):
        evaluate_well_mixed_water_exchange_v1(
            state,
            intervention,
            evaluation_id="eval-zero-volume",
        )


def test_state_replacement_logical_step_must_advance() -> None:
    with pytest.raises(ValueError, match="must advance"):
        _state().replace_quantities(
            (
                CanonicalQuantityV1(
                    variable_id=WATER_VOLUME_VARIABLE_ID,
                    value_decimal="200",
                    unit="L",
                    basis=_basis(),
                    zone_id="water",
                ),
            ),
            logical_step=0,
        )


def test_water_exchange_same_evaluator_supports_pond_fixture() -> None:
    fixture = (
        Path(__file__).parent
        / "fixtures"
        / "ecosystem_profiles"
        / "pond_v1.json"
    )
    profile = ecosystem_profile_from_mapping_v1(
        json.loads(fixture.read_text(encoding="utf-8"))
    )
    assert any(zone.id == "water" for zone in profile.zones)

    basis = _basis()
    pond_state = EcosystemStateV1(
        profile_id=profile.id,
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
    intervention = WaterExchangeInterventionV1(
        id="pond-exchange",
        water_zone_id="water",
        removed_volume_decimal="50",
        removed_volume_unit="L",
        replacement_volume_decimal="50",
        replacement_volume_unit="L",
        replacement_composition=(
            _zero_replacement("reduced_inorganic_nitrogen"),
            _zero_replacement("oxidized_inorganic_nitrogen"),
        ),
        basis=basis,
    )
    output, evaluation = evaluate_well_mixed_water_exchange_v1(
        pond_state,
        intervention,
        evaluation_id="pond-eval",
    )
    assert output.profile_id == profile.id
    assert evaluation.profile_id == profile.id


def test_water_exchange_rejects_negative_material_inventory() -> None:
    state = _state().replace_quantities(
        (
            CanonicalQuantityV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                value_decimal="-1",
                unit="mg N",
                basis=_basis(),
                zone_id="water",
                material_component_id="reduced_inorganic_nitrogen",
            ),
        )
    )
    intervention = WaterExchangeInterventionV1(
        id="exchange-negative-mass",
        water_zone_id="water",
        removed_volume_decimal="1",
        removed_volume_unit="L",
        replacement_volume_decimal="1",
        replacement_volume_unit="L",
        replacement_composition=(
            _zero_replacement("reduced_inorganic_nitrogen"),
            _zero_replacement("oxidized_inorganic_nitrogen"),
        ),
        basis=_basis(),
    )
    with pytest.raises(ValueError, match="inventories cannot be negative"):
        evaluate_well_mixed_water_exchange_v1(
            state,
            intervention,
            evaluation_id="eval-negative-mass",
        )



def test_process_evaluation_rejects_mechanism_supported_in_n4_v1() -> None:
    _, evaluation = evaluate_nitrogen_transformation_extent_v1(
        _state(),
        zone_id="water",
        source_component_id="reduced_inorganic_nitrogen",
        target_component_id="oxidized_inorganic_nitrogen",
        extent_decimal="5",
        extent_unit="mg N",
        extent_basis=_basis("observation", "extent-observation"),
        evaluation_id="eval-no-promotion",
        scientific_assertion_refs=(
            ScientificAssertionRefV1(
                assertion_id="assertion-1",
                assertion_revision=1,
                canonical_payload_sha256="c" * 64,
            ),
        ),
    )
    with pytest.raises(ValueError, match="unsupported support_status"):
        ProcessEvaluationV1(
            evaluation_id="eval-forged-support",
            definition=evaluation.definition,
            profile_id=evaluation.profile_id,
            input_state_sha256=evaluation.input_state_sha256,
            output_state_sha256=evaluation.output_state_sha256,
            parameters_json=evaluation.parameters_json,
            support_status="mechanism_supported",
            parameter_bases=evaluation.parameter_bases,
            scientific_assertion_refs=evaluation.scientific_assertion_refs,
            deltas=evaluation.deltas,
            assumptions=evaluation.assumptions,
            warnings=evaluation.warnings,
            unknowns=evaluation.unknowns,
        )
