"""Reproducible nitrogen vertical demonstration built from reviewed explanation provenance."""
from __future__ import annotations

import re
from dataclasses import dataclass

from ecobiome.knowledge_persistence.serialization import canonical_sha256
from ecobiome.reasoning.auditable_ecosystem_explanation_v1 import (
    AuditableEcosystemExplanationV1,
)
from ecobiome.simulation.ecosystem_state_v1 import EcosystemStateV1
from ecobiome.simulation.process_v1 import ProcessEvaluationV1

NITROGEN_VERTICAL_DEMONSTRATION_SCHEMA_VERSION = (
    "ecobiome-nitrogen-vertical-demonstration-v1"
)
_PROCESS_ID = "nitrogen_transformation_extent_v1"
_REQUIRED_TRANSFORMATIONS = (
    ("reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen"),
    ("dissolved_inorganic_nitrogen", "biological_nitrogen"),
)
_FORBIDDEN_PARAMETER_KEYS = frozenset(
    {
        "rate",
        "rate_model",
        "kinetics",
        "kinetic_model",
        "dt",
        "delta_t",
        "duration",
        "time_step",
    }
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class NitrogenVerticalDemonstrationV1Error(ValueError):
    """Raised when the vertical demonstration is not self-consistent."""


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise NitrogenVerticalDemonstrationV1Error(
            f"{field_name} must be non-empty"
        )
    return normalized


def _sha256(value: str, field_name: str) -> str:
    digest = value.strip()
    if not _SHA256_RE.fullmatch(digest):
        raise NitrogenVerticalDemonstrationV1Error(
            f"{field_name} must be lowercase SHA-256"
        )
    return digest


def _forbidden_parameter_paths(
    value: object,
    *,
    path: str = "$",
) -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            child_path = f"{path}/{key_text}"
            if key_text.strip().lower() in _FORBIDDEN_PARAMETER_KEYS:
                found.append(child_path)
            found.extend(
                _forbidden_parameter_paths(
                    nested,
                    path=child_path,
                )
            )
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            found.extend(
                _forbidden_parameter_paths(
                    nested,
                    path=f"{path}/{index}",
                )
            )
    return tuple(found)


def _explicit_extent_summary(
    evaluation: ProcessEvaluationV1,
) -> dict[str, object]:
    params = evaluation.parameters_payload
    extent = params.get("extent")
    extent_base = params.get("extent_base")
    extent_basis = params.get("extent_basis")
    if not isinstance(extent, dict):
        raise NitrogenVerticalDemonstrationV1Error(
            "nitrogen evaluation requires explicit extent object"
        )
    if not isinstance(extent_base, dict):
        raise NitrogenVerticalDemonstrationV1Error(
            "nitrogen evaluation requires explicit base extent object"
        )
    if not isinstance(extent_basis, dict):
        raise NitrogenVerticalDemonstrationV1Error(
            "nitrogen evaluation requires explicit extent basis"
        )

    value = extent.get("value")
    base_value = extent_base.get("value")
    if not isinstance(value, dict) or value.get("type") != "decimal":
        raise NitrogenVerticalDemonstrationV1Error(
            "explicit extent value must be canonical decimal"
        )
    if not isinstance(base_value, dict) or base_value.get("type") != "decimal":
        raise NitrogenVerticalDemonstrationV1Error(
            "explicit base extent value must be canonical decimal"
        )
    value_text = value.get("value")
    base_value_text = base_value.get("value")
    unit = extent.get("unit")
    base_unit = extent_base.get("unit")
    basis_kind = extent_basis.get("kind")
    basis_reference_id = extent_basis.get("reference_id")
    if not isinstance(value_text, str) or not value_text:
        raise NitrogenVerticalDemonstrationV1Error(
            "explicit extent decimal value is missing"
        )
    if not isinstance(base_value_text, str) or not base_value_text:
        raise NitrogenVerticalDemonstrationV1Error(
            "explicit base extent decimal value is missing"
        )
    if not isinstance(unit, str) or not unit.strip():
        raise NitrogenVerticalDemonstrationV1Error(
            "explicit extent unit is missing"
        )
    if base_unit != "mg N":
        raise NitrogenVerticalDemonstrationV1Error(
            "nitrogen vertical demonstration requires mg N base extent"
        )
    if not isinstance(basis_kind, str) or not basis_kind.strip():
        raise NitrogenVerticalDemonstrationV1Error(
            "explicit extent basis kind is missing"
        )
    if basis_kind == "derived":
        raise NitrogenVerticalDemonstrationV1Error(
            "vertical demonstration extent must be an explicit input, not derived"
        )
    if not isinstance(basis_reference_id, str) or not basis_reference_id.strip():
        raise NitrogenVerticalDemonstrationV1Error(
            "explicit extent basis reference is missing"
        )
    return {
        "value": value_text,
        "unit": unit.strip(),
        "base_value": base_value_text,
        "base_unit": "mg N",
        "basis_kind": basis_kind.strip(),
        "basis_reference_id": basis_reference_id.strip(),
        "is_explicit_input": True,
    }


@dataclass(frozen=True, slots=True)
class ScientificFoundationSnapshotRefV1:
    schema_version: int
    design_sha256: str
    database_sha256: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.schema_version, bool)
            or not isinstance(self.schema_version, int)
            or self.schema_version < 1
        ):
            raise NitrogenVerticalDemonstrationV1Error(
                "Scientific Foundation schema_version must be integer >= 1"
            )
        object.__setattr__(
            self,
            "design_sha256",
            _sha256(self.design_sha256, "design_sha256"),
        )
        object.__setattr__(
            self,
            "database_sha256",
            _sha256(self.database_sha256, "database_sha256"),
        )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "design_sha256": self.design_sha256,
            "database_sha256": self.database_sha256,
        }


