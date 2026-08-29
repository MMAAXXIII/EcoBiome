"""Deterministic two-step predictive nitrogen material-balance contracts.

RATE-1F transfers an explicit elemental-N extent between the canonical
RATE-1D/RATE-1E predictive inventories.  It does not calculate the extent,
does not integrate over time, and does not implement a kinetic rate law.
"""

from __future__ import annotations

from decimal import Decimal

from ecobiome.knowledge_persistence.serialization import (
    canonical_json_text,
    normalize_decimal,
)
from ecobiome.simulation.ecosystem_state_v1 import (
    CanonicalQuantityV1,
    EcosystemStateV1,
    QuantityBasisV1,
)
from ecobiome.simulation.nitrogen_state_v1 import (
    CANONICAL_NITROGEN_INVENTORY_UNIT,
    MATERIAL_INVENTORY_VARIABLE_ID,
    NITRATE_NITROGEN_COMPONENT_ID,
    NITRITE_NITROGEN_COMPONENT_ID,
    PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_IDS,
    TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
    validate_predictive_nitrogen_state_v1,
)
from ecobiome.simulation.process_v1 import (
    ProcessDefinitionV1,
    ProcessDeltaV1,
    ProcessEvaluationV1,
    ProcessScientificSupportV1,
    ScientificAssertionRefV1,
)

AMMONIA_OXIDATION_TO_NITRITE_EXTENT_V1 = ProcessDefinitionV1(
    process_id="ammonia_oxidation_to_nitrite_extent_v1",
    version="1",
    label="Elemental-N transfer from TAN-N to nitrite-N by explicit extent",
    input_variables=(MATERIAL_INVENTORY_VARIABLE_ID, "process_extent"),
    output_variables=(MATERIAL_INVENTORY_VARIABLE_ID,),
    assumptions=(
        "elemental_nitrogen_mass_is_conserved_within_transformation",
        "extent_is_supplied_externally_and_is_not_calculated_by_material_balance",
        "predictive_nitrogen_state_uses_non_overlapping_RATE_1D_components",
    ),
    required_scientific_assertion_roles=("mechanism",),
)

NITRITE_OXIDATION_TO_NITRATE_EXTENT_V1 = ProcessDefinitionV1(
    process_id="nitrite_oxidation_to_nitrate_extent_v1",
    version="1",
    label="Elemental-N transfer from nitrite-N to nitrate-N by explicit extent",
    input_variables=(MATERIAL_INVENTORY_VARIABLE_ID, "process_extent"),
    output_variables=(MATERIAL_INVENTORY_VARIABLE_ID,),
    assumptions=(
        "elemental_nitrogen_mass_is_conserved_within_transformation",
        "extent_is_supplied_externally_and_is_not_calculated_by_material_balance",
        "predictive_nitrogen_state_uses_non_overlapping_RATE_1D_components",
    ),
    required_scientific_assertion_roles=("mechanism",),
)

_TWO_STEP_PROCESS_DEFINITION_BY_PAIR = {
    (
        TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
        NITRITE_NITROGEN_COMPONENT_ID,
    ): AMMONIA_OXIDATION_TO_NITRITE_EXTENT_V1,
    (
        NITRITE_NITROGEN_COMPONENT_ID,
        NITRATE_NITROGEN_COMPONENT_ID,
    ): NITRITE_OXIDATION_TO_NITRATE_EXTENT_V1,
}


def _derived_basis(evaluation_id: str) -> QuantityBasisV1:
    return QuantityBasisV1(
        kind="derived",
        reference_id=evaluation_id,
        note="explicit RATE-1F two-step nitrogen transformation extent",
    )


def _primary_total(
    state: EcosystemStateV1,
    *,
    zone_id: str,
) -> Decimal:
    validation = validate_predictive_nitrogen_state_v1(
        state,
        zone_id=zone_id,
    )
    return sum(
        (item.decimal for item in validation.inventories),
        Decimal(0),
    )


