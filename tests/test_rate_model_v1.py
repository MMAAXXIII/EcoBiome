from __future__ import annotations

from dataclasses import fields

import pytest

from ecobiome.simulation.ecosystem_state_v1 import (
    CanonicalQuantityV1,
    EcosystemStateV1,
    QuantityBasisV1,
)
from ecobiome.simulation.process_v1 import ScientificAssertionRefV1
from ecobiome.simulation.rate_model_v1 import (
    RateApplicabilityResultV1,
    RateEvaluationV1,
    RateInputQuantityBindingV1,
    RateModelDefinitionV1,
    RateParameterSetV1,
    RateParameterV1,
    RateQuantityRequirementV1,
    RateScientificSupportV1,
    bind_rate_quantity_v1,
)


def _assertion_ref(seed: str) -> ScientificAssertionRefV1:
    return ScientificAssertionRefV1(
        assertion_id=f"assertion-{seed}",
        assertion_revision=1,
        canonical_payload_sha256=seed * 64,
    )


def _support(role: str, seed: str) -> RateScientificSupportV1:
    return RateScientificSupportV1(
        role=role,
        support_id=f"support-{role}-{seed}",
        support_sha256=seed * 64,
        assertion_ref=_assertion_ref(seed),
        reviewed_by="human",
        applicability_scope=f"scope-{seed}",
    )


def _requirements() -> tuple[RateQuantityRequirementV1, ...]:
    return (
        RateQuantityRequirementV1(
            requirement_id="substrate",
            variable_id="material_concentration",
            unit="mg N/L",
            semantic_role="kinetic_substrate",
            material_component_id="tan_n",
        ),
        RateQuantityRequirementV1(
            requirement_id="biofilter_area",
            variable_id="biofilter_surface_area",
            unit="m2",
            semantic_role="absolute_rate_scaling",
            zone_required=False,
        ),
    )


def _definition(*, complete_support: bool = True) -> RateModelDefinitionV1:
    supports = (
        (
            _support("kinetic_form", "a"),
            _support("applicability_domain", "b"),
        )
        if complete_support
        else (_support("kinetic_form", "a"),)
    )
    return RateModelDefinitionV1(
        rate_model_id="test-rate-model",
        version="1",
        process_id="test-process",
        process_version="1",
        source_component_id="tan_n",
        target_component_id="nitrite_n",
        required_state_quantities=_requirements(),
        required_parameters=("test_rate_coefficient",),
        scientific_supports=supports,
        assumptions=("test_only_no_concrete_nitrification_formula",),
    )


def _parameter(*, reviewed: bool = True) -> RateParameterV1:
    return RateParameterV1(
        parameter_id="test_rate_coefficient",
        value_decimal="2",
        unit="m/h",
        semantic_role="test_coefficient",
        scientific_supports=(
            (_support("kinetic_parameter", "c"),) if reviewed else ()
        ),
        applicability_scope="test-only",
    )


def _state() -> EcosystemStateV1:
    observed = QuantityBasisV1(
        kind="observation",
        reference_id="measurement-1",
    )
    return EcosystemStateV1(
        profile_id="profile-test",
        quantities=(
            CanonicalQuantityV1(
                variable_id="material_concentration",
                value_decimal="0.2",
                unit="mg N/L",
                basis=observed,
                zone_id="water",
                material_component_id="tan_n",
            ),
            CanonicalQuantityV1(
                variable_id="biofilter_surface_area",
                value_decimal="1.5",
                unit="m2",
                basis=QuantityBasisV1(
                    kind="observation",
                    reference_id="filter-area-1",
                ),
            ),
        ),
    )


def _bindings(
    state: EcosystemStateV1,
    definition: RateModelDefinitionV1,
) -> tuple[RateInputQuantityBindingV1, ...]:
    by_id = {
        item.requirement_id: item
        for item in definition.required_state_quantities
    }
    return (
        bind_rate_quantity_v1(
            state,
            by_id["substrate"],
            zone_id="water",
        ),
        bind_rate_quantity_v1(
            state,
            by_id["biofilter_area"],
            zone_id=None,
        ),
    )


def test_definition_is_canonical_across_requirement_and_support_order() -> None:
    first = _definition()
    second = RateModelDefinitionV1(
        rate_model_id=first.rate_model_id,
        version=first.version,
        process_id=first.process_id,
        process_version=first.process_version,
        source_component_id=first.source_component_id,
        target_component_id=first.target_component_id,
        required_state_quantities=tuple(reversed(first.required_state_quantities)),
        required_parameters=tuple(reversed(first.required_parameters)),
        scientific_supports=tuple(reversed(first.scientific_supports)),
        assumptions=first.assumptions,
    )
    assert first.canonical_payload() == second.canonical_payload()
    assert first.canonical_sha256 == second.canonical_sha256


