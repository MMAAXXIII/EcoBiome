"""N3-aware deterministic ecosystem explanation traces for N4."""
from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import pairwise

from ecobiome.knowledge_persistence.serialization import (
    canonical_sha256 as canonical_payload_sha256,
)
from ecobiome.simulation.ecosystem_state_v1 import EcosystemStateV1
from ecobiome.simulation.process_v1 import (
    ProcessDeltaV1,
    ProcessEvaluationV1,
    ProcessScientificSupportV1,
    ScientificAssertionRefV1,
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_BASIS_KINDS = frozenset(
    {
        "observation",
        "scientific_assertion",
        "user_assumption",
        "scenario_default",
        "derived",
    }
)
_SUPPORT_STATUSES = frozenset(
    {
        "deterministic_identity",
        "scenario_hypothesis",
        "scientific_alignment_reviewed",
        "support_missing",
    }
)


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _ordered_refs(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    normalized = tuple(_nonempty(item, field_name) for item in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicate references")
    return normalized


def _canonical_refs(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    normalized = tuple(item.strip() for item in values)
    if any(not item for item in normalized):
        raise ValueError(f"{field_name} must contain only non-empty references")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicate references")
    return tuple(sorted(normalized))


def _scientific_support_key(
    support: ProcessScientificSupportV1,
) -> str:
    return canonical_payload_sha256(support.canonical_payload())


def _evaluation_intervention_ref(
    evaluation: ProcessEvaluationV1,
) -> str | None:
    intervention = evaluation.parameters_payload.get("intervention")
    if intervention is None:
        return None
    if not isinstance(intervention, dict):
        raise TypeError("process intervention parameter must be an object")
    intervention_id = intervention.get("id")
    if not isinstance(intervention_id, str) or not intervention_id.strip():
        raise ValueError("process intervention parameter requires a non-empty id")
    digest = evaluation.parameters_payload.get("intervention_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("process intervention parameter requires a SHA-256 identity")
    if digest != canonical_payload_sha256(intervention):
        raise ValueError("process intervention SHA-256 does not match its payload")
    return intervention_id.strip()


@dataclass(frozen=True, slots=True)
class CausalStepV1:
    process_evaluation_id: str
    process_id: str
    delta: ProcessDeltaV1
    epistemic_basis_kinds: tuple[str, ...]
    support_status: str
    scientific_assertion_refs: tuple[ScientificAssertionRefV1, ...]
    assumptions: tuple[str, ...]
    unknowns: tuple[str, ...]
    scientific_supports: tuple[ProcessScientificSupportV1, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "process_evaluation_id",
            _nonempty(self.process_evaluation_id, "process_evaluation_id"),
        )
        object.__setattr__(self, "process_id", _nonempty(self.process_id, "process_id"))
        basis_kinds = tuple(sorted(set(self.epistemic_basis_kinds)))
        if any(item not in _BASIS_KINDS for item in basis_kinds):
            raise ValueError("unsupported causal-step epistemic basis kind")
        object.__setattr__(self, "epistemic_basis_kinds", basis_kinds)
        status = self.support_status.strip().lower()
        if status not in _SUPPORT_STATUSES:
            raise ValueError(f"unsupported causal-step support_status: {status!r}")
        object.__setattr__(self, "support_status", status)
        assertion_keys = [
            (
                item.assertion_id,
                item.assertion_revision,
                item.canonical_payload_sha256,
            )
            for item in self.scientific_assertion_refs
        ]
        if len(set(assertion_keys)) != len(assertion_keys):
            raise ValueError("causal-step ScientificAssertion refs must be unique")
        support_keys = [
            _scientific_support_key(item)
            for item in self.scientific_supports
        ]
        if len(set(support_keys)) != len(support_keys):
            raise ValueError("causal-step scientific supports must be unique")
        support_assertion_keys = {
            (
                item.assertion_ref.assertion_id,
                item.assertion_ref.assertion_revision,
                item.assertion_ref.canonical_payload_sha256,
            )
            for item in self.scientific_supports
        }
        if status == "scientific_alignment_reviewed":
            if not self.scientific_supports:
                raise ValueError(
                    "scientific_alignment_reviewed causal step requires supports"
                )
            if support_assertion_keys != set(assertion_keys):
                raise ValueError(
                    "causal-step scientific supports must exactly match "
                    "ScientificAssertion refs"
                )
        elif self.scientific_supports:
            raise ValueError(
                "causal-step scientific supports require "
                "scientific_alignment_reviewed"
            )
        for field_name in ("assumptions", "unknowns"):
            values = tuple(_nonempty(item, field_name) for item in getattr(self, field_name))
            if len(set(values)) != len(values):
                raise ValueError(f"{field_name} values must be unique")
            object.__setattr__(self, field_name, values)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "process_evaluation_id": self.process_evaluation_id,
            "process_id": self.process_id,
            "delta": self.delta.canonical_payload(),
            "epistemic_basis_kinds": list(self.epistemic_basis_kinds),
            "support_status": self.support_status,
            "scientific_assertion_refs": [
                item.canonical_payload()
                for item in sorted(
                    self.scientific_assertion_refs,
                    key=lambda item: (item.assertion_id, item.assertion_revision),
                )
            ],
            "scientific_supports": [
                item.canonical_payload()
                for item in sorted(
                    self.scientific_supports,
                    key=_scientific_support_key,
                )
            ],
            "assumptions": list(self.assumptions),
            "unknowns": list(self.unknowns),
        }


@dataclass(frozen=True, slots=True)
class EcosystemExplanationTraceV1:
    profile_id: str
    starting_state_sha256: str
    ending_state_sha256: str
    observation_refs: tuple[str, ...]
    intervention_refs: tuple[str, ...]
    process_evaluation_refs: tuple[str, ...]
    scientific_assertion_refs: tuple[ScientificAssertionRefV1, ...]
    causal_steps: tuple[CausalStepV1, ...]
    assumptions: tuple[str, ...]
    unknowns: tuple[str, ...]
    warnings: tuple[str, ...]
    scientific_supports: tuple[ProcessScientificSupportV1, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", _nonempty(self.profile_id, "profile_id"))
        for field_name in ("starting_state_sha256", "ending_state_sha256"):
            digest = getattr(self, field_name).strip()
            if not _SHA256_RE.fullmatch(digest):
                raise ValueError(f"{field_name} must be lowercase SHA-256")
            object.__setattr__(self, field_name, digest)
        object.__setattr__(
            self,
            "observation_refs",
            _canonical_refs(self.observation_refs, "observation_refs"),
        )
        object.__setattr__(
            self,
            "intervention_refs",
            _canonical_refs(self.intervention_refs, "intervention_refs"),
        )
        process_refs = _ordered_refs(
            self.process_evaluation_refs,
            "process_evaluation_refs",
        )
        if not process_refs:
            raise ValueError("ecosystem explanation requires process evaluation refs")
        object.__setattr__(self, "process_evaluation_refs", process_refs)
        if not self.causal_steps:
            raise ValueError("ecosystem explanation requires causal steps")

        step_process_order: list[str] = []
        seen_process_refs: set[str] = set()
        previous_ref: str | None = None
        for step in self.causal_steps:
            current_ref = step.process_evaluation_id
            if current_ref != previous_ref:
                if current_ref in seen_process_refs:
                    raise ValueError(
                        "causal steps cannot return to an earlier process evaluation"
                    )
                seen_process_refs.add(current_ref)
                step_process_order.append(current_ref)
                previous_ref = current_ref
        if tuple(step_process_order) != process_refs:
            raise ValueError(
                "process_evaluation_refs must exactly match causal-step evaluation order"
            )

        assertion_by_key = {
            (
                item.assertion_id,
                item.assertion_revision,
                item.canonical_payload_sha256,
            ): item
            for item in self.scientific_assertion_refs
        }
        if len(assertion_by_key) != len(self.scientific_assertion_refs):
            raise ValueError("ScientificAssertion refs must be unique")
        step_assertion_keys = {
            (
                item.assertion_id,
                item.assertion_revision,
                item.canonical_payload_sha256,
            )
            for step in self.causal_steps
            for item in step.scientific_assertion_refs
        }
        if set(assertion_by_key) != step_assertion_keys:
            raise ValueError(
                "trace ScientificAssertion refs must exactly match causal-step refs"
            )
        object.__setattr__(
            self,
            "scientific_assertion_refs",
            tuple(assertion_by_key[key] for key in sorted(assertion_by_key)),
        )
        support_by_key = {
            _scientific_support_key(item): item
            for item in self.scientific_supports
        }
        if len(support_by_key) != len(self.scientific_supports):
            raise ValueError("trace scientific supports must be unique")
        step_support_keys = {
            _scientific_support_key(item)
            for step in self.causal_steps
            for item in step.scientific_supports
        }
        if set(support_by_key) != step_support_keys:
            raise ValueError(
                "trace scientific supports must exactly match causal-step supports"
            )
        support_assertion_keys = {
            (
                item.assertion_ref.assertion_id,
                item.assertion_ref.assertion_revision,
                item.assertion_ref.canonical_payload_sha256,
            )
            for item in self.scientific_supports
        }
        if not support_assertion_keys.issubset(set(assertion_by_key)):
            raise ValueError(
                "trace scientific supports reference unbound ScientificAssertions"
            )
        object.__setattr__(
            self,
            "scientific_supports",
            tuple(
                support_by_key[key]
                for key in sorted(support_by_key)
            ),
        )
        for field_name in ("assumptions", "unknowns", "warnings"):
            values = tuple(_nonempty(item, field_name) for item in getattr(self, field_name))
            if len(set(values)) != len(values):
                raise ValueError(f"{field_name} values must be unique")
            object.__setattr__(self, field_name, values)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-ecosystem-explanation-trace-v1",
            "profile_id": self.profile_id,
            "starting_state_sha256": self.starting_state_sha256,
            "ending_state_sha256": self.ending_state_sha256,
            "observation_refs": list(self.observation_refs),
            "intervention_refs": list(self.intervention_refs),
            "process_evaluation_refs": list(self.process_evaluation_refs),
            "scientific_assertion_refs": [
                item.canonical_payload()
                for item in self.scientific_assertion_refs
            ],
            "scientific_supports": [
                item.canonical_payload()
                for item in self.scientific_supports
            ],
            "causal_steps": [item.canonical_payload() for item in self.causal_steps],
            "assumptions": list(self.assumptions),
            "unknowns": list(self.unknowns),
            "warnings": list(self.warnings),
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())

    def render_text(self) -> str:
        lines = ["Pourquoi cet état évolue-t-il ainsi ?", ""]
        for index, step in enumerate(self.causal_steps, start=1):
            delta = step.delta
            target = delta.material_component_id or delta.variable_id
            lines.append(
                f"{index}. {step.process_id}: {target} "
                f"{delta.before_decimal} {delta.unit} -> "
                f"{delta.after_decimal} {delta.unit} "
                f"(Δ {delta.change_decimal} {delta.unit})."
            )
            lines.append(
                "   Base épistémique: "
                + ", ".join(step.epistemic_basis_kinds)
                + f"; support: {step.support_status}."
            )
            if step.assumptions:
                lines.append("   Hypothèses: " + "; ".join(step.assumptions) + ".")
            if step.unknowns:
                lines.append("   Inconnues: " + "; ".join(step.unknowns) + ".")
        return "\n".join(lines)


def build_ecosystem_explanation_v1(
    starting_state: EcosystemStateV1,
    ending_state: EcosystemStateV1,
    evaluations: tuple[ProcessEvaluationV1, ...],
    *,
    observation_refs: tuple[str, ...] = (),
    intervention_refs: tuple[str, ...] = (),
) -> EcosystemExplanationTraceV1:
    """Build an auditable explanation from exact process evaluations."""
    if starting_state.profile_id != ending_state.profile_id:
        raise ValueError("explanation states must share one profile")
    if not evaluations:
        raise ValueError("explanation requires at least one process evaluation")
    if evaluations[0].input_state_sha256 != starting_state.canonical_sha256:
        raise ValueError("first process evaluation does not start from starting_state")
    for previous, current in pairwise(evaluations):
        if previous.output_state_sha256 != current.input_state_sha256:
            raise ValueError("process evaluations do not form a contiguous state chain")
    if evaluations[-1].output_state_sha256 != ending_state.canonical_sha256:
        raise ValueError("last process evaluation does not end at ending_state")

    causal_steps: list[CausalStepV1] = []
    assertion_by_key: dict[tuple[str, int, str], ScientificAssertionRefV1] = {}
    support_by_key: dict[str, ProcessScientificSupportV1] = {}
    assumptions: list[str] = []
    unknowns: list[str] = []
    warnings: list[str] = []
    basis_by_quantity_key = {
        item.key: (item.basis.kind, item.basis.reference_id)
        for item in starting_state.quantities
    }
    derived_observation_refs: set[str] = set()
    derived_intervention_refs: set[str] = set()

    for evaluation in evaluations:
        parameter_basis_kinds = {
            item.kind for item in evaluation.parameter_bases
        }
        derived_observation_refs.update(
            item.reference_id
            for item in evaluation.parameter_bases
            if item.kind == "observation"
        )
        intervention_ref = _evaluation_intervention_ref(evaluation)
        if intervention_ref is not None:
            derived_intervention_refs.add(intervention_ref)
        for assertion in evaluation.scientific_assertion_refs:
            assertion_by_key[
                (
                    assertion.assertion_id,
                    assertion.assertion_revision,
                    assertion.canonical_payload_sha256,
                )
            ] = assertion
        for support in evaluation.scientific_supports:
            support_by_key[_scientific_support_key(support)] = support
            for warning in support.warnings:
                if warning not in warnings:
                    warnings.append(warning)
            for uncertainty in support.uncertainties:
                if uncertainty not in unknowns:
                    unknowns.append(uncertainty)
        for value, target in (
            (evaluation.assumptions, assumptions),
            (evaluation.unknowns, unknowns),
            (evaluation.warnings, warnings),
        ):
            for item in value:
                if item not in target:
                    target.append(item)
        ordered_deltas = sorted(
            evaluation.deltas,
            key=lambda item: (
                item.variable_id,
                item.zone_id or "",
                item.material_component_id or "",
            ),
        )
        for delta in ordered_deltas:
            basis_kinds = set(parameter_basis_kinds)
            input_basis = basis_by_quantity_key.get(delta.key)
            if input_basis is not None:
                basis_kind, basis_reference = input_basis
                basis_kinds.add(basis_kind)
                if basis_kind == "observation":
                    derived_observation_refs.add(basis_reference)
            causal_steps.append(
                CausalStepV1(
                    process_evaluation_id=evaluation.evaluation_id,
                    process_id=evaluation.definition.process_id,
                    delta=delta,
                    epistemic_basis_kinds=tuple(sorted(basis_kinds)),
                    support_status=evaluation.support_status,
                    scientific_assertion_refs=evaluation.scientific_assertion_refs,
                    assumptions=evaluation.assumptions,
                    unknowns=evaluation.unknowns,
                    scientific_supports=evaluation.scientific_supports,
                )
            )
        for delta in ordered_deltas:
            basis_by_quantity_key[delta.key] = (
                "derived",
                evaluation.evaluation_id,
            )

    requested_observation_refs = _canonical_refs(
        observation_refs, "observation_refs"
    )
    expected_observation_refs = tuple(sorted(derived_observation_refs))
    if requested_observation_refs and (
        requested_observation_refs != expected_observation_refs
    ):
        raise ValueError(
            "observation_refs must exactly match observation bases used by the chain"
        )
    requested_intervention_refs = _canonical_refs(
        intervention_refs, "intervention_refs"
    )
    expected_intervention_refs = tuple(sorted(derived_intervention_refs))
    if requested_intervention_refs and (
        requested_intervention_refs != expected_intervention_refs
    ):
        raise ValueError(
            "intervention_refs must exactly match interventions bound to evaluations"
        )

    return EcosystemExplanationTraceV1(
        profile_id=starting_state.profile_id,
        starting_state_sha256=starting_state.canonical_sha256,
        ending_state_sha256=ending_state.canonical_sha256,
        observation_refs=(
            requested_observation_refs
            if requested_observation_refs
            else expected_observation_refs
        ),
        intervention_refs=(
            requested_intervention_refs
            if requested_intervention_refs
            else expected_intervention_refs
        ),
        process_evaluation_refs=tuple(item.evaluation_id for item in evaluations),
        scientific_assertion_refs=tuple(
            assertion_by_key[key] for key in sorted(assertion_by_key)
        ),
        causal_steps=tuple(causal_steps),
        scientific_supports=tuple(
            support_by_key[key] for key in sorted(support_by_key)
        ),
        assumptions=tuple(assumptions),
        unknowns=tuple(unknowns),
        warnings=tuple(warnings),
    )
