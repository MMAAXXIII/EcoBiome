from __future__ import annotations

from decimal import Decimal

import pytest

from ecobiome.simulation.ecosystem_state_v1 import (
    CanonicalQuantityV1,
    EcosystemStateV1,
    QuantityBasisV1,
)
from ecobiome.simulation.nitrogen_state_v1 import (
    CANONICAL_NITROGEN_CONCENTRATION_UNIT,
    CANONICAL_NITROGEN_INVENTORY_UNIT,
    MATERIAL_CONCENTRATION_VARIABLE_ID,
    MATERIAL_INVENTORY_VARIABLE_ID,
    NITRATE_NITROGEN_COMPONENT_ID,
    NITRITE_NITROGEN_COMPONENT_ID,
    PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_IDS,
    TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
    WATER_VOLUME_VARIABLE_ID,
    project_nitrogen_concentration_v1,
    project_predictive_nitrogen_concentrations_v1,
    validate_predictive_nitrogen_state_v1,
)


def _basis(reference_id: str) -> QuantityBasisV1:
    return QuantityBasisV1(
        kind="observation",
        reference_id=reference_id,
    )


def _inventory(
    component_id: str,
    value: str,
    *,
    unit: str = "mg N",
    zone_id: str = "water",
) -> CanonicalQuantityV1:
    return CanonicalQuantityV1(
        variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
        value_decimal=value,
        unit=unit,
        basis=_basis(f"inventory-{component_id}"),
        zone_id=zone_id,
        material_component_id=component_id,
    )


def _volume(
    value: str = "100",
    *,
    unit: str = "L",
    zone_id: str = "water",
) -> CanonicalQuantityV1:
    return CanonicalQuantityV1(
        variable_id=WATER_VOLUME_VARIABLE_ID,
        value_decimal=value,
        unit=unit,
        basis=_basis("water-volume"),
        zone_id=zone_id,
    )


def _state(
    *,
    tan: str = "10",
    nitrite: str = "2",
    nitrate: str = "5",
    volume: str = "100",
    volume_unit: str = "L",
    extra: tuple[CanonicalQuantityV1, ...] = (),
) -> EcosystemStateV1:
    return EcosystemStateV1(
        profile_id="profile-rate-1e",
        quantities=(
            _volume(volume, unit=volume_unit),
            _inventory(TOTAL_AMMONIA_NITROGEN_COMPONENT_ID, tan),
            _inventory(NITRITE_NITROGEN_COMPONENT_ID, nitrite),
            _inventory(NITRATE_NITROGEN_COMPONENT_ID, nitrate),
            *extra,
        ),
    )


def test_primary_predictive_component_contract_is_exact() -> None:
    assert PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_IDS == (
        "total_ammonia_nitrogen",
        "nitrite_nitrogen",
        "nitrate_nitrogen",
    )
    assert CANONICAL_NITROGEN_INVENTORY_UNIT == "mg N"
    assert CANONICAL_NITROGEN_CONCENTRATION_UNIT == "mg N/L"


def test_validation_binds_exact_three_primary_inventories() -> None:
    state = _state()
    validation = validate_predictive_nitrogen_state_v1(
        state,
        zone_id="water",
    )
    assert validation.input_state_sha256 == state.canonical_sha256
    assert validation.zone_id == "water"
    assert {
        item.component_id for item in validation.inventories
    } == set(PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_IDS)
    assert validation.get_inventory(
        TOTAL_AMMONIA_NITROGEN_COMPONENT_ID
    ).value_decimal == "10"


def test_validation_is_canonical_across_state_quantity_order() -> None:
    state = _state()
    reordered = EcosystemStateV1(
        profile_id=state.profile_id,
        quantities=tuple(reversed(state.quantities)),
    )
    first = validate_predictive_nitrogen_state_v1(
        state,
        zone_id="water",
    )
    second = validate_predictive_nitrogen_state_v1(
        reordered,
        zone_id="water",
    )
    assert state.canonical_sha256 == reordered.canonical_sha256
    assert first.canonical_payload() == second.canonical_payload()
    assert first.canonical_sha256 == second.canonical_sha256


