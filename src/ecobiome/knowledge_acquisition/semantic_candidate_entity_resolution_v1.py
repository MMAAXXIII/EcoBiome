"""Durable human-reviewed entity resolution for Semantic Candidate V2.11."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from ecobiome.knowledge_acquisition.semantic_candidate_v2_11 import (
    validate_semantic_candidate_v2_11,
)
from ecobiome.knowledge_persistence.contracts import (
    SemanticCandidateEntityResolutionEventsRow,
)
from ecobiome.knowledge_persistence.serialization import canonical_sha256

if TYPE_CHECKING:
    from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1 import (
        ReviewedEntityArgumentV1,
    )

ENTITY_RESOLUTION_POLICY_NAME = "ecobiome-semantic-candidate-entity-resolution"
ENTITY_RESOLUTION_POLICY_VERSION = "1"
ENTITY_RESOLUTION_POLICY_SHA256 = (
    "c2e31ae42c25610e4b6c299269bf50f05476b71772d1a0aefe01ff88329e329e"
)
ENTITY_RESOLUTION_POLICY_DESCRIPTOR_V1 = {
    "append_only": True,
    "candidate_contract_version": "2.11",
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
if canonical_sha256(ENTITY_RESOLUTION_POLICY_DESCRIPTOR_V1) != ENTITY_RESOLUTION_POLICY_SHA256:
    raise RuntimeError("Entity-resolution policy V1 identity mismatch")

_ALLOWED_MAPPING_STATUSES = frozenset({"exact", "synonym"})
_ALLOWED_DECISIONS = frozenset({"accept", "reject"})


class SemanticCandidateEntityResolutionV1Error(ValueError):
    """Raised when durable entity resolution cannot pass fail-closed review."""


def _candidate_arguments(
    candidate: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    semantic = candidate.get("semantic")
    if not isinstance(semantic, Mapping):
        raise SemanticCandidateEntityResolutionV1Error(
            "candidate.semantic must be an object"
        )
    raw_arguments = semantic.get("arguments")
    if not isinstance(raw_arguments, list) or not raw_arguments:
        raise SemanticCandidateEntityResolutionV1Error(
            "candidate.semantic.arguments must be non-empty"
        )
    result: dict[str, Mapping[str, Any]] = {}
    for raw in raw_arguments:
        if not isinstance(raw, Mapping):
            raise SemanticCandidateEntityResolutionV1Error(
                "candidate argument must be an object"
            )
        role = raw.get("role")
        if not isinstance(role, str) or not role.strip():
            raise SemanticCandidateEntityResolutionV1Error(
                "candidate argument role must be non-empty"
            )
        if role in result:
            raise SemanticCandidateEntityResolutionV1Error(
                f"duplicate candidate argument role: {role}"
            )
        result[role] = raw
    return result


def require_reviewed_entity_resolutions_v1(
    candidate: Mapping[str, Any],
    *,
    semantic_candidate_id: str,
    events: Sequence[SemanticCandidateEntityResolutionEventsRow],
    required_roles: Sequence[str],
) -> dict[str, ReviewedEntityArgumentV1]:
    """Reconstruct exact reviewed entity arguments or fail closed."""

    validate_semantic_candidate_v2_11(candidate)
    if not semantic_candidate_id.strip():
        raise SemanticCandidateEntityResolutionV1Error(
            "semantic_candidate_id must be non-empty"
        )
    candidate_sha = candidate.get("canonical_candidate_sha256")
    if not isinstance(candidate_sha, str) or len(candidate_sha) != 64:
        raise SemanticCandidateEntityResolutionV1Error(
            "candidate canonical SHA is invalid"
        )

    roles = tuple(required_roles)
    if not roles or len(roles) != len(set(roles)):
        raise SemanticCandidateEntityResolutionV1Error(
            "required entity roles must be non-empty and unique"
        )
    arguments = _candidate_arguments(candidate)
    unknown_required = set(roles) - set(arguments)
    if unknown_required:
        raise SemanticCandidateEntityResolutionV1Error(
            f"required entity role is absent from candidate: {sorted(unknown_required)}"
        )

    by_role: dict[str, list[SemanticCandidateEntityResolutionEventsRow]] = {
        role: [] for role in roles
    }
    for event in events:
        if event.semantic_candidate_id != semantic_candidate_id:
            raise SemanticCandidateEntityResolutionV1Error(
                "entity-resolution event belongs to a different candidate"
            )
        if event.semantic_candidate_sha256 != candidate_sha:
            raise SemanticCandidateEntityResolutionV1Error(
                "entity-resolution event is stale against candidate SHA"
            )
        if event.role not in by_role:
            raise SemanticCandidateEntityResolutionV1Error(
                f"extra entity-resolution role is forbidden: {event.role}"
            )
        if event.mapping_status not in _ALLOWED_MAPPING_STATUSES:
            raise SemanticCandidateEntityResolutionV1Error(
                f"unsupported entity mapping status: {event.mapping_status}"
            )
        if event.decision not in _ALLOWED_DECISIONS:
            raise SemanticCandidateEntityResolutionV1Error(
                f"unsupported entity-resolution decision: {event.decision}"
            )
        if (
            event.review_policy_name != ENTITY_RESOLUTION_POLICY_NAME
            or event.review_policy_version != ENTITY_RESOLUTION_POLICY_VERSION
            or event.review_policy_sha256 != ENTITY_RESOLUTION_POLICY_SHA256
        ):
            raise SemanticCandidateEntityResolutionV1Error(
                "entity-resolution review policy identity mismatch"
            )
        argument = arguments[event.role]
        if event.candidate_argument_sha256 != canonical_sha256(argument):
            raise SemanticCandidateEntityResolutionV1Error(
                f"entity-resolution event is stale for role: {event.role}"
            )
        by_role[event.role].append(event)

    from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1 import (
        ReviewedEntityArgumentV1,
    )

    result: dict[str, ReviewedEntityArgumentV1] = {}
    for role in roles:
        history = by_role[role]
        if not history:
            raise SemanticCandidateEntityResolutionV1Error(
                f"human-reviewed entity mapping is required for role: {role}"
            )
        latest = max(history, key=lambda item: (item.reviewed_at, item.id))
        if latest.decision == "reject":
            raise SemanticCandidateEntityResolutionV1Error(
                f"latest entity-resolution review is rejected for role: {role}"
            )
        if not latest.reviewer.strip():
            raise SemanticCandidateEntityResolutionV1Error(
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
