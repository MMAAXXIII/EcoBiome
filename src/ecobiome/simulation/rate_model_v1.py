"""Generic deterministic RateModel V1 contracts.

RATE-1C intentionally defines no concrete kinetic formula.  A numerical rate
can only be represented when the model definition, parameter set, required
state bindings, and applicability result satisfy the reviewed support boundary
adopted by RATE-1A/RATE-1B.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from ecobiome.knowledge_persistence.serialization import (
    canonical_sha256 as canonical_payload_sha256,
)
from ecobiome.knowledge_persistence.serialization import normalize_decimal
from ecobiome.simulation.ecosystem_state_v1 import EcosystemStateV1
from ecobiome.simulation.process_v1 import ScientificAssertionRefV1

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_RATE_SUPPORT_ROLES = frozenset(
    {
        "kinetic_form",
        "kinetic_parameter",
        "applicability_domain",
    }
)
_DEFINITION_SUPPORT_ROLES = frozenset(
    {
        "kinetic_form",
        "applicability_domain",
    }
)
_APPLICABILITY_STATUSES = frozenset(
    {
        "applicable",
        "missing_required_quantity",
        "outside_reviewed_domain",
        "scientific_support_missing",
        "parameter_support_missing",
    }
)
_FORBIDDEN_INTEGRATION_PARAMETER_IDS = frozenset(
    {
        "dt",
        "duration",
        "elapsed_time",
        "time_step",
        "timestep",
    }
)
_CANONICAL_RATE_UNIT = "mg N/h"


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


def _normalized_identifier(value: str, field_name: str) -> str:
    normalized = _nonempty(value, field_name)
    if normalized.strip().lower() in _FORBIDDEN_INTEGRATION_PARAMETER_IDS:
        raise ValueError(
            f"{field_name} cannot hide an integration-time parameter in RateModel V1"
        )
    return normalized


@dataclass(frozen=True, slots=True)
class RateScientificSupportV1:
    """Exact identity of one reviewed scientific support artifact."""

    role: str
    support_id: str
    support_sha256: str
    assertion_ref: ScientificAssertionRefV1
    reviewed_by: str
    applicability_scope: str

    def __post_init__(self) -> None:
        role = self.role.strip().lower()
        if role not in _RATE_SUPPORT_ROLES:
            raise ValueError(f"unsupported RateModel scientific support role: {self.role!r}")
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "support_id", _nonempty(self.support_id, "support_id"))
        object.__setattr__(
            self,
            "support_sha256",
            _sha256(self.support_sha256, "support_sha256"),
        )
        object.__setattr__(self, "reviewed_by", _nonempty(self.reviewed_by, "reviewed_by"))
        object.__setattr__(
            self,
            "applicability_scope",
            _nonempty(self.applicability_scope, "applicability_scope"),
        )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "role": self.role,
            "support_id": self.support_id,
            "support_sha256": self.support_sha256,
            "assertion_ref": self.assertion_ref.canonical_payload(),
            "reviewed_by": self.reviewed_by,
            "applicability_scope": self.applicability_scope,
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())


@dataclass(frozen=True, slots=True)
class RateQuantityRequirementV1:
    """One exact state quantity required by a rate model."""

    requirement_id: str
    variable_id: str
    unit: str
    semantic_role: str
    material_component_id: str | None = None
    zone_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "requirement_id",
            _normalized_identifier(self.requirement_id, "requirement_id"),
        )
        object.__setattr__(self, "variable_id", _nonempty(self.variable_id, "variable_id"))
        object.__setattr__(self, "unit", _nonempty(self.unit, "unit"))
        object.__setattr__(
            self,
            "semantic_role",
            _nonempty(self.semantic_role, "semantic_role"),
        )
        if self.material_component_id is not None:
            object.__setattr__(
                self,
                "material_component_id",
                _nonempty(self.material_component_id, "material_component_id"),
            )
        if not isinstance(self.zone_required, bool):
            raise TypeError("zone_required must be bool")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "requirement_id": self.requirement_id,
            "variable_id": self.variable_id,
            "unit": self.unit,
            "semantic_role": self.semantic_role,
            "material_component_id": self.material_component_id,
            "zone_required": self.zone_required,
        }


@dataclass(frozen=True, slots=True)
class RateInputQuantityBindingV1:
    """Exact quantity read from one immutable EcosystemStateV1."""

    requirement_id: str
    input_state_sha256: str
    variable_id: str
    zone_id: str | None
    material_component_id: str | None
    value_decimal: str | int | Decimal
    unit: str
    quantity_basis_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "requirement_id",
            _normalized_identifier(self.requirement_id, "requirement_id"),
        )
        object.__setattr__(
            self,
            "input_state_sha256",
            _sha256(self.input_state_sha256, "input_state_sha256"),
        )
        object.__setattr__(self, "variable_id", _nonempty(self.variable_id, "variable_id"))
        if self.zone_id is not None:
            object.__setattr__(self, "zone_id", _nonempty(self.zone_id, "zone_id"))
        if self.material_component_id is not None:
            object.__setattr__(
                self,
                "material_component_id",
                _nonempty(self.material_component_id, "material_component_id"),
            )
        object.__setattr__(self, "value_decimal", normalize_decimal(self.value_decimal))
        object.__setattr__(self, "unit", _nonempty(self.unit, "unit"))
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
            "requirement_id": self.requirement_id,
            "input_state_sha256": self.input_state_sha256,
            "variable_id": self.variable_id,
            "zone_id": self.zone_id,
            "material_component_id": self.material_component_id,
            "value": {"type": "decimal", "value": self.value_decimal},
            "unit": self.unit,
            "quantity_basis_sha256": self.quantity_basis_sha256,
        }


def bind_rate_quantity_v1(
    state: EcosystemStateV1,
    requirement: RateQuantityRequirementV1,
    *,
    zone_id: str | None,
) -> RateInputQuantityBindingV1:
    """Bind one definition requirement to an exact state quantity without mutation."""
    if requirement.zone_required and zone_id is None:
        raise ValueError(
            f"rate quantity requirement {requirement.requirement_id!r} requires zone_id"
        )
    if not requirement.zone_required and zone_id is not None:
        raise ValueError(
            f"rate quantity requirement {requirement.requirement_id!r} is not zone-bound"
        )
    quantity = state.get_quantity(
        requirement.variable_id,
        zone_id=zone_id,
        material_component_id=requirement.material_component_id,
    )
    if quantity.unit != requirement.unit:
        raise ValueError(
            f"rate quantity unit mismatch for {requirement.requirement_id!r}: "
            f"{quantity.unit!r} != {requirement.unit!r}"
        )
    return RateInputQuantityBindingV1(
        requirement_id=requirement.requirement_id,
        input_state_sha256=state.canonical_sha256,
        variable_id=quantity.variable_id,
        zone_id=quantity.zone_id,
        material_component_id=quantity.material_component_id,
        value_decimal=quantity.value_decimal,
        unit=quantity.unit,
        quantity_basis_sha256=canonical_payload_sha256(
            quantity.basis.canonical_payload()
        ),
    )


@dataclass(frozen=True, slots=True)
class RateParameterV1:
    """One numeric rate parameter and its reviewed kinetic-parameter support."""

    parameter_id: str
    value_decimal: str | int | Decimal
    unit: str
    semantic_role: str
    scientific_supports: tuple[RateScientificSupportV1, ...] = ()
    applicability_scope: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "parameter_id",
            _normalized_identifier(self.parameter_id, "parameter_id"),
        )
        object.__setattr__(self, "value_decimal", normalize_decimal(self.value_decimal))
        object.__setattr__(self, "unit", _nonempty(self.unit, "unit"))
        object.__setattr__(
            self,
            "semantic_role",
            _nonempty(self.semantic_role, "semantic_role"),
        )
        supports = tuple(self.scientific_supports)
        if any(item.role != "kinetic_parameter" for item in supports):
            raise ValueError(
                "RateParameterV1 scientific_supports must use role='kinetic_parameter'"
            )
        keys = [(item.support_id, item.support_sha256) for item in supports]
        if len(set(keys)) != len(keys):
            raise ValueError("RateParameterV1 scientific_supports must be unique")
        object.__setattr__(
            self,
            "scientific_supports",
            tuple(sorted(supports, key=lambda item: (item.support_id, item.support_sha256))),
        )
        object.__setattr__(
            self,
            "applicability_scope",
            self.applicability_scope.strip(),
        )

    @property
    def has_reviewed_support(self) -> bool:
        return bool(self.scientific_supports)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "parameter_id": self.parameter_id,
            "value": {"type": "decimal", "value": self.value_decimal},
            "unit": self.unit,
            "semantic_role": self.semantic_role,
            "scientific_supports": [
                item.canonical_payload() for item in self.scientific_supports
            ],
            "applicability_scope": self.applicability_scope,
        }


@dataclass(frozen=True, slots=True)
class RateParameterSetV1:
    parameter_set_id: str
    parameters: tuple[RateParameterV1, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "parameter_set_id",
            _nonempty(self.parameter_set_id, "parameter_set_id"),
        )
        parameters = tuple(self.parameters)
        ids = [item.parameter_id for item in parameters]
        if len(set(ids)) != len(ids):
            raise ValueError("RateParameterSetV1 parameter_id values must be unique")
        object.__setattr__(
            self,
            "parameters",
            tuple(sorted(parameters, key=lambda item: item.parameter_id)),
        )

    @property
    def parameter_ids(self) -> frozenset[str]:
        return frozenset(item.parameter_id for item in self.parameters)

    @property
    def all_parameters_reviewed(self) -> bool:
        return all(item.has_reviewed_support for item in self.parameters)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-rate-parameter-set-v1",
            "parameter_set_id": self.parameter_set_id,
            "parameters": [item.canonical_payload() for item in self.parameters],
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())


@dataclass(frozen=True, slots=True)
class RateModelDefinitionV1:
    rate_model_id: str
    version: str
    process_id: str
    process_version: str
    source_component_id: str
    target_component_id: str
    required_state_quantities: tuple[RateQuantityRequirementV1, ...]
    required_parameters: tuple[str, ...]
    scientific_supports: tuple[RateScientificSupportV1, ...] = ()
    assumptions: tuple[str, ...] = ()
    output_rate_unit: str = _CANONICAL_RATE_UNIT

    def __post_init__(self) -> None:
        for field_name in (
            "rate_model_id",
            "version",
            "process_id",
            "process_version",
            "source_component_id",
            "target_component_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonempty(str(getattr(self, field_name)), field_name),
            )
        requirements = tuple(self.required_state_quantities)
        if not requirements:
            raise ValueError("RateModelDefinitionV1 requires state quantities")
        requirement_ids = [item.requirement_id for item in requirements]
        if len(set(requirement_ids)) != len(requirement_ids):
            raise ValueError("required_state_quantities requirement_id values must be unique")
        object.__setattr__(
            self,
            "required_state_quantities",
            tuple(sorted(requirements, key=lambda item: item.requirement_id)),
        )
        parameters = tuple(
            _normalized_identifier(item, "required_parameters")
            for item in self.required_parameters
        )
        if len(set(parameters)) != len(parameters):
            raise ValueError("required_parameters values must be unique")
        object.__setattr__(self, "required_parameters", tuple(sorted(parameters)))
        supports = tuple(self.scientific_supports)
        if any(item.role not in _DEFINITION_SUPPORT_ROLES for item in supports):
            raise ValueError(
                "RateModelDefinitionV1 supports may only use kinetic_form or "
                "applicability_domain"
            )
        support_keys = [
            (item.role, item.support_id, item.support_sha256) for item in supports
        ]
        if len(set(support_keys)) != len(support_keys):
            raise ValueError("RateModelDefinitionV1 scientific_supports must be unique")
        object.__setattr__(
            self,
            "scientific_supports",
            tuple(
                sorted(
                    supports,
                    key=lambda item: (item.role, item.support_id, item.support_sha256),
                )
            ),
        )
        assumptions = tuple(_nonempty(item, "assumptions") for item in self.assumptions)
        object.__setattr__(self, "assumptions", assumptions)
        if self.output_rate_unit != _CANONICAL_RATE_UNIT:
            raise ValueError(
                f"RateModel V1 output_rate_unit must be {_CANONICAL_RATE_UNIT!r}"
            )

    @property
    def required_quantity_ids(self) -> frozenset[str]:
        return frozenset(item.requirement_id for item in self.required_state_quantities)

    @property
    def reviewed_support_roles(self) -> frozenset[str]:
        return frozenset(item.role for item in self.scientific_supports)

    @property
    def has_complete_definition_support(self) -> bool:
        return _DEFINITION_SUPPORT_ROLES <= self.reviewed_support_roles

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-rate-model-definition-v1",
            "rate_model_id": self.rate_model_id,
            "version": self.version,
            "process_id": self.process_id,
            "process_version": self.process_version,
            "source_component_id": self.source_component_id,
            "target_component_id": self.target_component_id,
            "required_state_quantities": [
                item.canonical_payload() for item in self.required_state_quantities
            ],
            "required_parameters": list(self.required_parameters),
            "scientific_supports": [
                item.canonical_payload() for item in self.scientific_supports
            ],
            "assumptions": list(self.assumptions),
            "output_rate_unit": self.output_rate_unit,
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())


@dataclass(frozen=True, slots=True)
class RateApplicabilityResultV1:
    status: str
    reason_codes: tuple[str, ...] = ()
    details: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        status = self.status.strip().lower()
        if status not in _APPLICABILITY_STATUSES:
            raise ValueError(f"unsupported RateModel applicability status: {self.status!r}")
        object.__setattr__(self, "status", status)
        reasons = tuple(_nonempty(item, "reason_codes") for item in self.reason_codes)
        details = tuple(_nonempty(item, "details") for item in self.details)
        if status == "applicable" and reasons:
            raise ValueError("applicable RateModel result cannot have blocking reason_codes")
        if status != "applicable" and not reasons:
            raise ValueError("non-applicable RateModel result requires reason_codes")
        object.__setattr__(self, "reason_codes", tuple(sorted(set(reasons))))
        object.__setattr__(self, "details", details)

    @property
    def is_applicable(self) -> bool:
        return self.status == "applicable"

    def canonical_payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "details": list(self.details),
        }


@dataclass(frozen=True, slots=True)
class RateEvaluationV1:
    """State-preserving instantaneous rate evaluation.

    This contract intentionally contains no output-state identity and no
    elapsed-time field.  Rate -> extent integration is a separate future
    boundary.
    """

    evaluation_id: str
    definition: RateModelDefinitionV1
    profile_id: str
    input_state_sha256: str
    zone_id: str
    applicability: RateApplicabilityResultV1
    quantity_bindings: tuple[RateInputQuantityBindingV1, ...]
    parameter_set: RateParameterSetV1 | None
    rate_decimal: str | int | Decimal | None
    rate_unit: str | None
    warnings: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evaluation_id",
            _nonempty(self.evaluation_id, "evaluation_id"),
        )
        object.__setattr__(self, "profile_id", _nonempty(self.profile_id, "profile_id"))
        object.__setattr__(
            self,
            "input_state_sha256",
            _sha256(self.input_state_sha256, "input_state_sha256"),
        )
        object.__setattr__(self, "zone_id", _nonempty(self.zone_id, "zone_id"))

        bindings = tuple(self.quantity_bindings)
        binding_ids = [item.requirement_id for item in bindings]
        if len(set(binding_ids)) != len(binding_ids):
            raise ValueError("RateEvaluationV1 quantity_bindings must be unique")
        if any(item.input_state_sha256 != self.input_state_sha256 for item in bindings):
            raise ValueError(
                "RateEvaluationV1 quantity_bindings must match input_state_sha256"
            )
        requirement_by_id = {
            item.requirement_id: item
            for item in self.definition.required_state_quantities
        }
        for binding in bindings:
            requirement = requirement_by_id.get(binding.requirement_id)
            if requirement is None:
                raise ValueError(
                    f"unknown RateModel quantity binding: {binding.requirement_id!r}"
                )
            if (
                binding.variable_id != requirement.variable_id
                or binding.material_component_id != requirement.material_component_id
                or binding.unit != requirement.unit
            ):
                raise ValueError(
                    f"RateModel quantity binding does not match requirement "
                    f"{binding.requirement_id!r}"
                )
            if requirement.zone_required and binding.zone_id != self.zone_id:
                raise ValueError(
                    f"RateModel quantity binding zone mismatch for "
                    f"{binding.requirement_id!r}"
                )
            if not requirement.zone_required and binding.zone_id is not None:
                raise ValueError(
                    f"non-zone RateModel quantity binding unexpectedly has zone_id "
                    f"for {binding.requirement_id!r}"
                )
        object.__setattr__(
            self,
            "quantity_bindings",
            tuple(sorted(bindings, key=lambda item: item.requirement_id)),
        )

        for field_name in ("warnings", "uncertainties"):
            values = tuple(_nonempty(item, field_name) for item in getattr(self, field_name))
            object.__setattr__(self, field_name, values)

        if self.applicability.is_applicable:
            if not self.definition.has_complete_definition_support:
                raise ValueError(
                    "applicable RateEvaluationV1 requires reviewed kinetic_form and "
                    "applicability_domain support"
                )
            if set(binding_ids) != set(self.definition.required_quantity_ids):
                raise ValueError(
                    "applicable RateEvaluationV1 requires all state quantity bindings"
                )
            if self.parameter_set is None:
                raise ValueError(
                    "applicable RateEvaluationV1 requires RateParameterSetV1"
                )
            if self.parameter_set.parameter_ids != frozenset(
                self.definition.required_parameters
            ):
                raise ValueError(
                    "applicable RateEvaluationV1 parameter set does not exactly "
                    "cover required_parameters"
                )
            if not self.parameter_set.all_parameters_reviewed:
                raise ValueError(
                    "applicable RateEvaluationV1 requires reviewed support for "
                    "every numeric parameter"
                )
            if self.rate_decimal is None:
                raise ValueError("applicable RateEvaluationV1 requires a numeric rate")
            normalized_rate = normalize_decimal(self.rate_decimal)
            if Decimal(normalized_rate) < 0:
                raise ValueError("RateEvaluationV1 rate cannot be negative")
            object.__setattr__(self, "rate_decimal", normalized_rate)
            if self.rate_unit != self.definition.output_rate_unit:
                raise ValueError(
                    "RateEvaluationV1 rate_unit must equal definition output_rate_unit"
                )
        else:
            if self.rate_decimal is not None or self.rate_unit is not None:
                raise ValueError(
                    "non-applicable RateEvaluationV1 cannot carry a numerical rate"
                )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-rate-evaluation-v1",
            "evaluation_id": self.evaluation_id,
            "definition": self.definition.canonical_payload(),
            "definition_sha256": self.definition.canonical_sha256,
            "profile_id": self.profile_id,
            "input_state_sha256": self.input_state_sha256,
            "zone_id": self.zone_id,
            "applicability": self.applicability.canonical_payload(),
            "quantity_bindings": [
                item.canonical_payload() for item in self.quantity_bindings
            ],
            "parameter_set": (
                self.parameter_set.canonical_payload()
                if self.parameter_set is not None
                else None
            ),
            "parameter_set_sha256": (
                self.parameter_set.canonical_sha256
                if self.parameter_set is not None
                else None
            ),
            "rate": (
                {
                    "value": {"type": "decimal", "value": self.rate_decimal},
                    "unit": self.rate_unit,
                }
                if self.rate_decimal is not None
                else None
            ),
            "warnings": list(self.warnings),
            "uncertainties": list(self.uncertainties),
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())
