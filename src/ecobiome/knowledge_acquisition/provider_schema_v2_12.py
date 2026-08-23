"""Provider-facing schema helpers for directional nitrogen V2.12."""

from __future__ import annotations

import copy
from typing import Any

from ecobiome.knowledge_acquisition.provider_provenance_v2_9 import (
    build_source_scope_branches_v2_9,
)
from ecobiome.knowledge_acquisition.provider_schema_v2_10 import (
    semantic_assertion_branch_v2_10,
)

PROVIDER_WIRE_CONTRACT_V2_12 = "ecobiome-provider-contract-v2.12-47-resolved"
PROVIDER_ONTOLOGY_V2_12 = "ecobiome-semantic-contract-v2.12-provider-eligible-v1"


def build_semantic_assertion_branches_v2_12(
    registry_v2_12: dict[str, Any],
) -> list[dict[str, Any]]:
    relations = registry_v2_12.get("relations")
    if not isinstance(relations, dict):
        raise TypeError("V2.12 relations must be an object")
    resolved = [
        relation
        for relation, spec in sorted(relations.items())
        if isinstance(spec, dict)
        and spec.get("semantic_type_contract_state") != "unresolved_blocked"
    ]
    if len(resolved) != 47:
        raise ValueError(
            f"V2.12 provider contract requires 47 resolved relations; got {len(resolved)}"
        )
    return [
        semantic_assertion_branch_v2_10(registry_v2_12, relation)
        for relation in resolved
    ]


def build_provider_schema_v2_12(
    source_request: dict[str, Any],
    registry_v2_12: dict[str, Any],
    *,
    max_proposals: int = 40,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(max_proposals, int):
        raise TypeError("max_proposals must be an integer")
    if max_proposals < 0:
        raise ValueError("max_proposals must be non-negative")
    source_branches = build_source_scope_branches_v2_9(source_request)
    semantic_branches = build_semantic_assertion_branches_v2_12(registry_v2_12)
    schema = {
        "type": "object",
        "properties": {
            "p": {
                "type": "array",
                "maxItems": max_proposals,
                "items": {
                    "type": "object",
                    "properties": {
                        "s": {"oneOf": source_branches},
                        "x": {"oneOf": semantic_branches},
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
        "contract_name": PROVIDER_WIRE_CONTRACT_V2_12,
        "source_scope_branch_count": len(source_branches),
        "semantic_assertion_branch_count": len(semantic_branches),
        "cartesian_branch_count_avoided": len(source_branches) * len(semantic_branches),
        "factorized_branch_count": len(source_branches) + len(semantic_branches),
        "relation_semantic_type_coupling": "registry_v2_12_resolved_relations_only",
        "claim_evidence_parent_coupling": "reused_v2_9_source_scope",
        "zero_proposals_allowed": True,
    }
    return schema, metadata


def build_provider_ontology_v2_12(
    registry_v2_12: dict[str, Any],
) -> dict[str, Any]:
    relations = registry_v2_12.get("relations")
    if not isinstance(relations, dict):
        raise TypeError("V2.12 relations must be an object")
    resolved: dict[str, Any] = {}
    blocked: list[str] = []
    for relation, spec in sorted(relations.items()):
        if not isinstance(spec, dict):
            raise TypeError(f"malformed V2.12 relation spec: {relation}")
        if spec.get("semantic_type_contract_state") == "unresolved_blocked":
            blocked.append(relation)
            continue
        resolved[relation] = copy.deepcopy(spec)
    if len(resolved) != 47 or len(blocked) != 18:
        raise ValueError("V2.12 provider ontology requires 47 resolved / 18 blocked")
    return {
        "ontology_version": PROVIDER_ONTOLOGY_V2_12,
        "base_relation_type_contract": "v2.10",
        "extension": "v2.12-directional-nitrogen-human-adopted",
        "fail_closed": True,
        "semantic_types": copy.deepcopy(registry_v2_12["semantic_types"]),
        "relations": resolved,
        "blocked_relation_ids": blocked,
        "argument_role_semantics": copy.deepcopy(
            registry_v2_12["argument_role_semantics"]
        ),
        "automatic_scientific_acceptance": False,
    }
