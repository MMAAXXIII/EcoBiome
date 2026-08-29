from __future__ import annotations

import json
from dataclasses import MISSING, fields
from pathlib import Path

import pytest

from ecobiome.simulation.ecosystem_state_v1 import (
    CanonicalQuantityV1,
    EcosystemStateV1,
    QuantityBasisV1,
)
from ecobiome.simulation.mnyoro2021_tan_rate_model_v1 import (
    Mnyoro2021FixedBedContextV1,
    Mnyoro2021TanRateSupportBundleV1,
    build_mnyoro2021_tan_rate_definition_v1,
    evaluate_mnyoro2021_tan_to_nitrite_rate_v1,
)
from ecobiome.simulation.process_v1 import ScientificAssertionRefV1
from ecobiome.simulation.rate_model_v1 import RateScientificSupportV1

_FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "rate_models"
    / "mnyoro2021_rate4f_shadow_supports.json"
)


def _support_bundle() -> Mnyoro2021TanRateSupportBundleV1:
    payload = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    supports = {}
    for role, row in payload["supports"].items():
        item = row["rate_scientific_support"]
        assertion = item["assertion_ref"]
        support = RateScientificSupportV1(
            role=item["role"],
            support_id=item["support_id"],
            support_sha256=item["support_sha256"],
            assertion_ref=ScientificAssertionRefV1(
                assertion_id=assertion["assertion_id"],
                assertion_revision=assertion["assertion_revision"],
                canonical_payload_sha256=assertion["canonical_payload_sha256"],
            ),
            reviewed_by=item["reviewed_by"],
            applicability_scope=item["applicability_scope"],
        )
        assert support.canonical_sha256 == row["rate_scientific_support_sha256"]
        supports[role] = support
    return Mnyoro2021TanRateSupportBundleV1(
        kinetic_form=supports["kinetic_form"],
        kinetic_parameter=supports["kinetic_parameter"],
        applicability_domain=supports["applicability_domain"],
    )


def test_same_role_but_different_support_identity_is_rejected() -> None:
    reviewed = _support_bundle()
    original = reviewed.kinetic_form
    forged = RateScientificSupportV1(
        role=original.role,
        support_id=original.support_id + "-forged",
        support_sha256=original.support_sha256,
        assertion_ref=original.assertion_ref,
        reviewed_by=original.reviewed_by,
        applicability_scope=original.applicability_scope,
    )
    with pytest.raises(
        ValueError,
        match="support identity is not the exact RATE-4F reviewed support",
    ):
        Mnyoro2021TanRateSupportBundleV1(
            kinetic_form=forged,
            kinetic_parameter=reviewed.kinetic_parameter,
            applicability_domain=reviewed.applicability_domain,
        )


def _basis(reference_id: str) -> QuantityBasisV1:
    return QuantityBasisV1(kind="observation", reference_id=reference_id)


def _state(
    *,
    tan: str = "0.5",
    area: str | None = "11.3",
    velocity: str = "10.8",
    temperature: str = "19.3",
    dissolved_oxygen: str = "9.5",
    ph: str = "7.85",
    alkalinity: str = "200",
    reverse: bool = False,
) -> EcosystemStateV1:
    quantities = [
        CanonicalQuantityV1(
            variable_id="material_concentration",
            value_decimal=tan,
            unit="mg N/L",
            basis=_basis("tan"),
            zone_id="water",
            material_component_id="total_ammonia_nitrogen",
        ),
        CanonicalQuantityV1(
            variable_id="biofilter_elevation_pore_velocity",
            value_decimal=velocity,
            unit="m/h",
            basis=_basis("velocity"),
        ),
        CanonicalQuantityV1(
            variable_id="water_temperature",
            value_decimal=temperature,
            unit="degC",
            basis=_basis("temperature"),
            zone_id="water",
        ),
        CanonicalQuantityV1(
            variable_id="dissolved_oxygen",
            value_decimal=dissolved_oxygen,
            unit="mg/L",
            basis=_basis("do"),
            zone_id="water",
        ),
        CanonicalQuantityV1(
            variable_id="pH",
            value_decimal=ph,
            unit="pH",
            basis=_basis("ph"),
            zone_id="water",
        ),
        CanonicalQuantityV1(
            variable_id="alkalinity_as_caco3",
            value_decimal=alkalinity,
            unit="mg/L as CaCO3",
            basis=_basis("alkalinity"),
            zone_id="water",
        ),
    ]
    if area is not None:
        quantities.append(
            CanonicalQuantityV1(
                variable_id="biofilter_nominal_active_surface_area",
                value_decimal=area,
                unit="m2",
                basis=_basis("area"),
            )
        )
    if reverse:
        quantities.reverse()
    return EcosystemStateV1(
        profile_id="shadow-mnyoro2021-rate4g",
        quantities=tuple(quantities),
    )


