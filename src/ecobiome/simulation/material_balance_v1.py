"""Exact deterministic material-balance evaluators for N4."""
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
from ecobiome.simulation.intervention_v1 import WaterExchangeInterventionV1
from ecobiome.simulation.process_v1 import (
    ProcessDefinitionV1,
    ProcessDeltaV1,
    ProcessEvaluationV1,
    ScientificAssertionRefV1,
)

WATER_VOLUME_VARIABLE_ID = "water_volume"
MATERIAL_INVENTORY_VARIABLE_ID = "material_inventory"

WELL_MIXED_WATER_EXCHANGE_V1 = ProcessDefinitionV1(
    process_id="well_mixed_water_exchange_v1",
    version="1",
    label="Well-mixed water exchange",
    input_variables=(WATER_VOLUME_VARIABLE_ID, MATERIAL_INVENTORY_VARIABLE_ID),
    output_variables=(WATER_VOLUME_VARIABLE_ID, MATERIAL_INVENTORY_VARIABLE_ID),
    assumptions=("water_zone_is_well_mixed_before_removal",),
)

NITROGEN_TRANSFORMATION_EXTENT_V1 = ProcessDefinitionV1(
    process_id="nitrogen_transformation_extent_v1",
    version="1",
    label="Elemental nitrogen transformation by explicit extent",
    input_variables=(MATERIAL_INVENTORY_VARIABLE_ID, "process_extent"),
    output_variables=(MATERIAL_INVENTORY_VARIABLE_ID,),
    assumptions=("elemental_nitrogen_mass_is_conserved_within_transformation",),
    required_scientific_assertion_roles=("mechanism",),
)

_ALLOWED_NITROGEN_TRANSFORMATIONS = frozenset(
    {
        ("reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen"),
        ("dissolved_inorganic_nitrogen", "biological_nitrogen"),
    }
)

_VOLUME_TO_L = {
    "L": Decimal(1),
    "liter": Decimal(1),
    "litre": Decimal(1),
    "mL": Decimal("0.001"),
}

_MASS_TO_BASE: dict[str, tuple[str, Decimal]] = {
    "mg": ("mg", Decimal(1)),
    "g": ("mg", Decimal(1000)),
    "mg N": ("mg N", Decimal(1)),
    "g N": ("mg N", Decimal(1000)),
}

_CONCENTRATION_TO_BASE: dict[str, tuple[str, Decimal]] = {
    "mg/L": ("mg", Decimal(1)),
    "g/L": ("mg", Decimal(1000)),
    "mg N/L": ("mg N", Decimal(1)),
    "g N/L": ("mg N", Decimal(1000)),
}


def _to_liters(value: Decimal, unit: str) -> Decimal:
    try:
        factor = _VOLUME_TO_L[unit]
    except KeyError as exc:
        raise ValueError(f"unsupported exact volume unit: {unit!r}") from exc
    return value * factor


def _mass_to_base(value: Decimal, unit: str) -> tuple[str, Decimal]:
    try:
        base_unit, factor = _MASS_TO_BASE[unit]
    except KeyError as exc:
        raise ValueError(f"unsupported exact mass unit: {unit!r}") from exc
    return base_unit, value * factor


def _concentration_to_base(value: Decimal, unit: str) -> tuple[str, Decimal]:
    try:
        mass_base_unit, factor = _CONCENTRATION_TO_BASE[unit]
    except KeyError as exc:
        raise ValueError(f"unsupported exact concentration unit: {unit!r}") from exc
    return mass_base_unit, value * factor


def _derived_basis(evaluation_id: str, note: str) -> QuantityBasisV1:
    return QuantityBasisV1(
        kind="derived",
        reference_id=evaluation_id,
        note=note,
    )


