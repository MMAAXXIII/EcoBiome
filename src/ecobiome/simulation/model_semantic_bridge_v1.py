"""Reviewed scoped bridges between ScientificEntities and coarse N4 material components."""

from __future__ import annotations

from dataclasses import dataclass

from ecobiome.knowledge_persistence.serialization import canonical_sha256
from ecobiome.simulation.process_v1 import ScientificAssertionRefV1

REVIEWED_MODEL_SEMANTIC_BRIDGE_DESIGN_SHA256 = (
    "5d6ea5088bb7b1b22b44ee56e8644f1860cbe6556b1e4139d5c2989ea8515157"
)
MODEL_SEMANTIC_BRIDGE_SCHEMA_VERSION = "ecobiome-reviewed-model-semantic-bridge-v1"
_MODEL_ABSTRACTION_MEMBERSHIP = "model_abstraction_membership"


class ReviewedModelSemanticBridgeV1Error(ValueError):
    """Raised when a reviewed model-semantic bridge violates its exact scope."""


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ReviewedModelSemanticBridgeV1Error(
            f"{field_name} must be non-empty"
        )
    return normalized


def _entity_key(
    role: str,
    entity_id: str,
    entity_revision: int,
) -> tuple[str, str, int]:
    return (role, entity_id, entity_revision)


@dataclass(frozen=True, slots=True)
class ModelSemanticParticipantBindingV1:
    """Map one exact assertion participant to one coarse model component in scope."""

    assertion_role: str
    entity_id: str
    entity_revision: int
    model_component_id: str
    mapping_kind: str
    context: str

    def __post_init__(self) -> None:
        for field_name in (
            "assertion_role",
            "entity_id",
            "model_component_id",
            "mapping_kind",
            "context",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonempty(str(getattr(self, field_name)), field_name),
            )
        if (
            isinstance(self.entity_revision, bool)
            or not isinstance(self.entity_revision, int)
            or self.entity_revision < 1
        ):
            raise ReviewedModelSemanticBridgeV1Error(
                "entity_revision must be an integer >= 1"
            )
        if self.mapping_kind != _MODEL_ABSTRACTION_MEMBERSHIP:
            raise ReviewedModelSemanticBridgeV1Error(
                "mapping_kind must be model_abstraction_membership; "
                "identity/equivalence mappings are forbidden"
            )

    @property
    def entity_key(self) -> tuple[str, str, int]:
        return _entity_key(
            self.assertion_role,
            self.entity_id,
            self.entity_revision,
        )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "assertion_role": self.assertion_role,
            "entity": {
                "entity_id": self.entity_id,
                "entity_revision": self.entity_revision,
            },
            "model_component_id": self.model_component_id,
            "mapping_kind": self.mapping_kind,
            "context": self.context,
        }


@dataclass(frozen=True, slots=True)
class ModelSemanticContextParticipantV1:
    """Retain an exact scientific participant as context, not material identity."""

    assertion_role: str
    entity_id: str
    entity_revision: int
    context: str

    def __post_init__(self) -> None:
        for field_name in ("assertion_role", "entity_id", "context"):
            object.__setattr__(
                self,
                field_name,
                _nonempty(str(getattr(self, field_name)), field_name),
            )
        if (
            isinstance(self.entity_revision, bool)
            or not isinstance(self.entity_revision, int)
            or self.entity_revision < 1
        ):
            raise ReviewedModelSemanticBridgeV1Error(
                "entity_revision must be an integer >= 1"
            )

    @property
    def entity_key(self) -> tuple[str, str, int]:
        return _entity_key(
            self.assertion_role,
            self.entity_id,
            self.entity_revision,
        )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "assertion_role": self.assertion_role,
            "entity": {
                "entity_id": self.entity_id,
                "entity_revision": self.entity_revision,
            },
            "context": self.context,
            "mapped_to_material_component": False,
        }


