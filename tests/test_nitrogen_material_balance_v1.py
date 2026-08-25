from __future__ import annotations

from decimal import Decimal

import pytest

from ecobiome.simulation.ecosystem_state_v1 import (
    CanonicalQuantityV1,
    EcosystemStateV1,
    QuantityBasisV1,
)
from ecobiome.simulation.nitrogen_material_balance_v1 import (
    AMMONIA_OXIDATION_TO_NITRITE_EXTENT_V1,
    NITRITE_OXIDATION_TO_NITRATE_EXTENT_V1,
    admitted_two_step_nitrogen_pairs_v1,
    evaluate_two_step_nitrogen_extent_v1,
    primary_predictive_nitrogen_components_v1,
)
from ecobiome.simulation.nitrogen_state_v1 import (
    MATERIAL_INVENTORY_VARIABLE_ID,
    NITRATE_NITROGEN_COMPONENT_ID,
    NITRITE_NITROGEN_COMPONENT_ID,
    TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
    WATER_VOLUME_VARIABLE_ID,
    validate_predictive_nitrogen_state_v1,
)
from ecobiome.simulation.process_v1 import (
    ProcessScientificEvaluationScopeV1,
    ProcessScientificParameterBindingV1,
    ProcessScientificSupportV1,
    ScientificAssertionRefV1,
)


def _basis(
    reference_id: str = "scenario-explicit-extent",
) -> QuantityBasisV1:
    return QuantityBasisV1(
        kind="user_assumption",
        reference_id=reference_id,
    )


def _observed(reference_id: str) -> QuantityBasisV1:
    return QuantityBasisV1(
        kind="observation",
        reference_id=reference_id,
    )


def _inventory(
    component_id: str,
    value: str,
    *,
    zone_id: str = "water",
) -> CanonicalQuantityV1:
    return CanonicalQuantityV1(
        variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
        value_decimal=value,
        unit="mg N",
        basis=_observed(f"inventory-{component_id}"),
        zone_id=zone_id,
        material_component_id=component_id,
    )


def _state(
    *,
    tan: str = "10",
    nitrite: str = "2",
    nitrate: str = "5",
    extra: tuple[CanonicalQuantityV1, ...] = (),
) -> EcosystemStateV1:
    return EcosystemStateV1(
        profile_id="profile-rate-1f",
        quantities=(
            CanonicalQuantityV1(
                variable_id=WATER_VOLUME_VARIABLE_ID,
                value_decimal="100",
                unit="L",
                basis=_observed("water-volume"),
                zone_id="water",
            ),
            _inventory(TOTAL_AMMONIA_NITROGEN_COMPONENT_ID, tan),
            _inventory(NITRITE_NITROGEN_COMPONENT_ID, nitrite),
            _inventory(NITRATE_NITROGEN_COMPONENT_ID, nitrate),
            *extra,
        ),
    )


def _primary_values(
    state: EcosystemStateV1,
) -> dict[str, Decimal]:
    validation = validate_predictive_nitrogen_state_v1(
        state,
        zone_id="water",
    )
    return {
        item.component_id: item.decimal
        for item in validation.inventories
    }


def _primary_total(state: EcosystemStateV1) -> Decimal:
    return sum(_primary_values(state).values(), Decimal(0))


def test_two_step_process_definitions_are_exact() -> None:
    assert AMMONIA_OXIDATION_TO_NITRITE_EXTENT_V1.process_id == (
        "ammonia_oxidation_to_nitrite_extent_v1"
    )
    assert NITRITE_OXIDATION_TO_NITRATE_EXTENT_V1.process_id == (
        "nitrite_oxidation_to_nitrate_extent_v1"
    )
    assert AMMONIA_OXIDATION_TO_NITRITE_EXTENT_V1.required_scientific_assertion_roles == (
        "mechanism",
    )
    assert NITRITE_OXIDATION_TO_NITRATE_EXTENT_V1.required_scientific_assertion_roles == (
        "mechanism",
    )
    assert admitted_two_step_nitrogen_pairs_v1() == (
        (
            TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
            NITRITE_NITROGEN_COMPONENT_ID,
        ),
        (
            NITRITE_NITROGEN_COMPONENT_ID,
            NITRATE_NITROGEN_COMPONENT_ID,
        ),
    )
    assert primary_predictive_nitrogen_components_v1() == (
        TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
        NITRITE_NITROGEN_COMPONENT_ID,
        NITRATE_NITROGEN_COMPONENT_ID,
    )


