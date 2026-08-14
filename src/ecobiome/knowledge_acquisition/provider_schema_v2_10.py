"""Registry-driven provider schema helpers for EcoBiome V2.10.

V2.10 preserves the proven V2.9 Claim -> Evidence source-scope contract while
building relation/type semantic branches directly from the V2.10 runtime
registry. Only resolved relations are exposed to the provider.
"""

from __future__ import annotations

import copy
from typing import Any

from ecobiome.knowledge_acquisition.provider_provenance_v2_9 import (
    build_source_scope_branches_v2_9,
)

PROVIDER_WIRE_CONTRACT_V2_10 = (
    "ecobiome-provider-contract-v2.10-45-resolved"
)
PROVIDER_ONTOLOGY_V2_10 = (
    "ecobiome-semantic-contract-v2.10-provider-eligible-v1"
)

STANDARD_ROLE_SCHEMA_KEYS = {
    "type",
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "enum",
    "pattern",
}


def clean_role_schema_v2_10(
    registry_v2_10: dict[str, Any],
    role: str,
) -> dict[str, Any]:
    """Return the provider-safe JSON Schema for one argument role."""
    roles = registry_v2_10.get("argument_roles")
    semantics = registry_v2_10.get("argument_role_semantics")

    if not isinstance(roles, dict) or role not in roles:
        raise ValueError(f"unknown V2.10 argument role: {role}")

    raw = roles[role]
    if not isinstance(raw, dict):
        raise TypeError(f"malformed V2.10 argument role schema: {role}")

    cleaned = {
        key: copy.deepcopy(value)
        for key, value in raw.items()
        if key in STANDARD_ROLE_SCHEMA_KEYS
    }

    if not isinstance(semantics, dict):
        raise TypeError("V2.10 argument_role_semantics must be an object")

    semantic = semantics.get(role)
    if isinstance(semantic, dict):
        description = semantic.get("description")
        domain = semantic.get("semantic_domain")

        if isinstance(description, str):
            cleaned["description"] = description
        if isinstance(domain, str) and "description" in cleaned:
            cleaned["description"] += f" Semantic domain: {domain}."

    return cleaned


def semantic_assertion_branch_v2_10(
    registry_v2_10: dict[str, Any],
    relation: str,
) -> dict[str, Any]:
    """Build one coupled relation/type branch from a resolved relation."""
    relations = registry_v2_10.get("relations")
    if not isinstance(relations, dict):
        raise TypeError("V2.10 relations must be an object")

    spec = relations.get(relation)
    if not isinstance(spec, dict):
        raise TypeError(f"unknown V2.10 relation: {relation}")

    if spec.get("semantic_type_contract_state") == "unresolved_blocked":
        raise ValueError(f"cannot expose fail-closed relation: {relation}")

    allowed = spec.get("semantic_types_allowed")
    argument_keys = spec.get("argument_keys")

    if not isinstance(allowed, list):
        raise TypeError(
            f"resolved relation semantic types must be an array: {relation}"
        )
    if not all(isinstance(item, str) for item in allowed):
        raise TypeError(
            f"resolved relation semantic types must be strings: {relation}"
        )
    if not allowed or not all(allowed):
        raise ValueError(
            f"resolved relation lacks allowed semantic types: {relation}"
        )

    if not isinstance(argument_keys, list):
        raise TypeError(
            f"relation argument_keys must be an array: {relation}"
        )
    if not all(isinstance(item, str) for item in argument_keys):
        raise TypeError(
            f"relation argument_keys must be strings: {relation}"
        )
    if not all(argument_keys):
        raise ValueError(f"malformed argument_keys for relation: {relation}")

    relation_schema: dict[str, Any] = {
        "const": relation,
    }

    description = spec.get("description")
    if isinstance(description, str):
        relation_schema["description"] = description

    return {
        "type": "object",
        "properties": {
            "t": {
                "type": "string",
                "enum": sorted(set(allowed)),
            },
            "m": {
                "type": "object",
                "properties": {
                    "r": relation_schema,
                    "a": {
                        "type": "object",
                        "properties": {
                            key: clean_role_schema_v2_10(
                                registry_v2_10,
                                key,
                            )
                            for key in argument_keys
                        },
                        "required": list(argument_keys),
                        "additionalProperties": False,
                    },
                },
                "required": ["r", "a"],
                "additionalProperties": False,
            },
        },
        "required": ["t", "m"],
        "additionalProperties": False,
    }