def _context(
    *,
    water_type: str = "freshwater",
    biofilter_mode: str = "fixed_bed_attached_biofilm",
    carrier_media: str = "RK Bioelements Heavy",
    mature_colonized_media: bool = True,
    velocity_measurement_kind: str = "elevation_pore_velocity_in_media_bed",
    days_since_hydraulic_change: int = 3,
) -> Mnyoro2021FixedBedContextV1:
    return Mnyoro2021FixedBedContextV1(
        water_type=water_type,
        biofilter_mode=biofilter_mode,
        carrier_media=carrier_media,
        mature_colonized_media=mature_colonized_media,
        velocity_measurement_kind=velocity_measurement_kind,
        days_since_hydraulic_change=days_since_hydraulic_change,
    )


def _evaluate(state: EcosystemStateV1, context=None, supports=True):
    return evaluate_mnyoro2021_tan_to_nitrite_rate_v1(
        state,
        _context() if context is None else context,
        _support_bundle() if supports else None,
        zone_id="water",
    )


def test_context_has_no_hidden_defaults() -> None:
    for item in fields(Mnyoro2021FixedBedContextV1):
        assert item.default is MISSING
        assert item.default_factory is MISSING


def test_definition_is_exactly_instantaneous_and_canonical() -> None:
    definition = build_mnyoro2021_tan_rate_definition_v1(_support_bundle())
    assert definition.process_id == "ammonia_oxidation_to_nitrite"
    assert definition.source_component_id == "total_ammonia_nitrogen"
    assert definition.target_component_id == "nitrite_nitrogen"
    assert definition.output_rate_unit == "mg N/h"
    assert definition.required_parameters == ("k1_surface_tan_first_order",)
    payload = definition.canonical_payload()
    encoded = json.dumps(payload, sort_keys=True).lower()
    assert '"dt"' not in encoded
    assert '"duration"' not in encoded
    assert "time_step" not in encoded
    assert "timestep" not in encoded


def test_baseline_rate_is_105_9375_mg_n_h_and_state_is_unchanged() -> None:
    state = _state()
    before = state.canonical_sha256
    result = _evaluate(state)
    assert state.canonical_sha256 == before
    assert result.applicability.status == "applicable"
    assert result.rate_decimal == "105.9375"
    assert result.rate_unit == "mg N/h"
    payload = result.canonical_payload()
    assert "output_state" not in payload
    assert "dt" not in payload
    assert "duration" not in payload


def test_exact_16_2_velocity_is_supported_without_rate_change() -> None:
    result = _evaluate(_state(velocity="16.2"))
    assert result.applicability.status == "applicable"
    assert result.rate_decimal == "105.9375"


@pytest.mark.parametrize(
    ("tan", "expected"),
    [
        ("0", "0"),
        ("1.0", "211.875"),
    ],
)
def test_tan_guard_boundaries_are_inclusive(tan: str, expected: str) -> None:
    result = _evaluate(_state(tan=tan))
    assert result.applicability.status == "applicable"
    assert result.rate_decimal == expected


def test_rate_scales_linearly_with_nominal_carrier_area() -> None:
    result = _evaluate(_state(area="5.65"))
    assert result.applicability.status == "applicable"
    assert result.rate_decimal == "52.96875"


