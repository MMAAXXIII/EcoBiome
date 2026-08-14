"""Claim-scoped provider provenance helpers for EcoBiome V2.9.

V2.9 adds structural Claim -> Evidence ownership to provider Structured Output.
It preserves the V2.8 relation/type contract and the existing deterministic
Claim-local grounding policy.

This module does not grant automatic scientific acceptance.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from ecobiome.knowledge_acquisition.semantic_contract_v2_8 import (
    relation_semantic_type_decision_v2_8,
)
from ecobiome.knowledge_acquisition.semantic_grounding import audit_arguments

PROVENANCE_POLICY_V2_9_VERSION = "2.9"
CLAIM_SCOPED_PROVENANCE_POLICY_V2_9_CANONICAL_SHA256 = (
    "4c9ab21e6824031092868fafccd910f9f2ec203b650f898f141231490c8bdfc0"
)
PROVIDER_WIRE_CONTRACT_V2_9 = (
    "ecobiome-claim-scoped-provider-provenance-v2.9"
)


def canonical_json_sha256(payload: object) -> str:
    """Return SHA-256 of canonical JSON for deterministic identity."""
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()




def validate_provenance_policy_v2_9(
    policy: Any,
) -> dict[str, Any]:
    """Validate the frozen source-independent V2.9 provenance policy."""
    if not isinstance(policy, dict):
        raise TypeError("V2.9 provenance policy must be an object")

    actual_sha = canonical_json_sha256(policy)
    if actual_sha != CLAIM_SCOPED_PROVENANCE_POLICY_V2_9_CANONICAL_SHA256:
        raise ValueError(
            "unsupported V2.9 provenance policy SHA-256: "
            f"{actual_sha}; expected "
            f"{CLAIM_SCOPED_PROVENANCE_POLICY_V2_9_CANONICAL_SHA256}"
        )

    if policy.get("policy_version") != PROVENANCE_POLICY_V2_9_VERSION:
        raise ValueError("unsupported V2.9 provenance policy version")

    principles = policy.get("principles")
    if not isinstance(principles, dict):
        raise TypeError("V2.9 provenance policy principles malformed")

    required_true = {
        "source_claim_ids_are_runtime_finite",
        "evidence_ids_are_runtime_finite",
        "evidence_parent_ownership_is_structural",
        "claim_and_semantic_contracts_are_factorized",
        "claim_local_argument_grounding_is_required",
        "exact_duplicates_are_deduplicated_before_downstream_admission",
        "zero_survivors_is_valid_abstention",
    }
    if any(principles.get(key) is not True for key in required_true):
        raise ValueError("V2.9 provenance policy safety principle missing")

    if principles.get("automatic_scientific_acceptance") is not False:
        raise ValueError(
            "V2.9 provenance policy must not grant scientific acceptance"
        )

    return policy


def load_provenance_policy_v2_9(
    path: Path,
) -> dict[str, Any]:
    """Load and validate the frozen source-independent V2.9 policy."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return validate_provenance_policy_v2_9(payload)