def test_rate_model_output_unit_is_fixed_to_mg_n_per_hour() -> None:
    with pytest.raises(ValueError, match="output_rate_unit"):
        RateModelDefinitionV1(
            rate_model_id="bad-unit",
            version="1",
            process_id="p",
            process_version="1",
            source_component_id="a",
            target_component_id="b",
            required_state_quantities=_requirements(),
            required_parameters=(),
            output_rate_unit="g N/d",
        )


@pytest.mark.parametrize(
    "forbidden",
    ["dt", "duration", "elapsed_time", "time_step", "timestep"],
)
def test_definition_rejects_hidden_integration_parameter_ids(
    forbidden: str,
) -> None:
    with pytest.raises(ValueError, match="integration-time"):
        RateModelDefinitionV1(
            rate_model_id="no-hidden-time",
            version="1",
            process_id="p",
            process_version="1",
            source_component_id="a",
            target_component_id="b",
            required_state_quantities=_requirements(),
            required_parameters=(forbidden,),
        )


def test_mechanism_role_cannot_be_used_as_rate_support() -> None:
    with pytest.raises(ValueError, match="unsupported RateModel"):
        _support("mechanism", "d")


def test_parameter_rejects_non_parameter_support_role() -> None:
    with pytest.raises(ValueError, match="kinetic_parameter"):
        RateParameterV1(
            parameter_id="x",
            value_decimal="1",
            unit="m/h",
            semantic_role="x",
            scientific_supports=(_support("kinetic_form", "a"),),
        )


def test_parameter_set_is_canonical_and_requires_unique_ids() -> None:
    a = _parameter()
    b = RateParameterV1(
        parameter_id="another",
        value_decimal="3",
        unit="1/h",
        semantic_role="test",
        scientific_supports=(_support("kinetic_parameter", "d"),),
    )
    first = RateParameterSetV1(
        parameter_set_id="set",
        parameters=(a, b),
    )
    second = RateParameterSetV1(
        parameter_set_id="set",
        parameters=(b, a),
    )
    assert first.canonical_sha256 == second.canonical_sha256
    with pytest.raises(ValueError, match="unique"):
        RateParameterSetV1(
            parameter_set_id="duplicate",
            parameters=(a, a),
        )


def test_bind_rate_quantity_records_exact_input_state_identity() -> None:
    state = _state()
    requirement = _requirements()[0]
    binding = bind_rate_quantity_v1(
        state,
        requirement,
        zone_id="water",
    )
    assert binding.input_state_sha256 == state.canonical_sha256
    assert binding.requirement_id == "substrate"
    assert binding.value_decimal == "0.2"
    assert binding.unit == "mg N/L"


def test_bind_rate_quantity_rejects_wrong_unit() -> None:
    state = _state()
    requirement = RateQuantityRequirementV1(
        requirement_id="substrate",
        variable_id="material_concentration",
        unit="g N/L",
        semantic_role="kinetic_substrate",
        material_component_id="tan_n",
    )
    with pytest.raises(ValueError, match="unit mismatch"):
        bind_rate_quantity_v1(
            state,
            requirement,
            zone_id="water",
        )


def test_applicable_evaluation_requires_complete_reviewed_boundary() -> None:
    definition = _definition()
    state = _state()
    parameter_set = RateParameterSetV1(
        parameter_set_id="supported",
        parameters=(_parameter(),),
    )
    evaluation = RateEvaluationV1(
        evaluation_id="rate-eval",
        definition=definition,
        profile_id=state.profile_id,
        input_state_sha256=state.canonical_sha256,
        zone_id="water",
        applicability=RateApplicabilityResultV1(status="applicable"),
        quantity_bindings=_bindings(state, definition),
        parameter_set=parameter_set,
        rate_decimal="0.3",
        rate_unit="mg N/h",
    )
    assert evaluation.rate_decimal == "0.3"
    assert evaluation.rate_unit == "mg N/h"
    assert evaluation.canonical_sha256 == RateEvaluationV1(
        evaluation_id="rate-eval",
        definition=definition,
        profile_id=state.profile_id,
        input_state_sha256=state.canonical_sha256,
        zone_id="water",
        applicability=RateApplicabilityResultV1(status="applicable"),
        quantity_bindings=tuple(reversed(_bindings(state, definition))),
        parameter_set=parameter_set,
        rate_decimal="0.30",
        rate_unit="mg N/h",
    ).canonical_sha256


