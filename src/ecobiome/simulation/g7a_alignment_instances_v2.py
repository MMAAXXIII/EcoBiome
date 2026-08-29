"""Human-reviewed G7A Alignment V2 instances for directional nitrogen mechanisms.

Importing this module freezes exact reviewed policy identities only. It does not
attach scientific support to any process evaluation and performs no persistence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from ecobiome.knowledge_persistence.serialization import canonical_sha256
from ecobiome.simulation.model_semantic_bridge_v1 import (
    G7A_NITROGEN_ASSIMILATION_BRIDGE_V1,
    G7A_NITROGEN_OXIDATION_BRIDGE_V1,
)
from ecobiome.simulation.process_v1 import (
    ProcessScientificEvaluationScopeV1,
    ProcessScientificParameterBindingV1,
)
from ecobiome.simulation.scientific_alignment_v1 import (
    ProcessScientificAlignmentPolicyV1,
    ProcessScientificParticipantRequirementV1,
)
from ecobiome.simulation.scientific_alignment_v2 import (
    ProcessScientificAlignmentPolicyV2,
)

G7A_ALIGNMENT_V2_SELECTION_SCHEMA_VERSION = (
    "ecobiome-human-reviewed-alignment-v2-selection-v1"
)
G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SHA256 = (
    "d20e41bac0fafa83e34a7f564e2952be75758e487ebce53ab75661fc0a940115"
)
G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SHA256 = (
    "3b516cb2dd8968c2f714f979678da4ee64d79608fe33524287ace5f99a8ab14f"
)


class HumanReviewedAlignmentV2SelectionError(ValueError):
    """Raised when a frozen human-reviewed Alignment V2 selection is invalid."""


def _base_policy(
    *,
    name: str,
    source_component_id: str,
    target_component_id: str,
    predicate: str,
    semantic_type: str,
    participants: tuple[tuple[str, str, int], ...],
) -> ProcessScientificAlignmentPolicyV1:
    return ProcessScientificAlignmentPolicyV1(
        name=name,
        version="1",
        process_id="nitrogen_transformation_extent_v1",
        process_version="1",
        role="mechanism",
        allowed_predicates=(predicate,),
        alignment_class="direct_mechanism_support",
        epistemic_class="explicit_causal_result",
        evaluation_scope=ProcessScientificEvaluationScopeV1(
            process_id="nitrogen_transformation_extent_v1",
            process_version="1",
            role="mechanism",
            required_parameter_bindings=(
                ProcessScientificParameterBindingV1(
                    json_pointer="/source_component_id",
                    expected_value_json=json.dumps(
                        source_component_id,
                        separators=(",", ":"),
                    ),
                ),
                ProcessScientificParameterBindingV1(
                    json_pointer="/target_component_id",
                    expected_value_json=json.dumps(
                        target_component_id,
                        separators=(",", ":"),
                    ),
                ),
            ),
        ),
        required_participants=tuple(
            ProcessScientificParticipantRequirementV1(
                role=role,
                entity_id=entity_id,
                entity_revision=entity_revision,
            )
            for role, entity_id, entity_revision in participants
        ),
        required_qualifiers_json=json.dumps(
            {"semantic_type": semantic_type},
            sort_keys=True,
            separators=(",", ":"),
        ),
        participant_match_mode="exact",
        qualifier_match_mode="exact",
    )


G7A_NITROGEN_OXIDATION_ALIGNMENT_V2 = ProcessScientificAlignmentPolicyV2(
    name="g7a-nitrogen-oxidation-mechanism-alignment-v2",
    version="2",
    assertion_ref=G7A_NITROGEN_OXIDATION_BRIDGE_V1.assertion_ref,
    base_policy_v1=_base_policy(
        name="g7a-nitrogen-oxidation-mechanism-alignment-v2-base-v1",
        source_component_id="reduced_inorganic_nitrogen",
        target_component_id="oxidized_inorganic_nitrogen",
        predicate="nitrogen_oxidized_from_to",
        semantic_type="nitrogen_oxidation",
        participants=(
            ("source_material", "entity-pubchem-cid-223", 1),
            ("target_material", "entity-pubchem-cid-943", 1),
            ("process_agent", "entity-ncbitaxon-1715989", 1),
        ),
    ),
    model_semantic_bridge=G7A_NITROGEN_OXIDATION_BRIDGE_V1,
)

G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2 = ProcessScientificAlignmentPolicyV2(
    name="g7a-nitrogen-assimilation-mechanism-alignment-v2",
    version="2",
    assertion_ref=G7A_NITROGEN_ASSIMILATION_BRIDGE_V1.assertion_ref,
    base_policy_v1=_base_policy(
        name="g7a-nitrogen-assimilation-mechanism-alignment-v2-base-v1",
        source_component_id="dissolved_inorganic_nitrogen",
        target_component_id="biological_nitrogen",
        predicate="nitrogen_assimilated_from_into",
        semantic_type="nitrogen_assimilation",
        participants=(
            ("source_material", "entity-pubchem-cid-223", 1),
            ("target_nitrogen_pool", "entity-pubchem-cid-5961", 1),
            ("process_agent", "entity-ipni-526178-1", 1),
        ),
    ),
    model_semantic_bridge=G7A_NITROGEN_ASSIMILATION_BRIDGE_V1,
)


@dataclass(frozen=True, slots=True)
class HumanReviewedAlignmentV2SelectionV1:
    """Explicit human acceptance of one exact Alignment V2 policy identity."""

    selection_id: str
    policy: ProcessScientificAlignmentPolicyV2
    decision: str = "accept"
    review_status: str = "reviewed_confirmed"
    reviewed_by: str = "human"
    automatic_attachment: bool = False

    def __post_init__(self) -> None:
        if not self.selection_id.strip():
            raise HumanReviewedAlignmentV2SelectionError(
                "selection_id must be non-empty"
            )
        if not isinstance(self.policy, ProcessScientificAlignmentPolicyV2):
            raise TypeError("policy must be ProcessScientificAlignmentPolicyV2")
        if self.decision != "accept":
            raise HumanReviewedAlignmentV2SelectionError(
                "frozen selection decision must be accept"
            )
        if self.review_status != "reviewed_confirmed":
            raise HumanReviewedAlignmentV2SelectionError(
                "review_status must be reviewed_confirmed"
            )
        if self.reviewed_by != "human":
            raise HumanReviewedAlignmentV2SelectionError(
                "reviewed_by must be human"
            )
        if self.automatic_attachment:
            raise HumanReviewedAlignmentV2SelectionError(
                "automatic_attachment must remain false"
            )

        payload = self.policy.canonical_payload()
        if payload.get("automatic_acceptance") is not False:
            raise HumanReviewedAlignmentV2SelectionError(
                "selected Alignment V2 policy must forbid automatic acceptance"
            )
        if payload.get("automatic_attachment") is not False:
            raise HumanReviewedAlignmentV2SelectionError(
                "selected Alignment V2 policy must forbid automatic attachment"
            )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": G7A_ALIGNMENT_V2_SELECTION_SCHEMA_VERSION,
            "selection_id": self.selection_id,
            "decision": self.decision,
            "review_status": self.review_status,
            "reviewed_by": self.reviewed_by,
            "policy": {
                "name": self.policy.name,
                "version": self.policy.version,
                "canonical_sha256": self.policy.canonical_sha256,
                "assertion_ref": self.policy.assertion_ref.canonical_payload(),
                "bridge_id": self.policy.model_semantic_bridge.bridge_id,
                "bridge_sha256": self.policy.bridge_sha256,
                "evaluation_scope_sha256": self.policy.evaluation_scope_sha256,
            },
            "automatic_attachment": False,
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_sha256(self.canonical_payload())


G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION = HumanReviewedAlignmentV2SelectionV1(
    selection_id="selection-g7a-nitrogen-oxidation-alignment-v2",
    policy=G7A_NITROGEN_OXIDATION_ALIGNMENT_V2,
)
G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION = HumanReviewedAlignmentV2SelectionV1(
    selection_id="selection-g7a-nitrogen-assimilation-alignment-v2",
    policy=G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2,
)

G7A_ALIGNMENT_V2_SELECTIONS = (
    G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION,
    G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION,
)

if (
    G7A_NITROGEN_OXIDATION_ALIGNMENT_V2.canonical_sha256
    != G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SHA256
):
    raise RuntimeError("G7A oxidation Alignment V2 identity mismatch")
if (
    G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2.canonical_sha256
    != G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SHA256
):
    raise RuntimeError("G7A assimilation Alignment V2 identity mismatch")
