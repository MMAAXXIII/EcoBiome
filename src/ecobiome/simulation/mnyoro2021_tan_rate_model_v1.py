"""Mnyoro 2021 TAN -> nitrite instantaneous RateModel candidate.

This module is intentionally narrow.  It implements only the RATE-4F
shadow-authorized fixed-bed freshwater context.  It does not integrate over
time, mutate EcosystemStateV1, invoke a MaterialBalance, infer portable
aquarium performance, or persist scientific supports.

The execution guard is an evidence-conservative policy fence, not a statement
of universal biological tolerance.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ecobiome.knowledge_persistence.serialization import (
    canonical_sha256 as canonical_payload_sha256,
)
from ecobiome.simulation.ecosystem_state_v1 import EcosystemStateV1
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

_RATE_MODEL_ID = "mnyoro2021-tan-to-nitrite-fixed-bed-first-order"
_RATE_MODEL_VERSION = "1-shadow-candidate"
_PROCESS_ID = "ammonia_oxidation_to_nitrite"
_PROCESS_VERSION = "1"
_SOURCE_COMPONENT_ID = "total_ammonia_nitrogen"
_TARGET_COMPONENT_ID = "nitrite_nitrogen"
_K1_PARAMETER_ID = "k1_surface_tan_first_order"
_K1_M_PER_DAY = Decimal("0.45")
_MG_PER_G = Decimal(1000)
_HOURS_PER_DAY = Decimal(24)

_ALLOWED_WATER_VELOCITIES_M_H = frozenset({Decimal("10.8"), Decimal("16.2")})
_TAN_MIN_MG_N_L = Decimal(0)
_TAN_MAX_MG_N_L = Decimal("1.0")
_TEMPERATURE_MIN_C = Decimal("19.1")
_TEMPERATURE_MAX_C = Decimal("19.6")
_DO_MIN_MG_L = Decimal("9.3")
_DO_MAX_MG_L = Decimal("10.1")
_PH_MIN = Decimal("7.8")
_PH_MAX = Decimal("7.9")
_ALKALINITY_MIN_MG_L_CACO3 = Decimal(185)
_ALKALINITY_MAX_MG_L_CACO3 = Decimal(222)
_MIN_HYDRAULIC_ACCLIMATION_DAYS = 3

_REQUIRED_WATER_TYPE = "freshwater"
_REQUIRED_BIOFILTER_MODE = "fixed_bed_attached_biofilm"
_REQUIRED_CARRIER_MEDIA = "RK Bioelements Heavy"
_REQUIRED_VELOCITY_MEASUREMENT_KIND = "elevation_pore_velocity_in_media_bed"

_REVIEWED_SUPPORT_CANONICAL_SHA256 = {
    "kinetic_form": (
        "54880171583ae690b779dd9eb2657163875197c171e11a0bfd5e3d639bdab9c8"
    ),
    "kinetic_parameter": (
        "81002e1b2c1e12cc2088403d1cec52af33b632ebd87ca331081fcd3f04e6c611"
    ),
    "applicability_domain": (
        "073d42bd620f04090714deecd2183ac40a41cd6028b4034299d47fd74c0bf703"
    ),
}


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


@dataclass(frozen=True, slots=True)
class Mnyoro2021FixedBedContextV1:
    """Categorical and hydraulic-context facts not represented as state quantities."""

    water_type: str
    biofilter_mode: str
    carrier_media: str
    mature_colonized_media: bool
    velocity_measurement_kind: str
    days_since_hydraulic_change: int

    def __post_init__(self) -> None:
        for field_name in (
            "water_type",
            "biofilter_mode",
            "carrier_media",
            "velocity_measurement_kind",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonempty(str(getattr(self, field_name)), field_name),
            )
        if not isinstance(self.mature_colonized_media, bool):
            raise TypeError("mature_colonized_media must be bool")
        if (
            isinstance(self.days_since_hydraulic_change, bool)
            or not isinstance(self.days_since_hydraulic_change, int)
        ):
            raise TypeError("days_since_hydraulic_change must be int")
        if self.days_since_hydraulic_change < 0:
            raise ValueError("days_since_hydraulic_change cannot be negative")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-mnyoro2021-fixed-bed-context-v1",
            "water_type": self.water_type,
            "biofilter_mode": self.biofilter_mode,
            "carrier_media": self.carrier_media,
            "mature_colonized_media": self.mature_colonized_media,
            "velocity_measurement_kind": self.velocity_measurement_kind,
            "days_since_hydraulic_change": self.days_since_hydraulic_change,
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())


@dataclass(frozen=True, slots=True)
class Mnyoro2021TanRateSupportBundleV1:
    """Reviewed supports required by the concrete rate candidate."""

    kinetic_form: RateScientificSupportV1
    kinetic_parameter: RateScientificSupportV1
    applicability_domain: RateScientificSupportV1

    def __post_init__(self) -> None:
        expected = (
            ("kinetic_form", self.kinetic_form),
            ("kinetic_parameter", self.kinetic_parameter),
            ("applicability_domain", self.applicability_domain),
        )
        for role, support in expected:
            if support.role != role:
                raise ValueError(
                    f"{role} support must have role={role!r}; got {support.role!r}"
                )
            expected_sha256 = _REVIEWED_SUPPORT_CANONICAL_SHA256[role]
            if support.canonical_sha256 != expected_sha256:
                raise ValueError(
                    f"{role} support identity is not the exact RATE-4F reviewed "
                    f"support: {support.canonical_sha256} != {expected_sha256}"
                )


def _requirements() -> tuple[RateQuantityRequirementV1, ...]:
    return (
        RateQuantityRequirementV1(
            requirement_id="tan_concentration",
            variable_id="material_concentration",
            unit="mg N/L",
            semantic_role="kinetic_substrate",
            material_component_id=_SOURCE_COMPONENT_ID,
            zone_required=True,
        ),
        RateQuantityRequirementV1(
            requirement_id="nominal_active_carrier_surface_area",
            variable_id="biofilter_nominal_active_surface_area",
            unit="m2",
            semantic_role="absolute_rate_scaling",
            zone_required=False,
        ),
        RateQuantityRequirementV1(
            requirement_id="water_velocity",
            variable_id="biofilter_elevation_pore_velocity",
            unit="m/h",
            semantic_role="applicability_driver",
            zone_required=False,
        ),
        RateQuantityRequirementV1(
            requirement_id="water_temperature",
            variable_id="water_temperature",
            unit="degC",
            semantic_role="applicability_driver",
            zone_required=True,
        ),
        RateQuantityRequirementV1(
            requirement_id="dissolved_oxygen",
            variable_id="dissolved_oxygen",
            unit="mg/L",
            semantic_role="applicability_driver",
            zone_required=True,
        ),
        RateQuantityRequirementV1(
            requirement_id="water_ph",
            variable_id="pH",
            unit="pH",
            semantic_role="applicability_driver",
            zone_required=True,
        ),
        RateQuantityRequirementV1(
            requirement_id="alkalinity",
            variable_id="alkalinity_as_caco3",
            unit="mg/L as CaCO3",
            semantic_role="applicability_driver",
            zone_required=True,
        ),
    )


def build_mnyoro2021_tan_rate_definition_v1(
    supports: Mnyoro2021TanRateSupportBundleV1 | None,
) -> RateModelDefinitionV1:
    definition_supports: tuple[RateScientificSupportV1, ...] = ()
    if supports is not None:
        definition_supports = (
            supports.kinetic_form,
            supports.applicability_domain,
        )
    return RateModelDefinitionV1(
        rate_model_id=_RATE_MODEL_ID,
        version=_RATE_MODEL_VERSION,
        process_id=_PROCESS_ID,
        process_version=_PROCESS_VERSION,
        source_component_id=_SOURCE_COMPONENT_ID,
        target_component_id=_TARGET_COMPONENT_ID,
        required_state_quantities=_requirements(),
        required_parameters=(_K1_PARAMETER_ID,),
        scientific_supports=definition_supports,
        assumptions=(
            "shadow_candidate_only",
            "no_state_mutation",
            "no_rate_to_extent_integration",
            "freshwater_fixed_bed_attached_biofilm_only",
            "carrier_media_exactly_RK_Bioelements_Heavy",
            "mature_colonized_media_required",
            "velocity_exactly_10.8_or_16.2_m_per_h",
            "no_velocity_interpolation_or_extrapolation",
            "k1_source_unit_conflict_preserved_and_adjudicated_to_m_per_d",
            "environmental_bounds_are_execution_fences_not_biological_tolerances",
            "no_cross_paper_modifiers",
            "scientific_supports_exactly_bound_to_RATE_4F_reviewed_identities",
        ),
        output_rate_unit="mg N/h",
    )


def build_mnyoro2021_tan_rate_parameter_set_v1(
    supports: Mnyoro2021TanRateSupportBundleV1,
) -> RateParameterSetV1:
    return RateParameterSetV1(
        parameter_set_id="mnyoro2021-k1-rate4f-reviewed-shadow-candidate",
        parameters=(
            RateParameterV1(
                parameter_id=_K1_PARAMETER_ID,
                value_decimal=_K1_M_PER_DAY,
                unit="m/d",
                semantic_role="surface_first_order_tan_removal_coefficient",
                scientific_supports=(supports.kinetic_parameter,),
                applicability_scope=(
                    "RATE-4E exact-context conservative guard; "
                    "RATE-4F shadow-only authorization"
                ),
            ),
        ),
    )


def _bind_quantities(
    state: EcosystemStateV1,
    definition: RateModelDefinitionV1,
    *,
    zone_id: str,
) -> tuple[
    tuple[RateInputQuantityBindingV1, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    bindings: list[RateInputQuantityBindingV1] = []
    reason_codes: list[str] = []
    details: list[str] = []
    for requirement in definition.required_state_quantities:
        required_zone = zone_id if requirement.zone_required else None
        try:
            binding = bind_rate_quantity_v1(
                state,
                requirement,
                zone_id=required_zone,
            )
        except (KeyError, ValueError) as exc:
            reason_codes.append(
                f"missing_or_invalid_quantity:{requirement.requirement_id}"
            )
            details.append(
                f"{requirement.requirement_id}: {type(exc).__name__}: {exc}"
            )
        else:
            bindings.append(binding)
    return tuple(bindings), tuple(reason_codes), tuple(details)


def _binding_values(
    bindings: tuple[RateInputQuantityBindingV1, ...],
) -> dict[str, Decimal]:
    return {item.requirement_id: item.decimal for item in bindings}


def _guard_reason_codes(
    values: dict[str, Decimal],
    context: Mnyoro2021FixedBedContextV1,
) -> tuple[str, ...]:
    reasons: list[str] = []

    if context.water_type != _REQUIRED_WATER_TYPE:
        reasons.append("water_type_outside_reviewed_domain")
    if context.biofilter_mode != _REQUIRED_BIOFILTER_MODE:
        reasons.append("biofilter_mode_outside_reviewed_domain")
    if context.carrier_media != _REQUIRED_CARRIER_MEDIA:
        reasons.append("carrier_media_outside_reviewed_domain")
    if not context.mature_colonized_media:
        reasons.append("mature_colonized_media_required")
    if context.velocity_measurement_kind != _REQUIRED_VELOCITY_MEASUREMENT_KIND:
        reasons.append("velocity_measurement_kind_outside_reviewed_domain")
    if context.days_since_hydraulic_change < _MIN_HYDRAULIC_ACCLIMATION_DAYS:
        reasons.append("hydraulic_acclimation_insufficient")

    velocity = values["water_velocity"]
    if velocity not in _ALLOWED_WATER_VELOCITIES_M_H:
        reasons.append("water_velocity_outside_exact_reviewed_values")

    tan = values["tan_concentration"]
    if tan < _TAN_MIN_MG_N_L or tan > _TAN_MAX_MG_N_L:
        reasons.append("tan_concentration_outside_conservative_guard")

    temperature = values["water_temperature"]
    if temperature < _TEMPERATURE_MIN_C or temperature > _TEMPERATURE_MAX_C:
        reasons.append("water_temperature_outside_central_context_fence")

    dissolved_oxygen = values["dissolved_oxygen"]
    if dissolved_oxygen < _DO_MIN_MG_L or dissolved_oxygen > _DO_MAX_MG_L:
        reasons.append("dissolved_oxygen_outside_central_context_fence")

    ph = values["water_ph"]
    if ph < _PH_MIN or ph > _PH_MAX:
        reasons.append("ph_outside_central_context_fence")

    alkalinity = values["alkalinity"]
    if (
        alkalinity < _ALKALINITY_MIN_MG_L_CACO3
        or alkalinity > _ALKALINITY_MAX_MG_L_CACO3
    ):
        reasons.append("alkalinity_outside_central_context_fence")

    area = values["nominal_active_carrier_surface_area"]
    if area <= 0:
        reasons.append("nominal_active_carrier_surface_area_must_be_positive")

    return tuple(sorted(set(reasons)))


def _instantaneous_rate_mg_n_h(values: dict[str, Decimal]) -> Decimal:
    tan_mg_n_l = values["tan_concentration"]
    nominal_area_m2 = values["nominal_active_carrier_surface_area"]
    return (
        _K1_M_PER_DAY
        * tan_mg_n_l
        * nominal_area_m2
        * _MG_PER_G
        / _HOURS_PER_DAY
    )


def evaluate_mnyoro2021_tan_to_nitrite_rate_v1(
    state: EcosystemStateV1,
    context: Mnyoro2021FixedBedContextV1,
    supports: Mnyoro2021TanRateSupportBundleV1 | None,
    *,
    zone_id: str,
) -> RateEvaluationV1:
    """Evaluate one instantaneous TAN -> nitrite-N rate without mutating state."""

    normalized_zone_id = _nonempty(zone_id, "zone_id")
    definition = build_mnyoro2021_tan_rate_definition_v1(supports)
    bindings, binding_reasons, binding_details = _bind_quantities(
        state,
        definition,
        zone_id=normalized_zone_id,
    )

    evaluation_id = (
        "mnyoro2021-tan-rate-"
        f"{state.canonical_sha256[:16]}-{context.canonical_sha256[:16]}"
    )

    if binding_reasons:
        return RateEvaluationV1(
            evaluation_id=evaluation_id,
            definition=definition,
            profile_id=state.profile_id,
            input_state_sha256=state.canonical_sha256,
            zone_id=normalized_zone_id,
            applicability=RateApplicabilityResultV1(
                status="missing_required_quantity",
                reason_codes=binding_reasons,
                details=binding_details,
            ),
            quantity_bindings=bindings,
            parameter_set=None,
            rate_decimal=None,
            rate_unit=None,
            warnings=("fail_closed_no_numeric_rate_emitted",),
        )

    if supports is None:
        return RateEvaluationV1(
            evaluation_id=evaluation_id,
            definition=definition,
            profile_id=state.profile_id,
            input_state_sha256=state.canonical_sha256,
            zone_id=normalized_zone_id,
            applicability=RateApplicabilityResultV1(
                status="scientific_support_missing",
                reason_codes=("reviewed_rate_support_bundle_missing",),
            ),
            quantity_bindings=bindings,
            parameter_set=None,
            rate_decimal=None,
            rate_unit=None,
            warnings=("fail_closed_no_numeric_rate_emitted",),
        )

    values = _binding_values(bindings)
    guard_reasons = _guard_reason_codes(values, context)
    if guard_reasons:
        return RateEvaluationV1(
            evaluation_id=evaluation_id,
            definition=definition,
            profile_id=state.profile_id,
            input_state_sha256=state.canonical_sha256,
            zone_id=normalized_zone_id,
            applicability=RateApplicabilityResultV1(
                status="outside_reviewed_domain",
                reason_codes=guard_reasons,
                details=(
                    "RATE-4E guard is an execution fence, not a biological tolerance range.",
                ),
            ),
            quantity_bindings=bindings,
            parameter_set=None,
            rate_decimal=None,
            rate_unit=None,
            warnings=("fail_closed_no_numeric_rate_emitted",),
        )

    parameter_set = build_mnyoro2021_tan_rate_parameter_set_v1(supports)
    return RateEvaluationV1(
        evaluation_id=evaluation_id,
        definition=definition,
        profile_id=state.profile_id,
        input_state_sha256=state.canonical_sha256,
        zone_id=normalized_zone_id,
        applicability=RateApplicabilityResultV1(status="applicable"),
        quantity_bindings=bindings,
        parameter_set=parameter_set,
        rate_decimal=_instantaneous_rate_mg_n_h(values),
        rate_unit="mg N/h",
        warnings=(
            "shadow_candidate_not_authorized_for_production_or_live_aquarium_prediction",
            "k1_source_unit_conflict_preserved_in_review_provenance",
            "mass_availability_cap_required_before_any_future_rate_to_extent_integration",
        ),
        uncertainties=(
            "applicability_guard_is_conservative_execution_policy_not_biological_tolerance",
        ),
    )