@dataclass(frozen=True, slots=True)
class ReviewedModelSemanticBridgeV1:
    """Human-reviewed, assertion/role/process-scoped model abstraction bridge."""

    bridge_id: str
    version: str
    assertion_ref: ScientificAssertionRefV1
    process_id: str
    process_version: str
    process_role: str
    source_component_id: str
    target_component_id: str
    participant_bindings: tuple[ModelSemanticParticipantBindingV1, ...]
    context_participants: tuple[ModelSemanticContextParticipantV1, ...]
    review_status: str = "reviewed_confirmed"
    reviewed_by: str = "human"
    design_basis_sha256: str = REVIEWED_MODEL_SEMANTIC_BRIDGE_DESIGN_SHA256

    def __post_init__(self) -> None:
        for field_name in (
            "bridge_id",
            "version",
            "process_id",
            "process_version",
            "process_role",
            "source_component_id",
            "target_component_id",
            "review_status",
            "reviewed_by",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonempty(str(getattr(self, field_name)), field_name),
            )
        if not isinstance(self.assertion_ref, ScientificAssertionRefV1):
            raise TypeError("assertion_ref must be ScientificAssertionRefV1")
        if self.source_component_id == self.target_component_id:
            raise ReviewedModelSemanticBridgeV1Error(
                "source_component_id and target_component_id must differ"
            )
        if self.review_status != "reviewed_confirmed":
            raise ReviewedModelSemanticBridgeV1Error(
                "review_status must be reviewed_confirmed"
            )
        if self.reviewed_by != "human":
            raise ReviewedModelSemanticBridgeV1Error(
                "reviewed model-semantic bridges require human review"
            )
        if (
            self.design_basis_sha256
            != REVIEWED_MODEL_SEMANTIC_BRIDGE_DESIGN_SHA256
        ):
            raise ReviewedModelSemanticBridgeV1Error(
                "design_basis_sha256 must match the adopted bridge design"
            )

        bindings = tuple(self.participant_bindings)
        contexts = tuple(self.context_participants)
        if not bindings:
            raise ReviewedModelSemanticBridgeV1Error(
                "participant_bindings must not be empty"
            )
        if not contexts:
            raise ReviewedModelSemanticBridgeV1Error(
                "context_participants must not be empty"
            )
        binding_roles = [item.assertion_role for item in bindings]
        context_roles = [item.assertion_role for item in contexts]
        if len(set(binding_roles)) != len(binding_roles):
            raise ReviewedModelSemanticBridgeV1Error(
                "participant binding roles must be unique"
            )
        if len(set(context_roles)) != len(context_roles):
            raise ReviewedModelSemanticBridgeV1Error(
                "context participant roles must be unique"
            )
        if set(binding_roles) & set(context_roles):
            raise ReviewedModelSemanticBridgeV1Error(
                "one assertion role cannot be both material-mapped and context-only"
            )

        model_components = [item.model_component_id for item in bindings]
        if model_components.count(self.source_component_id) != 1:
            raise ReviewedModelSemanticBridgeV1Error(
                "source_component_id must have exactly one participant binding"
            )
        if model_components.count(self.target_component_id) != 1:
            raise ReviewedModelSemanticBridgeV1Error(
                "target_component_id must have exactly one participant binding"
            )
        if set(model_components) != {
            self.source_component_id,
            self.target_component_id,
        }:
            raise ReviewedModelSemanticBridgeV1Error(
                "bridge may map participants only to its source/target model components"
            )

        object.__setattr__(
            self,
            "participant_bindings",
            tuple(sorted(bindings, key=lambda item: item.entity_key)),
        )
        object.__setattr__(
            self,
            "context_participants",
            tuple(sorted(contexts, key=lambda item: item.entity_key)),
        )

    @property
    def scientific_participant_keys(self) -> tuple[tuple[str, str, int], ...]:
        return tuple(
            sorted(
                (
                    *(item.entity_key for item in self.participant_bindings),
                    *(item.entity_key for item in self.context_participants),
                )
            )
        )

    def require_evaluation_match(
        self,
        *,
        process_id: str,
        process_version: str,
        role: str,
        parameters: dict[str, object],
    ) -> None:
        if process_id != self.process_id:
            raise ReviewedModelSemanticBridgeV1Error(
                "bridge process_id does not match evaluation"
            )
        if process_version != self.process_version:
            raise ReviewedModelSemanticBridgeV1Error(
                "bridge process_version does not match evaluation"
            )
        if role != self.process_role:
            raise ReviewedModelSemanticBridgeV1Error(
                "bridge role does not match evaluation"
            )
        if parameters.get("source_component_id") != self.source_component_id:
            raise ReviewedModelSemanticBridgeV1Error(
                "evaluation source_component_id is outside reviewed bridge scope"
            )
        if parameters.get("target_component_id") != self.target_component_id:
            raise ReviewedModelSemanticBridgeV1Error(
                "evaluation target_component_id is outside reviewed bridge scope"
            )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": MODEL_SEMANTIC_BRIDGE_SCHEMA_VERSION,
            "bridge_id": self.bridge_id,
            "version": self.version,
            "semantics": {
                "relation": "represented_by_model_component_within_reviewed_scope",
                "identity": False,
                "equivalence": False,
                "global_taxonomy": False,
                "assertion_scoped": True,
                "participant_role_scoped": True,
                "process_scope_scoped": True,
            },
            "assertion_ref": self.assertion_ref.canonical_payload(),
            "process_scope": {
                "process_id": self.process_id,
                "process_version": self.process_version,
                "role": self.process_role,
                "source_component_id": self.source_component_id,
                "target_component_id": self.target_component_id,
            },
            "participant_bindings": [
                item.canonical_payload() for item in self.participant_bindings
            ],
            "context_participants": [
                item.canonical_payload() for item in self.context_participants
            ],
            "review_status": self.review_status,
            "reviewed_by": self.reviewed_by,
            "automatic_acceptance": False,
            "design_basis_sha256": self.design_basis_sha256,
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_sha256(self.canonical_payload())


