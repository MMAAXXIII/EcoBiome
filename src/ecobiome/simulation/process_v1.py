"""Deterministic N4 process evaluation contracts."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal

from ecobiome.knowledge_persistence.serialization import (
    canonical_json_text,
    normalize_decimal,
)
from ecobiome.knowledge_persistence.serialization import (
    canonical_sha256 as canonical_payload_sha256,
)
from ecobiome.simulation.ecosystem_state_v1 import QuantityBasisV1

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SUPPORT_STATUSES = frozenset(
    {
        "deterministic_identity",
        "scenario_hypothesis",
        "support_missing",
    }
)


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


@dataclass(frozen=True, slots=True)
class ScientificAssertionRefV1:
    assertion_id: str
    assertion_revision: int
    canonical_payload_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "assertion_id", _nonempty(self.assertion_id, "assertion_id")
        )
        if (
            isinstance(self.assertion_revision, bool)
            or not isinstance(self.assertion_revision, int)
            or self.assertion_revision < 1
        ):
            raise ValueError("assertion_revision must be an integer >= 1")
        digest = self.canonical_payload_sha256.strip()
        if not _SHA256_RE.fullmatch(digest):
            raise ValueError("canonical_payload_sha256 must be lowercase SHA-256")
        object.__setattr__(self, "canonical_payload_sha256", digest)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "assertion_id": self.assertion_id,
            "assertion_revision": self.assertion_revision,
            "canonical_payload_sha256": self.canonical_payload_sha256,
        }


@dataclass(frozen=True, slots=True)
class ProcessDefinitionV1:
    process_id: str
    version: str
    label: str
    input_variables: tuple[str, ...]
    output_variables: tuple[str, ...]
    assumptions: tuple[str, ...] = ()
    required_scientific_assertion_roles: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "process_id", _nonempty(self.process_id, "process_id"))
        object.__setattr__(self, "version", _nonempty(self.version, "version"))
        object.__setattr__(self, "label", _nonempty(self.label, "label"))
        if not self.input_variables or not self.output_variables:
            raise ValueError("process definition requires inputs and outputs")
        for field_name in (
            "input_variables",
            "output_variables",
            "assumptions",
            "required_scientific_assertion_roles",
        ):
            values = tuple(_nonempty(item, field_name) for item in getattr(self, field_name))
            if len(set(values)) != len(values):
                raise ValueError(f"{field_name} values must be unique")
            object.__setattr__(self, field_name, values)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "process_id": self.process_id,
            "version": self.version,
            "label": self.label,
            "input_variables": list(self.input_variables),
            "output_variables": list(self.output_variables),
            "assumptions": list(self.assumptions),
            "required_scientific_assertion_roles": list(
                self.required_scientific_assertion_roles
            ),
        }


@dataclass(frozen=True, slots=True)
class ProcessDeltaV1:
    variable_id: str
    zone_id: str | None
    material_component_id: str | None
    before_decimal: str | int | Decimal
    change_decimal: str | int | Decimal
    after_decimal: str | int | Decimal
    unit: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "variable_id", _nonempty(self.variable_id, "variable_id"))
        object.__setattr__(self, "before_decimal", normalize_decimal(self.before_decimal))
        object.__setattr__(self, "change_decimal", normalize_decimal(self.change_decimal))
        object.__setattr__(self, "after_decimal", normalize_decimal(self.after_decimal))
        object.__setattr__(self, "unit", _nonempty(self.unit, "unit"))
        if Decimal(self.before_decimal) + Decimal(self.change_decimal) != Decimal(
            self.after_decimal
        ):
            raise ValueError("process delta before + change must equal after")
        if self.zone_id is not None:
            object.__setattr__(self, "zone_id", _nonempty(self.zone_id, "zone_id"))
        if self.material_component_id is not None:
            object.__setattr__(
                self,
                "material_component_id",
                _nonempty(self.material_component_id, "material_component_id"),
            )

    @property
    def key(self) -> tuple[str, str | None, str | None]:
        return (self.variable_id, self.zone_id, self.material_component_id)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "variable_id": self.variable_id,
            "zone_id": self.zone_id,
            "material_component_id": self.material_component_id,
            "before": {"type": "decimal", "value": self.before_decimal},
            "change": {"type": "decimal", "value": self.change_decimal},
            "after": {"type": "decimal", "value": self.after_decimal},
            "unit": self.unit,
        }


@dataclass(frozen=True, slots=True)
class ProcessEvaluationV1:
    evaluation_id: str
    definition: ProcessDefinitionV1
    profile_id: str
    input_state_sha256: str
    output_state_sha256: str
    parameters_json: str
    support_status: str
    parameter_bases: tuple[QuantityBasisV1, ...]
    scientific_assertion_refs: tuple[ScientificAssertionRefV1, ...]
    deltas: tuple[ProcessDeltaV1, ...]
    assumptions: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "evaluation_id", _nonempty(self.evaluation_id, "evaluation_id")
        )
        object.__setattr__(self, "profile_id", _nonempty(self.profile_id, "profile_id"))
        for field_name in ("input_state_sha256", "output_state_sha256"):
            digest = getattr(self, field_name).strip()
            if not _SHA256_RE.fullmatch(digest):
                raise ValueError(f"{field_name} must be lowercase SHA-256")
            object.__setattr__(self, field_name, digest)
        try:
            parameters = json.loads(self.parameters_json)
        except json.JSONDecodeError as exc:
            raise ValueError("parameters_json must contain valid JSON") from exc
        if not isinstance(parameters, dict):
            raise TypeError("parameters_json must decode to an object")
        object.__setattr__(
            self,
            "parameters_json",
            canonical_json_text(parameters),
        )
        status = self.support_status.strip().lower()
        if status not in _SUPPORT_STATUSES:
            raise ValueError(f"unsupported support_status: {self.support_status!r}")
        object.__setattr__(self, "support_status", status)
        if not self.deltas:
            raise ValueError("process evaluation requires at least one delta")
        delta_keys = [item.key for item in self.deltas]
        if len(set(delta_keys)) != len(delta_keys):
            raise ValueError("process evaluation delta keys must be unique")
        for field_name in ("assumptions", "warnings", "unknowns"):
            values = tuple(_nonempty(item, field_name) for item in getattr(self, field_name))
            object.__setattr__(self, field_name, values)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-process-evaluation-v1",
            "evaluation_id": self.evaluation_id,
            "definition": self.definition.canonical_payload(),
            "profile_id": self.profile_id,
            "input_state_sha256": self.input_state_sha256,
            "output_state_sha256": self.output_state_sha256,
            "parameters": json.loads(self.parameters_json),
            "support_status": self.support_status,
            "parameter_bases": [
                item.canonical_payload() for item in self.parameter_bases
            ],
            "scientific_assertion_refs": [
                item.canonical_payload()
                for item in sorted(
                    self.scientific_assertion_refs,
                    key=lambda item: (item.assertion_id, item.assertion_revision),
                )
            ],
            "deltas": [
                item.canonical_payload()
                for item in sorted(
                    self.deltas,
                    key=lambda item: (
                        item.variable_id,
                        item.zone_id or "",
                        item.material_component_id or "",
                    ),
                )
            ],
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
            "unknowns": list(self.unknowns),
        }

    @property
    def parameters_payload(self) -> dict[str, object]:
        value = json.loads(self.parameters_json)
        if not isinstance(value, dict):
            raise TypeError("canonical parameters must remain an object")
        return value

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())