def test_ammonia_to_nitrite_transfer_is_exact_and_conservative() -> None:
    state = _state()
    before_sha = state.canonical_sha256
    before_total = _primary_total(state)

    output, evaluation = evaluate_two_step_nitrogen_extent_v1(
        state,
        zone_id="water",
        source_component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
        target_component_id=NITRITE_NITROGEN_COMPONENT_ID,
        extent_decimal="1",
        extent_unit="mg N",
        extent_basis=_basis(),
        evaluation_id="ammonia-step",
    )

    assert state.canonical_sha256 == before_sha
    assert _primary_values(output) == {
        TOTAL_AMMONIA_NITROGEN_COMPONENT_ID: Decimal(9),
        NITRITE_NITROGEN_COMPONENT_ID: Decimal(3),
        NITRATE_NITROGEN_COMPONENT_ID: Decimal(5),
    }
    assert _primary_total(output) == before_total
    assert evaluation.definition == AMMONIA_OXIDATION_TO_NITRITE_EXTENT_V1
    assert evaluation.support_status == "scenario_hypothesis"
    assert evaluation.input_state_sha256 == before_sha
    assert evaluation.output_state_sha256 == output.canonical_sha256
    assert len(evaluation.deltas) == 2


def test_nitrite_to_nitrate_transfer_is_exact_and_conservative() -> None:
    state = _state()
    before_total = _primary_total(state)

    output, evaluation = evaluate_two_step_nitrogen_extent_v1(
        state,
        zone_id="water",
        source_component_id=NITRITE_NITROGEN_COMPONENT_ID,
        target_component_id=NITRATE_NITROGEN_COMPONENT_ID,
        extent_decimal="0.5",
        extent_unit="mg N",
        extent_basis=_basis(),
        evaluation_id="nitrite-step",
    )

    assert _primary_values(output) == {
        TOTAL_AMMONIA_NITROGEN_COMPONENT_ID: Decimal(10),
        NITRITE_NITROGEN_COMPONENT_ID: Decimal("1.5"),
        NITRATE_NITROGEN_COMPONENT_ID: Decimal("5.5"),
    }
    assert _primary_total(output) == before_total
    assert evaluation.definition == NITRITE_OXIDATION_TO_NITRATE_EXTENT_V1


def test_sequential_two_step_transfer_preserves_total_nitrogen() -> None:
    initial = _state()
    after_ammonia, first = evaluate_two_step_nitrogen_extent_v1(
        initial,
        zone_id="water",
        source_component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
        target_component_id=NITRITE_NITROGEN_COMPONENT_ID,
        extent_decimal="1",
        extent_unit="mg N",
        extent_basis=_basis("step-1"),
        evaluation_id="step-1",
    )
    final, second = evaluate_two_step_nitrogen_extent_v1(
        after_ammonia,
        zone_id="water",
        source_component_id=NITRITE_NITROGEN_COMPONENT_ID,
        target_component_id=NITRATE_NITROGEN_COMPONENT_ID,
        extent_decimal="0.5",
        extent_unit="mg N",
        extent_basis=_basis("step-2"),
        evaluation_id="step-2",
    )

    assert _primary_values(final) == {
        TOTAL_AMMONIA_NITROGEN_COMPONENT_ID: Decimal(9),
        NITRITE_NITROGEN_COMPONENT_ID: Decimal("2.5"),
        NITRATE_NITROGEN_COMPONENT_ID: Decimal("5.5"),
    }
    assert _primary_total(initial) == _primary_total(after_ammonia)
    assert _primary_total(after_ammonia) == _primary_total(final)
    assert first.output_state_sha256 == second.input_state_sha256


