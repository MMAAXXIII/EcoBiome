"""Fail-closed V2.8 relation/type contract helpers for EcoBiome.

V2.8 is an overlay on the frozen V2.7 semantic relation registry. It does not
rewrite or supersede the V2.7 artifact in place.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

RELATION_TYPE_CONTRACT_V2_8_CANONICAL_SHA256 = (
    "0abdc1b33682b52cac65c7c081dddafe36f303735deeea81436739b4522b848e"
)

_ALLOWED_STATES = {
    "constrained_existing_v2_7",
    "constrained_reviewed_singleton_v2_8",
    "unresolved_blocked",
}


def canonical_json_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_relation_type_contract_v2_8(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_relation_type_contract_v2_8(payload)
    return payload


def validate_relation_type_contract_v2_8(
    contract: Any,
) -> dict[str, Any]:
    if not isinstance(contract, dict):
        raise TypeError("V2.8 relation/type contract must be an object")

    actual_sha = canonical_json_sha256(contract)
    if actual_sha != RELATION_TYPE_CONTRACT_V2_8_CANONICAL_SHA256:
        raise ValueError(
            "unsupported V2.8 relation/type contract SHA-256: "
            f"{actual_sha}; expected "
            f"{RELATION_TYPE_CONTRACT_V2_8_CANONICAL_SHA256}"
        )

    relations = contract.get("relations")
    if not isinstance(relations, dict) or len(relations) != 63:
        raise ValueError("V2.8 contract must contain exactly 63 relations")

    counts = {
        "constrained_existing_v2_7": 0,
        "constrained_reviewed_singleton_v2_8": 0,
        "unresolved_blocked": 0,
    }

    for relation, spec in relations.items():
        if not isinstance(relation, str) or not relation:
            raise ValueError("V2.8 relation identifier must be non-empty")
        if not isinstance(spec, dict):
            raise TypeError(f"V2.8 relation spec malformed: {relation}")

        state = spec.get("state")
        allowed = spec.get("semantic_types_allowed")

        if state not in _ALLOWED_STATES:
            raise ValueError(
                f"V2.8 relation {relation!r} has unsupported state {state!r}"
            )
        if (
            not isinstance(allowed, list)
            or not all(isinstance(item, str) and item for item in allowed)
            or len(allowed) != len(set(allowed))
        ):
            raise ValueError(
                f"V2.8 relation {relation!r} has malformed allowed types"
            )

        if state == "unresolved_blocked" and allowed:
            raise ValueError(
                f"V2.8 unresolved relation {relation!r} must fail closed"
            )
        if state != "unresolved_blocked" and not allowed:
            raise ValueError(
                f"V2.8 constrained relation {relation!r} needs an allowed type"
            )

        counts[state] += 1

    expected = contract.get("counts")
    if not isinstance(expected, dict):
        raise TypeError("V2.8 contract counts missing")

    if counts != {
        "constrained_existing_v2_7":
            expected.get("constrained_existing_v2_7"),
        "constrained_reviewed_singleton_v2_8":
            expected.get("constrained_reviewed_singleton_v2_8"),
        "unresolved_blocked":
            expected.get("unresolved_blocked"),
    }:
        raise ValueError("V2.8 relation-state counts do not match payload")

    if sum(counts.values()) != expected.get("relations_total"):
        raise ValueError("V2.8 total relation count does not match payload")

    return contract


def apply_relation_type_contract_v2_8(
    registry_v2_7: dict[str, Any],
    contract_v2_8: dict[str, Any],
) -> dict[str, Any]:
    """Return a V2.8 registry view without mutating the frozen V2.7 object."""
    validate_relation_type_contract_v2_8(contract_v2_8)

    relations = registry_v2_7.get("relations")
    semantic_types = registry_v2_7.get("semantic_types")
    if not isinstance(relations, dict):
        raise TypeError("V2.7 registry relations malformed")
    if not isinstance(semantic_types, list):
        raise TypeError("V2.7 registry semantic_types malformed")

    contract_relations = contract_v2_8["relations"]
    if set(relations) != set(contract_relations):
        raise ValueError(
            "V2.8 contract relation set differs from frozen V2.7 registry"
        )

    semantic_type_ids = {
        str(item)
        for item in semantic_types
        if isinstance(item, str)
    }

    merged = copy.deepcopy(registry_v2_7)
    merged_relations = merged["relations"]

    for relation, contract_spec in contract_relations.items():
        base_spec = relations[relation]
        if not isinstance(base_spec, dict):
            raise TypeError(f"V2.7 relation malformed: {relation}")

        state = contract_spec["state"]
        allowed = list(contract_spec["semantic_types_allowed"])

        if any(item not in semantic_type_ids for item in allowed):
            raise ValueError(
                f"V2.8 relation {relation!r} references unknown semantic type"
            )

        existing_allowed = base_spec.get("semantic_types_allowed")
        if state == "constrained_existing_v2_7":
            if existing_allowed != allowed:
                raise ValueError(
                    f"V2.8 changed frozen V2.7 constraint for {relation!r}"
                )
        else:
            if isinstance(existing_allowed, list):
                raise ValueError(
                    f"V2.8 expected open V2.7 relation for {relation!r}"
                )

        merged_relations[relation]["semantic_types_allowed"] = allowed
        merged_relations[relation]["semantic_type_contract_state"] = state

    merged["registry_overlay"] = {
        "base": "v2.7",
        "relation_type_contract": "v2.8",
        "relation_type_contract_canonical_sha256":
            RELATION_TYPE_CONTRACT_V2_8_CANONICAL_SHA256,
        "fail_closed_unresolved_relations": True,
    }
    return merged


def relation_semantic_type_decision_v2_8(
    registry_v2_8: dict[str, Any],
    relation: str,
    semantic_type: str,
) -> dict[str, Any]:
    relations = registry_v2_8.get("relations")
    if not isinstance(relations, dict):
        raise TypeError("V2.8 registry relations malformed")

    spec = relations.get(relation)
    if not isinstance(spec, dict):
        return {
            "accepted": False,
            "state": "unknown_relation",
            "relation": relation,
            "semantic_type": semantic_type,
        }

    contract_state = spec.get("semantic_type_contract_state")
    allowed = spec.get("semantic_types_allowed")

    if not isinstance(allowed, list):
        return {
            "accepted": False,
            "state": "missing_explicit_contract",
            "relation": relation,
            "semantic_type": semantic_type,
        }

    if contract_state == "unresolved_blocked":
        return {
            "accepted": False,
            "state": "unresolved_blocked",
            "relation": relation,
            "semantic_type": semantic_type,
            "allowed": [],
        }

    if semantic_type not in allowed:
        return {
            "accepted": False,
            "state": "relation_semantic_type_incompatible",
            "relation": relation,
            "semantic_type": semantic_type,
            "allowed": allowed,
        }

    return {
        "accepted": True,
        "state": "allowed",
        "relation": relation,
        "semantic_type": semantic_type,
        "allowed": allowed,
    }
