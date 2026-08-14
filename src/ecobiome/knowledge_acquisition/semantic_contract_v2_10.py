"""Reviewed V2.10 relation/type contract extension for EcoBiome Collector.

V2.10 applies the frozen, human-reviewed historical-Golden delta on top of the
V2.8 merged registry. It does not mutate the frozen V2.7 registry or the V2.8
contract and it grants no automatic scientific acceptance.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

CONTRACT_DELTA_V2_10_SCHEMA_VERSION = (
    "ecobiome-semantic-relation-type-contract-v2.10-review-candidate-v1"
)
CONTRACT_DELTA_V2_10_STATUS = "HUMAN_REVIEWED_CANDIDATE_NOT_INTEGRATED"
CONTRACT_DELTA_V2_10_STATE = "historical_golden_reviewed_constrained"

EXPECTED_BASE_RESOLVED = 21
EXPECTED_BASE_UNRESOLVED = 42
EXPECTED_NEWLY_RESOLVED = 24
EXPECTED_PROJECTED_RESOLVED = 45
EXPECTED_PROJECTED_UNRESOLVED = 18
EXPECTED_TOTAL_RELATIONS = 63


def load_relation_type_delta_v2_10(path: Path) -> dict[str, Any]:
    """Load and validate the frozen V2.10 reviewed delta."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("V2.10 relation/type delta must be a JSON object")
    validate_relation_type_delta_v2_10(payload)
    return payload


def validate_relation_type_delta_v2_10(
    delta: dict[str, Any],
) -> dict[str, Any]:
    """Validate source-independent structure of the reviewed V2.10 delta."""
    if not isinstance(delta, dict):
        raise TypeError("V2.10 relation/type delta must be an object")

    if delta.get("schema_version") != CONTRACT_DELTA_V2_10_SCHEMA_VERSION:
        raise ValueError("unexpected V2.10 delta schema_version")

    if delta.get("status") != CONTRACT_DELTA_V2_10_STATUS:
        raise ValueError("unexpected V2.10 delta status")

    if delta.get("base_contract") != "semantic-relation-type-contract-v2.8":
        raise ValueError("unexpected V2.10 delta base contract")

    if delta.get("automatic_scientific_acceptance") is not False:
        raise ValueError(
            "V2.10 delta must not grant automatic scientific acceptance"
        )

    candidates = delta.get("candidate_resolutions")
    blocked = delta.get("remain_unresolved_blocked")
    counts = delta.get("counts")

    if not isinstance(candidates, dict):
        raise TypeError("V2.10 candidate_resolutions must be an object")
    if len(candidates) != EXPECTED_NEWLY_RESOLVED:
        raise ValueError("V2.10 must contain exactly 24 reviewed resolutions")

    if not isinstance(blocked, list):
        raise TypeError("V2.10 remain_unresolved_blocked must be an array")
    if len(blocked) != EXPECTED_PROJECTED_UNRESOLVED:
        raise ValueError("V2.10 must retain exactly 18 blocked relations")
    if not all(isinstance(item, str) for item in blocked):
        raise TypeError("V2.10 blocked relation IDs must be strings")
    if not all(blocked):
        raise ValueError("V2.10 blocked relation IDs must be non-empty")
    if len(set(blocked)) != len(blocked):
        raise ValueError("V2.10 blocked relation IDs must be unique")

    if set(candidates) & set(blocked):
        raise ValueError("V2.10 resolved and blocked relation sets overlap")

    if not isinstance(counts, dict):
        raise TypeError("V2.10 counts must be an object")

    expected_counts = {
        "base_resolved": EXPECTED_BASE_RESOLVED,
        "candidate_newly_resolved": EXPECTED_NEWLY_RESOLVED,
        "projected_resolved": EXPECTED_PROJECTED_RESOLVED,
        "projected_unresolved_blocked": EXPECTED_PROJECTED_UNRESOLVED,
        "total_relations": EXPECTED_TOTAL_RELATIONS,
    }
    if counts != expected_counts:
        raise ValueError("V2.10 delta counts differ from reviewed freeze")

    for relation, decision in sorted(candidates.items()):
        if not isinstance(relation, str):
            raise TypeError("V2.10 candidate relation ID must be a string")
        if not relation:
            raise ValueError("V2.10 candidate relation ID must be non-empty")
        if not isinstance(decision, dict):
            raise TypeError(f"V2.10 decision must be an object: {relation}")

        if (
            decision.get("semantic_type_contract_state")
            != CONTRACT_DELTA_V2_10_STATE
        ):
            raise ValueError(
                f"unexpected V2.10 contract state for relation: {relation}"
            )

        allowed = decision.get("semantic_types_allowed")
        argument_keys = decision.get("argument_keys")
        epistemic_class = decision.get("epistemic_class")

        if not isinstance(allowed, list):
            raise TypeError(
                f"V2.10 semantic_types_allowed must be an array: {relation}"
            )
        if not all(isinstance(item, str) for item in allowed):
            raise TypeError(
                f"V2.10 semantic types must be strings: {relation}"
            )
        if (
            not allowed
            or not all(allowed)
            or len(set(allowed)) != len(allowed)
        ):
            raise ValueError(
                f"invalid V2.10 semantic_types_allowed for: {relation}"
            )

        if not isinstance(argument_keys, list):
            raise TypeError(
                f"V2.10 argument_keys must be an array: {relation}"
            )
        if not all(isinstance(item, str) for item in argument_keys):
            raise TypeError(
                f"V2.10 argument keys must be strings: {relation}"
            )
        if (
            not argument_keys
            or not all(argument_keys)
            or len(set(argument_keys)) != len(argument_keys)
        ):
            raise ValueError(f"invalid V2.10 argument_keys for: {relation}")

        if not isinstance(epistemic_class, str):
            raise TypeError(
                f"V2.10 epistemic_class must be a string: {relation}"
            )
        if not epistemic_class:
            raise ValueError(
                f"invalid V2.10 epistemic_class for: {relation}"
            )

    return delta