def test_zero_extent_is_an_exact_identity_on_values_but_advances_state() -> None:
    state = _state()
    output, evaluation = evaluate_two_step_nitrogen_extent_v1(
        state,
        zone_id="water",
        source_component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
        target_component_id=NITRITE_NITROGEN_COMPONENT_ID,
        extent_decimal="0",
        extent_unit="mg N",
        extent_basis=_basis(),
        evaluation_id="zero",
    )
    assert _primary_values(output) == _primary_values(state)
    assert output.logical_step == state.logical_step + 1
    assert evaluation.output_state_sha256 == output.canonical_sha256


def test_extent_cannot_exceed_source_inventory() -> None:
    with pytest.raises(ValueError, match="exceeds source inventory"):
        evaluate_two_step_nitrogen_extent_v1(
            _state(tan="1"),
            zone_id="water",
            source_component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
            target_component_id=NITRITE_NITROGEN_COMPONENT_ID,
            extent_decimal="1.1",
            extent_unit="mg N",
            extent_basis=_basis(),
            evaluation_id="too-large",
        )


def test_negative_extent_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        evaluate_two_step_nitrogen_extent_v1(
            _state(),
            zone_id="water",
            source_component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
            target_component_id=NITRITE_NITROGEN_COMPONENT_ID,
            extent_decimal="-0.1",
            extent_unit="mg N",
            extent_basis=_basis(),
            evaluation_id="negative",
        )


@pytest.mark.parametrize("bad_unit", ["g N", "mg", "mg N/h"])
def test_extent_requires_exact_mg_n_unit(bad_unit: str) -> None:
    with pytest.raises(ValueError, match="must use exactly 'mg N'"):
        evaluate_two_step_nitrogen_extent_v1(
            _state(),
            zone_id="water",
            source_component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
            target_component_id=NITRITE_NITROGEN_COMPONENT_ID,
            extent_decimal="1",
            extent_unit=bad_unit,
            extent_basis=_basis(),
            evaluation_id="bad-unit",
        )


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (
            NITRITE_NITROGEN_COMPONENT_ID,
            TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
        ),
        (
            TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
            NITRATE_NITROGEN_COMPONENT_ID,
        ),
        (
            NITRATE_NITROGEN_COMPONENT_ID,
            NITRITE_NITROGEN_COMPONENT_ID,
        ),
    ],
)
def test_only_two_forward_predictive_edges_are_admitted(
    source: str,
    target: str,
) -> None:
    with pytest.raises(ValueError, match="unsupported two-step"):
        evaluate_two_step_nitrogen_extent_v1(
            _state(),
            zone_id="water",
            source_component_id=source,
            target_component_id=target,
            extent_decimal="0.1",
            extent_unit="mg N",
            extent_basis=_basis(),
            evaluation_id="unsupported",
        )


def test_incomplete_predictive_state_is_rejected() -> None:
    state = _state()
    incomplete = EcosystemStateV1(
        profile_id=state.profile_id,
        quantities=tuple(
            item
            for item in state.quantities
            if item.material_component_id != NITRATE_NITROGEN_COMPONENT_ID
        ),
    )
    with pytest.raises(ValueError, match="missing primary inventory"):
        evaluate_two_step_nitrogen_extent_v1(
            incomplete,
            zone_id="water",
            source_component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
            target_component_id=NITRITE_NITROGEN_COMPONENT_ID,
            extent_decimal="0.1",
            extent_unit="mg N",
            extent_basis=_basis(),
            evaluation_id="incomplete",
        )


def test_overlapping_predictive_state_is_rejected() -> None:
    overlapping = _state(
        extra=(
            _inventory("ammonium_nitrogen", "1"),
        )
    )
    with pytest.raises(ValueError, match="overlapping primary inventory"):
        evaluate_two_step_nitrogen_extent_v1(
            overlapping,
            zone_id="water",
            source_component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
            target_component_id=NITRITE_NITROGEN_COMPONENT_ID,
            extent_decimal="0.1",
            extent_unit="mg N",
            extent_basis=_basis(),
            evaluation_id="overlap",
        )


