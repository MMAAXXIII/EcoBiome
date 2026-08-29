"""Canonical predictive nitrogen-state validation and projection contracts.

RATE-1E introduces no kinetic formula, no elapsed-time integration, and no
MaterialBalance mutation.  It validates a non-overlapping predictive nitrogen
inventory view inside EcosystemStateV1 and derives deterministic
inventory-to-concentration projections from an explicit water volume.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, localcontext

from ecobiome.knowledge_persistence.serialization import (
    canonical_sha256 as canonical_payload_sha256,
)
from ecobiome.knowledge_persistence.serialization import normalize_decimal
from ecobiome.simulation.ecosystem_state_v1 import (
    CanonicalQuantityV1,
    EcosystemStateV1,
    QuantityBasisV1,
)

MATERIAL_INVENTORY_VARIABLE_ID = "material_inventory"
MATERIAL_CONCENTRATION_VARIABLE_ID = "material_concentration"
WATER_VOLUME_VARIABLE_ID = "water_volume"

TOTAL_AMMONIA_NITROGEN_COMPONENT_ID = "total_ammonia_nitrogen"
NITRITE_NITROGEN_COMPONENT_ID = "nitrite_nitrogen"
NITRATE_NITROGEN_COMPONENT_ID = "nitrate_nitrogen"

PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_IDS = (
    TOTAL_AMMONIA_NITROGEN_COMPONENT_ID,
    NITRITE_NITROGEN_COMPONENT_ID,
    NITRATE_NITROGEN_COMPONENT_ID,
)
_PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_ID_SET = frozenset(
    PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_IDS
)

# These identifiers overlap one or more RATE-1D predictive inventories and
# therefore cannot coexist as additional primary material inventories inside
# a validated predictive nitrogen zone.
OVERLAPPING_NITROGEN_INVENTORY_COMPONENT_IDS = frozenset(
    {
        "unionized_ammonia_nitrogen",
        "ammonium_nitrogen",
        "dissolved_inorganic_nitrogen",
        "reduced_inorganic_nitrogen",
        "oxidized_inorganic_nitrogen",
    }
)

CANONICAL_NITROGEN_INVENTORY_UNIT = "mg N"
CANONICAL_NITROGEN_CONCENTRATION_UNIT = "mg N/L"

CONCENTRATION_PROJECTION_PRECISION_DIGITS = 28
CONCENTRATION_PROJECTION_ROUNDING = ROUND_HALF_EVEN

_VOLUME_TO_L = {
    "L": Decimal(1),
    "liter": Decimal(1),
    "litre": Decimal(1),
    "mL": Decimal("0.001"),
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _sha256(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not _SHA256_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return normalized


def _basis_sha256(quantity: CanonicalQuantityV1) -> str:
    return canonical_payload_sha256(quantity.basis.canonical_payload())


def _volume_liters(quantity: CanonicalQuantityV1) -> Decimal:
    try:
        factor = _VOLUME_TO_L[quantity.unit]
    except KeyError as exc:
        raise ValueError(
            f"unsupported exact water-volume unit for nitrogen projection: "
            f"{quantity.unit!r}"
        ) from exc
    liters = quantity.decimal * factor
    if liters <= 0:
        raise ValueError(
            "predictive nitrogen concentration projection requires positive "
            "water volume"
        )
    return liters


def _normalized_concentration(
    inventory_mg_n: Decimal,
    water_volume_l: Decimal,
) -> str:
    with localcontext() as context:
        context.prec = CONCENTRATION_PROJECTION_PRECISION_DIGITS
        context.rounding = CONCENTRATION_PROJECTION_ROUNDING
        value = inventory_mg_n / water_volume_l
        return normalize_decimal(value)


@dataclass(frozen=True, slots=True)
class PredictiveNitrogenInventoryBindingV1:
    """Exact primary nitrogen inventory bound to one immutable input state."""

    component_id: str
    input_state_sha256: str
    zone_id: str
    value_decimal: str | int | Decimal
    unit: str
    quantity_basis_sha256: str

    def __post_init__(self) -> None:
        component_id = _nonempty(self.component_id, "component_id")
        if component_id not in _PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_ID_SET:
            raise ValueError(
                f"unsupported predictive nitrogen component: {component_id!r}"
            )
        object.__setattr__(self, "component_id", component_id)
        object.__setattr__(
            self,
            "input_state_sha256",
            _sha256(self.input_state_sha256, "input_state_sha256"),
        )
        object.__setattr__(self, "zone_id", _nonempty(self.zone_id, "zone_id"))
        object.__setattr__(self, "value_decimal", normalize_decimal(self.value_decimal))
        if Decimal(self.value_decimal) < 0:
            raise ValueError("predictive nitrogen inventories cannot be negative")
        if self.unit != CANONICAL_NITROGEN_INVENTORY_UNIT:
            raise ValueError(
                "predictive nitrogen inventory unit must be exactly "
                f"{CANONICAL_NITROGEN_INVENTORY_UNIT!r}"
            )
        object.__setattr__(
            self,
            "quantity_basis_sha256",
            _sha256(self.quantity_basis_sha256, "quantity_basis_sha256"),
        )

    @property
    def decimal(self) -> Decimal:
        return Decimal(self.value_decimal)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "component_id": self.component_id,
            "input_state_sha256": self.input_state_sha256,
            "zone_id": self.zone_id,
            "value": {"type": "decimal", "value": self.value_decimal},
            "unit": self.unit,
            "quantity_basis_sha256": self.quantity_basis_sha256,
        }


@dataclass(frozen=True, slots=True)
class PredictiveNitrogenStateValidationV1:
    """Auditable receipt for a non-overlapping predictive nitrogen inventory set."""

    profile_id: str
    input_state_sha256: str
    zone_id: str
    inventories: tuple[PredictiveNitrogenInventoryBindingV1, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", _nonempty(self.profile_id, "profile_id"))
        object.__setattr__(
            self,
            "input_state_sha256",
            _sha256(self.input_state_sha256, "input_state_sha256"),
        )
        object.__setattr__(self, "zone_id", _nonempty(self.zone_id, "zone_id"))
        inventories = tuple(self.inventories)
        component_ids = [item.component_id for item in inventories]
        if set(component_ids) != _PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_ID_SET:
            raise ValueError(
                "PredictiveNitrogenStateValidationV1 requires exactly TAN-N, "
                "nitrite-N and nitrate-N inventories"
            )
        if len(component_ids) != len(_PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_ID_SET):
            raise ValueError(
                "PredictiveNitrogenStateValidationV1 inventories must be unique"
            )
        if any(
            item.input_state_sha256 != self.input_state_sha256
            for item in inventories
        ):
            raise ValueError(
                "predictive nitrogen inventory bindings must match input state SHA"
            )
        if any(item.zone_id != self.zone_id for item in inventories):
            raise ValueError(
                "predictive nitrogen inventory bindings must match validation zone"
            )
        object.__setattr__(
            self,
            "inventories",
            tuple(sorted(inventories, key=lambda item: item.component_id)),
        )

    def get_inventory(
        self,
        component_id: str,
    ) -> PredictiveNitrogenInventoryBindingV1:
        matches = [
            item for item in self.inventories if item.component_id == component_id
        ]
        if len(matches) != 1:
            raise KeyError(
                f"expected one predictive nitrogen inventory for {component_id!r}"
            )
        return matches[0]

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-predictive-nitrogen-state-validation-v1",
            "profile_id": self.profile_id,
            "input_state_sha256": self.input_state_sha256,
            "zone_id": self.zone_id,
            "inventories": [
                item.canonical_payload() for item in self.inventories
            ],
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())


def validate_predictive_nitrogen_state_v1(
    state: EcosystemStateV1,
    *,
    zone_id: str,
) -> PredictiveNitrogenStateValidationV1:
    """Validate RATE-1D primary nitrogen inventories without mutating state."""
    normalized_zone_id = _nonempty(zone_id, "zone_id")

    overlapping = sorted(
        {
            item.material_component_id
            for item in state.quantities
            if item.variable_id == MATERIAL_INVENTORY_VARIABLE_ID
            and item.zone_id == normalized_zone_id
            and item.material_component_id
            in OVERLAPPING_NITROGEN_INVENTORY_COMPONENT_IDS
        }
    )
    if overlapping:
        raise ValueError(
            "predictive nitrogen state contains overlapping primary inventory "
            f"components: {overlapping!r}"
        )

    bindings: list[PredictiveNitrogenInventoryBindingV1] = []
    for component_id in PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_IDS:
        try:
            quantity = state.get_quantity(
                MATERIAL_INVENTORY_VARIABLE_ID,
                zone_id=normalized_zone_id,
                material_component_id=component_id,
            )
        except KeyError as exc:
            raise ValueError(
                "predictive nitrogen state is missing primary inventory "
                f"{component_id!r}"
            ) from exc

        if quantity.unit != CANONICAL_NITROGEN_INVENTORY_UNIT:
            raise ValueError(
                f"predictive nitrogen inventory {component_id!r} must use "
                f"{CANONICAL_NITROGEN_INVENTORY_UNIT!r}"
            )
        if quantity.decimal < 0:
            raise ValueError(
                f"predictive nitrogen inventory {component_id!r} cannot be negative"
            )
        bindings.append(
            PredictiveNitrogenInventoryBindingV1(
                component_id=component_id,
                input_state_sha256=state.canonical_sha256,
                zone_id=normalized_zone_id,
                value_decimal=quantity.value_decimal,
                unit=quantity.unit,
                quantity_basis_sha256=_basis_sha256(quantity),
            )
        )

    return PredictiveNitrogenStateValidationV1(
        profile_id=state.profile_id,
        input_state_sha256=state.canonical_sha256,
        zone_id=normalized_zone_id,
        inventories=tuple(bindings),
    )


@dataclass(frozen=True, slots=True)
class NitrogenConcentrationProjectionV1:
    """One deterministic primary-inventory -> concentration projection."""

    projection_id: str
    profile_id: str
    input_state_sha256: str
    zone_id: str
    component_id: str
    inventory_quantity: CanonicalQuantityV1
    water_volume_quantity: CanonicalQuantityV1
    concentration_quantity: CanonicalQuantityV1
    precision_digits: int = CONCENTRATION_PROJECTION_PRECISION_DIGITS
    rounding: str = "ROUND_HALF_EVEN"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "projection_id",
            _nonempty(self.projection_id, "projection_id"),
        )
        object.__setattr__(self, "profile_id", _nonempty(self.profile_id, "profile_id"))
        object.__setattr__(
            self,
            "input_state_sha256",
            _sha256(self.input_state_sha256, "input_state_sha256"),
        )
        object.__setattr__(self, "zone_id", _nonempty(self.zone_id, "zone_id"))
        component_id = _nonempty(self.component_id, "component_id")
        if component_id not in _PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_ID_SET:
            raise ValueError(
                f"unsupported predictive nitrogen component: {component_id!r}"
            )
        object.__setattr__(self, "component_id", component_id)

        if self.inventory_quantity.key != (
            MATERIAL_INVENTORY_VARIABLE_ID,
            self.zone_id,
            self.component_id,
        ):
            raise ValueError(
                "NitrogenConcentrationProjectionV1 inventory quantity key mismatch"
            )
        if self.inventory_quantity.unit != CANONICAL_NITROGEN_INVENTORY_UNIT:
            raise ValueError(
                "NitrogenConcentrationProjectionV1 inventory must use 'mg N'"
            )
        if self.inventory_quantity.decimal < 0:
            raise ValueError(
                "NitrogenConcentrationProjectionV1 inventory cannot be negative"
            )

        if self.water_volume_quantity.key != (
            WATER_VOLUME_VARIABLE_ID,
            self.zone_id,
            None,
        ):
            raise ValueError(
                "NitrogenConcentrationProjectionV1 water-volume quantity key mismatch"
            )
        _volume_liters(self.water_volume_quantity)

        if self.concentration_quantity.key != (
            MATERIAL_CONCENTRATION_VARIABLE_ID,
            self.zone_id,
            self.component_id,
        ):
            raise ValueError(
                "NitrogenConcentrationProjectionV1 concentration quantity key mismatch"
            )
        if (
            self.concentration_quantity.unit
            != CANONICAL_NITROGEN_CONCENTRATION_UNIT
        ):
            raise ValueError(
                "NitrogenConcentrationProjectionV1 concentration must use 'mg N/L'"
            )
        if self.concentration_quantity.basis.kind != "derived":
            raise ValueError(
                "NitrogenConcentrationProjectionV1 concentration basis must be derived"
            )
        if self.concentration_quantity.basis.reference_id != self.projection_id:
            raise ValueError(
                "NitrogenConcentrationProjectionV1 derived basis must reference "
                "projection_id"
            )

        if (
            isinstance(self.precision_digits, bool)
            or not isinstance(self.precision_digits, int)
            or self.precision_digits
            != CONCENTRATION_PROJECTION_PRECISION_DIGITS
        ):
            raise ValueError(
                "NitrogenConcentrationProjectionV1 precision_digits must equal "
                f"{CONCENTRATION_PROJECTION_PRECISION_DIGITS}"
            )
        if self.rounding != "ROUND_HALF_EVEN":
            raise ValueError(
                "NitrogenConcentrationProjectionV1 rounding must be "
                "'ROUND_HALF_EVEN'"
            )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-nitrogen-concentration-projection-v1",
            "projection_id": self.projection_id,
            "profile_id": self.profile_id,
            "input_state_sha256": self.input_state_sha256,
            "zone_id": self.zone_id,
            "component_id": self.component_id,
            "inventory_quantity": self.inventory_quantity.canonical_payload(),
            "inventory_basis_sha256": _basis_sha256(self.inventory_quantity),
            "water_volume_quantity": self.water_volume_quantity.canonical_payload(),
            "water_volume_basis_sha256": _basis_sha256(self.water_volume_quantity),
            "concentration_quantity": self.concentration_quantity.canonical_payload(),
            "precision_digits": self.precision_digits,
            "rounding": self.rounding,
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())


def project_nitrogen_concentration_v1(
    state: EcosystemStateV1,
    *,
    zone_id: str,
    component_id: str,
    projection_id: str,
) -> NitrogenConcentrationProjectionV1:
    """Project one validated primary nitrogen inventory to `mg N/L`."""
    validation = validate_predictive_nitrogen_state_v1(
        state,
        zone_id=zone_id,
    )
    if component_id not in _PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_ID_SET:
        raise ValueError(
            f"unsupported predictive nitrogen component: {component_id!r}"
        )
    inventory = state.get_quantity(
        MATERIAL_INVENTORY_VARIABLE_ID,
        zone_id=validation.zone_id,
        material_component_id=component_id,
    )
    try:
        water_volume = state.get_quantity(
            WATER_VOLUME_VARIABLE_ID,
            zone_id=validation.zone_id,
            material_component_id=None,
        )
    except KeyError as exc:
        raise ValueError(
            "predictive nitrogen concentration projection requires exact water volume"
        ) from exc
    volume_liters = _volume_liters(water_volume)
    concentration_decimal = _normalized_concentration(
        inventory.decimal,
        volume_liters,
    )
    concentration = CanonicalQuantityV1(
        variable_id=MATERIAL_CONCENTRATION_VARIABLE_ID,
        value_decimal=concentration_decimal,
        unit=CANONICAL_NITROGEN_CONCENTRATION_UNIT,
        basis=QuantityBasisV1(
            kind="derived",
            reference_id=_nonempty(projection_id, "projection_id"),
            note=(
                "predictive nitrogen inventory divided by exact water volume; "
                "RATE-1E deterministic projection"
            ),
        ),
        zone_id=validation.zone_id,
        material_component_id=component_id,
    )
    return NitrogenConcentrationProjectionV1(
        projection_id=projection_id,
        profile_id=state.profile_id,
        input_state_sha256=state.canonical_sha256,
        zone_id=validation.zone_id,
        component_id=component_id,
        inventory_quantity=inventory,
        water_volume_quantity=water_volume,
        concentration_quantity=concentration,
    )


@dataclass(frozen=True, slots=True)
class PredictiveNitrogenConcentrationSetV1:
    """All three deterministic primary nitrogen concentration projections."""

    projection_set_id: str
    profile_id: str
    input_state_sha256: str
    zone_id: str
    state_validation_sha256: str
    projections: tuple[NitrogenConcentrationProjectionV1, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "projection_set_id",
            _nonempty(self.projection_set_id, "projection_set_id"),
        )
        object.__setattr__(self, "profile_id", _nonempty(self.profile_id, "profile_id"))
        object.__setattr__(
            self,
            "input_state_sha256",
            _sha256(self.input_state_sha256, "input_state_sha256"),
        )
        object.__setattr__(self, "zone_id", _nonempty(self.zone_id, "zone_id"))
        object.__setattr__(
            self,
            "state_validation_sha256",
            _sha256(self.state_validation_sha256, "state_validation_sha256"),
        )
        projections = tuple(self.projections)
        component_ids = [item.component_id for item in projections]
        if set(component_ids) != _PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_ID_SET:
            raise ValueError(
                "PredictiveNitrogenConcentrationSetV1 requires exactly three "
                "primary nitrogen projections"
            )
        if len(component_ids) != len(_PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_ID_SET):
            raise ValueError(
                "PredictiveNitrogenConcentrationSetV1 projections must be unique"
            )
        if any(
            item.input_state_sha256 != self.input_state_sha256
            for item in projections
        ):
            raise ValueError(
                "nitrogen concentration projections must match input state SHA"
            )
        if any(item.zone_id != self.zone_id for item in projections):
            raise ValueError(
                "nitrogen concentration projections must match projection-set zone"
            )
        object.__setattr__(
            self,
            "projections",
            tuple(sorted(projections, key=lambda item: item.component_id)),
        )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-predictive-nitrogen-concentration-set-v1",
            "projection_set_id": self.projection_set_id,
            "profile_id": self.profile_id,
            "input_state_sha256": self.input_state_sha256,
            "zone_id": self.zone_id,
            "state_validation_sha256": self.state_validation_sha256,
            "projections": [
                item.canonical_payload() for item in self.projections
            ],
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())


def project_predictive_nitrogen_concentrations_v1(
    state: EcosystemStateV1,
    *,
    zone_id: str,
    projection_set_id: str,
) -> PredictiveNitrogenConcentrationSetV1:
    """Project TAN-N, nitrite-N and nitrate-N inventories without state mutation."""
    validation = validate_predictive_nitrogen_state_v1(
        state,
        zone_id=zone_id,
    )
    projections = tuple(
        project_nitrogen_concentration_v1(
            state,
            zone_id=validation.zone_id,
            component_id=component_id,
            projection_id=f"{_nonempty(projection_set_id, 'projection_set_id')}:{component_id}",
        )
        for component_id in PRIMARY_PREDICTIVE_NITROGEN_COMPONENT_IDS
    )
    return PredictiveNitrogenConcentrationSetV1(
        projection_set_id=projection_set_id,
        profile_id=state.profile_id,
        input_state_sha256=state.canonical_sha256,
        zone_id=validation.zone_id,
        state_validation_sha256=validation.canonical_sha256,
        projections=projections,
    )