def apply_relation_type_delta_v2_10(
    registry_v2_8: dict[str, Any],
    delta_v2_10: dict[str, Any],
) -> dict[str, Any]:
    """Apply the reviewed V2.10 delta to a merged V2.8 registry."""
    validate_relation_type_delta_v2_10(delta_v2_10)

    if not isinstance(registry_v2_8, dict):
        raise TypeError("V2.8 registry must be an object")

    merged = copy.deepcopy(registry_v2_8)
    relations = merged.get("relations")
    semantic_types = merged.get("semantic_types")

    if not isinstance(relations, dict):
        raise TypeError("V2.8 registry relations must be an object")
    if len(relations) != EXPECTED_TOTAL_RELATIONS:
        raise ValueError("V2.8 registry must contain exactly 63 relations")
    if not isinstance(semantic_types, list):
        raise TypeError("V2.8 registry semantic_types must be an array")

    semantic_type_set = {
        str(item)
        for item in semantic_types
    }

    input_resolved = {
        relation
        for relation, spec in relations.items()
        if isinstance(spec, dict)
        and spec.get("semantic_type_contract_state")
        != "unresolved_blocked"
    }
    input_unresolved = set(relations) - input_resolved

    if len(input_resolved) != EXPECTED_BASE_RESOLVED:
        raise ValueError("V2.8 registry must start with 21 resolved relations")
    if len(input_unresolved) != EXPECTED_BASE_UNRESOLVED:
        raise ValueError("V2.8 registry must start with 42 blocked relations")

    candidates = delta_v2_10["candidate_resolutions"]
    blocked = set(delta_v2_10["remain_unresolved_blocked"])
    candidate_names = set(candidates)

    if candidate_names | blocked != input_unresolved:
        raise ValueError(
            "V2.10 delta must partition all 42 V2.8 blocked relations"
        )

    for relation, decision in sorted(candidates.items()):
        spec = relations.get(relation)
        if not isinstance(spec, dict):
            raise TypeError(
                f"V2.10 candidate missing from registry: {relation}"
            )
        if spec.get("semantic_type_contract_state") != "unresolved_blocked":
            raise ValueError(
                f"V2.10 candidate was not V2.8 fail-closed: {relation}"
            )

        if decision["argument_keys"] != spec.get("argument_keys"):
            raise ValueError(
                f"V2.10 delta mutates argument_keys: {relation}"
            )
        if decision["epistemic_class"] != spec.get("epistemic_class"):
            raise ValueError(
                f"V2.10 delta mutates epistemic_class: {relation}"
            )

        allowed = decision["semantic_types_allowed"]
        if any(item not in semantic_type_set for item in allowed):
            raise ValueError(
                f"V2.10 delta uses unknown semantic type: {relation}"
            )

        spec["semantic_types_allowed"] = sorted(set(allowed))
        spec["semantic_type_contract_state"] = CONTRACT_DELTA_V2_10_STATE

    output_resolved = {
        relation
        for relation, spec in relations.items()
        if isinstance(spec, dict)
        and spec.get("semantic_type_contract_state")
        != "unresolved_blocked"
    }
    output_unresolved = set(relations) - output_resolved

    if len(output_resolved) != EXPECTED_PROJECTED_RESOLVED:
        raise RuntimeError("V2.10 output must contain 45 resolved relations")
    if len(output_unresolved) != EXPECTED_PROJECTED_UNRESOLVED:
        raise RuntimeError("V2.10 output must contain 18 blocked relations")
    if output_unresolved != blocked:
        raise RuntimeError(
            "V2.10 output blocked set differs from reviewed freeze"
        )

    return merged