def evaluate_well_mixed_water_exchange_v1(
    state: EcosystemStateV1,
    intervention: WaterExchangeInterventionV1,
    *,
    evaluation_id: str,
) -> tuple[EcosystemStateV1, ProcessEvaluationV1]:
    """Apply exact well-mixed removal and explicit replacement composition."""
    volume = state.get_quantity(
        WATER_VOLUME_VARIABLE_ID,
        zone_id=intervention.water_zone_id,
        material_component_id=None,
    )
    volume_before_l = _to_liters(volume.decimal, volume.unit)
    if volume_before_l <= 0:
        raise ValueError("water exchange requires a positive current water volume")
    removed_l = _to_liters(
        Decimal(intervention.removed_volume_decimal),
        intervention.removed_volume_unit,
    )
    replacement_l = _to_liters(
        Decimal(intervention.replacement_volume_decimal),
        intervention.replacement_volume_unit,
    )
    if removed_l > volume_before_l:
        raise ValueError("removed volume cannot exceed current water volume")
    final_volume_l = volume_before_l - removed_l + replacement_l
    if final_volume_l <= 0:
        raise ValueError("water exchange must leave a positive final water volume")

    inventories = tuple(
        item
        for item in state.quantities
        if item.variable_id == MATERIAL_INVENTORY_VARIABLE_ID
        and item.zone_id == intervention.water_zone_id
        and item.material_component_id is not None
    )
    if not inventories:
        raise ValueError("water exchange requires at least one material inventory")

    composition = {
        item.material_component_id: item
        for item in intervention.replacement_composition
    }
    required_components = {
        item.material_component_id
        for item in inventories
        if item.material_component_id is not None
    }
    missing = required_components - set(composition)
    extra = set(composition) - required_components
    if missing:
        raise ValueError(
            "replacement composition is unknown for material components: "
            f"{sorted(missing)!r}"
        )
    if extra:
        raise ValueError(
            f"replacement composition contains untracked components: {sorted(extra)!r}"
        )

    replacements: list[CanonicalQuantityV1] = [
        CanonicalQuantityV1(
            variable_id=WATER_VOLUME_VARIABLE_ID,
            value_decimal=normalize_decimal(final_volume_l),
            unit="L",
            basis=_derived_basis(evaluation_id, "water exchange volume balance"),
            zone_id=intervention.water_zone_id,
        )
    ]
    deltas: list[ProcessDeltaV1] = [
        ProcessDeltaV1(
            variable_id=WATER_VOLUME_VARIABLE_ID,
            zone_id=intervention.water_zone_id,
            material_component_id=None,
            before_decimal=normalize_decimal(volume_before_l),
            change_decimal=normalize_decimal(final_volume_l - volume_before_l),
            after_decimal=normalize_decimal(final_volume_l),
            unit="L",
        )
    ]
    parameter_bases = [intervention.basis]

    retained_fraction = (volume_before_l - removed_l) / volume_before_l

    for inventory in inventories:
        assert inventory.material_component_id is not None
        base_unit, mass_before = _mass_to_base(inventory.decimal, inventory.unit)
        if mass_before < 0:
            raise ValueError(
                "water exchange material inventories cannot be negative"
            )
        replacement = composition[inventory.material_component_id]
        concentration_base_unit, concentration = _concentration_to_base(
            Decimal(replacement.concentration_decimal),
            replacement.unit,
        )
        if concentration_base_unit != base_unit:
            raise ValueError(
                "replacement concentration mass basis does not match inventory "
                f"for component {inventory.material_component_id!r}"
            )
        remaining_mass = mass_before * retained_fraction
        replacement_mass = concentration * replacement_l
        mass_after = remaining_mass + replacement_mass
        replacements.append(
            CanonicalQuantityV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                value_decimal=normalize_decimal(mass_after),
                unit=base_unit,
                basis=_derived_basis(
                    evaluation_id,
                    "well-mixed removal plus explicit replacement composition",
                ),
                zone_id=intervention.water_zone_id,
                material_component_id=inventory.material_component_id,
            )
        )
        deltas.append(
            ProcessDeltaV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                zone_id=intervention.water_zone_id,
                material_component_id=inventory.material_component_id,
                before_decimal=normalize_decimal(mass_before),
                change_decimal=normalize_decimal(mass_after - mass_before),
                after_decimal=normalize_decimal(mass_after),
                unit=base_unit,
            )
        )
        parameter_bases.append(replacement.basis)

    output_state = state.replace_quantities(
        tuple(replacements),
        logical_step=(
            intervention.logical_step
            if intervention.logical_step is not None
            else state.logical_step + 1
        ),
    )
    evaluation = ProcessEvaluationV1(
        evaluation_id=evaluation_id,
        definition=WELL_MIXED_WATER_EXCHANGE_V1,
        profile_id=state.profile_id,
        input_state_sha256=state.canonical_sha256,
        output_state_sha256=output_state.canonical_sha256,
        parameters_json=canonical_json_text(
            {
                "intervention": intervention.canonical_payload(),
                "intervention_sha256": intervention.canonical_sha256,
            }
        ),
        support_status="deterministic_identity",
        parameter_bases=tuple(parameter_bases),
        scientific_assertion_refs=(),
        deltas=tuple(deltas),
        assumptions=WELL_MIXED_WATER_EXCHANGE_V1.assumptions,
    )
    return output_state, evaluation


