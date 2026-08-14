"""Deterministic V2.6 epistemic and coordinated-span controls for EcoBiome."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

REGISTRY_V2_6_SHA256 = "46e768e56310c2f48efb4fe9b1f62b94c65ff38b5aeba97ea5d204cd4d9a3ce7"
EPISTEMIC_POLICY_V1_SHA256 = "1b4b25aca3cf57f1ed2c02b1fa27cf2208961d1b7c3d9b15508f7fea39852b2c"


def _canonical_sha(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def validate_registry_v2_6(registry: Any) -> dict[str, Any]:
    if not isinstance(registry, dict):
        raise TypeError("V2.6 registry must be an object")
    actual = _canonical_sha(registry)
    if actual != REGISTRY_V2_6_SHA256:
        raise ValueError(f"unexpected V2.6 registry SHA: {actual}")
    return registry


def validate_epistemic_policy(policy: Any) -> dict[str, Any]:
    if not isinstance(policy, dict):
        raise TypeError("epistemic policy must be an object")
    actual = _canonical_sha(policy)
    if actual != EPISTEMIC_POLICY_V1_SHA256:
        raise ValueError(f"unexpected epistemic policy SHA: {actual}")
    return policy


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _has_coordination(text: str, policy: dict[str, Any]) -> bool:
    normalized = _normalize(text)
    patterns = policy["coordinated_span_policy"]["coordination_patterns"]
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in patterns)


def coordinated_span_state(
    role: str,
    surface: str,
    source_text: str,
    policy: Any,
) -> dict[str, Any]:
    validated = validate_epistemic_policy(policy)
    grounded = bool(_normalize(surface)) and _normalize(surface) in _normalize(source_text)
    coordinated = _has_coordination(surface, validated)

    if not grounded:
        state = "ungrounded"
    elif not coordinated:
        state = "grounded_scalar_unresolved"
    elif role not in set(validated["coordinated_span_policy"]["eligible_roles"]):
        state = "role_cardinality_conflict"
    else:
        state = "grounded_coordinated_unresolved"

    return {
        "state": state,
        "role": role,
        "surface": surface,
        "source_grounded": grounded,
        "coordinated": coordinated,
        "scientifically_scoreable": False,
    }


def relation_epistemic_class(
    registry: Any,
    relation: str,
) -> str | None:
    validated = validate_registry_v2_6(registry)
    spec = validated["relations"].get(relation)
    if not isinstance(spec, dict):
        return None
    value = spec.get("epistemic_class")
    return value if isinstance(value, str) else None


def classify_epistemic_transition(
    expected_class: str,
    candidate_class: str,
    policy: Any,
) -> dict[str, Any]:
    validated = validate_epistemic_policy(policy)
    known = set(validated["epistemic_policy"]["known_classes"])
    if expected_class not in known:
        raise ValueError(f"unknown expected epistemic class: {expected_class}")
    if candidate_class not in known:
        raise ValueError(f"unknown candidate epistemic class: {candidate_class}")

    forbidden = {
        (item["expected"], item["candidate"])
        for item in validated["epistemic_policy"]["forbidden_upgrades"]
    }
    if expected_class == candidate_class:
        status = "compatible_same_class"
        blocking = False
    elif (expected_class, candidate_class) in forbidden:
        status = "epistemic_overclaim"
        blocking = True
    else:
        status = "different_not_ordered"
        blocking = False

    return {
        "expected_class": expected_class,
        "candidate_class": candidate_class,
        "status": status,
        "blocking": blocking,
        "entailed_by_class_alone": False,
    }


def _fixture_arrays(fixture: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(fixture, dict):
        raise TypeError("fixture must be an object")
    required = fixture.get("required_propositions", fixture.get("required_in_registry", []))
    admissible = fixture.get("admissible_propositions", fixture.get("admissible", []))
    if not isinstance(required, list) or not isinstance(admissible, list):
        raise TypeError("fixture proposition arrays must be lists")
    return required, admissible


def audit_epistemic_overclaims(
    candidate_payload: Any,
    fixture: Any,
    registry: Any,
    policy: Any,
) -> dict[str, Any]:
    validated_registry = validate_registry_v2_6(registry)
    validated_policy = validate_epistemic_policy(policy)
    required, admissible = _fixture_arrays(fixture)
    gold = [*required, *admissible]

    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in gold:
        if not isinstance(item, dict):
            continue
        claim_id = item.get("source_claim_id")
        semantic_type = item.get("semantic_type")
        meaning = item.get("meaning")
        if isinstance(claim_id, str) and isinstance(semantic_type, str) and isinstance(meaning, dict):
            groups.setdefault((claim_id, semantic_type), []).append(item)

    proposals = candidate_payload.get("proposals", []) if isinstance(candidate_payload, dict) else []
    violations: list[dict[str, Any]] = []

    for index, proposal in enumerate(proposals):
        if not isinstance(proposal, dict):
            continue
        claim_id = proposal.get("source_claim_id")
        semantic_type = proposal.get("semantic_type")
        meaning = proposal.get("benchmark_meaning")
        if not isinstance(claim_id, str) or not isinstance(semantic_type, str) or not isinstance(meaning, dict):
            continue
        candidate_relation = meaning.get("relation")
        if not isinstance(candidate_relation, str):
            continue

        candidate_class = relation_epistemic_class(validated_registry, candidate_relation)
        if candidate_class is None:
            continue

        group = groups.get((claim_id, semantic_type), [])
        exact_relation_exists = any(
            isinstance(item.get("meaning"), dict)
            and item["meaning"].get("relation") == candidate_relation
            for item in group
        )
        if exact_relation_exists:
            continue

        seen: set[tuple[str, str, str]] = set()
        for item in group:
            expected_relation = item["meaning"].get("relation")
            if not isinstance(expected_relation, str):
                continue
            expected_class = relation_epistemic_class(validated_registry, expected_relation)
            if expected_class is None:
                continue
            transition = classify_epistemic_transition(
                expected_class,
                candidate_class,
                validated_policy,
            )
            if transition["status"] != "epistemic_overclaim":
                continue
            key = (str(item.get("id")), expected_relation, candidate_relation)
            if key in seen:
                continue
            seen.add(key)
            violations.append(
                {
                    "candidate_index": index,
                    "gold_id": item.get("id"),
                    "source_claim_id": claim_id,
                    "semantic_type": semantic_type,
                    "expected_relation": expected_relation,
                    "candidate_relation": candidate_relation,
                    **transition,
                }
            )

    return {
        "violation_count": len(violations),
        "violations": violations,
        "blocking": bool(violations),
    }


def audit_coordinated_arguments(
    candidate_payload: Any,
    semantic_export: Any,
    registry: Any,
    policy: Any,
) -> dict[str, Any]:
    validated_registry = validate_registry_v2_6(registry)
    validated_policy = validate_epistemic_policy(policy)

    claims_value = semantic_export.get("source_claims", []) if isinstance(semantic_export, dict) else []
    claims = {
        item.get("claim_id"): item
        for item in claims_value
        if isinstance(item, dict) and isinstance(item.get("claim_id"), str)
    }

    proposals = candidate_payload.get("proposals", []) if isinstance(candidate_payload, dict) else []
    diagnostics: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []

    for index, proposal in enumerate(proposals):
        if not isinstance(proposal, dict):
            continue
        claim_id = proposal.get("source_claim_id")
        meaning = proposal.get("benchmark_meaning")
        if claim_id not in claims or not isinstance(meaning, dict):
            continue
        relation = meaning.get("relation")
        arguments = meaning.get("arguments")
        spec = validated_registry["relations"].get(relation)
        if not isinstance(spec, dict) or not isinstance(arguments, dict):
            continue
        source_text = claims[claim_id].get("effective_text")
        if not isinstance(source_text, str):
            continue

        for role, value in arguments.items():
            if not isinstance(value, str) or not _has_coordination(value, validated_policy):
                continue
            record = coordinated_span_state(role, value, source_text, validated_policy)
            item = {
                "candidate_index": index,
                "source_claim_id": claim_id,
                "relation": relation,
                **record,
            }
            diagnostics.append(item)
            if record["state"] == "role_cardinality_conflict":
                conflicts.append(item)

    return {
        "diagnostic_count": len(diagnostics),
        "diagnostics": diagnostics,
        "role_cardinality_conflict_count": len(conflicts),
        "role_cardinality_conflicts": conflicts,
        "blocking": bool(conflicts),
    }