@pytest.mark.parametrize("velocity", ["1.4", "5.4", "13.5", "16.3"])
def test_nonreviewed_velocity_is_fail_closed(velocity: str) -> None:
    result = _evaluate(_state(velocity=velocity))
    assert result.applicability.status == "outside_reviewed_domain"
    assert result.rate_decimal is None
    assert result.rate_unit is None
    assert "water_velocity_outside_exact_reviewed_values" in (
        result.applicability.reason_codes
    )


def test_other_carrier_media_is_not_generalized() -> None:
    result = _evaluate(
        _state(),
        context=_context(carrier_media="generic foam"),
    )
    assert result.applicability.status == "outside_reviewed_domain"
    assert result.rate_decimal is None
    assert "carrier_media_outside_reviewed_domain" in (
        result.applicability.reason_codes
    )


def test_tan_above_conservative_ceiling_is_rejected() -> None:
    result = _evaluate(_state(tan="1.1"))
    assert result.applicability.status == "outside_reviewed_domain"
    assert result.rate_decimal is None
    assert "tan_concentration_outside_conservative_guard" in (
        result.applicability.reason_codes
    )


@pytest.mark.parametrize(
    ("temperature", "dissolved_oxygen", "ph", "alkalinity", "reason"),
    [
        (
            "20.0",
            "9.5",
            "7.85",
            "200",
            "water_temperature_outside_central_context_fence",
        ),
        (
            "19.3",
            "9.0",
            "7.85",
            "200",
            "dissolved_oxygen_outside_central_context_fence",
        ),
        (
            "19.3",
            "9.5",
            "7.7",
            "200",
            "ph_outside_central_context_fence",
        ),
        (
            "19.3",
            "9.5",
            "7.85",
            "180",
            "alkalinity_outside_central_context_fence",
        ),
    ],
)
def test_environmental_fence_is_fail_closed(
    temperature: str,
    dissolved_oxygen: str,
    ph: str,
    alkalinity: str,
    reason: str,
) -> None:
    result = _evaluate(
        _state(
            temperature=temperature,
            dissolved_oxygen=dissolved_oxygen,
            ph=ph,
            alkalinity=alkalinity,
        )
    )
    assert result.applicability.status == "outside_reviewed_domain"
    assert result.rate_decimal is None
    assert reason in result.applicability.reason_codes


def test_hydraulic_acclimation_is_required() -> None:
    result = _evaluate(
        _state(),
        context=_context(days_since_hydraulic_change=2),
    )
    assert result.applicability.status == "outside_reviewed_domain"
    assert result.rate_decimal is None
    assert "hydraulic_acclimation_insufficient" in (
        result.applicability.reason_codes
    )


def test_missing_area_is_missing_required_quantity_not_numeric_zero() -> None:
    result = _evaluate(_state(area=None))
    assert result.applicability.status == "missing_required_quantity"
    assert result.rate_decimal is None
    assert result.rate_unit is None
    assert any(
        code == "missing_or_invalid_quantity:nominal_active_carrier_surface_area"
        for code in result.applicability.reason_codes
    )


def test_missing_scientific_supports_fail_closed() -> None:
    result = _evaluate(_state(), supports=False)
    assert result.applicability.status == "scientific_support_missing"
    assert result.rate_decimal is None
    assert result.rate_unit is None


def test_state_quantity_order_does_not_change_evaluation_identity() -> None:
    first = _evaluate(_state())
    second = _evaluate(_state(reverse=True))
    assert first.input_state_sha256 == second.input_state_sha256
    assert first.canonical_sha256 == second.canonical_sha256


def test_context_identity_changes_evaluation_identity() -> None:
    first = _evaluate(_state())
    second = _evaluate(
        _state(),
        context=_context(days_since_hydraulic_change=4),
    )
    assert first.applicability.status == "applicable"
    assert second.applicability.status == "applicable"
    assert first.evaluation_id != second.evaluation_id


def test_rate_evaluation_never_contains_material_balance_or_integration_output() -> None:
    payload = _evaluate(_state()).canonical_payload()
    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "material_balance",
        "output_state",
        '"dt"',
        '"duration"',
        "elapsed_time",
        "time_step",
        "timestep",
    ):
        assert forbidden not in encoded
