"""Additive V2 scientific process alignment bound to a reviewed model-semantic bridge."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace

from ecobiome.knowledge_persistence.contracts import (
    KnowledgeSynthesisRepository,
    ScientificAssertionRepository,
)
from ecobiome.knowledge_persistence.serialization import canonical_sha256
from ecobiome.simulation.model_semantic_bridge_v1 import (
    REVIEWED_MODEL_SEMANTIC_BRIDGE_DESIGN_SHA256,
    ReviewedModelSemanticBridgeV1,
    ReviewedModelSemanticBridgeV1Error,
)
from ecobiome.simulation.process_v1 import (
    ProcessEvaluationV1,
    ProcessScientificSupportV1,
    ScientificAssertionRefV1,
)
from ecobiome.simulation.scientific_alignment_v1 import (
    ProcessScientificAlignmentPolicyV1,
    ScientificProcessAlignmentV1Error,
    align_scientific_assertion_to_process_v1,
)

ALIGNMENT_V2_CONTRACT_DESCRIPTOR = {
    "schema_version": "ecobiome-process-scientific-alignment-policy-v2-contract",
    "preserves_v1": True,
    "requires_exact_assertion_ref": True,
    "requires_exact_reviewed_model_semantic_bridge_sha": True,
    "requires_exact_evaluation_scope_sha": True,
    "requires_exact_predicate": True,
    "requires_exact_participant_role_entity_revision": True,
    "requires_exact_qualifiers": True,
    "alignment_class": "direct_mechanism_support",
    "epistemic_class": "explicit_causal_result",
    "fail_closed_on": [
        "missing_bridge",
        "bridge_sha_mismatch",
        "assertion_ref_mismatch",
        "role_entity_revision_mismatch",
        "source_target_component_mismatch",
        "evaluation_scope_mismatch",
        "qualifier_mismatch",
        "inverse_or_contrapositive_use",
    ],
}
ALIGNMENT_V2_CONTRACT_SHA256 = (
    "a17302146a8656ec11363f929ebf2a8e9c23ead9da39779cd399ac1ec57b3fe3"
)


class ScientificProcessAlignmentV2Error(ValueError):
    """Raised when V2 bridge-bound alignment invariants are violated."""


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ScientificProcessAlignmentV2Error(
            f"{field_name} must be non-empty"
        )
    return normalized


def _required_scope_value(
    policy: ProcessScientificAlignmentPolicyV1,
    pointer: str,
) -> object:
    matches = [
        item
        for item in policy.evaluation_scope.required_parameter_bindings
        if item.json_pointer == pointer
    ]
    if len(matches) != 1:
        raise ScientificProcessAlignmentV2Error(
            f"base V1 policy must bind exactly one {pointer!r} value"
        )
    return json.loads(matches[0].expected_value_json)


@dataclass(frozen=True, slots=True)
class ProcessScientificAlignmentPolicyV2:
    """V2 policy that transitively binds exact science, bridge, and N4 scope."""

    name: str
    version: str
    assertion_ref: ScientificAssertionRefV1
    base_policy_v1: ProcessScientificAlignmentPolicyV1
    model_semantic_bridge: ReviewedModelSemanticBridgeV1
    contract_sha256: str = ALIGNMENT_V2_CONTRACT_SHA256

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _nonempty(self.name, "name"))
        object.__setattr__(self, "version", _nonempty(self.version, "version"))
        if not isinstance(self.assertion_ref, ScientificAssertionRefV1):
            raise TypeError("assertion_ref must be ScientificAssertionRefV1")
        if not isinstance(
            self.base_policy_v1,
            ProcessScientificAlignmentPolicyV1,
        ):
            raise TypeError(
                "base_policy_v1 must be ProcessScientificAlignmentPolicyV1"
            )
        if not isinstance(
            self.model_semantic_bridge,
            ReviewedModelSemanticBridgeV1,
        ):
            raise TypeError(
                "model_semantic_bridge must be ReviewedModelSemanticBridgeV1"
            )
        if self.contract_sha256 != ALIGNMENT_V2_CONTRACT_SHA256:
            raise ScientificProcessAlignmentV2Error(
                "contract_sha256 must equal the frozen Alignment V2 contract"
            )

        base = self.base_policy_v1
        bridge = self.model_semantic_bridge

        if self.assertion_ref != bridge.assertion_ref:
            raise ScientificProcessAlignmentV2Error(
                "assertion_ref must exactly match reviewed model-semantic bridge"
            )
        if (
            bridge.design_basis_sha256
            != REVIEWED_MODEL_SEMANTIC_BRIDGE_DESIGN_SHA256
        ):
            raise ScientificProcessAlignmentV2Error(
                "bridge design basis identity mismatch"
            )
        if base.process_id != bridge.process_id:
            raise ScientificProcessAlignmentV2Error(
                "base policy process_id must match bridge"
            )
        if base.process_version != bridge.process_version:
            raise ScientificProcessAlignmentV2Error(
                "base policy process_version must match bridge"
            )
        if base.role != bridge.process_role:
            raise ScientificProcessAlignmentV2Error(
                "base policy role must match bridge"
            )
        if base.alignment_class != "direct_mechanism_support":
            raise ScientificProcessAlignmentV2Error(
                "Alignment V2 requires direct_mechanism_support"
            )
        if base.epistemic_class != "explicit_causal_result":
            raise ScientificProcessAlignmentV2Error(
                "Alignment V2 requires explicit_causal_result"
            )
        if base.participant_match_mode != "exact":
            raise ScientificProcessAlignmentV2Error(
                "Alignment V2 requires exact participant matching"
            )
        if base.qualifier_match_mode != "exact":
            raise ScientificProcessAlignmentV2Error(
                "Alignment V2 requires exact qualifier matching"
            )
        if len(base.allowed_predicates) != 1:
            raise ScientificProcessAlignmentV2Error(
                "Alignment V2 requires exactly one reviewed predicate"
            )
        if any(
            item.occurrence_json is not None
            for item in base.required_participants
        ):
            raise ScientificProcessAlignmentV2Error(
                "bridge V1 cannot silently drop participant occurrence scope"
            )

        base_participants = tuple(
            sorted(
                (
                    item.role,
                    item.entity_id,
                    item.entity_revision,
                )
                for item in base.required_participants
            )
        )
        if base_participants != bridge.scientific_participant_keys:
            raise ScientificProcessAlignmentV2Error(
                "base policy scientific participants must exactly match bridge"
            )

        source_value = _required_scope_value(
            base,
            "/source_component_id",
        )
        target_value = _required_scope_value(
            base,
            "/target_component_id",
        )
        if source_value != bridge.source_component_id:
            raise ScientificProcessAlignmentV2Error(
                "base policy source component scope must match bridge"
            )
        if target_value != bridge.target_component_id:
            raise ScientificProcessAlignmentV2Error(
                "base policy target component scope must match bridge"
            )

    @property
    def predicate(self) -> str:
        return self.base_policy_v1.allowed_predicates[0]

    @property
    def bridge_sha256(self) -> str:
        return self.model_semantic_bridge.canonical_sha256

    @property
    def evaluation_scope_sha256(self) -> str:
        return self.base_policy_v1.evaluation_scope.canonical_sha256

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": (
                "ecobiome-process-scientific-alignment-policy-v2"
            ),
            "name": self.name,
            "version": self.version,
            "contract_sha256": self.contract_sha256,
            "assertion_ref": self.assertion_ref.canonical_payload(),
            "reviewed_model_semantic_bridge": {
                "bridge_id": self.model_semantic_bridge.bridge_id,
                "bridge_sha256": self.bridge_sha256,
                "design_basis_sha256": (
                    self.model_semantic_bridge.design_basis_sha256
                ),
            },
            "base_policy_v1": {
                "canonical_sha256": self.base_policy_v1.canonical_sha256,
                "predicate": self.predicate,
                "evaluation_scope_sha256": self.evaluation_scope_sha256,
                "alignment_class": self.base_policy_v1.alignment_class,
                "epistemic_class": self.base_policy_v1.epistemic_class,
                "participant_match_mode": (
                    self.base_policy_v1.participant_match_mode
                ),
                "qualifier_match_mode": (
                    self.base_policy_v1.qualifier_match_mode
                ),
            },
            "automatic_acceptance": False,
            "automatic_attachment": False,
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_sha256(self.canonical_payload())


def align_scientific_assertion_to_process_v2(
    *,
    evaluation: ProcessEvaluationV1,
    assertion_ref: ScientificAssertionRefV1,
    policy: ProcessScientificAlignmentPolicyV2,
    assertions: ScientificAssertionRepository,
    syntheses: KnowledgeSynthesisRepository,
) -> ProcessScientificSupportV1:
    """Run exact V1 scientific checks plus the adopted bridge-bound V2 checks."""
    if assertion_ref != policy.assertion_ref:
        raise ScientificProcessAlignmentV2Error(
            "assertion_ref does not match selected Alignment V2 policy"
        )

    bridge = policy.model_semantic_bridge
    try:
        bridge.require_evaluation_match(
            process_id=evaluation.definition.process_id,
            process_version=evaluation.definition.version,
            role=policy.base_policy_v1.role,
            parameters=evaluation.parameters_payload,
        )
    except ReviewedModelSemanticBridgeV1Error as exc:
        raise ScientificProcessAlignmentV2Error(
            "evaluation is outside reviewed model-semantic bridge scope"
        ) from exc

    try:
        support = align_scientific_assertion_to_process_v1(
            evaluation=evaluation,
            assertion_ref=assertion_ref,
            policy=policy.base_policy_v1,
            assertions=assertions,
            syntheses=syntheses,
        )
    except ScientificProcessAlignmentV1Error as exc:
        raise ScientificProcessAlignmentV2Error(
            "underlying reviewed V1 scientific alignment failed"
        ) from exc

    return replace(
        support,
        alignment_policy_name=policy.name,
        alignment_policy_version=policy.version,
        alignment_policy_sha256=policy.canonical_sha256,
    )


if (
    canonical_sha256(ALIGNMENT_V2_CONTRACT_DESCRIPTOR)
    != ALIGNMENT_V2_CONTRACT_SHA256
):
    raise RuntimeError("Alignment V2 contract identity mismatch")