def evaluate_two_step_nitrogen_extent_v1(
    state: EcosystemStateV1,
    *,
    zone_id: str,
    source_component_id: str,
    target_component_id: str,
    extent_decimal: str | int | Decimal,
    extent_unit: str,
    extent_basis: QuantityBasisV1,
    evaluation_id: str,
    scientific_assertion_refs: tuple[ScientificAssertionRefV1, ...] = (),
    scientific_supports: tuple[ProcessScientificSupportV1, ...] = (),
) -> tuple[EcosystemStateV1, ProcessEvaluationV1]:
    """Transfer an explicit `mg N` extent along one admitted two-step edge."""
    pair = (source_component_id, target_component_id)
    try:
        definition = _TWO_STEP_PROCESS_DEFINITION_BY_PAIR[pair]
    except KeyError as exc:
        raise ValueError(
            f"unsupported two-step predictive nitrogen transformation: {pair!r}"
        ) from exc

    validation_before = validate_predictive_nitrogen_state_v1(
        state,
        zone_id=zone_id,
    )
    source = state.get_quantity(
        MATERIAL_INVENTORY_VARIABLE_ID,
        zone_id=validation_before.zone_id,
        material_component_id=source_component_id,
    )
    target = state.get_quantity(
        MATERIAL_INVENTORY_VARIABLE_ID,
        zone_id=validation_before.zone_id,
        material_component_id=target_component_id,
    )

    if extent_unit != CANONICAL_NITROGEN_INVENTORY_UNIT:
        raise ValueError(
            "two-step nitrogen transformation extent must use exactly 'mg N'"
        )
    extent = Decimal(normalize_decimal(extent_decimal))
    if extent < 0:
        raise ValueError(
            "two-step nitrogen transformation extent cannot be negative"
        )
    if extent > source.decimal:
        raise ValueError(
            "two-step nitrogen transformation extent exceeds source inventory"
        )

    total_before = _primary_total(
        state,
        zone_id=validation_before.zone_id,
    )
    source_after = source.decimal - extent
    target_after = target.decimal + extent

    replacements = (
        CanonicalQuantityV1(
            variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
            value_decimal=normalize_decimal(source_after),
            unit=CANONICAL_NITROGEN_INVENTORY_UNIT,
            basis=_derived_basis(evaluation_id),
            zone_id=validation_before.zone_id,
            material_component_id=source_component_id,
        ),
        CanonicalQuantityV1(
            variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
            value_decimal=normalize_decimal(target_after),
            unit=CANONICAL_NITROGEN_INVENTORY_UNIT,
            basis=_derived_basis(evaluation_id),
            zone_id=validation_before.zone_id,
            material_component_id=target_component_id,
        ),
    )
    output_state = state.replace_quantities(replacements)
    validation_after = validate_predictive_nitrogen_state_v1(
        output_state,
        zone_id=validation_before.zone_id,
    )
    total_after = _primary_total(
        output_state,
        zone_id=validation_before.zone_id,
    )
    if total_after != total_before:
        raise RuntimeError(
            "RATE-1F elemental-N conservation invariant failed"
        )

    deltas = (
        ProcessDeltaV1(
            variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
            zone_id=validation_before.zone_id,
            material_component_id=source_component_id,
            before_decimal=normalize_decimal(source.decimal),
            change_decimal=normalize_decimal(-extent),
            after_decimal=normalize_decimal(source_after),
            unit=CANONICAL_NITROGEN_INVENTORY_UNIT,
        ),
        ProcessDeltaV1(
            variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
            zone_id=validation_before.zone_id,
            material_component_id=target_component_id,
            before_decimal=normalize_decimal(target.decimal),
            change_decimal=normalize_decimal(extent),
            after_decimal=normalize_decimal(target_after),
            unit=CANONICAL_NITROGEN_INVENTORY_UNIT,
        ),
    )

    parameters = {
        "zone_id": validation_before.zone_id,
        "source_component_id": source_component_id,
        "target_component_id": target_component_id,
        "extent": {
            "value": {
                "type": "decimal",
                "value": normalize_decimal(extent),
            },
            "unit": CANONICAL_NITROGEN_INVENTORY_UNIT,
        },
        "extent_basis": extent_basis.canonical_payload(),
        "predictive_nitrogen_validation_before_sha256": (
            validation_before.canonical_sha256
        ),
        "predictive_nitrogen_validation_after_sha256": (
            validation_after.canonical_sha256
        ),
        "primary_nitrogen_total_before": {
            "value": {
                "type": "decimal",
                "value": normalize_decimal(total_before),
            },
            "unit": CANONICAL_NITROGEN_INVENTORY_UNIT,
        },
        "primary_nitrogen_total_after": {
            "value": {
                "type": "decimal",
                "value": normalize_decimal(total_after),
            },
            "unit": CANONICAL_NITROGEN_INVENTORY_UNIT,
        },
    }

    if scientific_supports:
        support_status = "scientific_alignment_reviewed"
        unknowns: tuple[str, ...] = ()
    elif scientific_assertion_refs:
        support_status = "support_missing"
        unknowns = (
            (
                "scientific assertion refs supplied but process-specific two-step "
                "nitrification alignment is not reviewed"
            ),
        )
    elif extent_basis.kind in {"user_assumption", "scenario_default"}:
        support_status = "scenario_hypothesis"
        unknowns = (
            (
                "reviewed process-specific two-step nitrification mechanism "
                "support not supplied"
            ),
        )
    else:
        support_status = "support_missing"
        unknowns = (
            (
                "reviewed process-specific two-step nitrification mechanism "
                "support not supplied"
            ),
        )

    evaluation = ProcessEvaluationV1(
        evaluation_id=evaluation_id,
        definition=definition,
        profile_id=state.profile_id,
        input_state_sha256=state.canonical_sha256,
        output_state_sha256=output_state.canonical_sha256,
        parameters_json=canonical_json_text(parameters),
        support_status=support_status,
        parameter_bases=(extent_basis,),
        scientific_assertion_refs=scientific_assertion_refs,
        scientific_supports=scientific_supports,
        deltas=deltas,
        assumptions=definition.assumptions,
        unknowns=unknowns,
    )
    return output_state, evaluation


def admitted_two_step_nitrogen_pairs_v1() -> tuple[tuple[str, str], ...]:
    """Return the two RATE-1F predictive transformation edges in canonical order."""
    return tuple(
        pair
        for pair in (
            (
                TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
                NITRITE_NITROGEN_COMPONENT_ID,
            ),
            (
                NITRITE_NITROGEN_COMPONENT_ID,
                NITRATE_NITROGEN_COMPONENT_ID,
            ),
        )
    )


def primary_predictive_nitrogen_components_v1() -> tuple[str, ...]:
    """Expose the exact RATE-1D primary inventory component order."""
    return PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_IDS