@pytest.mark.parametrize(
    "missing_component",
    PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_IDS,
)
def test_validation_rejects_missing_primary_inventory(
    missing_component: str,
) -> None:
    state = _state()
    quantities = tuple(
        item
        for item in state.quantities
        if item.material_component_id != missing_component
    )
    incomplete = EcosystemStateV1(
        profile_id=state.profile_id,
        quantities=quantities,
    )
    with pytest.raises(ValueError, match="missing primary inventory"):
        validate_predictive_nitrogen_state_v1(
            incomplete,
            zone_id="water",
        )


def test_validation_rejects_wrong_inventory_unit() -> None:
    state = _state()
    wrong = tuple(
        _inventory(
            item.material_component_id,
            item.value_decimal,
            unit="g N",
        )
        if (
            item.variable_id == MATERIAL_INVENTORY_VARIABLE_ID
            and item.material_component_id
            == TOTAL_AMMONIA_NITROGEN_COMPONENT_ID
        )
        else item
        for item in state.quantities
    )
    with pytest.raises(ValueError, match="must use 'mg N'"):
        validate_predictive_nitrogen_state_v1(
            EcosystemStateV1(
                profile_id=state.profile_id,
                quantities=wrong,
            ),
            zone_id="water",
        )


def test_validation_rejects_negative_inventory() -> None:
    state = _state(tan="-0.1")
    with pytest.raises(ValueError, match="cannot be negative"):
        validate_predictive_nitrogen_state_v1(
            state,
            zone_id="water",
        )


@pytest.mark.parametrize(
    "overlap_component",
    [
        "unionized_ammonia_nitrogen",
        "ammonium_nitrogen",
        "dissolved_inorganic_nitrogen",
        "reduced_inorganic_nitrogen",
        "oxidized_inorganic_nitrogen",
    ],
)
def test_validation_rejects_overlapping_primary_inventory(
    overlap_component: str,
) -> None:
    state = _state(
        extra=(
            _inventory(overlap_component, "1"),
        )
    )
    with pytest.raises(ValueError, match="overlapping primary inventory"):
        validate_predictive_nitrogen_state_v1(
            state,
            zone_id="water",
        )


def test_validation_allows_nonoverlapping_biological_nitrogen_inventory() -> None:
    state = _state(
        extra=(
            _inventory("biological_nitrogen", "3"),
        )
    )
    validation = validate_predictive_nitrogen_state_v1(
        state,
        zone_id="water",
    )
    assert validation.input_state_sha256 == state.canonical_sha256


def test_single_projection_is_exact_and_state_preserving() -> None:
    state = _state()
    before_sha = state.canonical_sha256
    projection = project_nitrogen_concentration_v1(
        state,
        zone_id="water",
        component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
        projection_id="projection-tan",
    )
    assert state.canonical_sha256 == before_sha
    assert projection.input_state_sha256 == before_sha
    assert projection.inventory_quantity.value_decimal == "10"
    assert projection.water_volume_quantity.value_decimal == "100"
    assert projection.concentration_quantity.key == (
        MATERIAL_CONCENTRATION_VARIABLE_ID,
        "water",
        TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
    )
    assert projection.concentration_quantity.value_decimal == "0.1"
    assert projection.concentration_quantity.unit == "mg N/L"
    assert projection.concentration_quantity.basis.kind == "derived"
    assert (
        projection.concentration_quantity.basis.reference_id
        == "projection-tan"
    )


def test_projection_normalizes_milliliter_water_volume() -> None:
    state = _state(
        tan="10",
        volume="100000",
        volume_unit="mL",
    )
    projection = project_nitrogen_concentration_v1(
        state,
        zone_id="water",
        component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
        projection_id="projection-ml",
    )
    assert projection.concentration_quantity.value_decimal == "0.1"


