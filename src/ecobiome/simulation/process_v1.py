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
        "scientific_alignment_reviewed",
        "support_missing",
    }
)
_SCIENTIFIC_SUPPORT_EPISTEMIC_BY_ALIGNMENT = {
    "direct_mechanism_support": frozenset({"explicit_causal_result"}),
    "interpretive_mechanism_support": frozenset({"interpretive_support"}),
}


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


_SCIENTIFIC_ALIGNMENT_NOT_REVIEWED_UNKNOWN = (
    "scientific assertion refs supplied but process-to-assertion alignment "
    "is not reviewed in N4 V1"
)


def _is_stale_scientific_alignment_unknown(value: str) -> bool:
    return value.strip() == _SCIENTIFIC_ALIGNMENT_NOT_REVIEWED_UNKNOWN


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


def _decode_json_pointer_token(token: str) -> str:
    if re.search(r"~(?![01])", token):
        raise ValueError("JSON Pointer contains an invalid escape")
    return token.replace("~1", "/").replace("~0", "~")


def _resolve_json_pointer(payload: object, pointer: str) -> object:
    current = payload
    for raw_token in pointer.split("/")[1:]:
        token = _decode_json_pointer_token(raw_token)
        if isinstance(current, dict):
            if token not in current:
                raise ValueError(
                    f"evaluation parameter JSON Pointer is missing: {pointer!r}"
                )
            current = current[token]
            continue
        if isinstance(current, list):
            if not re.fullmatch(r"0|[1-9]\d*", token):
                raise ValueError(
                    f"evaluation parameter JSON Pointer has invalid array index: {pointer!r}"
                )
            index = int(token)
            if index >= len(current):
                raise ValueError(
                    f"evaluation parameter JSON Pointer is missing: {pointer!r}"
                )
            current = current[index]
            continue
        raise ValueError(
            f"evaluation parameter JSON Pointer cannot traverse scalar: {pointer!r}"
        )
    return current


@dataclass(frozen=True, slots=True)
class ProcessScientificParameterBindingV1:
    json_pointer: str
    expected_value_json: str

    def __post_init__(self) -> None:
        pointer = self.json_pointer.strip()
        if not pointer or not pointer.startswith("/"):
            raise ValueError(
                "json_pointer must be a non-empty absolute JSON Pointer"
            )
        for token in pointer.split("/")[1:]:
            _decode_json_pointer_token(token)
        object.__setattr__(self, "json_pointer", pointer)
        try:
            expected_value = json.loads(self.expected_value_json)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "expected_value_json must contain valid canonicalizable JSON"
            ) from exc
        object.__setattr__(
            self,
            "expected_value_json",
            canonical_json_text(expected_value),
        )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "json_pointer": self.json_pointer,
            "expected_value": json.loads(self.expected_value_json),
        }


@dataclass(frozen=True, slots=True)
class ProcessScientificEvaluationScopeV1:
    process_id: str
    process_version: str
    role: str
    required_parameter_bindings: tuple[
        ProcessScientificParameterBindingV1, ...
    ]
    parameter_match_mode: str = "contains_exact_required"

    def __post_init__(self) -> None:
        for field_name in ("process_id", "process_version", "role"):
            object.__setattr__(
                self,
                field_name,
                _nonempty(str(getattr(self, field_name)), field_name),
            )
        if self.parameter_match_mode != "contains_exact_required":
            raise ValueError(
                "parameter_match_mode must be 'contains_exact_required' in V1"
            )
        bindings = tuple(self.required_parameter_bindings)
        if not bindings:
            raise ValueError("required_parameter_bindings must not be empty")
        if not all(isinstance(item, ProcessScientificParameterBindingV1) for item in bindings):
            raise TypeError(
                "required_parameter_bindings must contain ProcessScientificParameterBindingV1 values"
            )
        pointers = [item.json_pointer for item in bindings]
        if len(set(pointers)) != len(pointers):
            raise ValueError("required_parameter_bindings JSON Pointers must be unique")
        object.__setattr__(
            self,
            "required_parameter_bindings",
            tuple(sorted(bindings, key=lambda item: item.json_pointer)),
        )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-process-scientific-evaluation-scope-v1",
            "process_id": self.process_id,
            "process_version": self.process_version,
            "role": self.role,
            "parameter_match_mode": self.parameter_match_mode,
            "required_parameter_bindings": [
                item.canonical_payload() for item in self.required_parameter_bindings
            ],
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())

    def require_match(
        self,
        *,
        process_id: str,
        process_version: str,
        role: str,
        parameters: dict[str, object],
    ) -> None:
        if process_id != self.process_id:
            raise ValueError("evaluation scope process_id mismatch")
        if process_version != self.process_version:
            raise ValueError("evaluation scope process_version mismatch")
        if role != self.role:
            raise ValueError("evaluation scope role mismatch")
        for binding in self.required_parameter_bindings:
            observed = _resolve_json_pointer(parameters, binding.json_pointer)
            if canonical_json_text(observed) != binding.expected_value_json:
                raise ValueError(
                    "evaluation parameter does not match reviewed scientific "
                    f"scope at {binding.json_pointer!r}"
                )