G7A_NITROGEN_OXIDATION_BRIDGE_V1 = ReviewedModelSemanticBridgeV1(
    bridge_id="bridge-g7a-oxidation-v1",
    version="1",
    assertion_ref=ScientificAssertionRefV1(
        assertion_id="assertion-g7a-nitrogen-oxidation-ammonium-to-nitrate-v1",
        assertion_revision=1,
        canonical_payload_sha256=(
            "8d1b57be960c4d258edd6675563df57cd2aff1185be16162159332683ae901b5"
        ),
    ),
    process_id="nitrogen_transformation_extent_v1",
    process_version="1",
    process_role="mechanism",
    source_component_id="reduced_inorganic_nitrogen",
    target_component_id="oxidized_inorganic_nitrogen",
    participant_bindings=(
        ModelSemanticParticipantBindingV1(
            assertion_role="source_material",
            entity_id="entity-pubchem-cid-223",
            entity_revision=1,
            model_component_id="reduced_inorganic_nitrogen",
            mapping_kind="model_abstraction_membership",
            context="elemental-N inventory at N4 coarse-category level",
        ),
        ModelSemanticParticipantBindingV1(
            assertion_role="target_material",
            entity_id="entity-pubchem-cid-943",
            entity_revision=1,
            model_component_id="oxidized_inorganic_nitrogen",
            mapping_kind="model_abstraction_membership",
            context="elemental-N inventory at N4 coarse-category level",
        ),
    ),
    context_participants=(
        ModelSemanticContextParticipantV1(
            assertion_role="process_agent",
            entity_id="entity-ncbitaxon-1715989",
            entity_revision=1,
            context=(
                "scientific mechanism context; not an N4 material component"
            ),
        ),
    ),
)

G7A_NITROGEN_ASSIMILATION_BRIDGE_V1 = ReviewedModelSemanticBridgeV1(
    bridge_id="bridge-g7a-assimilation-v1",
    version="1",
    assertion_ref=ScientificAssertionRefV1(
        assertion_id=(
            "assertion-g7a-nitrogen-assimilation-ammonium-to-l-glutamine-v1"
        ),
        assertion_revision=1,
        canonical_payload_sha256=(
            "209b9eef66a7dc1ec74200be417c168da9670ce323acf61028e06ecdbfb17d63"
        ),
    ),
    process_id="nitrogen_transformation_extent_v1",
    process_version="1",
    process_role="mechanism",
    source_component_id="dissolved_inorganic_nitrogen",
    target_component_id="biological_nitrogen",
    participant_bindings=(
        ModelSemanticParticipantBindingV1(
            assertion_role="source_material",
            entity_id="entity-pubchem-cid-223",
            entity_revision=1,
            model_component_id="dissolved_inorganic_nitrogen",
            mapping_kind="model_abstraction_membership",
            context=(
                "ammonium nitrogen in the aqueous dissolved inorganic nitrogen pool"
            ),
        ),
        ModelSemanticParticipantBindingV1(
            assertion_role="target_nitrogen_pool",
            entity_id="entity-pubchem-cid-5961",
            entity_revision=1,
            model_component_id="biological_nitrogen",
            mapping_kind="model_abstraction_membership",
            context=(
                "L-glutamine nitrogen incorporated in Lemna gibba biological material; "
                "excludes dissolved or extracellular glutamine"
            ),
        ),
    ),
    context_participants=(
        ModelSemanticContextParticipantV1(
            assertion_role="process_agent",
            entity_id="entity-ipni-526178-1",
            entity_revision=1,
            context=(
                "organism supplies biological-compartment context; "
                "not an N4 material component"
            ),
        ),
    ),
)