@pytest.mark.parametrize("volume", ["0", "-1"])
def test_projection_rejects_nonpositive_volume(volume: str) -> None:
    state = _state(volume=volume)
    with pytest.raises(ValueError, match="positive water volume"):
        project_nitrogen_concentration_v1(
            state,
            zone_id="water",
            component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
            projection_id="bad-volume",
        )


def test_projection_rejects_unsupported_volume_unit() -> None:
    state = _state(volume_unit="m3")
    with pytest.raises(ValueError, match="unsupported exact water-volume unit"):
        project_nitrogen_concentration_v1(
            state,
            zone_id="water",
            component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
            projection_id="bad-unit",
        )


def test_projection_rejects_missing_water_volume() -> None:
    state = _state()
    without_volume = EcosystemStateV1(
        profile_id=state.profile_id,
        quantities=tuple(
            item
            for item in state.quantities
            if item.variable_id != WATER_VOLUME_VARIABLE_ID
        ),
    )
    with pytest.raises(ValueError, match="requires exact water volume"):
        project_nitrogen_concentration_v1(
            without_volume,
            zone_id="water",
            component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
            projection_id="missing-volume",
        )


def test_projection_precision_is_deterministic_for_repeating_decimal() -> None:
    state = _state(tan="1", volume="3")
    projection = project_nitrogen_concentration_v1(
        state,
        zone_id="water",
        component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
        projection_id="repeating",
    )
    assert (
        projection.concentration_quantity.value_decimal
        == "0.3333333333333333333333333333"
    )
    assert projection.precision_digits == 28
    assert projection.rounding == "ROUND_HALF_EVEN"


def test_projection_set_contains_exact_three_primary_concentrations() -> None:
    state = _state()
    projection_set = project_predictive_nitrogen_concentrations_v1(
        state,
        zone_id="water",
        projection_set_id="nitrogen-concentrations",
    )
    by_component = {
        item.component_id: item.concentration_quantity.value_decimal
        for item in projection_set.projections
    }
    assert by_component == {
        TOTAL_AMMONIA_NITROGEN_COMPONENT_ID: "0.1",
        NITRITE_NITROGEN_COMPONENT_ID: "0.02",
        NITRATE_NITROGEN_COMPONENT_ID: "0.05",
    }
    validation = validate_predictive_nitrogen_state_v1(
        state,
        zone_id="water",
    )
    assert projection_set.state_validation_sha256 == validation.canonical_sha256


def test_projection_set_is_canonical_and_does_not_mutate_state() -> None:
    state = _state()
    before_payload = state.canonical_payload()
    before_sha = state.canonical_sha256
    first = project_predictive_nitrogen_concentrations_v1(
        state,
        zone_id="water",
        projection_set_id="set",
    )
    second = project_predictive_nitrogen_concentrations_v1(
        state,
        zone_id="water",
        projection_set_id="set",
    )
    assert first.canonical_payload() == second.canonical_payload()
    assert first.canonical_sha256 == second.canonical_sha256
    assert state.canonical_payload() == before_payload
    assert state.canonical_sha256 == before_sha


def test_observed_concentration_is_not_counted_as_inventory() -> None:
    observed_concentration = CanonicalQuantityV1(
        variable_id=MATERIAL_CONCENTRATION_VARIABLE_ID,
        value_decimal="0.1",
        unit="mg N/L",
        basis=_basis("observed-tan-concentration"),
        zone_id="water",
        material_component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
    )
    state = _state(extra=(observed_concentration,))
    validation = validate_predictive_nitrogen_state_v1(
        state,
        zone_id="water",
    )
    assert len(validation.inventories) == 3
    assert all(
        item.unit == CANONICAL_NITROGEN_INVENTORY_UNIT
        for item in validation.inventories
    )


def test_projection_uses_decimal_not_native_float() -> None:
    state = _state(tan="0.2", volume="3")
    projection = project_nitrogen_concentration_v1(
        state,
        zone_id="water",
        component_id=TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
        projection_id="decimal-only",
    )
    Decimal(projection.concentration_quantity.value_decimal)