@dataclass(frozen=True, slots=True)
class NitrogenVerticalDemonstrationV1:
    """One specific, reproducible, non-kinetic nitrogen explanation scenario."""

    demo_id: str
    starting_state: EcosystemStateV1
    intermediate_state: EcosystemStateV1
    ending_state: EcosystemStateV1
    evaluations: tuple[ProcessEvaluationV1, ProcessEvaluationV1]
    auditable_explanation: AuditableEcosystemExplanationV1
    scientific_foundation_snapshot: ScientificFoundationSnapshotRefV1

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "demo_id",
            _nonempty(self.demo_id, "demo_id"),
        )
        if not isinstance(
            self.scientific_foundation_snapshot,
            ScientificFoundationSnapshotRefV1,
        ):
            raise TypeError(
                "scientific_foundation_snapshot must be "
                "ScientificFoundationSnapshotRefV1"
            )
        profiles = {
            self.starting_state.profile_id,
            self.intermediate_state.profile_id,
            self.ending_state.profile_id,
        }
        if len(profiles) != 1:
            raise NitrogenVerticalDemonstrationV1Error(
                "all demonstration states must share one profile"
            )

        evaluations = tuple(self.evaluations)
        if len(evaluations) != 2:
            raise NitrogenVerticalDemonstrationV1Error(
                "nitrogen vertical demonstration requires exactly two evaluations"
            )

        state_links = (
            (
                self.starting_state.canonical_sha256,
                self.intermediate_state.canonical_sha256,
            ),
            (
                self.intermediate_state.canonical_sha256,
                self.ending_state.canonical_sha256,
            ),
        )
        for index, (evaluation, expected_pair, state_link) in enumerate(
            zip(
                evaluations,
                _REQUIRED_TRANSFORMATIONS,
                state_links,
                strict=True,
            ),
            start=1,
        ):
            if evaluation.definition.process_id != _PROCESS_ID:
                raise NitrogenVerticalDemonstrationV1Error(
                    f"step {index} must use {_PROCESS_ID}"
                )
            if evaluation.support_status != "scientific_alignment_reviewed":
                raise NitrogenVerticalDemonstrationV1Error(
                    f"step {index} must be scientific_alignment_reviewed"
                )
            if (
                evaluation.input_state_sha256,
                evaluation.output_state_sha256,
            ) != state_link:
                raise NitrogenVerticalDemonstrationV1Error(
                    f"step {index} state identities are not contiguous"
                )
            forbidden = _forbidden_parameter_paths(
                evaluation.parameters_payload
            )
            if forbidden:
                raise NitrogenVerticalDemonstrationV1Error(
                    "rate/dt/kinetic parameters are forbidden in V1: "
                    + repr(forbidden)
                )
            source = evaluation.parameters_payload.get(
                "source_component_id"
            )
            target = evaluation.parameters_payload.get(
                "target_component_id"
            )
            if (source, target) != expected_pair:
                raise NitrogenVerticalDemonstrationV1Error(
                    f"step {index} transformation is outside the frozen vertical scope"
                )
            _explicit_extent_summary(evaluation)

        trace = self.auditable_explanation.explanation_trace
        if trace.starting_state_sha256 != self.starting_state.canonical_sha256:
            raise NitrogenVerticalDemonstrationV1Error(
                "auditable explanation starting state does not match demonstration"
            )
        if trace.ending_state_sha256 != self.ending_state.canonical_sha256:
            raise NitrogenVerticalDemonstrationV1Error(
                "auditable explanation ending state does not match demonstration"
            )
        expected_evaluation_ids = tuple(
            item.evaluation_id for item in evaluations
        )
        if trace.process_evaluation_refs != expected_evaluation_ids:
            raise NitrogenVerticalDemonstrationV1Error(
                "auditable explanation process order does not match demonstration"
            )
        identities = self.auditable_explanation.process_evaluation_identities
        if tuple(item.evaluation_id for item in identities) != expected_evaluation_ids:
            raise NitrogenVerticalDemonstrationV1Error(
                "auditable evaluation identities do not match demonstration"
            )
        if tuple(item.canonical_sha256 for item in identities) != tuple(
            item.canonical_sha256 for item in evaluations
        ):
            raise NitrogenVerticalDemonstrationV1Error(
                "auditable evaluation SHA identities do not match demonstration"
            )
        if len(trace.scientific_assertion_refs) != 2:
            raise NitrogenVerticalDemonstrationV1Error(
                "vertical demonstration requires exactly two ScientificAssertions"
            )
        if len(trace.scientific_supports) != 2:
            raise NitrogenVerticalDemonstrationV1Error(
                "vertical demonstration requires exactly two scientific supports"
            )
        if len(
            self.auditable_explanation.reviewed_support_attachment_receipts
        ) != 2:
            raise NitrogenVerticalDemonstrationV1Error(
                "vertical demonstration requires exactly two reviewed receipts"
            )
        if any(
            step.support_status != "scientific_alignment_reviewed"
            for step in trace.causal_steps
        ):
            raise NitrogenVerticalDemonstrationV1Error(
                "every vertical causal step must be scientifically reviewed"
            )
        object.__setattr__(self, "evaluations", evaluations)

    @property
    def model_limitations(self) -> tuple[str, ...]:
        return (
            "process extents are explicit scenario inputs",
            "no kinetic or rate model computes process extent",
            "no dt or elapsed-time prediction is performed",
            (
                "the artifact demonstrates deterministic mass transfer and reviewed "
                "mechanism provenance, not a forecast"
            ),
        )

    def canonical_payload(self) -> dict[str, object]:
        receipts_by_evaluation: dict[str, list[dict[str, object]]] = {}
        for receipt in (
            self.auditable_explanation.reviewed_support_attachment_receipts
        ):
            receipts_by_evaluation.setdefault(
                receipt.evaluation_id,
                [],
            ).append(receipt.canonical_payload())

        steps: list[dict[str, object]] = []
        for index, evaluation in enumerate(self.evaluations, start=1):
            params = evaluation.parameters_payload
            steps.append(
                {
                    "ordinal": index,
                    "evaluation_id": evaluation.evaluation_id,
                    "evaluation_sha256": evaluation.canonical_sha256,
                    "source_component_id": params["source_component_id"],
                    "target_component_id": params["target_component_id"],
                    "explicit_extent": _explicit_extent_summary(evaluation),
                    "scientific_assertion_refs": [
                        item.canonical_payload()
                        for item in evaluation.scientific_assertion_refs
                    ],
                    "scientific_supports": [
                        item.canonical_payload()
                        for item in evaluation.scientific_supports
                    ],
                    "reviewed_attachment_receipts": receipts_by_evaluation.get(
                        evaluation.evaluation_id,
                        [],
                    ),
                    "evaluation": evaluation.canonical_payload(),
                }
            )

        return {
            "schema_version": NITROGEN_VERTICAL_DEMONSTRATION_SCHEMA_VERSION,
            "demo_id": self.demo_id,
            "profile_id": self.starting_state.profile_id,
            "scientific_foundation_snapshot": (
                self.scientific_foundation_snapshot.canonical_payload()
            ),
            "starting_state": {
                "sha256": self.starting_state.canonical_sha256,
                "state": self.starting_state.canonical_payload(),
            },
            "intermediate_state": {
                "sha256": self.intermediate_state.canonical_sha256,
                "state": self.intermediate_state.canonical_payload(),
            },
            "ending_state": {
                "sha256": self.ending_state.canonical_sha256,
                "state": self.ending_state.canonical_payload(),
            },
            "process_steps": steps,
            "auditable_explanation": {
                "sha256": self.auditable_explanation.canonical_sha256,
                "core_trace_sha256": (
                    self.auditable_explanation.explanation_trace.canonical_sha256
                ),
                "payload": self.auditable_explanation.canonical_payload(),
            },
            "model_boundary": {
                "extent_is_explicit_input": True,
                "kinetic_or_rate_model_present": False,
                "dt_or_elapsed_time_prediction_present": False,
                "forecast_claim": False,
            },
            "limitations": list(self.model_limitations),
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_sha256(self.canonical_payload())

    def _state_markdown_rows(self, state: EcosystemStateV1) -> list[str]:
        rows: list[str] = []
        for quantity in sorted(
            state.quantities,
            key=lambda item: (
                item.material_component_id or "",
                item.variable_id,
            ),
        ):
            if quantity.material_component_id is None:
                continue
            rows.append(
                "| "
                f"{quantity.material_component_id} | "
                f"{quantity.value_decimal} | {quantity.unit} |"
            )
        return rows

    def render_markdown(self) -> str:
        lines = [
            "# EcoBiome - Demonstration verticale azote V1",
            "",
            "**Statut : scenario deterministe explicable; pas une prediction cinetique.**",
            "",
            f"- Demo ID: `{self.demo_id}`",
            f"- Artifact SHA-256: `{self.canonical_sha256}`",
            (
                "- Scientific Foundation V6 SHA-256: "
                f"`{self.scientific_foundation_snapshot.database_sha256}`"
            ),
            (
                "- Auditable explanation SHA-256: "
                f"`{self.auditable_explanation.canonical_sha256}`"
            ),
            "",
            "## Etat initial",
            "",
            "| Compartiment N | Valeur | Unite |",
            "| --- | ---: | --- |",
            *self._state_markdown_rows(self.starting_state),
            "",
            "## Transformations explicites",
            "",
        ]
        for index, evaluation in enumerate(self.evaluations, start=1):
            params = evaluation.parameters_payload
            extent = _explicit_extent_summary(evaluation)
            lines.extend(
                [
                    (
                        f"{index}. `{params['source_component_id']}` -> "
                        f"`{params['target_component_id']}` : "
                        f"**{extent['value']} {extent['unit']}** "
                        f"(entree explicite, base `{extent['basis_kind']}`)."
                    ),
                    (
                        "   Support: `scientific_alignment_reviewed`; "
                        f"evaluation `{evaluation.evaluation_id}`."
                    ),
                ]
            )
        lines.extend(
            [
                "",
                "## Etat final",
                "",
                "| Compartiment N | Valeur | Unite |",
                "| --- | ---: | --- |",
                *self._state_markdown_rows(self.ending_state),
                "",
                "## Pourquoi ?",
                "",
                self.auditable_explanation.render_text(),
                "",
                "## Limites du modele V1",
                "",
            ]
        )
        lines.extend(f"- {item}." for item in self.model_limitations)
        lines.extend(
            [
                "",
                (
                    "Aucune vitesse, duree, constante cinetique ou prediction de "
                    "l'extent n'est calculee dans cette demonstration."
                ),
            ]
        )
        return "\n".join(lines)


def build_nitrogen_vertical_demonstration_v1(
    *,
    demo_id: str,
    starting_state: EcosystemStateV1,
    intermediate_state: EcosystemStateV1,
    ending_state: EcosystemStateV1,
    evaluations: tuple[ProcessEvaluationV1, ProcessEvaluationV1],
    auditable_explanation: AuditableEcosystemExplanationV1,
    scientific_foundation_snapshot: ScientificFoundationSnapshotRefV1,
) -> NitrogenVerticalDemonstrationV1:
    """Build the first vertical artifact without adding kinetic semantics."""
    return NitrogenVerticalDemonstrationV1(
        demo_id=demo_id,
        starting_state=starting_state,
        intermediate_state=intermediate_state,
        ending_state=ending_state,
        evaluations=evaluations,
        auditable_explanation=auditable_explanation,
        scientific_foundation_snapshot=scientific_foundation_snapshot,
    )