def evaluate_nitrogen_transformation_extent_v1(
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
) -> tuple[EcosystemStateV1, ProcessEvaluationV1]:
    """Move an explicit elemental-N extent between two admitted inventories."""
    pair = (source_component_id, target_component_id)
    if pair not in _ALLOWED_NITROGEN_TRANSFORMATIONS:
        raise ValueError(f"unsupported nitrogen transformation: {pair!r}")
    source = state.get_quantity(
        MATERIAL_INVENTORY_VARIABLE_ID,
        zone_id=zone_id,
        material_component_id=source_component_id,
    )
    target = state.get_quantity(
        MATERIAL_INVENTORY_VARIABLE_ID,
        zone_id=zone_id,
        material_component_id=target_component_id,
    )
    source_unit, source_mass = _mass_to_base(source.decimal, source.unit)
    target_unit, target_mass = _mass_to_base(target.decimal, target.unit)
    extent_base_unit, extent = _mass_to_base(
        Decimal(normalize_decimal(extent_decimal)),
        extent_unit,
    )
    if source_unit != "mg N" or target_unit != "mg N" or extent_base_unit != "mg N":
        raise ValueError("nitrogen transformation requires an elemental-N mass basis")
    if source_mass < 0 or target_mass < 0:
        raise ValueError("nitrogen transformation inventories cannot be negative")
    if extent < 0:
        raise ValueError("nitrogen transformation extent cannot be negative")
    if extent > source_mass:
        raise ValueError("nitrogen transformation extent exceeds source inventory")

    source_after = source_mass - extent
    target_after = target_mass + extent
    replacements = (
        CanonicalQuantityV1(
            variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
            value_decimal=normalize_decimal(source_after),
            unit="mg N",
            basis=_derived_basis(evaluation_id, "explicit nitrogen transformation extent"),
            zone_id=zone_id,
            material_component_id=source_component_id,
        ),
        CanonicalQuantityV1(
            variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
            value_decimal=normalize_decimal(target_after),
            unit="mg N",
            basis=_derived_basis(evaluation_id, "explicit nitrogen transformation extent"),
            zone_id=zone_id,
            material_component_id=target_component_id,
        ),
    )
    output_state = state.replace_quantities(replacements)
    deltas = (
        ProcessDeltaV1(
            variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
            zone_id=zone_id,
            material_component_id=source_component_id,
            before_decimal=normalize_decimal(source_mass),
            change_decimal=normalize_decimal(-extent),
            after_decimal=normalize_decimal(source_after),
            unit="mg N",
        ),
        ProcessDeltaV1(
            variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
            zone_id=zone_id,
            material_component_id=target_component_id,
            before_decimal=normalize_decimal(target_mass),
            change_decimal=normalize_decimal(extent),
            after_decimal=normalize_decimal(target_after),
            unit="mg N",
        ),
    )

    if scientific_assertion_refs:
        support_status = "support_missing"
        unknowns: tuple[str, ...] = (
            (
                "scientific assertion refs supplied but process-to-assertion "
                "alignment is not reviewed in N4 V1"
            ),
        )
    elif extent_basis.kind in {"user_assumption", "scenario_default"}:
        support_status = "scenario_hypothesis"
        unknowns = ("scientific mechanism assertion not supplied",)
    else:
        support_status = "support_missing"
        unknowns = ("scientific mechanism assertion not supplied",)

    evaluation = ProcessEvaluationV1(
        evaluation_id=evaluation_id,
        definition=NITROGEN_TRANSFORMATION_EXTENT_V1,
        profile_id=state.profile_id,
        input_state_sha256=state.canonical_sha256,
        output_state_sha256=output_state.canonical_sha256,
        parameters_json=canonical_json_text(
            {
                "zone_id": zone_id,
                "source_component_id": source_component_id,
                "target_component_id": target_component_id,
                "extent": {
                    "value": {
                        "type": "decimal",
                        "value": normalize_decimal(extent_decimal),
                    },
                    "unit": extent_unit,
                },
                "extent_base": {
                    "value": {
                        "type": "decimal",
                        "value": normalize_decimal(extent),
                    },
                    "unit": "mg N",
                },
                "extent_basis": extent_basis.canonical_payload(),
            }
        ),
        support_status=support_status,
        parameter_bases=(extent_basis,),
        scientific_assertion_refs=scientific_assertion_refs,
        deltas=deltas,
        assumptions=NITROGEN_TRANSFORMATION_EXTENT_V1.assumptions,
        unknowns=unknowns,
    )
    return output_state, evaluation