def test_assertion_ref_without_reviewed_alignment_remains_support_missing() -> None:
    assertion_ref = ScientificAssertionRefV1(
        assertion_id="synthetic-two-step-mechanism",
        assertion_revision=1,
        canonical_payload_sha256="a" * 64,
    )
    _, evaluation = evaluate_two_step_nitrogen_extent_v1(
        _state(),
        zone_id="water",
        source_component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
        target_component_id=NITRITE_NITROGEN_COMPONENT_ID,
        extent_decimal="0.1",
        extent_unit="mg N",
        extent_basis=_basis(),
        evaluation_id="ref-only",
        scientific_assertion_refs=(assertion_ref,),
    )
    assert evaluation.support_status == "support_missing"
    assert evaluation.scientific_supports == ()


def test_exact_future_reviewed_support_can_attach_without_changing_balance() -> None:
    assertion_ref = ScientificAssertionRefV1(
        assertion_id="synthetic-reviewed-ammonia-to-nitrite",
        assertion_revision=1,
        canonical_payload_sha256="b" * 64,
    )
    scope = ProcessScientificEvaluationScopeV1(
        process_id=AMMONIA_OXIDATION_TO_NITRITE_EXTENT_V1.process_id,
        process_version=AMMONIA_OXIDATION_TO_NITRITE_EXTENT_V1.version,
        role="mechanism",
        required_parameter_bindings=(
            ProcessScientificParameterBindingV1(
                json_pointer="/source_component_id",
                expected_value_json='"total_ammonia_nitrogen"',
            ),
            ProcessScientificParameterBindingV1(
                json_pointer="/target_component_id",
                expected_value_json='"nitrite_nitrogen"',
            ),
        ),
    )
    support = ProcessScientificSupportV1(
        role="mechanism",
        assertion_ref=assertion_ref,
        alignment_class="direct_mechanism_support",
        epistemic_class="explicit_causal_result",
        alignment_policy_name="synthetic-test-policy",
        alignment_policy_version="1",
        alignment_policy_sha256="c" * 64,
        evaluation_scope=scope,
        evaluation_scope_sha256=scope.canonical_sha256,
    )

    state = _state()
    output, evaluation = evaluate_two_step_nitrogen_extent_v1(
        state,
        zone_id="water",
        source_component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
        target_component_id=NITRITE_NITROGEN_COMPONENT_ID,
        extent_decimal="0.1",
        extent_unit="mg N",
        extent_basis=_basis(),
        evaluation_id="reviewed-synthetic",
        scientific_assertion_refs=(assertion_ref,),
        scientific_supports=(support,),
    )
    assert evaluation.support_status == "scientific_alignment_reviewed"
    assert evaluation.scientific_supports == (support,)
    assert _primary_total(output) == _primary_total(state)


def test_parameters_record_exact_validation_and_total_identities() -> None:
    state = _state()
    output, evaluation = evaluate_two_step_nitrogen_extent_v1(
        state,
        zone_id="water",
        source_component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
        target_component_id=NITRITE_NITROGEN_COMPONENT_ID,
        extent_decimal="1",
        extent_unit="mg N",
        extent_basis=_basis(),
        evaluation_id="audit-identities",
    )
    before = validate_predictive_nitrogen_state_v1(
        state,
        zone_id="water",
    )
    after = validate_predictive_nitrogen_state_v1(
        output,
        zone_id="water",
    )
    parameters = evaluation.parameters_payload
    assert parameters["predictive_nitrogen_validation_before_sha256"] == (
        before.canonical_sha256
    )
    assert parameters["predictive_nitrogen_validation_after_sha256"] == (
        after.canonical_sha256
    )
    assert parameters["primary_nitrogen_total_before"] == {
        "value": {"type": "decimal", "value": "17"},
        "unit": "mg N",
    }
    assert parameters["primary_nitrogen_total_after"] == {
        "value": {"type": "decimal", "value": "17"},
        "unit": "mg N",
    }
