"""Fail-closed projection from V2.11 candidates to scientific assertions V1."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ecobiome.knowledge_acquisition.semantic_candidate_review_v1 import (
    SemanticCandidateReviewV1Error,
    require_candidate_acceptance_v1,
)
from ecobiome.knowledge_acquisition.semantic_candidate_v2_11 import (
    validate_semantic_candidate_v2_11,
)
from ecobiome.knowledge_persistence.contracts import (
    ClaimEvidenceLinksRow,
    ClaimReviewEventsRow,
    SegmentReviewEventsRow,
    SegmentsRow,
    SemanticCandidateReviewEventsRow,
    SourceClaimsRow,
    SourceEvidenceRow,
)
from ecobiome.knowledge_persistence.serialization import (
    canonical_assertion_payload,
    canonical_json_text,
    canonical_sha256,
    decimal_value,
    entity_ref,
)

PROJECTION_SCHEMA_VERSION = "ecobiome-scientific-assertion-projection-v1"
PROJECTION_CONTRACT_NAME = "ecobiome-scientific-assertion-projection"
PROJECTION_CONTRACT_VERSION = "1.7"
PROJECTION_CONTRACT_SHA256 = (
    "11c72c4411c98191413c5288d0a1ad76655c92c8bd731c317591a5c5bdd87c75"
)
ENTITY_RESOLUTION_POLICY_SHA256 = (
    "c2e31ae42c25610e4b6c299269bf50f05476b71772d1a0aefe01ff88329e329e"
)

ENTITY_ARGUMENT = "ENTITY_ARGUMENT"
EXACT_NUMERIC_ARGUMENT = "EXACT_NUMERIC_ARGUMENT"
CONTROLLED_LITERAL_ARGUMENT = "CONTROLLED_LITERAL_ARGUMENT"
CONTEXT_ARGUMENT = "CONTEXT_ARGUMENT"

_REVIEWED_MAPPING_STATUSES = frozenset({"exact", "synonym"})
_REVIEW_CONFIRMED = "reviewed_confirmed"
_HASH_LENGTH = 64


class ScientificAssertionProjectionV1Error(ValueError):
    """Raised when a candidate cannot cross the fail-closed projection gate."""


@dataclass(frozen=True, slots=True)
class ReviewedEntityArgumentV1:
    role: str
    candidate_argument_sha256: str
    entity_id: str
    entity_revision: int
    mapping_status: str
    mapping_review_status: str
    reviewed_by: str


@dataclass(frozen=True, slots=True)
class ReviewedContextArgumentV1:
    role: str
    candidate_argument_sha256: str
    canonical_value: str
    mapping_review_status: str
    reviewed_by: str


@dataclass(frozen=True, slots=True)
class ProjectionSpecV1:
    spec_id: str
    semantic_type: str
    relation: str
    assertion_kind: str
    predicate: str
    builder: str
    role_classes: tuple[tuple[str, str], ...]


_PROJECTION_SPECS = (
    ProjectionSpecV1(
        spec_id="maintained_at.measurement.v1",
        semantic_type="experimental_condition",
        relation="maintained_at",
        assertion_kind="measurement",
        predicate="maintained_at",
        builder="maintained_at_measurement_v1",
        role_classes=(
            ("variable", ENTITY_ARGUMENT),
            ("value", EXACT_NUMERIC_ARGUMENT),
            ("unit", CONTROLLED_LITERAL_ARGUMENT),
        ),
    ),
    ProjectionSpecV1(
        spec_id="adversely_affects.health_effect.relational.v1",
        semantic_type="health_effect",
        relation="adversely_affects",
        assertion_kind="relational",
        predicate="adversely_affects",
        builder="binary_entity_relation_v1",
        role_classes=(("cause", ENTITY_ARGUMENT), ("target", ENTITY_ARGUMENT)),
    ),
    ProjectionSpecV1(
        spec_id="adversely_affects.knowledge_gap.relational.v1",
        semantic_type="knowledge_gap",
        relation="adversely_affects",
        assertion_kind="relational",
        predicate="adversely_affects",
        builder="binary_entity_relation_v1",
        role_classes=(("cause", ENTITY_ARGUMENT), ("target", ENTITY_ARGUMENT)),
    ),
    ProjectionSpecV1(
        spec_id="poses_significant_threat_to.risk_factor.relational.v1",
        semantic_type="risk_factor",
        relation="poses_significant_threat_to",
        assertion_kind="relational",
        predicate="poses_significant_threat_to",
        builder="binary_entity_relation_v1",
        role_classes=(("cause", ENTITY_ARGUMENT), ("target", ENTITY_ARGUMENT)),
    ),
    ProjectionSpecV1(
        spec_id="poses_significant_threat_to.industry_impact.relational.v1",
        semantic_type="industry_impact",
        relation="poses_significant_threat_to",
        assertion_kind="relational",
        predicate="poses_significant_threat_to",
        builder="binary_entity_relation_v1",
        role_classes=(("cause", ENTITY_ARGUMENT), ("target", ENTITY_ARGUMENT)),
    ),
    ProjectionSpecV1(
        spec_id="caused_decrease.biological_effect.relational.v1",
        semantic_type="biological_effect",
        relation="caused_decrease",
        assertion_kind="relational",
        predicate="caused_decrease",
        builder="spec_binary_entity_relation_v1",
        role_classes=(
            ("exposure", ENTITY_ARGUMENT),
            ("variable", ENTITY_ARGUMENT),
        ),
    ),
    ProjectionSpecV1(
        spec_id="affected_gene_expression_in.combined_effect.relational.v1",
        semantic_type="combined_effect",
        relation="affected_gene_expression_in",
        assertion_kind="relational",
        predicate="affected_gene_expression_in",
        builder="spec_binary_entity_relation_v1",
        role_classes=(
            ("exposure", ENTITY_ARGUMENT),
            ("pathway", ENTITY_ARGUMENT),
        ),
    ),
    ProjectionSpecV1(
        spec_id="primarily_associated_with.gene_function_association.relational.v1",
        semantic_type="gene_function_association",
        relation="primarily_associated_with",
        assertion_kind="relational",
        predicate="primarily_associated_with",
        builder="spec_binary_entity_relation_v1",
        role_classes=(
            ("gene_set", ENTITY_ARGUMENT),
            ("process", ENTITY_ARGUMENT),
        ),
    ),
    ProjectionSpecV1(
        spec_id="prone_to.risk_factor.relational.v1",
        semantic_type="risk_factor",
        relation="prone_to",
        assertion_kind="relational",
        predicate="prone_to",
        builder="spec_binary_entity_relation_v1",
        role_classes=(
            ("subject", ENTITY_ARGUMENT),
            ("outcome", ENTITY_ARGUMENT),
        ),
    ),
)

PROJECTION_CONTRACT_DESCRIPTOR_V1_7 = {
    "automatic_persistence": False,
    "entity_resolution_policy_sha256": ENTITY_RESOLUTION_POLICY_SHA256,
    "name": PROJECTION_CONTRACT_NAME,
    "schema_version": PROJECTION_SCHEMA_VERSION,
    "specs": [
        {
            "assertion_kind": spec.assertion_kind,
            "builder": spec.builder,
            "predicate": spec.predicate,
            "relation": spec.relation,
            "role_classes": spec.role_classes,
            "semantic_type": spec.semantic_type,
            "spec_id": spec.spec_id,
        }
        for spec in _PROJECTION_SPECS
    ],
    "version": PROJECTION_CONTRACT_VERSION,
}
if canonical_sha256(PROJECTION_CONTRACT_DESCRIPTOR_V1_7) != PROJECTION_CONTRACT_SHA256:
    raise RuntimeError("Scientific Assertion Projection V1.7 identity mismatch")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _require_sha256(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != _HASH_LENGTH
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise ScientificAssertionProjectionV1Error(
            f"{label} must be a lowercase SHA-256"
        )
    return value


def _require_nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScientificAssertionProjectionV1Error(
            f"{label} must be a non-empty string"
        )
    return value


def _candidate_source(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
    source = candidate.get("source")
    if not isinstance(source, Mapping):
        raise ScientificAssertionProjectionV1Error(
            "candidate.source must be an object"
        )
    return source


def _candidate_semantic(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
    semantic = candidate.get("semantic")
    if not isinstance(semantic, Mapping):
        raise ScientificAssertionProjectionV1Error(
            "candidate.semantic must be an object"
        )
    return semantic


def _candidate_arguments(
    candidate: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    semantic = _candidate_semantic(candidate)
    raw_arguments = semantic.get("arguments")
    if not isinstance(raw_arguments, list) or not raw_arguments:
        raise ScientificAssertionProjectionV1Error(
            "candidate.semantic.arguments must be non-empty"
        )

    by_role: dict[str, Mapping[str, Any]] = {}
    for raw_argument in raw_arguments:
        if not isinstance(raw_argument, Mapping):
            raise ScientificAssertionProjectionV1Error(
                "candidate argument must be an object"
            )
        role = _require_nonempty_string(
            raw_argument.get("role"),
            "candidate argument role",
        )
        if role in by_role:
            raise ScientificAssertionProjectionV1Error(
                f"duplicate candidate argument role: {role}"
            )
        by_role[role] = raw_argument
    return by_role


def candidate_argument_sha256_v1(argument: Mapping[str, Any]) -> str:
    """Bind a human-reviewed mapping to one exact V2.11 argument."""
    return canonical_sha256(argument)


def _latest_review_event(
    events: Sequence[ClaimReviewEventsRow],
) -> ClaimReviewEventsRow:
    if not events:
        raise ScientificAssertionProjectionV1Error(
            "source Claim requires at least one human review event"
        )
    return max(events, key=lambda item: (item.reviewed_at, item.id))


def _effective_claim_sha256(
    claim: SourceClaimsRow,
    events: Sequence[ClaimReviewEventsRow],
) -> tuple[str, ClaimReviewEventsRow]:
    if _sha256_text(claim.claim_text) != claim.claim_text_sha256:
        raise ScientificAssertionProjectionV1Error(
            "source Claim claim_text_sha256 does not match claim_text"
        )

    ordered = sorted(events, key=lambda item: (item.reviewed_at, item.id))
    latest = _latest_review_event(ordered)
    if latest.claim_id != claim.id:
        raise ScientificAssertionProjectionV1Error(
            "latest Claim review belongs to a different Claim"
        )
    if latest.decision == "reject":
        raise ScientificAssertionProjectionV1Error(
            "latest source Claim review is rejected"
        )
    _require_nonempty_string(
        latest.reviewer,
        "latest source Claim reviewer",
    )

    effective_sha = claim.claim_text_sha256
    for event in ordered:
        if event.claim_id != claim.id:
            raise ScientificAssertionProjectionV1Error(
                "Claim review event belongs to a different Claim"
            )
        if event.decision not in {"accept", "correct", "reject"}:
            raise ScientificAssertionProjectionV1Error(
                f"invalid Claim review decision: {event.decision!r}"
            )
        if event.decision != "correct":
            continue
        corrected_text = _require_nonempty_string(
            event.corrected_text,
            "corrected Claim text",
        )
        corrected_sha = _require_sha256(
            event.corrected_text_sha256,
            "corrected Claim text SHA",
        )
        if _sha256_text(corrected_text) != corrected_sha:
            raise ScientificAssertionProjectionV1Error(
                "corrected Claim SHA does not match corrected text"
            )
        effective_sha = corrected_sha

    return effective_sha, latest


def _validate_claim_binding(
    candidate: Mapping[str, Any],
    claim: SourceClaimsRow,
    claim_reviews: Sequence[ClaimReviewEventsRow],
) -> dict[str, str]:
    source = _candidate_source(candidate)
    candidate_claim_id = _require_nonempty_string(
        source.get("source_statement_claim_id"),
        "candidate source Claim ID",
    )
    if candidate_claim_id != claim.id:
        raise ScientificAssertionProjectionV1Error(
            "candidate is linked to a different source Claim"
        )
    if claim.claim_layer != "atomic":
        raise ScientificAssertionProjectionV1Error(
            "scientific projection requires an atomic source Claim"
        )

    effective_sha, latest_review = _effective_claim_sha256(
        claim,
        claim_reviews,
    )
    candidate_effective_sha = _require_sha256(
        source.get("source_claim_effective_text_sha256"),
        "candidate source Claim effective-text SHA",
    )
    if candidate_effective_sha != effective_sha:
        raise ScientificAssertionProjectionV1Error(
            "candidate is stale against the reviewed source Claim effective text"
        )

    return {
        "claim_id": claim.id,
        "effective_text_sha256": effective_sha,
        "latest_review_id": latest_review.id,
        "latest_review_decision": latest_review.decision,
        "latest_reviewer": str(latest_review.reviewer),
    }


def _latest_segment_review(
    events: Sequence[SegmentReviewEventsRow],
) -> SegmentReviewEventsRow | None:
    if not events:
        return None
    return max(events, key=lambda item: (item.reviewed_at, item.id))


def _validate_evidence_binding(
    candidate: Mapping[str, Any],
    claim: SourceClaimsRow,
    claim_evidence_links: Sequence[ClaimEvidenceLinksRow],
    evidence_rows: Sequence[SourceEvidenceRow],
    segments: Mapping[str, SegmentsRow],
    segment_reviews: Mapping[str, Sequence[SegmentReviewEventsRow]],
) -> dict[str, object]:
    source = _candidate_source(candidate)
    raw_ids = source.get("evidence_ids")
    if (
        not isinstance(raw_ids, list)
        or not raw_ids
        or not all(isinstance(item, str) and item for item in raw_ids)
    ):
        raise ScientificAssertionProjectionV1Error(
            "candidate Evidence IDs must be non-empty strings"
        )
    candidate_ids = tuple(raw_ids)
    if list(candidate_ids) != sorted(set(candidate_ids)):
        raise ScientificAssertionProjectionV1Error(
            "candidate Evidence IDs must be sorted and unique"
        )

    links_by_evidence: dict[str, ClaimEvidenceLinksRow] = {}
    for link in claim_evidence_links:
        if link.claim_id != claim.id:
            continue
        if link.evidence_id in links_by_evidence:
            raise ScientificAssertionProjectionV1Error(
                f"duplicate Claim/Evidence link: {link.evidence_id}"
            )
        links_by_evidence[link.evidence_id] = link

    evidence_by_id: dict[str, SourceEvidenceRow] = {}
    for evidence in evidence_rows:
        if evidence.id in evidence_by_id:
            raise ScientificAssertionProjectionV1Error(
                f"duplicate Evidence row: {evidence.id}"
            )
        evidence_by_id[evidence.id] = evidence

    segment_ids: list[str] = []
    for evidence_id in candidate_ids:
        candidate_link = links_by_evidence.get(evidence_id)
        if candidate_link is None:
            raise ScientificAssertionProjectionV1Error(
                f"candidate Evidence is not linked to the atomic Claim: {evidence_id}"
            )
        if candidate_link.link_role != "supports_source_claim":
            raise ScientificAssertionProjectionV1Error(
                "candidate Evidence link has unsupported role: "
                f"{candidate_link.link_role}"
            )

        candidate_evidence = evidence_by_id.get(evidence_id)
        if candidate_evidence is None:
            raise ScientificAssertionProjectionV1Error(
                f"candidate Evidence row is missing: {evidence_id}"
            )
        segment = segments.get(candidate_evidence.segment_id)
        if segment is None:
            raise ScientificAssertionProjectionV1Error(
                f"Evidence segment is missing: {candidate_evidence.segment_id}"
            )
        if segment.review_status == "rejected":
            raise ScientificAssertionProjectionV1Error(
                f"Evidence segment is rejected: {segment.id}"
            )

        reviews = segment_reviews.get(segment.id, ())
        for review in reviews:
            if review.segment_id != segment.id:
                raise ScientificAssertionProjectionV1Error(
                    "segment review is attached to a different segment"
                )
        latest = _latest_segment_review(reviews)
        if latest is not None and latest.decision == "reject":
            raise ScientificAssertionProjectionV1Error(
                f"latest Evidence segment review is rejected: {segment.id}"
            )
        segment_ids.append(segment.id)

    return {
        "evidence_ids": list(candidate_ids),
        "segment_ids": sorted(set(segment_ids)),
    }


def _find_projection_spec(
    candidate: Mapping[str, Any],
) -> ProjectionSpecV1:
    semantic = _candidate_semantic(candidate)
    semantic_type = _require_nonempty_string(
        semantic.get("semantic_type"),
        "candidate semantic type",
    )
    relation = _require_nonempty_string(
        semantic.get("relation"),
        "candidate relation",
    )
    matches = [
        spec
        for spec in _PROJECTION_SPECS
        if spec.semantic_type == semantic_type and spec.relation == relation
    ]
    if len(matches) != 1:
        raise ScientificAssertionProjectionV1Error(
            "no exact Scientific Assertion Projection V1 mapping exists for "
            f"{semantic_type}/{relation}"
        )
    return matches[0]


def _validate_exact_role_signature(
    spec: ProjectionSpecV1,
    arguments: Mapping[str, Mapping[str, Any]],
) -> None:
    expected_roles = [role for role, _ in spec.role_classes]
    if set(arguments) != set(expected_roles):
        raise ScientificAssertionProjectionV1Error(
            "projection role signature does not exactly match the candidate"
        )
    if len(expected_roles) != len(set(expected_roles)):
        raise ScientificAssertionProjectionV1Error(
            "projection spec contains duplicate roles"
        )


def _validate_entity_resolution(
    role: str,
    argument: Mapping[str, Any],
    resolution: ReviewedEntityArgumentV1 | None,
) -> dict[str, object]:
    if argument.get("resolution_state") != "grounded_opaque_unresolved":
        raise ScientificAssertionProjectionV1Error(
            f"entity argument is not source-grounded for role: {role}"
        )
    argument_value = argument.get("value")
    if (
        not isinstance(argument_value, Mapping)
        or argument_value.get("kind") != "source_text"
    ):
        raise ScientificAssertionProjectionV1Error(
            f"entity argument must preserve source text for role: {role}"
        )
    if resolution is None:
        raise ScientificAssertionProjectionV1Error(
            f"human-reviewed entity mapping is required for role: {role}"
        )
    if resolution.role != role:
        raise ScientificAssertionProjectionV1Error(
            f"entity mapping role mismatch for: {role}"
        )
    expected_argument_sha = candidate_argument_sha256_v1(argument)
    if resolution.candidate_argument_sha256 != expected_argument_sha:
        raise ScientificAssertionProjectionV1Error(
            f"entity mapping is stale for candidate role: {role}"
        )
    if resolution.mapping_status not in _REVIEWED_MAPPING_STATUSES:
        raise ScientificAssertionProjectionV1Error(
            f"entity mapping is not exact/synonym for role: {role}"
        )
    if resolution.mapping_review_status != _REVIEW_CONFIRMED:
        raise ScientificAssertionProjectionV1Error(
            f"entity mapping is not human-reviewed for role: {role}"
        )
    _require_nonempty_string(
        resolution.reviewed_by,
        f"entity mapping reviewer for {role}",
    )
    _require_nonempty_string(
        resolution.entity_id,
        f"entity ID for {role}",
    )
    if (
        isinstance(resolution.entity_revision, bool)
        or not isinstance(resolution.entity_revision, int)
        or resolution.entity_revision < 1
    ):
        raise ScientificAssertionProjectionV1Error(
            f"entity revision must be >= 1 for role: {role}"
        )
    return entity_ref(
        resolution.entity_id,
        resolution.entity_revision,
    )


def _validate_numeric_argument(
    role: str,
    argument: Mapping[str, Any],
) -> dict[str, str]:
    if argument.get("resolution_state") != "resolved":
        raise ScientificAssertionProjectionV1Error(
            f"numeric grounding is unresolved for role: {role}"
        )
    value = argument.get("value")
    if not isinstance(value, Mapping):
        raise ScientificAssertionProjectionV1Error(
            f"numeric value must be typed for role: {role}"
        )
    kind = value.get("kind")
    if kind == "decimal":
        raw = value.get("value")
        if not isinstance(raw, str):
            raise ScientificAssertionProjectionV1Error(
                f"decimal value must be canonical text for role: {role}"
            )
        return decimal_value(raw)
    if kind == "integer":
        raw = value.get("value")
        if isinstance(raw, bool) or not isinstance(raw, int):
            raise ScientificAssertionProjectionV1Error(
                f"integer value must be an integer for role: {role}"
            )
        return decimal_value(raw)
    raise ScientificAssertionProjectionV1Error(
        f"unsupported exact numeric kind for role {role}: {kind!r}"
    )


def _validate_controlled_literal_argument(
    role: str,
    argument: Mapping[str, Any],
) -> str:
    if argument.get("resolution_state") != "resolved":
        raise ScientificAssertionProjectionV1Error(
            f"controlled literal is unresolved for role: {role}"
        )
    value = argument.get("value")
    if not isinstance(value, Mapping):
        raise ScientificAssertionProjectionV1Error(
            f"controlled literal must be typed for role: {role}"
        )
    if value.get("kind") != "controlled_literal":
        raise ScientificAssertionProjectionV1Error(
            f"role is not a controlled literal: {role}"
        )
    return _require_nonempty_string(
        value.get("value"),
        f"controlled literal value for {role}",
    )


def _validate_context_resolution(
    role: str,
    argument: Mapping[str, Any],
    resolution: ReviewedContextArgumentV1 | None,
) -> str:
    if resolution is None:
        raise ScientificAssertionProjectionV1Error(
            f"human-reviewed context mapping is required for role: {role}"
        )
    if resolution.role != role:
        raise ScientificAssertionProjectionV1Error(
            f"context mapping role mismatch for: {role}"
        )
    if (
        resolution.candidate_argument_sha256
        != candidate_argument_sha256_v1(argument)
    ):
        raise ScientificAssertionProjectionV1Error(
            f"context mapping is stale for candidate role: {role}"
        )
    if resolution.mapping_review_status != _REVIEW_CONFIRMED:
        raise ScientificAssertionProjectionV1Error(
            f"context mapping is not human-reviewed for role: {role}"
        )
    _require_nonempty_string(
        resolution.reviewed_by,
        f"context mapping reviewer for {role}",
    )
    return _require_nonempty_string(
        resolution.canonical_value,
        f"canonical context value for {role}",
    )


def _build_maintained_at_measurement(
    *,
    spec: ProjectionSpecV1,
    candidate: Mapping[str, Any],
    arguments: Mapping[str, Mapping[str, Any]],
    entity_resolutions: Mapping[str, ReviewedEntityArgumentV1],
    context_resolutions: Mapping[str, ReviewedContextArgumentV1],
) -> tuple[dict[str, Any], str]:
    if spec.spec_id != "maintained_at.measurement.v1":
        raise ScientificAssertionProjectionV1Error(
            f"unsupported reviewed projection spec: {spec.spec_id}"
        )

    variable = _validate_entity_resolution(
        "variable",
        arguments["variable"],
        entity_resolutions.get("variable"),
    )
    amount = _validate_numeric_argument(
        "value",
        arguments["value"],
    )
    unit = _validate_controlled_literal_argument(
        "unit",
        arguments["unit"],
    )
    if context_resolutions:
        raise ScientificAssertionProjectionV1Error(
            "maintained_at projection accepts no context reconstruction"
        )

    semantic = _candidate_semantic(candidate)
    payload = canonical_assertion_payload(
        assertion_kind=spec.assertion_kind,
        predicate=spec.predicate,
        participants=[
            {
                "role": "variable",
                "entity": variable,
            }
        ],
        value={
            "kind": "measurement",
            "amount": amount,
            "unit": unit,
        },
        qualifiers={
            "semantic_type": semantic["semantic_type"],
        },
    )

    entity_id = variable["entity_id"]
    entity_revision = variable["entity_revision"]
    amount_text = amount["value"]
    normalized_text = (
        f'{spec.predicate}('
        f'variable=entity_ref("{entity_id}",{entity_revision}), '
        f"value={amount_text}, "
        f"unit={json.dumps(unit, ensure_ascii=False)}"
        ")"
    )
    return payload, normalized_text


def _build_binary_entity_relation(
    *,
    spec: ProjectionSpecV1,
    candidate: Mapping[str, Any],
    arguments: Mapping[str, Mapping[str, Any]],
    entity_resolutions: Mapping[str, ReviewedEntityArgumentV1],
    context_resolutions: Mapping[str, ReviewedContextArgumentV1],
) -> tuple[dict[str, Any], str]:
    if spec.builder != "binary_entity_relation_v1":
        raise ScientificAssertionProjectionV1Error(
            f"unsupported binary entity projection spec: {spec.spec_id}"
        )
    if context_resolutions:
        raise ScientificAssertionProjectionV1Error(
            "binary entity relation accepts no context reconstruction"
        )
    cause = _validate_entity_resolution(
        "cause", arguments["cause"], entity_resolutions.get("cause")
    )
    target = _validate_entity_resolution(
        "target", arguments["target"], entity_resolutions.get("target")
    )
    semantic = _candidate_semantic(candidate)
    payload = canonical_assertion_payload(
        assertion_kind=spec.assertion_kind,
        predicate=spec.predicate,
        participants=[
            {"role": "cause", "entity": cause},
            {"role": "target", "entity": target},
        ],
        value={"kind": "none"},
        qualifiers={"semantic_type": semantic["semantic_type"]},
    )
    normalized_text = (
        f'{spec.predicate}('
        f'cause=entity_ref("{cause["entity_id"]}",{cause["entity_revision"]}), '
        f'target=entity_ref("{target["entity_id"]}",{target["entity_revision"]})'
        ")"
    )
    return payload, normalized_text


def _build_spec_binary_entity_relation(
    *,
    spec: ProjectionSpecV1,
    candidate: Mapping[str, Any],
    arguments: Mapping[str, Mapping[str, Any]],
    entity_resolutions: Mapping[str, ReviewedEntityArgumentV1],
    context_resolutions: Mapping[str, ReviewedContextArgumentV1],
) -> tuple[dict[str, Any], str]:
    if spec.builder != "spec_binary_entity_relation_v1":
        raise ScientificAssertionProjectionV1Error(
            f"unsupported spec-binary entity projection spec: {spec.spec_id}"
        )
    if context_resolutions:
        raise ScientificAssertionProjectionV1Error(
            "spec-binary entity relation accepts no context reconstruction"
        )
    if (
        len(spec.role_classes) != 2
        or any(
            role_class != ENTITY_ARGUMENT
            for _, role_class in spec.role_classes
        )
    ):
        raise ScientificAssertionProjectionV1Error(
            "spec-binary entity relation requires exactly two ENTITY_ARGUMENT roles"
        )

    participants: list[dict[str, object]] = []
    for role, _ in spec.role_classes:
        entity = _validate_entity_resolution(
            role,
            arguments[role],
            entity_resolutions.get(role),
        )
        participants.append({"role": role, "entity": entity})

    semantic = _candidate_semantic(candidate)
    payload = canonical_assertion_payload(
        assertion_kind=spec.assertion_kind,
        predicate=spec.predicate,
        participants=participants,
        value={"kind": "none"},
        qualifiers={"semantic_type": semantic["semantic_type"]},
    )

    canonical_participants = payload.get("participants")
    if (
        not isinstance(canonical_participants, list)
        or len(canonical_participants) != 2
    ):
        raise ScientificAssertionProjectionV1Error(
            "canonical spec-binary relation must contain exactly two participants"
        )

    normalized_parts: list[str] = []
    for participant in canonical_participants:
        if not isinstance(participant, Mapping):
            raise ScientificAssertionProjectionV1Error(
                "canonical participant must be an object"
            )
        role = _require_nonempty_string(
            participant.get("role"),
            "canonical participant role",
        )
        participant_entity = participant.get("entity")
        if not isinstance(participant_entity, Mapping):
            raise ScientificAssertionProjectionV1Error(
                f"canonical participant entity is invalid for role: {role}"
            )
        entity_id = _require_nonempty_string(
            participant_entity.get("entity_id"),
            f"canonical participant entity ID for {role}",
        )
        revision = participant_entity.get("entity_revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 1
        ):
            raise ScientificAssertionProjectionV1Error(
                f"canonical participant entity revision is invalid for role: {role}"
            )
        normalized_parts.append(
            f'{role}=entity_ref("{entity_id}",{revision})'
        )

    normalized_text = (
        f"{spec.predicate}(" + ", ".join(normalized_parts) + ")"
    )
    return payload, normalized_text


def project_scientific_assertion_v1(
    candidate: Mapping[str, Any],
    *,
    source_claim: SourceClaimsRow,
    claim_reviews: Sequence[ClaimReviewEventsRow],
    candidate_reviews: Sequence[SemanticCandidateReviewEventsRow],
    claim_evidence_links: Sequence[ClaimEvidenceLinksRow],
    evidence_rows: Sequence[SourceEvidenceRow],
    segments: Mapping[str, SegmentsRow],
    segment_reviews: Mapping[str, Sequence[SegmentReviewEventsRow]],
    entity_resolutions: Mapping[str, ReviewedEntityArgumentV1],
    context_resolutions: Mapping[str, ReviewedContextArgumentV1] | None = None,
) -> dict[str, Any]:
    """Project one reviewed V2.11 candidate or fail closed without persistence."""
    validate_semantic_candidate_v2_11(candidate)
    try:
        candidate_review_trace = require_candidate_acceptance_v1(
            candidate,
            candidate_reviews,
        )
    except SemanticCandidateReviewV1Error as exc:
        raise ScientificAssertionProjectionV1Error(str(exc)) from exc

    claim_trace = _validate_claim_binding(
        candidate,
        source_claim,
        claim_reviews,
    )
    evidence_trace = _validate_evidence_binding(
        candidate,
        source_claim,
        claim_evidence_links,
        evidence_rows,
        segments,
        segment_reviews,
    )
    spec = _find_projection_spec(candidate)
    arguments = _candidate_arguments(candidate)
    _validate_exact_role_signature(spec, arguments)

    class_by_role = dict(spec.role_classes)
    for role, argument in arguments.items():
        role_class = class_by_role[role]
        if role_class == ENTITY_ARGUMENT:
            _validate_entity_resolution(
                role,
                argument,
                entity_resolutions.get(role),
            )
        elif role_class == EXACT_NUMERIC_ARGUMENT:
            _validate_numeric_argument(role, argument)
        elif role_class == CONTROLLED_LITERAL_ARGUMENT:
            _validate_controlled_literal_argument(role, argument)
        elif role_class == CONTEXT_ARGUMENT:
            _validate_context_resolution(
                role,
                argument,
                (context_resolutions or {}).get(role),
            )
        else:
            raise ScientificAssertionProjectionV1Error(
                f"unsupported projection role class: {role_class}"
            )

    unused_entity_roles = set(entity_resolutions) - {
        role
        for role, role_class in spec.role_classes
        if role_class == ENTITY_ARGUMENT
    }
    if unused_entity_roles:
        raise ScientificAssertionProjectionV1Error(
            "cross-Claim or extra entity reconstruction is forbidden: "
            f"{sorted(unused_entity_roles)}"
        )

    supplied_context = context_resolutions or {}
    unused_context_roles = set(supplied_context) - {
        role
        for role, role_class in spec.role_classes
        if role_class == CONTEXT_ARGUMENT
    }
    if unused_context_roles:
        raise ScientificAssertionProjectionV1Error(
            "cross-Claim or extra context reconstruction is forbidden: "
            f"{sorted(unused_context_roles)}"
        )

    if spec.builder == "maintained_at_measurement_v1":
        assertion_payload, normalized_text = _build_maintained_at_measurement(
            spec=spec,
            candidate=candidate,
            arguments=arguments,
            entity_resolutions=entity_resolutions,
            context_resolutions=supplied_context,
        )
    elif spec.builder == "binary_entity_relation_v1":
        assertion_payload, normalized_text = _build_binary_entity_relation(
            spec=spec,
            candidate=candidate,
            arguments=arguments,
            entity_resolutions=entity_resolutions,
            context_resolutions=supplied_context,
        )
    elif spec.builder == "spec_binary_entity_relation_v1":
        assertion_payload, normalized_text = _build_spec_binary_entity_relation(
            spec=spec,
            candidate=candidate,
            arguments=arguments,
            entity_resolutions=entity_resolutions,
            context_resolutions=supplied_context,
        )
    else:
        raise ScientificAssertionProjectionV1Error(
            f"unsupported reviewed projection builder: {spec.builder}"
        )
    assertion_sha = canonical_sha256(assertion_payload)

    candidate_sha = _require_sha256(
        candidate.get("canonical_candidate_sha256"),
        "candidate canonical SHA",
    )
    projection_audit = {
        "projection_contract_sha256": PROJECTION_CONTRACT_SHA256,
        "entity_resolution_policy_sha256": ENTITY_RESOLUTION_POLICY_SHA256,
        "projection_spec_id": spec.spec_id,
        "semantic_candidate_sha256": candidate_sha,
        "candidate_review_id": candidate_review_trace["review_id"],
        "candidate_review_policy_sha256": candidate_review_trace["review_policy_sha256"],
        "source_claim_id": source_claim.id,
        "source_claim_effective_text_sha256": claim_trace[
            "effective_text_sha256"
        ],
        "claim_review_id": claim_trace["latest_review_id"],
        "evidence_ids": evidence_trace["evidence_ids"],
        "entity_argument_sha256": {
            role: resolution.candidate_argument_sha256
            for role, resolution in sorted(entity_resolutions.items())
        },
        "context_argument_sha256": {
            role: resolution.candidate_argument_sha256
            for role, resolution in sorted(supplied_context.items())
        },
        "scientific_assertion_payload_sha256": assertion_sha,
    }

    result = {
        "schema_version": PROJECTION_SCHEMA_VERSION,
        "contract": {
            "name": PROJECTION_CONTRACT_NAME,
            "version": PROJECTION_CONTRACT_VERSION,
            "canonical_sha256": PROJECTION_CONTRACT_SHA256,
            "entity_resolution_policy_sha256": ENTITY_RESOLUTION_POLICY_SHA256,
            "projection_spec_id": spec.spec_id,
        },
        "source": {
            "semantic_candidate_sha256": candidate_sha,
            "candidate_review_id": candidate_review_trace["review_id"],
            "candidate_reviewer": candidate_review_trace["reviewer"],
            "candidate_review_policy_sha256": candidate_review_trace["review_policy_sha256"],
            "source_claim_id": source_claim.id,
            "source_claim_effective_text_sha256": claim_trace[
                "effective_text_sha256"
            ],
            "claim_review_id": claim_trace["latest_review_id"],
            "claim_review_decision": claim_trace[
                "latest_review_decision"
            ],
            "evidence_ids": evidence_trace["evidence_ids"],
            "segment_ids": evidence_trace["segment_ids"],
        },
        "assertion": {
            "payload": assertion_payload,
            "canonical_payload_sha256": assertion_sha,
            "normalized_text": normalized_text,
        },
        "claim_link_proposal": {
            "claim_id": source_claim.id,
            "stance": "supports",
            "support_mode": "unknown",
            "scope_alignment": "exact",
            "semantic_alignment": "exact",
            "requires_persistence_review": True,
        },
        "projection_audit_sha256": canonical_sha256(projection_audit),
        "projection_gate_passed": True,
        "automatic_persistence": False,
    }
    canonical_json_text(result)
    return result