def _source_claims(source_request: dict[str, Any]) -> list[dict[str, Any]]:
    claims = source_request.get("source_claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError("source_request must contain non-empty source_claims")

    claim_ids: set[str] = set()
    evidence_ids: set[str] = set()

    for claim in claims:
        if not isinstance(claim, dict):
            raise TypeError("source Claim must be an object")

        claim_id = claim.get("claim_id")
        effective_text = claim.get("effective_text")
        evidence = claim.get("evidence")

        if not isinstance(claim_id, str) or not claim_id:
            raise ValueError("source Claim ID must be non-empty")
        if claim_id in claim_ids:
            raise ValueError(f"duplicate source Claim ID: {claim_id}")
        claim_ids.add(claim_id)

        if not isinstance(effective_text, str):
            raise TypeError(
                f"source Claim effective_text must be a string: {claim_id}"
            )

        if not isinstance(evidence, list) or not evidence:
            raise ValueError(
                f"source Claim must contain non-empty evidence: {claim_id}"
            )

        local_ids: set[str] = set()
        for item in evidence:
            if not isinstance(item, dict):
                raise TypeError("Evidence item must be an object")
            evidence_id = item.get("evidence_id")
            if not isinstance(evidence_id, str) or not evidence_id:
                raise ValueError("Evidence ID must be non-empty")
            if evidence_id in local_ids:
                raise ValueError(
                    f"duplicate Evidence ID inside Claim {claim_id}: "
                    f"{evidence_id}"
                )
            if evidence_id in evidence_ids:
                raise ValueError(
                    f"Evidence ID owned by multiple Claims: {evidence_id}"
                )
            local_ids.add(evidence_id)
            evidence_ids.add(evidence_id)

    return claims


def source_claim_index_v2_9(
    source_request: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return validated Claim objects indexed by Claim ID."""
    return {
        claim["claim_id"]: claim
        for claim in _source_claims(source_request)
    }


def evidence_owner_index_v2_9(
    source_request: dict[str, Any],
) -> dict[str, str]:
    """Return validated Evidence ID -> parent Claim ID ownership."""
    owners: dict[str, str] = {}

    for claim in _source_claims(source_request):
        claim_id = claim["claim_id"]
        for item in claim["evidence"]:
            owners[item["evidence_id"]] = claim_id

    return owners


def build_source_scope_branches_v2_9(
    source_request: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build one finite Claim -> local-Evidence schema branch per Claim."""
    branches: list[dict[str, Any]] = []

    for claim in _source_claims(source_request):
        evidence_ids = sorted(
            item["evidence_id"]
            for item in claim["evidence"]
        )
        branches.append(
            {
                "type": "object",
                "properties": {
                    "c": {
                        "type": "string",
                        "const": claim["claim_id"],
                    },
                    "e": {
                        "type": "array",
                        "minItems": 1,
                        "uniqueItems": True,
                        "items": {
                            "type": "string",
                            "enum": evidence_ids,
                        },
                    },
                },
                "required": ["c", "e"],
                "additionalProperties": False,
            }
        )

    return branches


def _semantic_assertion_branch_v2_9(
    v2_8_branch: dict[str, Any],
) -> dict[str, Any]:
    properties = v2_8_branch.get("properties")
    if not isinstance(properties, dict):
        raise TypeError("V2.8 proposal branch properties malformed")

    semantic_type = properties.get("t")
    meaning = properties.get("m")

    if not isinstance(semantic_type, dict):
        raise TypeError("V2.8 semantic type schema malformed")
    if not isinstance(meaning, dict):
        raise TypeError("V2.8 meaning schema malformed")

    return {
        "type": "object",
        "properties": {
            "t": copy.deepcopy(semantic_type),
            "m": copy.deepcopy(meaning),
        },
        "required": ["t", "m"],
        "additionalProperties": False,
    }


def build_provider_schema_v2_9(
    source_request: dict[str, Any],
    v2_8_provider_schema: dict[str, Any],
    *,
    max_proposals: int = 40,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Factor provenance and semantics without a Claim x relation product."""
    if not isinstance(max_proposals, int):
        raise TypeError("max_proposals must be an integer")
    if max_proposals < 0:
        raise ValueError("max_proposals must be non-negative")

    try:
        old_branches = (
            v2_8_provider_schema["properties"]["p"]["items"]["oneOf"]
        )
    except (KeyError, TypeError) as exc:
        raise ValueError("V2.8 provider schema malformed") from exc

    if not isinstance(old_branches, list) or not old_branches:
        raise ValueError("V2.8 provider schema has no semantic branches")

    source_branches = build_source_scope_branches_v2_9(
        source_request
    )
    semantic_branches = [
        _semantic_assertion_branch_v2_9(branch)
        for branch in old_branches
    ]

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
        "contract_name": PROVIDER_WIRE_CONTRACT_V2_9,
        "contract_version": PROVENANCE_POLICY_V2_9_VERSION,
        "source_scope_branch_count": len(source_branches),
        "semantic_assertion_branch_count": len(semantic_branches),
        "cartesian_branch_count_avoided": (
            len(source_branches) * len(semantic_branches)
        ),
        "factorized_branch_count": (
            len(source_branches) + len(semantic_branches)
        ),
        "claim_evidence_parent_coupling":
            "structural_by_source_scope_oneOf",
        "relation_semantic_type_coupling":
            "preserved_from_v2_8_semantic_oneOf",
        "zero_proposals_allowed": True,
    }

    return schema, metadata


def source_scope_decision_v2_9(
    source_request: dict[str, Any],
    source_scope: Any,
) -> dict[str, Any]:
    """Validate Claim/Evidence ownership independently of provider intent."""
    claims = source_claim_index_v2_9(source_request)
    owners = evidence_owner_index_v2_9(source_request)

    if not isinstance(source_scope, dict):
        return {
            "accepted": False,
            "state": "source_scope_not_object",
        }

    if set(source_scope) != {"c", "e"}:
        return {
            "accepted": False,
            "state": "source_scope_keys",
            "actual": sorted(source_scope),
        }

    claim_id = source_scope.get("c")
    evidence_ids = source_scope.get("e")

    if not isinstance(claim_id, str) or claim_id not in claims:
        return {
            "accepted": False,
            "state": "unknown_claim_id",
            "claim_id": claim_id,
        }

    if (
        not isinstance(evidence_ids, list)
        or not evidence_ids
        or not all(isinstance(item, str) for item in evidence_ids)
        or len(evidence_ids) != len(set(evidence_ids))
    ):
        return {
            "accepted": False,
            "state": "malformed_evidence_ids",
            "claim_id": claim_id,
        }

    unknown = sorted(
        evidence_id
        for evidence_id in evidence_ids
        if evidence_id not in owners
    )
    if unknown:
        return {
            "accepted": False,
            "state": "unknown_evidence_id",
            "claim_id": claim_id,
            "evidence_ids": list(evidence_ids),
            "unknown_evidence_ids": unknown,
        }

    foreign = sorted(
        evidence_id
        for evidence_id in evidence_ids
        if owners[evidence_id] != claim_id
    )
    if foreign:
        return {
            "accepted": False,
            "state": "foreign_parent_evidence_id",
            "claim_id": claim_id,
            "evidence_ids": list(evidence_ids),
            "foreign_evidence_ids": foreign,
        }

    return {
        "accepted": True,
        "state": "claim_local_evidence",
        "claim_id": claim_id,
        "evidence_ids": list(evidence_ids),
    }


def normalize_wire_proposal_v2_9(
    proposal: Any,
) -> dict[str, Any]:
    """Convert provider V2.9 wire shape to the internal flat proposal shape."""
    if not isinstance(proposal, dict):
        raise TypeError("V2.9 proposal must be an object")
    if set(proposal) != {"s", "x"}:
        raise ValueError("V2.9 proposal must contain exactly s and x")

    source_scope = proposal["s"]
    semantic_assertion = proposal["x"]

    if not isinstance(source_scope, dict):
        raise TypeError("V2.9 source scope must be an object")
    if not isinstance(semantic_assertion, dict):
        raise TypeError("V2.9 semantic assertion must be an object")

    if set(source_scope) != {"c", "e"}:
        raise ValueError("V2.9 source scope must contain exactly c and e")
    if set(semantic_assertion) != {"t", "m"}:
        raise ValueError(
            "V2.9 semantic assertion must contain exactly t and m"
        )

    claim_id = source_scope.get("c")
    evidence_ids = source_scope.get("e")
    semantic_type = semantic_assertion.get("t")
    meaning = semantic_assertion.get("m")

    if not isinstance(claim_id, str):
        raise TypeError("V2.9 Claim ID must be a string")
    if not isinstance(evidence_ids, list):
        raise TypeError("V2.9 Evidence IDs must be an array")
    if not isinstance(semantic_type, str):
        raise TypeError("V2.9 semantic type must be a string")
    if not isinstance(meaning, dict):
        raise TypeError("V2.9 meaning must be an object")
    if set(meaning) != {"r", "a"}:
        raise ValueError("V2.9 meaning must contain exactly r and a")

    relation = meaning.get("r")
    arguments = meaning.get("a")

    if not isinstance(relation, str):
        raise TypeError("V2.9 relation must be a string")
    if not isinstance(arguments, dict):
        raise TypeError("V2.9 arguments must be an object")

    return {
        "c": claim_id,
        "e": list(evidence_ids),
        "t": semantic_type,
        "m": {
            "r": relation,
            "a": copy.deepcopy(arguments),
        },
    }


def _wire_normalization_decision_v2_9(
    proposal: Any,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return normalize_wire_proposal_v2_9(proposal), None
    except (TypeError, ValueError) as exc:
        return None, str(exc)


def deduplicate_proposals_v2_9(
    proposals: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Keep first exact canonical proposal and report duplicate groups."""
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    counts: Counter[str] = Counter()

    for proposal in proposals:
        key = canonical_json_sha256(proposal)
        counts[key] += 1

        if key in seen:
            continue

        seen.add(key)
        unique.append(proposal)

    duplicate_groups = [
        {
            "canonical_key_sha256": key,
            "occurrences": count,
        }
        for key, count in sorted(counts.items())
        if count > 1
    ]

    return unique, {
        "input_count": len(proposals),
        "unique_count": len(unique),
        "removed_duplicate_count": len(proposals) - len(unique),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_groups": duplicate_groups,
    }


def admit_provider_candidates_v2_9(
    compact: dict[str, Any],
    source_request: dict[str, Any],
    registry_v2_8: dict[str, Any],
    *,
    max_proposals: int = 40,
) -> dict[str, Any]:
    """Apply provenance, semantic contract, grounding, then exact dedup."""
    if not isinstance(compact, dict):
        raise TypeError("provider compact output must be an object")

    proposals = compact.get("p")
    if not isinstance(proposals, list):
        raise TypeError("provider compact output p must be an array")
    if len(proposals) > max_proposals:
        raise ValueError("provider compact output exceeds proposal limit")

    claims = source_claim_index_v2_9(source_request)
    survivors_before_dedup: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for candidate_index, raw in enumerate(proposals):
        normalized, wire_error = _wire_normalization_decision_v2_9(
            raw
        )
        if normalized is None:
            rejected.append(
                {
                    "candidate_index": candidate_index,
                    "stage": "wire_shape",
                    "state": "invalid_wire_shape",
                    "detail": wire_error,
                }
            )
            continue

        source_decision = source_scope_decision_v2_9(
            source_request,
            raw["s"],
        )
        if not source_decision["accepted"]:
            rejected.append(
                {
                    "candidate_index": candidate_index,
                    "stage": "source_scope",
                    **source_decision,
                }
            )
            continue

        semantic_decision = relation_semantic_type_decision_v2_8(
            registry_v2_8,
            normalized["m"]["r"],
            normalized["t"],
        )
        if not semantic_decision["accepted"]:
            rejected.append(
                {
                    "candidate_index": candidate_index,
                    "stage": "relation_type",
                    **semantic_decision,
                }
            )
            continue

        parent_text = claims[normalized["c"]]["effective_text"]
        grounding = audit_arguments(
            normalized["m"]["a"],
            parent_text,
        )
        if grounding.get("blocking"):
            rejected.append(
                {
                    "candidate_index": candidate_index,
                    "stage": "claim_local_grounding",
                    "state": "grounding_blocked",
                    "audit": grounding,
                }
            )
            continue

        survivors_before_dedup.append(normalized)

    survivors, dedup = deduplicate_proposals_v2_9(
        survivors_before_dedup
    )

    rejection_counts = Counter(
        item["stage"]
        for item in rejected
    )

    return {
        "input_proposal_count": len(proposals),
        "survivor_count_before_dedup":
            len(survivors_before_dedup),
        "survivor_count": len(survivors),
        "survivors": survivors,
        "rejected_count": len(rejected),
        "rejected": rejected,
        "rejection_stage_counts":
            dict(sorted(rejection_counts.items())),
        "deduplication": dedup,
        "zero_survivors_is_valid_abstention": True,
        "automatic_scientific_acceptance": False,
    }
