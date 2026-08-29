"""Durable human-reviewed entity resolution for Semantic Candidate V2.12."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from ecobiome.knowledge_acquisition.semantic_candidate_v2_12 import (
    validate_semantic_candidate_v2_12,
)
from ecobiome.knowledge_persistence.contracts import (
    SemanticCandidateEntityResolutionEventsRow,
)
from ecobiome.knowledge_persistence.serialization import canonical_sha256

if TYPE_CHECKING:
    from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1_8 import (
        ReviewedEntityArgumentV1,
    )

ENTITY_RESOLUTION_POLICY_NAME = "ecobiome-semantic-candidate-entity-resolution"
ENTITY_RESOLUTION_POLICY_VERSION = "1.1"
ENTITY_RESOLUTION_POLICY_SHA256 = (
    "82f4ebbd6b785224eb1fa2c85c659f8a9ba5cbdbb8d8e3175191688cf5eb4dd6"
)
ENTITY_RESOLUTION_POLICY_DESCRIPTOR_V1_1 = {
    "append_only": True,
    "candidate_contract_version": "2.12",
    "decisions": ["accept", "reject"],
    "entity_revision_review_status": "reviewed_confirmed",
    "latest_review_order": ["reviewed_at", "id"],
    "mapping_statuses": ["exact", "synonym"],
    "name": ENTITY_RESOLUTION_POLICY_NAME,
    "name_usage_mapping_review_status": "reviewed_confirmed",
    "projection_requires_latest_accept": True,
    "source_anchor": {
        "candidate_evidence_containment_required": True,
        "candidate_source_claim_match_required": True,
        "segment_offsets_required": True,
        "surface_comparison": "unicode_nfc_exact_case_sensitive",
    },
    "version": ENTITY_RESOLUTION_POLICY_VERSION,
}
if (
    canonical_sha256(ENTITY_RESOLUTION_POLICY_DESCRIPTOR_V1_1)
    != ENTITY_RESOLUTION_POLICY_SHA256
):
    raise RuntimeError("Entity-resolution policy V1.1 identity mismatch")

_ALLOWED_MAPPING_STATUSES = frozenset({"exact", "synonym"})
_ALLOWED_DECISIONS = frozenset({"accept", "reject"})


class SemanticCandidateEntityResolutionV11Error(ValueError):
    """Raised when durable V2.12 entity resolution cannot pass fail-closed review."""


def _candidate_arguments(
    candidate: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    semantic = candidate.get("semantic")
    if not isinstance(semantic, Mapping):
        raise SemanticCandidateEntityResolutionV11Error(
            "candidate.semantic must be an object"
        )
    raw_arguments = semantic.get("arguments")
    if not isinstance(raw_arguments, list) or not raw_arguments:
        raise SemanticCandidateEntityResolutionV11Error(
            "candidate.semantic.arguments must be non-empty"
        )
    result: dict[str, Mapping[str, Any]] = {}
    for raw in raw_arguments:
        if not isinstance(raw, Mapping):
            raise SemanticCandidateEntityResolutionV11Error(
                "candidate argument must be an object"
            )
        role = raw.get("role")
        if not isinstance(role, str) or not role.strip():
            raise SemanticCandidateEntityResolutionV11Error(
                "candidate argument role must be non-empty"
            )
        if role in result:
            raise SemanticCandidateEntityResolutionV11Error(
                f"duplicate candidate argument role: {role}"
            )
        result[role] = raw
    return result


def build_semantic_candidate_entity_resolution_event_v1_1(
    candidate: Mapping[str, Any],
    *,
    event_id: str,
    semantic_candidate_id: str,
    role: str,
    entity_name_usage_id: str,
    entity_id: str,
    entity_revision: int,
    mapping_status: str,
    decision: str,
    reviewer: str,
    reviewed_at: str,
    rationale: str = "",
) -> SemanticCandidateEntityResolutionEventsRow:
    """Build one append-only human entity-resolution review event for V2.12."""
    validate_semantic_candidate_v2_12(candidate)

    required_strings = {
        "event_id": event_id,
        "semantic_candidate_id": semantic_candidate_id,
        "role": role,
        "entity_name_usage_id": entity_name_usage_id,
        "entity_id": entity_id,
        "reviewer": reviewer,
        "reviewed_at": reviewed_at,
    }
    for label, value in required_strings.items():
        if not value.strip():
            raise SemanticCandidateEntityResolutionV11Error(
                f"{label} must be non-empty"
            )

    if mapping_status not in _ALLOWED_MAPPING_STATUSES:
        raise SemanticCandidateEntityResolutionV11Error(
            f"unsupported entity mapping status: {mapping_status}"
        )
    if decision not in _ALLOWED_DECISIONS:
        raise SemanticCandidateEntityResolutionV11Error(
            f"unsupported entity-resolution decision: {decision}"
        )
    if isinstance(entity_revision, bool) or entity_revision < 1:
        raise SemanticCandidateEntityResolutionV11Error(
            "entity_revision must be a positive integer"
        )

    arguments = _candidate_arguments(candidate)
    argument = arguments.get(role)
    if argument is None:
        raise SemanticCandidateEntityResolutionV11Error(
            f"entity-resolution role is absent from candidate: {role}"
        )
    if argument.get("resolution_state") != "grounded_opaque_unresolved":
        raise SemanticCandidateEntityResolutionV11Error(
            f"entity-resolution role is not grounded opaque text: {role}"
        )
    argument_value = argument.get("value")
    if (
        not isinstance(argument_value, Mapping)
        or argument_value.get("kind") != "source_text"
        or not isinstance(argument_value.get("source_surface"), str)
        or not argument_value["source_surface"]
    ):
        raise SemanticCandidateEntityResolutionV11Error(
            f"entity-resolution role lacks an exact source surface: {role}"
        )

    candidate_sha = candidate.get("canonical_candidate_sha256")
    if not isinstance(candidate_sha, str) or len(candidate_sha) != 64:
        raise SemanticCandidateEntityResolutionV11Error(
            "candidate canonical SHA is invalid"
        )

    return SemanticCandidateEntityResolutionEventsRow(
        id=event_id,
        semantic_candidate_id=semantic_candidate_id,
        semantic_candidate_sha256=candidate_sha,
        role=role,
        candidate_argument_sha256=canonical_sha256(argument),
        entity_name_usage_id=entity_name_usage_id,
        entity_id=entity_id,
        entity_revision=entity_revision,
        mapping_status=mapping_status,
        decision=decision,
        reviewer=reviewer,
        rationale=rationale,
        review_policy_name=ENTITY_RESOLUTION_POLICY_NAME,
        review_policy_version=ENTITY_RESOLUTION_POLICY_VERSION,
        review_policy_sha256=ENTITY_RESOLUTION_POLICY_SHA256,
        reviewed_at=reviewed_at,
    )


def require_reviewed_entity_resolutions_v1_1(
    candidate: Mapping[str, Any],
    *,
    semantic_candidate_id: str,
    events: Sequence[SemanticCandidateEntityResolutionEventsRow],
    required_roles: Sequence[str],
) -> dict[str, ReviewedEntityArgumentV1]:
    """Reconstruct exact reviewed V2.12 entity arguments or fail closed."""
    validate_semantic_candidate_v2_12(candidate)
    if not semantic_candidate_id.strip():
        raise SemanticCandidateEntityResolutionV11Error(
            "semantic_candidate_id must be non-empty"
        )
    candidate_sha = candidate.get("canonical_candidate_sha256")
    if not isinstance(candidate_sha, str) or len(candidate_sha) != 64:
        raise SemanticCandidateEntityResolutionV11Error(
            "candidate canonical SHA is invalid"
        )

    roles = tuple(required_roles)
    if not roles or len(roles) != len(set(roles)):
        raise SemanticCandidateEntityResolutionV11Error(
            "required entity roles must be non-empty and unique"
        )
    arguments = _candidate_arguments(candidate)
    unknown_required = set(roles) - set(arguments)
    if unknown_required:
        raise SemanticCandidateEntityResolutionV11Error(
            f"required entity role is absent from candidate: {sorted(unknown_required)}"
        )

    by_role: dict[str, list[SemanticCandidateEntityResolutionEventsRow]] = {
        role: [] for role in roles
    }
    for event in events:
        if event.semantic_candidate_id != semantic_candidate_id:
            raise SemanticCandidateEntityResolutionV11Error(
                "entity-resolution event belongs to a different candidate"
            )
        if event.semantic_candidate_sha256 != candidate_sha:
            raise SemanticCandidateEntityResolutionV11Error(
                "entity-resolution event is stale against candidate SHA"
            )
        if event.role not in by_role:
            raise SemanticCandidateEntityResolutionV11Error(
                f"extra entity-resolution role is forbidden: {event.role}"
            )
        if event.mapping_status not in _ALLOWED_MAPPING_STATUSES:
            raise SemanticCandidateEntityResolutionV11Error(
                f"unsupported entity mapping status: {event.mapping_status}"
            )
        if event.decision not in _ALLOWED_DECISIONS:
            raise SemanticCandidateEntityResolutionV11Error(
                f"unsupported entity-resolution decision: {event.decision}"
            )
        if (
            event.review_policy_name != ENTITY_RESOLUTION_POLICY_NAME
            or event.review_policy_version != ENTITY_RESOLUTION_POLICY_VERSION
            or event.review_policy_sha256 != ENTITY_RESOLUTION_POLICY_SHA256
        ):
            raise SemanticCandidateEntityResolutionV11Error(
                "entity-resolution review policy identity mismatch"
            )
        argument = arguments[event.role]
        if event.candidate_argument_sha256 != canonical_sha256(argument):
            raise SemanticCandidateEntityResolutionV11Error(
                f"entity-resolution event is stale for role: {event.role}"
            )
        by_role[event.role].append(event)

    from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1_8 import (
        ReviewedEntityArgumentV1,
    )

    result: dict[str, ReviewedEntityArgumentV1] = {}
    for role in roles:
        history = by_role[role]
        if not history:
            raise SemanticCandidateEntityResolutionV11Error(
                f"human-reviewed entity mapping is required for role: {role}"
            )
        latest = max(history, key=lambda item: (item.reviewed_at, item.id))
        if latest.decision == "reject":
            raise SemanticCandidateEntityResolutionV11Error(
                f"latest entity-resolution review is rejected for role: {role}"
            )
        if not latest.reviewer.strip():
            raise SemanticCandidateEntityResolutionV11Error(
                f"entity-resolution reviewer is empty for role: {role}"
            )
        result[role] = ReviewedEntityArgumentV1(
            role=role,
            candidate_argument_sha256=latest.candidate_argument_sha256,
            entity_id=latest.entity_id,
            entity_revision=latest.entity_revision,
            mapping_status=latest.mapping_status,
            mapping_review_status="reviewed_confirmed",
            reviewed_by=latest.reviewer,
        )
    return result
