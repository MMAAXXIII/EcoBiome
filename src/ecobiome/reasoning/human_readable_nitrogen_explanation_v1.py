"""Human-readable projection for the reviewed G7A nitrogen vertical.

This module is presentation-only. It does not alter process evaluation,
scientific support, material balance, persistence, or the frozen vertical
artifact. It projects already-reviewed identities into explicit user-facing
language while preserving a separate technical provenance payload.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from ecobiome.knowledge_persistence.serialization import canonical_sha256
from ecobiome.simulation.g7a_alignment_instances_v2 import (
    G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION,
    G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION,
    HumanReviewedAlignmentV2SelectionV1,
)
from ecobiome.simulation.model_semantic_bridge_v1 import (
    G7A_NITROGEN_ASSIMILATION_BRIDGE_V1,
    G7A_NITROGEN_OXIDATION_BRIDGE_V1,
    ReviewedModelSemanticBridgeV1,
)

HUMAN_READABLE_NITROGEN_EXPLANATION_SCHEMA_VERSION = (
    "ecobiome-human-readable-nitrogen-explanation-v1"
)
_VERTICAL_SCHEMA = "ecobiome-nitrogen-vertical-demonstration-v1"


class HumanReadableNitrogenExplanationV1Error(ValueError):
    """Raised when the reviewed vertical cannot be projected safely."""


def _mapping(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise HumanReadableNitrogenExplanationV1Error(
            f"{field_name} must be an object"
        )
    return cast(dict[str, object], value)


def _sequence(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise HumanReadableNitrogenExplanationV1Error(
            f"{field_name} must be an array"
        )
    return value


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HumanReadableNitrogenExplanationV1Error(
            f"{field_name} must be non-empty text"
        )
    return value.strip()


def _canonical_decimal(value: object, field_name: str) -> str:
    payload = _mapping(value, field_name)
    if payload.get("type") != "decimal":
        raise HumanReadableNitrogenExplanationV1Error(
            f"{field_name} must be a canonical decimal"
        )
    return _text(payload.get("value"), f"{field_name}.value")


@dataclass(frozen=True, slots=True)
class HumanReadableNitrogenProcessV1:
    key: str
    title: str
    source_label: str
    target_label: str
    source_before: str
    source_after: str
    target_before: str
    target_after: str
    unit: str
    explicit_extent_value: str
    explicit_extent_unit: str
    what_happens: str
    scientific_basis: str
    scenario_boundary: str
    evaluation_id: str
    assertion_id: str
    assertion_sha256: str
    bridge_id: str
    bridge_sha256: str
    selection_id: str
    selection_sha256: str
    receipt_id: str
    support_sha256: str

    def __post_init__(self) -> None:
        for field_name in (
            "key",
            "title",
            "source_label",
            "target_label",
            "source_before",
            "source_after",
            "target_before",
            "target_after",
            "unit",
            "explicit_extent_value",
            "explicit_extent_unit",
            "what_happens",
            "scientific_basis",
            "scenario_boundary",
            "evaluation_id",
            "assertion_id",
            "assertion_sha256",
            "bridge_id",
            "bridge_sha256",
            "selection_id",
            "selection_sha256",
            "receipt_id",
            "support_sha256",
        ):
            if not str(getattr(self, field_name)).strip():
                raise HumanReadableNitrogenExplanationV1Error(
                    f"{field_name} must be non-empty"
                )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "key": self.key,
            "title": self.title,
            "model_view": {
                "source": {
                    "label": self.source_label,
                    "before": self.source_before,
                    "after": self.source_after,
                    "unit": self.unit,
                },
                "target": {
                    "label": self.target_label,
                    "before": self.target_before,
                    "after": self.target_after,
                    "unit": self.unit,
                },
            },
            "explicit_extent": {
                "value": self.explicit_extent_value,
                "unit": self.explicit_extent_unit,
                "is_scenario_input": True,
            },
            "explanation": {
                "what_happens": self.what_happens,
                "scientific_basis": self.scientific_basis,
                "scenario_boundary": self.scenario_boundary,
            },
            "technical_provenance": {
                "evaluation_id": self.evaluation_id,
                "assertion_id": self.assertion_id,
                "assertion_sha256": self.assertion_sha256,
                "bridge_id": self.bridge_id,
                "bridge_sha256": self.bridge_sha256,
                "selection_id": self.selection_id,
                "selection_sha256": self.selection_sha256,
                "receipt_id": self.receipt_id,
                "support_sha256": self.support_sha256,
            },
        }


@dataclass(frozen=True, slots=True)
class HumanReadableNitrogenExplanationV1:
    title: str
    introduction: str
    abstraction_note: str
    model_limit: str
    processes: tuple[
        HumanReadableNitrogenProcessV1,
        HumanReadableNitrogenProcessV1,
    ]

    def __post_init__(self) -> None:
        if tuple(item.key for item in self.processes) != (
            "oxidation",
            "assimilation",
        ):
            raise HumanReadableNitrogenExplanationV1Error(
                "human-readable nitrogen projection requires oxidation then assimilation"
            )
        for field_name in (
            "title",
            "introduction",
            "abstraction_note",
            "model_limit",
        ):
            if not str(getattr(self, field_name)).strip():
                raise HumanReadableNitrogenExplanationV1Error(
                    f"{field_name} must be non-empty"
                )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": HUMAN_READABLE_NITROGEN_EXPLANATION_SCHEMA_VERSION,
            "title": self.title,
            "introduction": self.introduction,
            "abstraction_note": self.abstraction_note,
            "model_limit": self.model_limit,
            "processes": [item.canonical_payload() for item in self.processes],
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_sha256(self.canonical_payload())


@dataclass(frozen=True, slots=True)
class _ProcessPresentationSpec:
    key: str
    title: str
    source_label: str
    target_label: str
    bridge: ReviewedModelSemanticBridgeV1
    selection: HumanReviewedAlignmentV2SelectionV1
    receipt_id: str
    scientific_basis: str


_OXIDATION_SPEC = _ProcessPresentationSpec(
    key="oxidation",
    title="Oxydation de l'azote réduit",
    source_label="Azote inorganique réduit",
    target_label="Azote inorganique oxydé",
    bridge=G7A_NITROGEN_OXIDATION_BRIDGE_V1,
    selection=G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION,
    receipt_id="receipt-g7a-mech5b-oxidation-v1",
    scientific_basis=(
        "Le support scientifique revu décrit une oxydation de l'ammonium vers "
        "le nitrate. Pour ce mécanisme seulement, EcoBiome projette l'ammonium "
        "vers « azote inorganique réduit » et le nitrate vers "
        "« azote inorganique oxydé »."
    ),
)

_ASSIMILATION_SPEC = _ProcessPresentationSpec(
    key="assimilation",
    title="Assimilation biologique de l'azote",
    source_label="Azote inorganique dissous",
    target_label="Azote biologique",
    bridge=G7A_NITROGEN_ASSIMILATION_BRIDGE_V1,
    selection=G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION,
    receipt_id="receipt-g7a-mech5b-assimilation-v1",
    scientific_basis=(
        "Le support scientifique revu décrit l'assimilation de l'ammonium vers "
        "de la L-glutamine biologique. Pour ce mécanisme seulement, EcoBiome "
        "projette l'ammonium vers « azote inorganique dissous » et l'azote de "
        "la L-glutamine incorporée vers « azote biologique »."
    ),
)

_SPECS = (_OXIDATION_SPEC, _ASSIMILATION_SPEC)


def _delta_values(
    evaluation: dict[str, object],
    component_id: str,
) -> tuple[str, str, str]:
    deltas = _sequence(evaluation.get("deltas"), "evaluation.deltas")
    matches: list[dict[str, object]] = []
    for raw in deltas:
        delta = _mapping(raw, "evaluation.delta")
        if delta.get("material_component_id") == component_id:
            matches.append(delta)
    if len(matches) != 1:
        raise HumanReadableNitrogenExplanationV1Error(
            f"expected one delta for {component_id!r}"
        )
    delta = matches[0]
    before = _canonical_decimal(delta.get("before"), "delta.before")
    after = _canonical_decimal(delta.get("after"), "delta.after")
    unit = _text(delta.get("unit"), "delta.unit")
    return before, after, unit


def _validate_common_ammonium_scope() -> None:
    oxidation_source = tuple(
        binding.entity_id
        for binding in G7A_NITROGEN_OXIDATION_BRIDGE_V1.participant_bindings
        if binding.model_component_id
        == G7A_NITROGEN_OXIDATION_BRIDGE_V1.source_component_id
    )
    assimilation_source = tuple(
        binding.entity_id
        for binding in G7A_NITROGEN_ASSIMILATION_BRIDGE_V1.participant_bindings
        if binding.model_component_id
        == G7A_NITROGEN_ASSIMILATION_BRIDGE_V1.source_component_id
    )
    if oxidation_source != ("entity-pubchem-cid-223",):
        raise HumanReadableNitrogenExplanationV1Error(
            "oxidation source bridge identity drift"
        )
    if assimilation_source != oxidation_source:
        raise HumanReadableNitrogenExplanationV1Error(
            "process-scoped ammonium bridge identity drift"
        )


def _project_process(
    raw_step: object,
    spec: _ProcessPresentationSpec,
) -> HumanReadableNitrogenProcessV1:
    step = _mapping(raw_step, "process_step")
    bridge = spec.bridge
    selection = spec.selection

    if step.get("source_component_id") != bridge.source_component_id:
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} source component drift"
        )
    if step.get("target_component_id") != bridge.target_component_id:
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} target component drift"
        )

    explicit_extent = _mapping(
        step.get("explicit_extent"),
        f"{spec.key}.explicit_extent",
    )
    if explicit_extent.get("is_explicit_input") is not True:
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} extent must remain an explicit input"
        )
    extent_value = _text(
        explicit_extent.get("value"),
        f"{spec.key}.explicit_extent.value",
    )
    extent_unit = _text(
        explicit_extent.get("unit"),
        f"{spec.key}.explicit_extent.unit",
    )

    evaluation = _mapping(step.get("evaluation"), f"{spec.key}.evaluation")
    if evaluation.get("support_status") != "scientific_alignment_reviewed":
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} evaluation is not scientifically reviewed"
        )
    definition = _mapping(
        evaluation.get("definition"),
        f"{spec.key}.evaluation.definition",
    )
    if definition.get("process_id") != bridge.process_id:
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} process identity drift"
        )
    evaluation_id = _text(
        evaluation.get("evaluation_id"),
        f"{spec.key}.evaluation_id",
    )

    source_before, source_after, source_unit = _delta_values(
        evaluation,
        bridge.source_component_id,
    )
    target_before, target_after, target_unit = _delta_values(
        evaluation,
        bridge.target_component_id,
    )
    if source_unit != target_unit:
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} delta units differ"
        )

    assertion_refs = _sequence(
        step.get("scientific_assertion_refs"),
        f"{spec.key}.scientific_assertion_refs",
    )
    if len(assertion_refs) != 1:
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} requires exactly one scientific assertion"
        )
    assertion_ref = _mapping(
        assertion_refs[0],
        f"{spec.key}.scientific_assertion_ref",
    )
    expected_assertion = bridge.assertion_ref
    if (
        assertion_ref.get("assertion_id") != expected_assertion.assertion_id
        or assertion_ref.get("assertion_revision")
        != expected_assertion.assertion_revision
        or assertion_ref.get("canonical_payload_sha256")
        != expected_assertion.canonical_payload_sha256
    ):
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} assertion identity drift"
        )

    receipts = _sequence(
        step.get("reviewed_attachment_receipts"),
        f"{spec.key}.reviewed_attachment_receipts",
    )
    if len(receipts) != 1:
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} requires exactly one reviewed attachment receipt"
        )
    receipt = _mapping(receipts[0], f"{spec.key}.receipt")
    if receipt.get("receipt_id") != spec.receipt_id:
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} receipt identity drift"
        )

    binding = _mapping(
        receipt.get("scientific_binding"),
        f"{spec.key}.scientific_binding",
    )
    if binding.get("bridge_id") != bridge.bridge_id:
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} bridge id drift"
        )
    if binding.get("bridge_sha256") != bridge.canonical_sha256:
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} bridge SHA drift"
        )
    support_sha256 = _text(
        binding.get("support_sha256"),
        f"{spec.key}.support_sha256",
    )

    human_selection = _mapping(
        receipt.get("human_reviewed_selection"),
        f"{spec.key}.human_reviewed_selection",
    )
    if human_selection.get("canonical_sha256") != selection.canonical_sha256:
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} selection SHA drift"
        )
    selection_payload = _mapping(
        human_selection.get("payload"),
        f"{spec.key}.selection_payload",
    )
    if selection_payload.get("selection_id") != selection.selection_id:
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} selection id drift"
        )
    if (
        selection_payload.get("decision") != "accept"
        or selection_payload.get("review_status") != "reviewed_confirmed"
        or selection_payload.get("reviewed_by") != "human"
        or selection_payload.get("automatic_attachment") is not False
    ):
        raise HumanReadableNitrogenExplanationV1Error(
            f"{spec.key} human review state drift"
        )

    what_happens = (
        f"Dans ce scénario, {extent_value} {extent_unit} est transféré de "
        f"« {spec.source_label} » vers « {spec.target_label} ». "
        f"La source passe de {source_before} à {source_after} {source_unit}, "
        f"et la cible de {target_before} à {target_after} {target_unit}."
    )
    scenario_boundary = (
        f"La quantité de {extent_value} {extent_unit} est imposée par le "
        "scénario. Le support scientifique revu justifie ici le mécanisme et "
        "sa direction, mais EcoBiome ne calcule pas encore sa vitesse ni la "
        "quantité transformée pendant un intervalle de temps."
    )

    return HumanReadableNitrogenProcessV1(
        key=spec.key,
        title=spec.title,
        source_label=spec.source_label,
        target_label=spec.target_label,
        source_before=source_before,
        source_after=source_after,
        target_before=target_before,
        target_after=target_after,
        unit=source_unit,
        explicit_extent_value=extent_value,
        explicit_extent_unit=extent_unit,
        what_happens=what_happens,
        scientific_basis=spec.scientific_basis,
        scenario_boundary=scenario_boundary,
        evaluation_id=evaluation_id,
        assertion_id=expected_assertion.assertion_id,
        assertion_sha256=expected_assertion.canonical_payload_sha256,
        bridge_id=bridge.bridge_id,
        bridge_sha256=bridge.canonical_sha256,
        selection_id=selection.selection_id,
        selection_sha256=selection.canonical_sha256,
        receipt_id=spec.receipt_id,
        support_sha256=support_sha256,
    )


def build_human_readable_nitrogen_explanation_v1(
    artifact: dict[str, object],
) -> HumanReadableNitrogenExplanationV1:
    """Project the exact reviewed vertical into human-facing semantics."""
    if artifact.get("schema_version") != _VERTICAL_SCHEMA:
        raise HumanReadableNitrogenExplanationV1Error(
            "unsupported nitrogen vertical schema"
        )
    boundary = _mapping(artifact.get("model_boundary"), "model_boundary")
    if boundary != {
        "extent_is_explicit_input": True,
        "kinetic_or_rate_model_present": False,
        "dt_or_elapsed_time_prediction_present": False,
        "forecast_claim": False,
    }:
        raise HumanReadableNitrogenExplanationV1Error(
            "human-readable projection requires the frozen non-predictive boundary"
        )

    _validate_common_ammonium_scope()

    steps = _sequence(artifact.get("process_steps"), "process_steps")
    if len(steps) != 2:
        raise HumanReadableNitrogenExplanationV1Error(
            "reviewed nitrogen vertical requires exactly two process steps"
        )

    projected = tuple(
        _project_process(raw_step, spec)
        for raw_step, spec in zip(steps, _SPECS, strict=True)
    )
    return HumanReadableNitrogenExplanationV1(
        title="Pourquoi l'azote se transforme-t-il ?",
        introduction=(
            "EcoBiome distingue ici deux mécanismes revus : une oxydation et "
            "une assimilation biologique. Les transferts de matière sont "
            "déterministes, mais leurs quantités sont encore imposées par le scénario."
        ),
        abstraction_note=(
            "Les catégories affichées sont des vues de modèle propres à chaque "
            "mécanisme. Une même forme chimique — ici l'ammonium — peut être "
            "représentée dans une catégorie différente selon le processus. "
            "Les quatre valeurs ne doivent donc pas être additionnées comme "
            "quatre stocks physiques indépendants."
        ),
        model_limit=(
            "Cette verticale n'est pas prédictive : aucun RateModel, aucune "
            "vitesse et aucun Δt ne calculent encore l'extent. La prochaine "
            "étape scientifique pourra traiter ce manque séparément."
        ),
        processes=cast(
            tuple[
                HumanReadableNitrogenProcessV1,
                HumanReadableNitrogenProcessV1,
            ],
            projected,
        ),
    )