def build_semantic_assertion_branches_v2_10(
    registry_v2_10: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build branches for all and only resolved V2.10 relations."""
    relations = registry_v2_10.get("relations")
    if not isinstance(relations, dict):
        raise TypeError("V2.10 relations must be an object")

    resolved = [
        relation
        for relation, spec in sorted(relations.items())
        if isinstance(spec, dict)
        and spec.get("semantic_type_contract_state")
        != "unresolved_blocked"
    ]

    if len(resolved) != 45:
        raise ValueError(
            f"V2.10 provider contract requires 45 resolved relations; "
            f"got {len(resolved)}"
        )

    return [
        semantic_assertion_branch_v2_10(
            registry_v2_10,
            relation,
        )
        for relation in resolved
    ]


def build_provider_schema_v2_10(
    source_request: dict[str, Any],
    registry_v2_10: dict[str, Any],
    *,
    max_proposals: int = 40,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build factorized Claim-scope x semantic Structured Output schema."""
    if not isinstance(max_proposals, int):
        raise TypeError("max_proposals must be an integer")
    if max_proposals < 0:
        raise ValueError("max_proposals must be non-negative")

    source_branches = build_source_scope_branches_v2_9(source_request)
    semantic_branches = build_semantic_assertion_branches_v2_10(
        registry_v2_10
    )

    schema = {
        "type": "object",
        "properties": {
            "p": {
                "type": "array",
                "maxItems": max_proposals,
                "items": {
                    "type": "object",
                    "properties": {
                        "s": {
                            "oneOf": source_branches,
                        },
                        "x": {
                            "oneOf": semantic_branches,
                        },
                    },
                    "required": ["s", "x"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["p"],
        "additionalProperties": False,
    }

    metadata = {
        "contract_name": PROVIDER_WIRE_CONTRACT_V2_10,
        "source_scope_branch_count": len(source_branches),
        "semantic_assertion_branch_count": len(semantic_branches),
        "cartesian_branch_count_avoided": (
            len(source_branches) * len(semantic_branches)
        ),
        "factorized_branch_count": (
            len(source_branches) + len(semantic_branches)
        ),
        "relation_semantic_type_coupling": (
            "registry_v2_10_resolved_relations_only"
        ),
        "claim_evidence_parent_coupling": "reused_v2_9_source_scope",
        "zero_proposals_allowed": True,
    }

    return schema, metadata


def build_provider_ontology_v2_10(
    registry_v2_10: dict[str, Any],
) -> dict[str, Any]:
    """Build provider ontology containing only resolved V2.10 relations."""
    relations = registry_v2_10.get("relations")
    if not isinstance(relations, dict):
        raise TypeError("V2.10 relations must be an object")

    resolved: dict[str, Any] = {}
    blocked: list[str] = []

    for relation, spec in sorted(relations.items()):
        if not isinstance(spec, dict):
            raise TypeError(f"malformed V2.10 relation spec: {relation}")

        if spec.get("semantic_type_contract_state") == "unresolved_blocked":
            blocked.append(relation)
            continue

        resolved[relation] = {
            key: copy.deepcopy(spec[key])
            for key in (
                "argument_keys",
                "description",
                "epistemic_class",
                "semantic_types_allowed",
                "semantic_type_contract_state",
            )
            if key in spec
        }

    if len(resolved) != 45 or len(blocked) != 18:
        raise ValueError(
            "V2.10 provider ontology requires 45 resolved / 18 blocked"
        )

    return {
        "ontology_version": PROVIDER_ONTOLOGY_V2_10,
        "base_registry": "v2.7",
        "base_relation_type_contract": "v2.8",
        "extension": "v2.10-historical-golden-reviewed",
        "fail_closed": True,
        "semantic_types": copy.deepcopy(
            registry_v2_10["semantic_types"]
        ),
        "relations": resolved,
        "blocked_relation_ids": blocked,
        "argument_role_semantics": copy.deepcopy(
            registry_v2_10["argument_role_semantics"]
        ),
        "automatic_scientific_acceptance": False,
    }