def test_applicable_evaluation_rejects_incomplete_definition_support() -> None:
    definition = _definition(complete_support=False)
    state = _state()
    with pytest.raises(ValueError, match="kinetic_form and applicability_domain"):
        RateEvaluationV1(
            evaluation_id="blocked",
            definition=definition,
            profile_id=state.profile_id,
            input_state_sha256=state.canonical_sha256,
            zone_id="water",
            applicability=RateApplicabilityResultV1(status="applicable"),
            quantity_bindings=_bindings(state, definition),
            parameter_set=RateParameterSetV1(
                parameter_set_id="supported",
                parameters=(_parameter(),),
            ),
            rate_decimal="0.3",
            rate_unit="mg N/h",
        )


def test_applicable_evaluation_rejects_unreviewed_parameter() -> None:
    definition = _definition()
    state = _state()
    with pytest.raises(ValueError, match="every numeric parameter"):
        RateEvaluationV1(
            evaluation_id="blocked",
            definition=definition,
            profile_id=state.profile_id,
            input_state_sha256=state.canonical_sha256,
            zone_id="water",
            applicability=RateApplicabilityResultV1(status="applicable"),
            quantity_bindings=_bindings(state, definition),
            parameter_set=RateParameterSetV1(
                parameter_set_id="unsupported",
                parameters=(_parameter(reviewed=False),),
            ),
            rate_decimal="0.3",
            rate_unit="mg N/h",
        )


def test_applicable_evaluation_rejects_missing_quantity_binding() -> None:
    definition = _definition()
    state = _state()
    with pytest.raises(ValueError, match="all state quantity bindings"):
        RateEvaluationV1(
            evaluation_id="blocked",
            definition=definition,
            profile_id=state.profile_id,
            input_state_sha256=state.canonical_sha256,
            zone_id="water",
            applicability=RateApplicabilityResultV1(status="applicable"),
            quantity_bindings=_bindings(state, definition)[:1],
            parameter_set=RateParameterSetV1(
                parameter_set_id="supported",
                parameters=(_parameter(),),
            ),
            rate_decimal="0.3",
            rate_unit="mg N/h",
        )


def test_applicable_evaluation_rejects_wrong_parameter_coverage() -> None:
    definition = _definition()
    state = _state()
    with pytest.raises(ValueError, match="exactly cover"):
        RateEvaluationV1(
            evaluation_id="blocked",
            definition=definition,
            profile_id=state.profile_id,
            input_state_sha256=state.canonical_sha256,
            zone_id="water",
            applicability=RateApplicabilityResultV1(status="applicable"),
            quantity_bindings=_bindings(state, definition),
            parameter_set=RateParameterSetV1(
                parameter_set_id="wrong",
                parameters=(),
            ),
            rate_decimal="0.3",
            rate_unit="mg N/h",
        )


def test_non_applicable_evaluation_cannot_carry_rate() -> None:
    definition = _definition()
    state = _state()
    with pytest.raises(ValueError, match="cannot carry"):
        RateEvaluationV1(
            evaluation_id="blocked",
            definition=definition,
            profile_id=state.profile_id,
            input_state_sha256=state.canonical_sha256,
            zone_id="water",
            applicability=RateApplicabilityResultV1(
                status="outside_reviewed_domain",
                reason_codes=("temperature_outside_domain",),
            ),
            quantity_bindings=_bindings(state, definition),
            parameter_set=None,
            rate_decimal="0.3",
            rate_unit="mg N/h",
        )


def test_non_applicable_evaluation_can_record_fail_closed_result() -> None:
    definition = _definition(complete_support=False)
    state = _state()
    evaluation = RateEvaluationV1(
        evaluation_id="blocked",
        definition=definition,
        profile_id=state.profile_id,
        input_state_sha256=state.canonical_sha256,
        zone_id="water",
        applicability=RateApplicabilityResultV1(
            status="scientific_support_missing",
            reason_codes=("applicability_support_missing",),
        ),
        quantity_bindings=(),
        parameter_set=None,
        rate_decimal=None,
        rate_unit=None,
    )
    assert evaluation.rate_decimal is None
    assert evaluation.canonical_payload()["rate"] is None


def test_negative_rate_is_rejected() -> None:
    definition = _definition()
    state = _state()
    with pytest.raises(ValueError, match="cannot be negative"):
        RateEvaluationV1(
            evaluation_id="negative",
            definition=definition,
            profile_id=state.profile_id,
            input_state_sha256=state.canonical_sha256,
            zone_id="water",
            applicability=RateApplicabilityResultV1(status="applicable"),
            quantity_bindings=_bindings(state, definition),
            parameter_set=RateParameterSetV1(
                parameter_set_id="supported",
                parameters=(_parameter(),),
            ),
            rate_decimal="-0.1",
            rate_unit="mg N/h",
        )


def test_rate_evaluation_contract_has_no_output_state_or_time_step_fields() -> None:
    names = {item.name for item in fields(RateEvaluationV1)}
    assert "output_state_sha256" not in names
    assert "duration" not in names
    assert "dt" not in names
    assert "elapsed_time" not in names
    assert "time_step" not in names