@dataclass(frozen=True, slots=True)
class ProcessScientificSupportV1:
    role: str
    assertion_ref: ScientificAssertionRefV1
    alignment_class: str
    epistemic_class: str
    alignment_policy_name: str
    alignment_policy_version: str
    alignment_policy_sha256: str
    evaluation_scope: ProcessScientificEvaluationScopeV1
    evaluation_scope_sha256: str
    evidence_state: str | None = None
    warnings: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "role",
            "alignment_class",
            "epistemic_class",
            "alignment_policy_name",
            "alignment_policy_version",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonempty(str(getattr(self, field_name)), field_name),
            )
        if self.alignment_class not in _SCIENTIFIC_SUPPORT_EPISTEMIC_BY_ALIGNMENT:
            raise ValueError(
                f"unsupported alignment_class: {self.alignment_class!r}"
            )
        allowed_epistemic = _SCIENTIFIC_SUPPORT_EPISTEMIC_BY_ALIGNMENT[
            self.alignment_class
        ]
        if self.epistemic_class not in allowed_epistemic:
            raise ValueError(
                "alignment_class cannot increase or reinterpret epistemic strength"
            )
        digest = self.alignment_policy_sha256.strip()
        if not _SHA256_RE.fullmatch(digest):
            raise ValueError(
                "alignment_policy_sha256 must be lowercase SHA-256"
            )
        object.__setattr__(self, "alignment_policy_sha256", digest)
        if not isinstance(self.evaluation_scope, ProcessScientificEvaluationScopeV1):
            raise TypeError("evaluation_scope must be ProcessScientificEvaluationScopeV1")
        if self.evaluation_scope.role != self.role:
            raise ValueError("evaluation_scope role must equal support role")
        scope_digest = self.evaluation_scope_sha256.strip()
        if not _SHA256_RE.fullmatch(scope_digest):
            raise ValueError("evaluation_scope_sha256 must be lowercase SHA-256")
        if scope_digest != self.evaluation_scope.canonical_sha256:
            raise ValueError("evaluation_scope_sha256 must match evaluation_scope")
        object.__setattr__(self, "evaluation_scope_sha256", scope_digest)
        if self.evidence_state is not None:
            object.__setattr__(
                self,
                "evidence_state",
                _nonempty(self.evidence_state, "evidence_state"),
            )
        for field_name in ("warnings", "uncertainties"):
            values = tuple(
                _nonempty(item, field_name)
                for item in getattr(self, field_name)
            )
            object.__setattr__(self, field_name, values)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "role": self.role,
            "assertion_ref": self.assertion_ref.canonical_payload(),
            "alignment_class": self.alignment_class,
            "epistemic_class": self.epistemic_class,
            "alignment_policy_name": self.alignment_policy_name,
            "alignment_policy_version": self.alignment_policy_version,
            "alignment_policy_sha256": self.alignment_policy_sha256,
            "evaluation_scope": self.evaluation_scope.canonical_payload(),
            "evaluation_scope_sha256": self.evaluation_scope_sha256,
            "evidence_state": self.evidence_state,
            "warnings": list(self.warnings),
            "uncertainties": list(self.uncertainties),
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
    scientific_supports: tuple[ProcessScientificSupportV1, ...] = ()
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
        if self.support_status == "scientific_alignment_reviewed":
            if not self.scientific_supports:
                raise ValueError(
                    "scientific_alignment_reviewed requires scientific_supports"
                )
            for support in self.scientific_supports:
                try:
                    support.evaluation_scope.require_match(
                        process_id=self.definition.process_id,
                        process_version=self.definition.version,
                        role=support.role,
                        parameters=self.parameters_payload,
                    )
                except ValueError as exc:
                    raise ValueError(
                        "scientific_supports evaluation scope mismatch"
                    ) from exc
            stale_alignment_unknowns = tuple(
                item
                for item in self.unknowns
                if _is_stale_scientific_alignment_unknown(item)
            )
            if stale_alignment_unknowns:
                raise ValueError(
                    "scientific_alignment_reviewed forbids pending/not-reviewed "
                    "alignment unknowns"
                )
            support_keys = [
                (
                    item.role,
                    item.assertion_ref.assertion_id,
                    item.assertion_ref.assertion_revision,
                    item.assertion_ref.canonical_payload_sha256,
                    item.alignment_class,
                    item.epistemic_class,
                    item.alignment_policy_sha256,
                )
                for item in self.scientific_supports
            ]
            if len(set(support_keys)) != len(support_keys):
                raise ValueError("scientific_supports must be unique")
            support_roles = {item.role for item in self.scientific_supports}
            missing_roles = (
                set(self.definition.required_scientific_assertion_roles)
                - support_roles
            )
            if missing_roles:
                raise ValueError(
                    "scientific_supports do not cover required roles: "
                    f"{sorted(missing_roles)!r}"
                )
            support_refs = {
                item.assertion_ref for item in self.scientific_supports
            }
            if support_refs != set(self.scientific_assertion_refs):
                raise ValueError(
                    "scientific_supports must match scientific_assertion_refs"
                )
        elif self.scientific_supports:
            raise ValueError(
                "scientific_supports require scientific_alignment_reviewed"
            )

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
            **(
                {
                    "scientific_supports": [
                        item.canonical_payload()
                        for item in sorted(
                            self.scientific_supports,
                            key=lambda item: (
                                item.role,
                                item.assertion_ref.assertion_id,
                                item.assertion_ref.assertion_revision,
                            ),
                        )
                    ]
                }
                if self.scientific_supports
                else {}
            ),
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
