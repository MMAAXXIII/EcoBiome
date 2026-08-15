"""Explicit N4 intervention contracts."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ecobiome.knowledge_persistence.serialization import (
    canonical_sha256 as canonical_payload_sha256,
)
from ecobiome.knowledge_persistence.serialization import normalize_decimal
from ecobiome.simulation.ecosystem_state_v1 import QuantityBasisV1


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


@dataclass(frozen=True, slots=True)
class ReplacementCompositionV1:
    material_component_id: str
    concentration_decimal: str | int | Decimal
    unit: str
    basis: QuantityBasisV1

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "material_component_id",
            _nonempty(self.material_component_id, "material_component_id"),
        )
        object.__setattr__(
            self, "concentration_decimal", normalize_decimal(self.concentration_decimal)
        )
        object.__setattr__(self, "unit", _nonempty(self.unit, "unit"))
        if Decimal(self.concentration_decimal) < 0:
            raise ValueError("replacement concentration cannot be negative")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "material_component_id": self.material_component_id,
            "concentration": {
                "value": {
                    "type": "decimal",
                    "value": self.concentration_decimal,
                },
                "unit": self.unit,
            },
            "basis": self.basis.canonical_payload(),
        }


@dataclass(frozen=True, slots=True)
class WaterExchangeInterventionV1:
    id: str
    water_zone_id: str
    removed_volume_decimal: str | int | Decimal
    removed_volume_unit: str
    replacement_volume_decimal: str | int | Decimal
    replacement_volume_unit: str
    replacement_composition: tuple[ReplacementCompositionV1, ...]
    basis: QuantityBasisV1
    logical_step: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _nonempty(self.id, "intervention id"))
        object.__setattr__(
            self, "water_zone_id", _nonempty(self.water_zone_id, "water_zone_id")
        )
        object.__setattr__(
            self, "removed_volume_decimal", normalize_decimal(self.removed_volume_decimal)
        )
        object.__setattr__(
            self,
            "replacement_volume_decimal",
            normalize_decimal(self.replacement_volume_decimal),
        )
        object.__setattr__(
            self, "removed_volume_unit", _nonempty(self.removed_volume_unit, "unit")
        )
        object.__setattr__(
            self, "replacement_volume_unit", _nonempty(self.replacement_volume_unit, "unit")
        )
        if Decimal(self.removed_volume_decimal) < 0:
            raise ValueError("removed volume cannot be negative")
        if Decimal(self.replacement_volume_decimal) < 0:
            raise ValueError("replacement volume cannot be negative")
        ids = [item.material_component_id for item in self.replacement_composition]
        if len(set(ids)) != len(ids):
            raise ValueError("replacement composition component ids must be unique")
        if self.logical_step is not None and (
            isinstance(self.logical_step, bool)
            or not isinstance(self.logical_step, int)
            or self.logical_step < 0
        ):
            raise ValueError("logical_step must be an integer >= 0")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-water-exchange-intervention-v1",
            "id": self.id,
            "water_zone_id": self.water_zone_id,
            "removed_volume": {
                "value": {
                    "type": "decimal",
                    "value": self.removed_volume_decimal,
                },
                "unit": self.removed_volume_unit,
            },
            "replacement_volume": {
                "value": {
                    "type": "decimal",
                    "value": self.replacement_volume_decimal,
                },
                "unit": self.replacement_volume_unit,
            },
            "replacement_composition": [
                item.canonical_payload()
                for item in sorted(
                    self.replacement_composition,
                    key=lambda item: item.material_component_id,
                )
            ],
            "basis": self.basis.canonical_payload(),
            "logical_step": self.logical_step,
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())
