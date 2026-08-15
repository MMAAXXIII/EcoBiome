"""Canonical exact ecosystem state contracts for N4."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ecobiome.knowledge_persistence.serialization import (
    canonical_sha256 as canonical_payload_sha256,
)
from ecobiome.knowledge_persistence.serialization import normalize_decimal

_BASIS_KINDS = frozenset(
    {
        "observation",
        "scientific_assertion",
        "user_assumption",
        "scenario_default",
        "derived",
    }
)


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


@dataclass(frozen=True, slots=True)
class QuantityBasisV1:
    kind: str
    reference_id: str
    reference_revision: int | None = None
    note: str = ""

    def __post_init__(self) -> None:
        kind = self.kind.strip().lower()
        if kind not in _BASIS_KINDS:
            raise ValueError(f"unsupported basis kind: {self.kind!r}")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(
            self, "reference_id", _nonempty(self.reference_id, "reference_id")
        )
        if self.reference_revision is not None and (
            isinstance(self.reference_revision, bool)
            or not isinstance(self.reference_revision, int)
            or self.reference_revision < 1
        ):
            raise ValueError("reference_revision must be an integer >= 1")
        if kind == "scientific_assertion" and self.reference_revision is None:
            raise ValueError(
                "scientific_assertion basis requires an exact reference_revision"
            )
        object.__setattr__(self, "note", self.note.strip())

    def canonical_payload(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "reference_id": self.reference_id,
            "reference_revision": self.reference_revision,
            "note": self.note,
        }


@dataclass(frozen=True, slots=True)
class CanonicalQuantityV1:
    variable_id: str
    value_decimal: str | int | Decimal
    unit: str
    basis: QuantityBasisV1
    zone_id: str | None = None
    material_component_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "variable_id", _nonempty(self.variable_id, "variable_id"))
        object.__setattr__(self, "value_decimal", normalize_decimal(self.value_decimal))
        object.__setattr__(self, "unit", _nonempty(self.unit, "unit"))
        if self.zone_id is not None:
            object.__setattr__(self, "zone_id", _nonempty(self.zone_id, "zone_id"))
        if self.material_component_id is not None:
            object.__setattr__(
                self,
                "material_component_id",
                _nonempty(self.material_component_id, "material_component_id"),
            )

    @property
    def decimal(self) -> Decimal:
        return Decimal(self.value_decimal)

    @property
    def key(self) -> tuple[str, str | None, str | None]:
        return (self.variable_id, self.zone_id, self.material_component_id)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "variable_id": self.variable_id,
            "value": {"type": "decimal", "value": self.value_decimal},
            "unit": self.unit,
            "basis": self.basis.canonical_payload(),
            "zone_id": self.zone_id,
            "material_component_id": self.material_component_id,
        }


@dataclass(frozen=True, slots=True)
class EcosystemStateV1:
    profile_id: str
    quantities: tuple[CanonicalQuantityV1, ...]
    logical_step: int = 0
    captured_at: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", _nonempty(self.profile_id, "profile_id"))
        if (
            isinstance(self.logical_step, bool)
            or not isinstance(self.logical_step, int)
            or self.logical_step < 0
        ):
            raise ValueError("logical_step must be an integer >= 0")
        if not self.quantities:
            raise ValueError("ecosystem state requires at least one quantity")
        keys = [item.key for item in self.quantities]
        if len(set(keys)) != len(keys):
            raise ValueError("ecosystem state quantity keys must be unique")
        if self.captured_at is not None:
            object.__setattr__(self, "captured_at", _nonempty(self.captured_at, "captured_at"))

    def get_quantity(
        self,
        variable_id: str,
        *,
        zone_id: str | None = None,
        material_component_id: str | None = None,
    ) -> CanonicalQuantityV1:
        key = (variable_id, zone_id, material_component_id)
        matches = [item for item in self.quantities if item.key == key]
        if len(matches) != 1:
            raise KeyError(f"expected exactly one quantity for key {key!r}")
        return matches[0]

    def replace_quantities(
        self,
        replacements: tuple[CanonicalQuantityV1, ...],
        *,
        logical_step: int | None = None,
    ) -> EcosystemStateV1:
        replacement_map = {item.key: item for item in replacements}
        if len(replacement_map) != len(replacements):
            raise ValueError("replacement quantity keys must be unique")
        existing_keys = {item.key for item in self.quantities}
        unknown = set(replacement_map) - existing_keys
        if unknown:
            ordered_unknown = sorted(
                unknown,
                key=lambda item: (item[0], item[1] or "", item[2] or ""),
            )
            raise KeyError(
                "cannot replace unknown quantity keys: " + repr(ordered_unknown)
            )
        if logical_step is not None and logical_step <= self.logical_step:
            raise ValueError(
                "explicit replacement logical_step must advance the ecosystem state"
            )
        updated = tuple(replacement_map.get(item.key, item) for item in self.quantities)
        return EcosystemStateV1(
            profile_id=self.profile_id,
            quantities=updated,
            logical_step=self.logical_step + 1 if logical_step is None else logical_step,
            captured_at=self.captured_at,
        )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-ecosystem-state-v1",
            "profile_id": self.profile_id,
            "logical_step": self.logical_step,
            "captured_at": self.captured_at,
            "quantities": [
                item.canonical_payload()
                for item in sorted(
                    self.quantities,
                    key=lambda item: (
                        item.variable_id,
                        item.zone_id or "",
                        item.material_component_id or "",
                    ),
                )
            ],
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())
