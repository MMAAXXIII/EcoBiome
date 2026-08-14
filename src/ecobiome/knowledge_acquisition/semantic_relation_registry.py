"""Source-independent structured semantic relation registry utilities.

This module is benchmark infrastructure. It validates a versioned relation
registry, builds the provider-facing compact JSON Schema, and scores structural
provider defects without embedding source-specific categorical values.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

_ALLOWED_ROLE_TYPES = {"string", "integer", "number"}


def canonical_payload_sha256(payload: object) -> str:
    """Return SHA-256 of canonical UTF-8 JSON for a JSON-compatible payload."""
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_registry(registry: Any) -> dict[str, Any]:
    """Validate registry infrastructure.

    Registry corruption is an infrastructure failure and therefore raises.
    Provider-output defects are handled separately by the tolerant validators.
    """
    if not isinstance(registry, dict):
        raise TypeError("semantic relation registry must be an object")

    semantic_types = registry.get("semantic_types")
    argument_roles = registry.get("argument_roles")
    relations = registry.get("relations")

    if (
        not isinstance(semantic_types, list)
        or not semantic_types
        or not all(isinstance(item, str) and item for item in semantic_types)
    ):
        raise TypeError("registry semantic_types must be a non-empty list of strings")
    if len(semantic_types) != len(set(semantic_types)):
        raise ValueError("registry semantic_types contain duplicates")

    if not isinstance(argument_roles, dict) or not argument_roles:
        raise TypeError("registry argument_roles must be a non-empty object")
    for role, spec in argument_roles.items():
        if not isinstance(role, str) or not role or not isinstance(spec, dict):
            raise TypeError("registry argument role entries are malformed")
        if "enum" in spec:
            raise ValueError(f"argument role {role!r} must not contain an enum")
        expected_type = spec.get("type")
        if expected_type not in _ALLOWED_ROLE_TYPES:
            raise ValueError(
                f"argument role {role!r} has unsupported type: {expected_type!r}"
            )
        allowed_keys = {"type"}
        if expected_type == "string":
            allowed_keys.add("minLength")
            minimum = spec.get("minLength", 1)
            if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
                raise ValueError(
                    f"argument role {role!r} has invalid string minLength"
                )
        if set(spec) - allowed_keys:
            raise ValueError(f"argument role {role!r} has unsupported schema keys")

    if not isinstance(relations, dict) or not relations:
        raise TypeError("registry relations must be a non-empty object")
    for relation, spec in relations.items():
        if not isinstance(relation, str) or not relation or not isinstance(spec, dict):
            raise TypeError("registry relation entries are malformed")
        if set(spec) != {"argument_keys"}:
            raise ValueError(f"relation {relation!r} has unsupported fields")
        keys = spec.get("argument_keys")
        if not isinstance(keys, list) or not all(
            isinstance(key, str) and key for key in keys
        ):
            raise TypeError(f"relation {relation!r} argument_keys are malformed")
        if len(keys) != len(set(keys)):
            raise ValueError(f"relation {relation!r} contains duplicate argument roles")
        unknown = sorted(set(keys) - set(argument_roles))
        if unknown:
            raise ValueError(
                f"relation {relation!r} references unknown argument roles: {unknown}"
            )

    return registry


def build_source_independent_wire_schema(registry: Any) -> dict[str, object]:
    """Build the compact relation-conditioned JSON Schema from a registry."""
    validated = validate_registry(registry)
    semantic_types = validated["semantic_types"]
    argument_roles = validated["argument_roles"]
    relations = validated["relations"]

    branches: list[dict[str, object]] = []
    for relation in sorted(relations):
        relation_spec = relations[relation]
        keys = relation_spec["argument_keys"]
        properties = {key: dict(argument_roles[key]) for key in keys}
        branches.append(
            {
                "type": "object",
                "properties": {
                    "r": {"const": relation},
                    "a": {
                        "type": "object",
                        "properties": properties,
                        "required": list(keys),
                        "additionalProperties": False,
                    },
                },
                "required": ["r", "a"],
                "additionalProperties": False,
            }
        )

    return {
        "type": "object",
        "properties": {
            "p": {
                "type": "array",
                "maxItems": 100,
                "items": {
                    "type": "object",
                    "properties": {
                        "c": {"type": "string", "minLength": 1},
                        "t": {"type": "string", "enum": list(semantic_types)},
                        "e": {
                            "type": "array",
                            "minItems": 1,
                            "uniqueItems": True,
                            "items": {"type": "string", "minLength": 1},
                        },
                        "m": {"oneOf": branches},
                    },
                    "required": ["c", "t", "e", "m"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["p"],
        "additionalProperties": False,
    }


def _value_matches_spec(value: object, spec: dict[str, object]) -> bool:
    expected_type = spec.get("type")
    if expected_type == "string":
        if not isinstance(value, str):
            return False
        minimum = spec.get("minLength", 1)
        return isinstance(minimum, int) and len(value) >= minimum
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    raise ValueError(f"unsupported registry role type: {expected_type!r}")


def validate_meaning(
    meaning: Any,
    registry: Any,
) -> list[dict[str, object]]:
    """Return structural issues in one compact meaning without raising on provider defects."""
    validated = validate_registry(registry)
    issues: list[dict[str, object]] = []

    if not isinstance(meaning, dict):
        return [{"kind": "meaning_not_object"}]

    if set(meaning) != {"r", "a"}:
        issues.append(
            {
                "kind": "meaning_keys_mismatch",
                "expected": ["a", "r"],
                "actual": sorted(str(key) for key in meaning),
            }
        )

    relation = meaning.get("r")
    arguments = meaning.get("a")
    relations = validated["relations"]
    argument_roles = validated["argument_roles"]

    if not isinstance(relation, str) or relation not in relations:
        issues.append({"kind": "unsupported_relation", "relation": relation})
        return issues
    if not isinstance(arguments, dict):
        issues.append({"kind": "arguments_not_object"})
        return issues

    expected_keys = relations[relation]["argument_keys"]
    if set(arguments) != set(expected_keys):
        issues.append(
            {
                "kind": "argument_keys_mismatch",
                "relation": relation,
                "expected": sorted(expected_keys),
                "actual": sorted(str(key) for key in arguments),
            }
        )

    for key, value in arguments.items():
        if not isinstance(key, str) or key not in argument_roles:
            issues.append({"kind": "unknown_argument_role", "key": repr(key)})
            continue
        if not _value_matches_spec(value, argument_roles[key]):
            issues.append(
                {
                    "kind": "invalid_argument_type",
                    "key": key,
                    "value": value,
                }
            )

    return issues


def validate_compact_proposal(
    proposal: Any,
    registry: Any,
) -> list[dict[str, object]]:
    """Return provider-contract issues for one compact proposal."""
    validated = validate_registry(registry)
    issues: list[dict[str, object]] = []

    if not isinstance(proposal, dict):
        return [{"kind": "proposal_not_object"}]

    expected_keys = {"c", "t", "e", "m"}
    if set(proposal) != expected_keys:
        issues.append(
            {
                "kind": "proposal_keys_mismatch",
                "expected": sorted(expected_keys),
                "actual": sorted(str(key) for key in proposal),
            }
        )

    claim_id = proposal.get("c")
    semantic_type = proposal.get("t")
    evidence_ids = proposal.get("e")

    if not isinstance(claim_id, str) or not claim_id:
        issues.append({"kind": "invalid_claim_id"})
    if (
        not isinstance(semantic_type, str)
        or semantic_type not in validated["semantic_types"]
    ):
        issues.append(
            {"kind": "unsupported_semantic_type", "value": semantic_type}
        )
    if (
        not isinstance(evidence_ids, list)
        or not evidence_ids
        or not all(isinstance(item, str) and item for item in evidence_ids)
        or len(evidence_ids) != len(set(evidence_ids))
    ):
        issues.append({"kind": "invalid_evidence_ids"})

    issues.extend(validate_meaning(proposal.get("m"), validated))
    return issues


def validate_compact_payload(
    payload: Any,
    registry: Any,
) -> dict[str, object]:
    """Score structural provider defects for a complete compact payload."""
    validate_registry(registry)
    if not isinstance(payload, dict) or set(payload) != {"p"}:
        return {
            "candidate_count": 0,
            "conforming_count": 0,
            "violation_count": 1,
            "violations": [{"proposal_number": None, "issues": [{"kind": "payload_malformed"}]}],
        }

    proposals = payload.get("p")
    if not isinstance(proposals, list):
        return {
            "candidate_count": 0,
            "conforming_count": 0,
            "violation_count": 1,
            "violations": [{"proposal_number": None, "issues": [{"kind": "proposals_not_array"}]}],
        }

    violations: list[dict[str, object]] = []
    for number, proposal in enumerate(proposals, start=1):
        proposal_issues = validate_compact_proposal(proposal, registry)
        if proposal_issues:
            violations.append(
                {"proposal_number": number, "issues": proposal_issues}
            )

    return {
        "candidate_count": len(proposals),
        "conforming_count": len(proposals) - len(violations),
        "violation_count": len(violations),
        "violations": violations,
    }
