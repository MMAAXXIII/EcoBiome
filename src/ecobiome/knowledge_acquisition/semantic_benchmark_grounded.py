"""Grounded structured semantic benchmark core for EcoBiome.

Semantic Evaluator V2.3.3. This version keeps V2.3.2 provider-error tolerance,
adds relation-first blind alignment, global exact-duplicate diagnostics, and
optional Source-Grounded Argument Role Contract V1.1 evaluation. Grounding
never manufactures semantic equivalence for unresolved open-text arguments.
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any

from ecobiome.knowledge_acquisition.semantic_grounding import (
    GROUNDING_POLICY_V1_1_SHA256,
    audit_arguments,
    canonical_json_sha256,
    resolved_argument_equal,
    validate_grounding_policy,
)


def _source_claim_index(payload: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict):
        raise TypeError("semantic export must be an object")
    source_claims = payload.get("source_claims")
    if not isinstance(source_claims, list):
        raise TypeError("semantic export source_claims must be a list")
    result: dict[str, dict[str, Any]] = {}
    for claim in source_claims:
        if not isinstance(claim, dict):
            raise TypeError("source claim must be an object")
        claim_id = claim.get("claim_id")
        evidence = claim.get("evidence")
        if not isinstance(claim_id, str) or not isinstance(evidence, list):
            raise TypeError("source claim is malformed")
        if claim_id in result:
            raise ValueError(f"duplicate source claim id: {claim_id}")
        result[claim_id] = claim
    return result


def _evidence_by_id(claim: dict[str, Any]) -> dict[str, dict[str, Any]]:
    evidence = claim.get("evidence")
    if not isinstance(evidence, list):
        raise TypeError("source claim evidence must be a list")
    result: dict[str, dict[str, Any]] = {}
    for item in evidence:
        if not isinstance(item, dict):
            raise TypeError("evidence item must be an object")
        evidence_id = item.get("evidence_id")
        if not isinstance(evidence_id, str):
            raise TypeError("evidence id must be a string")
        if evidence_id in result:
            raise ValueError(f"duplicate evidence id: {evidence_id}")
        result[evidence_id] = item
    return result


def _fixture_arrays(
    fixture: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(fixture, dict):
        raise TypeError("fixture must be an object")
    result: list[list[dict[str, Any]]] = []
    for key in (
        "required_propositions",
        "admissible_propositions",
        "excluded_propositions",
    ):
        value = fixture.get(key)
        if not isinstance(value, list) or not all(
            isinstance(item, dict) for item in value
        ):
            raise TypeError(f"fixture {key} must be a list of objects")
        result.append(value)
    return result[0], result[1], result[2]


def _meaning(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError("meaning must be an object")
    facet = value.get("facet")
    relation = value.get("relation")
    arguments = value.get("arguments", {})
    essential = value.get("essential_argument_keys", [])
    if not isinstance(facet, str) or not facet:
        raise TypeError("fixture meaning facet must be a non-empty string")
    if not isinstance(relation, str) or not relation:
        raise TypeError("meaning relation must be a non-empty string")
    if not isinstance(arguments, dict):
        raise TypeError("meaning arguments must be an object")
    if not isinstance(essential, list) or not all(
        isinstance(key, str) and key for key in essential
    ):
        raise TypeError("essential_argument_keys must be a list of strings")
    if len(set(essential)) != len(essential):
        raise ValueError("duplicate essential argument key")
    for key in essential:
        if key not in arguments:
            raise ValueError(f"fixture meaning lacks essential argument: {key}")
    for key, item in arguments.items():
        if not isinstance(key, str) or not key:
            raise TypeError("meaning argument keys must be non-empty strings")
        if isinstance(item, (dict, list)):
            raise TypeError("meaning argument values must be scalar")
    return {
        "facet": facet,
        "relation": relation,
        "arguments": dict(arguments),
        "essential_argument_keys": list(essential),
    }


def _candidate_violation(
    candidate_index: int | None,
    kind: str,
    *,
    path: str,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "candidate_index": candidate_index,
        "kind": kind,
        "path": path,
    }
    if detail:
        item.update(detail)
    return item


def _candidate_meaning_tolerant(
    value: Any,
    candidate_index: int,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    violations: list[dict[str, Any]] = []
    if value is None:
        violations.append(
            _candidate_violation(
                candidate_index,
                "missing_structured_meaning",
                path="benchmark_meaning",
            )
        )
        return None, violations
    if not isinstance(value, dict):
        violations.append(
            _candidate_violation(
                candidate_index,
                "meaning_not_object",
                path="benchmark_meaning",
                detail={"actual_type": type(value).__name__},
            )
        )
        return None, violations

    relation = value.get("relation")
    arguments = value.get("arguments")
    facet = value.get("facet")

    if not isinstance(relation, str) or not relation:
        violations.append(
            _candidate_violation(
                candidate_index,
                "invalid_relation_field",
                path="benchmark_meaning.relation",
                detail={"actual_value": relation},
            )
        )
    if not isinstance(arguments, dict):
        violations.append(
            _candidate_violation(
                candidate_index,
                "arguments_not_object",
                path="benchmark_meaning.arguments",
                detail={"actual_type": type(arguments).__name__},
            )
        )
    if facet is not None and (not isinstance(facet, str) or not facet):
        violations.append(
            _candidate_violation(
                candidate_index,
                "invalid_optional_facet",
                path="benchmark_meaning.facet",
                detail={"actual_value": facet},
            )
        )

    if not isinstance(relation, str) or not relation or not isinstance(arguments, dict):
        return None, violations

    bad_scalar = False
    for key, item in arguments.items():
        if not isinstance(key, str) or not key:
            violations.append(
                _candidate_violation(
                    candidate_index,
                    "invalid_argument_key",
                    path="benchmark_meaning.arguments",
                    detail={"actual_key": repr(key)},
                )
            )
            bad_scalar = True
            continue
        if isinstance(item, (dict, list)):
            violations.append(
                _candidate_violation(
                    candidate_index,
                    "non_scalar_argument_value",
                    path=f"benchmark_meaning.arguments.{key}",
                    detail={"actual_type": type(item).__name__},
                )
            )
            bad_scalar = True

    if bad_scalar:
        return None, violations

    return {
        "relation": relation,
        "arguments": dict(arguments),
        "facet": facet,
    }, violations


def _validate_candidate_contract_asset(contract: Any) -> dict[str, Any] | None:
    """Validate evaluator configuration. Contract corruption is not a provider error."""
    if contract is None:
        return None
    if not isinstance(contract, dict):
        raise TypeError("candidate_contract must be an object or null")

    semantic_types = contract.get("semantic_types")
    relations = contract.get("relations")
    vocabulary = contract.get("argument_vocabulary")
    if isinstance(semantic_types, dict):
        if not all(isinstance(item, str) and item for item in semantic_types):
            raise TypeError("candidate_contract semantic_types keys must be strings")
        semantic_type_values = list(semantic_types)
    elif isinstance(semantic_types, list) and all(
        isinstance(item, str) and item for item in semantic_types
    ):
        semantic_type_values = list(semantic_types)
    else:
        raise TypeError(
            "candidate_contract semantic_types must be a list of strings or object"
        )
    if not isinstance(relations, dict):
        raise TypeError("candidate_contract relations must be an object")
    if not isinstance(vocabulary, dict):
        raise TypeError("candidate_contract argument_vocabulary must be an object")

    for relation, spec in relations.items():
        if not isinstance(relation, str) or not relation or not isinstance(spec, dict):
            raise TypeError("candidate_contract relation entries are malformed")
        keys = spec.get("argument_keys")
        if not isinstance(keys, list) or not all(
            isinstance(key, str) and key for key in keys
        ):
            raise TypeError(
                f"candidate_contract relation {relation} argument_keys are malformed"
            )
        if len(keys) != len(set(keys)):
            raise ValueError(
                f"candidate_contract relation {relation} has duplicate argument keys"
            )

    for key, spec in vocabulary.items():
        if not isinstance(key, str) or not key or not isinstance(spec, dict):
            raise TypeError("candidate_contract argument_vocabulary is malformed")
        expected_type = spec.get("type")
        if expected_type not in {"string", "integer", "number", "boolean"}:
            raise ValueError(
                "candidate_contract argument "
                f"{key} has unsupported type: {expected_type}"
            )
        enum = spec.get("enum")
        if enum is not None and not isinstance(enum, list):
            raise TypeError(f"candidate_contract argument {key} enum must be a list")

    return {
        "semantic_types": semantic_type_values,
        "relations": relations,
        "argument_vocabulary": vocabulary,
        "ontology_version": contract.get("ontology_version"),
    }


def _value_matches_contract_type(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    raise ValueError(f"unsupported contract type: {expected_type}")


def _validate_candidate_against_contract(
    proposal: dict[str, Any],
    candidate_index: int,
    contract: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if contract is None:
        return []

    violations: list[dict[str, Any]] = []
    semantic_type = proposal["semantic_type"]
    meaning = proposal["benchmark_meaning"]

    if semantic_type not in contract["semantic_types"]:
        violations.append(
            _candidate_violation(
                candidate_index,
                "unknown_semantic_type",
                path="semantic_type",
                detail={"semantic_type": semantic_type},
            )
        )

    if meaning is None:
        return violations

    relation = meaning["relation"]
    arguments = meaning["arguments"]
    relation_spec = contract["relations"].get(relation)
    if relation_spec is None:
        violations.append(
            _candidate_violation(
                candidate_index,
                "unknown_relation",
                path="benchmark_meaning.relation",
                detail={"relation": relation},
            )
        )
        return violations

    expected_keys = sorted(map(str, relation_spec["argument_keys"]))
    actual_keys = sorted(arguments)
    if expected_keys != actual_keys:
        violations.append(
            _candidate_violation(
                candidate_index,
                "argument_keys_mismatch",
                path="benchmark_meaning.arguments",
                detail={
                    "semantic_type": semantic_type,
                    "relation": relation,
                    "expected_argument_keys": expected_keys,
                    "actual_argument_keys": actual_keys,
                    "arguments": dict(arguments),
                },
            )
        )

    vocabulary = contract["argument_vocabulary"]
    for key, value in arguments.items():
        spec = vocabulary.get(key)
        if spec is None:
            violations.append(
                _candidate_violation(
                    candidate_index,
                    "unknown_argument_key",
                    path=f"benchmark_meaning.arguments.{key}",
                    detail={"argument_key": key},
                )
            )
            continue
        expected_type = str(spec["type"])
        if not _value_matches_contract_type(value, expected_type):
            violations.append(
                _candidate_violation(
                    candidate_index,
                    "argument_type_mismatch",
                    path=f"benchmark_meaning.arguments.{key}",
                    detail={
                        "argument_key": key,
                        "expected_type": expected_type,
                        "actual_value": value,
                    },
                )
            )
        allowed = spec.get("enum")
        if isinstance(allowed, list) and value not in allowed:
            violations.append(
                _candidate_violation(
                    candidate_index,
                    "argument_enum_mismatch",
                    path=f"benchmark_meaning.arguments.{key}",
                    detail={
                        "argument_key": key,
                        "actual_value": value,
                        "allowed": list(allowed),
                    },
                )
            )
    return violations


def _numeric(value: Any) -> Decimal | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None
    return None


def _argument_equal(left: Any, right: Any) -> bool:
    left_num = _numeric(left)
    right_num = _numeric(right)
    if left_num is not None or right_num is not None:
        return (
            left_num is not None
            and right_num is not None
            and left_num == right_num
        )
    return type(left) is type(right) and left == right


def _claim_effective_text(claim: dict[str, Any]) -> str:
    value = claim.get("effective_text")
    if not isinstance(value, str) or not value:
        raise TypeError(
            "semantic export source claim effective_text is required "
            "when argument grounding is enabled"
        )
    return value


def _compare_meaning_grounded(
    expected: dict[str, Any],
    candidate: dict[str, Any] | None,
    *,
    source_text: str | None,
    grounding_policy: dict[str, Any] | None,
) -> dict[str, Any]:
    base = _compare_meaning(expected, candidate)
    result = dict(base)
    result["argument_grounding"] = None

    if grounding_policy is None or candidate is None:
        return result

    if source_text is None:
        raise TypeError("source_text is required when grounding policy is enabled")

    grounding = audit_arguments(candidate["arguments"], source_text)
    result["argument_grounding"] = grounding

    if not result["relation_match"]:
        result["status"] = "contradicted"
        return result

    if result["missing_essential_arguments"]:
        result["status"] = "ambiguous"
        return result

    if result["unexpected_argument_keys"]:
        result["status"] = "overclaimed"
        return result

    resolved_mismatches: list[dict[str, Any]] = []
    unresolved_keys: list[str] = []
    grounding_failed_keys: list[str] = []

    records = grounding["records"]
    for key in expected["essential_argument_keys"]:
        record = records.get(key)
        if not isinstance(record, dict):
            grounding_failed_keys.append(key)
            continue

        state = str(record.get("state"))
        equality = resolved_argument_equal(
            key,
            candidate["arguments"].get(key),
            expected["arguments"].get(key),
            record,
        )
        if equality is False:
            resolved_mismatches.append(
                {
                    "key": key,
                    "expected": expected["arguments"].get(key),
                    "actual": candidate["arguments"].get(key),
                }
            )
        elif equality is None:
            if state in {
                "ambiguous",
                "domain_mismatch",
                "scalar_type_violation",
                "ungrounded",
                "ungrounded_pair",
                "unknown_role",
                "unsupported_literal",
                "unsupported_unit",
            }:
                grounding_failed_keys.append(key)
            else:
                unresolved_keys.append(key)

    result["resolved_mismatched_arguments"] = resolved_mismatches
    result["grounded_unresolved_argument_keys"] = unresolved_keys
    result["grounding_failed_argument_keys"] = grounding_failed_keys

    if resolved_mismatches:
        result["status"] = "contradicted"
    elif grounding_failed_keys:
        result["status"] = "grounding_failed"
    elif unresolved_keys:
        result["status"] = "grounded_unresolved"
    else:
        result["status"] = "match"
    return result


def _proposal_identity(candidate: dict[str, Any]) -> str | None:
    meaning = candidate.get("benchmark_meaning")
    if not isinstance(meaning, dict):
        return None
    payload = {
        "source_claim_id": candidate["source_claim_id"],
        "semantic_type": candidate["semantic_type"],
        "evidence_ids": sorted(map(str, candidate["evidence_ids"])),
        "relation": meaning["relation"],
        "arguments": meaning["arguments"],
    }
    return canonical_json_sha256(payload)


def _compare_meaning(
    expected: dict[str, Any],
    candidate: dict[str, Any] | None,
) -> dict[str, Any]:
    if candidate is None:
        return {
            "status": "ambiguous",
            "relation_match": False,
            "missing_essential_arguments": list(expected["essential_argument_keys"]),
            "mismatched_arguments": [],
            "unexpected_argument_keys": [],
        }

    relation_match = candidate["relation"] == expected["relation"]
    if candidate["relation"] in {"unknown", "ambiguous", "unspecified"}:
        relation_status = "ambiguous"
    elif relation_match:
        relation_status = "match"
    else:
        relation_status = "contradicted"

    candidate_arguments = candidate["arguments"]
    expected_arguments = expected["arguments"]
    essential = expected["essential_argument_keys"]
    missing = [key for key in essential if key not in candidate_arguments]
    mismatched: list[dict[str, Any]] = []
    for key in essential:
        if key in candidate_arguments and not _argument_equal(
            expected_arguments[key],
            candidate_arguments[key],
        ):
            mismatched.append(
                {
                    "key": key,
                    "expected": expected_arguments[key],
                    "actual": candidate_arguments[key],
                }
            )

    unexpected = sorted(set(candidate_arguments) - set(expected_arguments))
    if relation_status == "contradicted" or mismatched:
        status = "contradicted"
    elif missing:
        status = "ambiguous"
    elif unexpected:
        status = "overclaimed"
    else:
        status = "match"

    return {
        "status": status,
        "relation_match": relation_match,
        "missing_essential_arguments": missing,
        "mismatched_arguments": mismatched,
        "unexpected_argument_keys": unexpected,
    }


def _essential_identity_matches(
    expected: dict[str, Any],
    candidate: dict[str, Any] | None,
) -> bool:
    if candidate is None:
        return False
    for key in expected["essential_argument_keys"]:
        if key not in candidate["arguments"]:
            return False
        if not _argument_equal(
            expected["arguments"][key],
            candidate["arguments"][key],
        ):
            return False
    return True


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 1.0
    return round(len(left & right) / len(union), 6)


def _matches_forbidden(
    candidate: dict[str, Any],
    excluded: dict[str, Any],
) -> bool:
    if candidate["source_claim_id"] != excluded.get("source_claim_id"):
        return False
    mode = excluded.get("match_mode")
    if mode == "parent_semantic_type":
        return candidate["semantic_type"] == excluded.get("semantic_type")

    if candidate["semantic_type"] != excluded.get("semantic_type"):
        return False
    forbidden_raw = excluded.get("forbidden_meaning")
    if not isinstance(forbidden_raw, dict):
        return False
    forbidden = _meaning(forbidden_raw)
    parsed = candidate.get("benchmark_meaning")
    if not isinstance(parsed, dict):
        return False
    if parsed["relation"] != forbidden["relation"]:
        return False
    for key in forbidden["essential_argument_keys"]:
        if key not in parsed["arguments"]:
            return False
        if not _argument_equal(
            forbidden["arguments"][key],
            parsed["arguments"][key],
        ):
            return False
    return True


def _pair_quality(
    gold: dict[str, Any],
    candidate: dict[str, Any],
    *,
    source_text: str | None,
    grounding_policy: dict[str, Any] | None,
) -> tuple[int, int, int, int, int, int, str]:
    expected = _meaning(gold["meaning"])
    comparison = _compare_meaning_grounded(
        expected,
        candidate["benchmark_meaning"],
        source_text=source_text,
        grounding_policy=grounding_policy,
    )
    relation_rank = int(comparison["relation_match"])
    status_rank = {
        "match": 6,
        "grounded_unresolved": 5,
        "ambiguous": 4,
        "overclaimed": 3,
        "grounding_failed": 2,
        "contradicted": 1,
    }[comparison["status"]]
    required_ids = set(map(str, gold["minimal_evidence_ids"]))
    selected_ids = set(map(str, candidate["evidence_ids"]))
    provenance = int(required_ids.issubset(selected_ids))
    exact_evidence = int(required_ids == selected_ids)
    mismatch_penalty = -len(comparison["mismatched_arguments"])
    missing_penalty = -len(comparison["missing_essential_arguments"])
    stable = json.dumps(
        {
            "relation": candidate["benchmark_meaning"]["relation"],
            "arguments": candidate["benchmark_meaning"]["arguments"],
            "evidence_ids": candidate["evidence_ids"],
            "text": candidate["text"],
        },
        sort_keys=True,
        ensure_ascii=True,
    )
    return (
        relation_rank,
        status_rank,
        provenance,
        exact_evidence,
        mismatch_penalty,
        missing_penalty,
        stable,
    )


def _align_group(
    gold_items: list[dict[str, Any]],
    candidates: list[tuple[int, dict[str, Any]]],
    *,
    source_text: str | None,
    grounding_policy: dict[str, Any] | None,
) -> tuple[
    dict[str, tuple[int, dict[str, Any]]],
    list[tuple[int, dict[str, Any]]],
]:
    """Deterministic relation-first one-to-one blind alignment.

    A candidate is never aligned to a Golden atom with a different relation.
    Such candidates remain extras and the unrelated Golden atom remains missing.
    """
    remaining_gold = {str(item["id"]): item for item in gold_items}
    remaining_candidates = list(candidates)
    assignments: dict[str, tuple[int, dict[str, Any]]] = {}

    while remaining_gold and remaining_candidates:
        pairs: list[
            tuple[
                tuple[int, int, int, int, int, int, str],
                str,
                int,
                dict[str, Any],
            ]
        ] = []
        for gold_id, gold in remaining_gold.items():
            expected_relation = _meaning(gold["meaning"])["relation"]
            for candidate_index, candidate in remaining_candidates:
                candidate_meaning = candidate.get("benchmark_meaning")
                if not isinstance(candidate_meaning, dict):
                    continue
                if candidate_meaning["relation"] != expected_relation:
                    continue
                quality = _pair_quality(
                    gold,
                    candidate,
                    source_text=source_text,
                    grounding_policy=grounding_policy,
                )
                pairs.append((quality, gold_id, candidate_index, candidate))

        if not pairs:
            break

        pairs.sort(
            key=lambda item: (
                item[0][0],
                item[0][1],
                item[0][2],
                item[0][3],
                item[0][4],
                item[0][5],
                item[0][6],
                item[1],
                -item[2],
            ),
            reverse=True,
        )
        _, gold_id, candidate_index, candidate = pairs[0]
        assignments[gold_id] = (candidate_index, candidate)
        del remaining_gold[gold_id]
        remaining_candidates = [
            entry for entry in remaining_candidates
            if entry[0] != candidate_index
        ]

    return assignments, remaining_candidates


def evaluate_structured_semantic_benchmark(
    candidate_payload: Any,
    fixture: Any,
    semantic_export: Any,
    *,
    label: str,
    candidate_contract: Any | None = None,
    argument_grounding_policy: Any | None = None,
) -> dict[str, Any]:
    # Benchmark/scoring assets are trusted inputs and remain strict/fatal.
    claims = _source_claim_index(semantic_export)
    required, admissible, excluded = _fixture_arrays(fixture)
    validated_contract = _validate_candidate_contract_asset(candidate_contract)
    validated_grounding_policy = (
        validate_grounding_policy(argument_grounding_policy)
        if argument_grounding_policy is not None
        else None
    )

    required_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    admissible_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for values, groups in (
        (required, required_groups),
        (admissible, admissible_groups),
    ):
        for item in values:
            claim_id = item.get("source_claim_id")
            semantic_type = item.get("semantic_type")
            _meaning(item.get("meaning"))
            if not isinstance(claim_id, str) or not isinstance(semantic_type, str):
                raise TypeError("fixture semantic key is malformed")
            groups.setdefault((claim_id, semantic_type), []).append(item)

    overlap = sorted(set(required_groups) & set(admissible_groups))
    if overlap:
        raise ValueError(
            "required/admissible groups must not overlap in blind alignment: "
            f"{overlap}"
        )

    candidate_contract_violations: list[dict[str, Any]] = []
    unscoreable_candidates: list[dict[str, Any]] = []

    if not isinstance(candidate_payload, dict):
        candidate_contract_violations.append(
            _candidate_violation(
                None,
                "candidate_payload_not_object",
                path="$",
                detail={"actual_type": type(candidate_payload).__name__},
            )
        )
        raw_proposals: list[Any] = []
        emitted_candidate_count = 0
    else:
        proposals_value = candidate_payload.get("proposals")
        if not isinstance(proposals_value, list):
            candidate_contract_violations.append(
                _candidate_violation(
                    None,
                    "proposals_not_list",
                    path="proposals",
                    detail={"actual_type": type(proposals_value).__name__},
                )
            )
            raw_proposals = []
            emitted_candidate_count = 0
        else:
            raw_proposals = proposals_value
            emitted_candidate_count = len(raw_proposals)

    proposals: list[dict[str, Any]] = []
    for index, item in enumerate(raw_proposals):
        if not isinstance(item, dict):
            candidate_contract_violations.append(
                _candidate_violation(
                    index,
                    "proposal_not_object",
                    path=f"proposals[{index}]",
                    detail={"actual_type": type(item).__name__},
                )
            )
            unscoreable_candidates.append(
                {
                    "candidate_index": index,
                    "reason": "proposal_not_object",
                }
            )
            continue

        claim_id = item.get("source_claim_id")
        semantic_type = item.get("semantic_type")
        text = item.get("text")
        evidence_value = item.get("evidence_ids")

        identity_valid = True
        if not isinstance(claim_id, str) or not claim_id:
            candidate_contract_violations.append(
                _candidate_violation(
                    index,
                    "invalid_source_claim_id",
                    path=f"proposals[{index}].source_claim_id",
                    detail={"actual_value": claim_id},
                )
            )
            identity_valid = False
        if not isinstance(semantic_type, str) or not semantic_type:
            candidate_contract_violations.append(
                _candidate_violation(
                    index,
                    "invalid_semantic_type",
                    path=f"proposals[{index}].semantic_type",
                    detail={"actual_value": semantic_type},
                )
            )
            identity_valid = False

        if not isinstance(text, str):
            candidate_contract_violations.append(
                _candidate_violation(
                    index,
                    "invalid_text",
                    path=f"proposals[{index}].text",
                    detail={"actual_type": type(text).__name__},
                )
            )
            text = f"<candidate-{index}-text-invalid>"

        if not isinstance(evidence_value, list):
            candidate_contract_violations.append(
                _candidate_violation(
                    index,
                    "evidence_ids_not_list",
                    path=f"proposals[{index}].evidence_ids",
                    detail={"actual_type": type(evidence_value).__name__},
                )
            )
            evidence_ids: list[str] = []
        else:
            evidence_ids = []
            for evidence_position, evidence_id in enumerate(evidence_value):
                if isinstance(evidence_id, str):
                    evidence_ids.append(evidence_id)
                else:
                    candidate_contract_violations.append(
                        _candidate_violation(
                            index,
                            "invalid_evidence_id",
                            path=(
                                f"proposals[{index}].evidence_ids"
                                f"[{evidence_position}]"
                            ),
                            detail={"actual_value": evidence_id},
                        )
                    )

        meaning, meaning_violations = _candidate_meaning_tolerant(
            item.get("benchmark_meaning"),
            index,
        )
        candidate_contract_violations.extend(meaning_violations)

        if not identity_valid:
            unscoreable_candidates.append(
                {
                    "candidate_index": index,
                    "reason": "invalid_semantic_identity",
                    "candidate_text": text,
                }
            )
            continue

        assert isinstance(claim_id, str)
        assert isinstance(semantic_type, str)

        if claim_id not in claims:
            candidate_contract_violations.append(
                _candidate_violation(
                    index,
                    "unknown_parent_claim",
                    path=f"proposals[{index}].source_claim_id",
                    detail={"source_claim_id": claim_id},
                )
            )
            unscoreable_candidates.append(
                {
                    "candidate_index": index,
                    "reason": "unknown_parent_claim",
                    "source_claim_id": claim_id,
                    "semantic_type": semantic_type,
                    "candidate_text": text,
                }
            )
            continue

        owned = _evidence_by_id(claims[claim_id])
        for evidence_id in evidence_ids:
            if evidence_id not in owned:
                candidate_contract_violations.append(
                    _candidate_violation(
                        index,
                        "evidence_not_owned_by_parent",
                        path=f"proposals[{index}].evidence_ids",
                        detail={
                            "source_claim_id": claim_id,
                            "evidence_id": evidence_id,
                        },
                    )
                )

        proposal = dict(item)
        proposal["source_claim_id"] = claim_id
        proposal["semantic_type"] = semantic_type
        proposal["text"] = text
        proposal["evidence_ids"] = evidence_ids
        proposal["benchmark_meaning"] = meaning
        candidate_contract_violations.extend(
            _validate_candidate_against_contract(
                proposal,
                index,
                validated_contract,
            )
        )
        proposals.append(proposal)

    argument_grounding_diagnostics: list[dict[str, Any]] = []
    semantic_role_violations: list[dict[str, Any]] = []
    if validated_grounding_policy is not None:
        for candidate_index, item in enumerate(proposals):
            if item["benchmark_meaning"] is None:
                continue
            source_text = _claim_effective_text(claims[item["source_claim_id"]])
            grounding = audit_arguments(
                item["benchmark_meaning"]["arguments"],
                source_text,
            )
            argument_grounding_diagnostics.append(
                {
                    "candidate_index": candidate_index,
                    "source_claim_id": item["source_claim_id"],
                    "semantic_type": item["semantic_type"],
                    **grounding,
                }
            )
            for key, record in grounding["records"].items():
                if record.get("state") in {
                    "ambiguous",
                    "domain_mismatch",
                    "scalar_type_violation",
                    "ungrounded",
                    "ungrounded_pair",
                    "unknown_role",
                    "unsupported_literal",
                    "unsupported_unit",
                }:
                    semantic_role_violations.append(
                        {
                            "candidate_index": candidate_index,
                            "source_claim_id": item["source_claim_id"],
                            "semantic_type": item["semantic_type"],
                            "argument_key": key,
                            "state": record.get("state"),
                            "record": record,
                        }
                    )

    global_exact_duplicate_candidates: list[dict[str, Any]] = []
    first_identity: dict[str, int] = {}
    for candidate_index, item in enumerate(proposals):
        identity = _proposal_identity(item)
        if identity is None:
            continue
        if identity in first_identity:
            global_exact_duplicate_candidates.append(
                {
                    "candidate_index": candidate_index,
                    "duplicate_of_candidate_index": first_identity[identity],
                    "identity_sha256": identity,
                }
            )
        else:
            first_identity[identity] = candidate_index

    duplicate_evidence_candidates: list[dict[str, Any]] = []
    policy_violations: list[dict[str, Any]] = []
    extras: list[dict[str, Any]] = []
    candidates_by_group: dict[
        tuple[str, str],
        list[tuple[int, dict[str, Any]]],
    ] = {}

    for candidate_index, item in enumerate(proposals):
        evidence_ids = list(item["evidence_ids"])
        if len(evidence_ids) != len(set(evidence_ids)):
            duplicate_evidence_candidates.append(
                {
                    "candidate_index": candidate_index,
                    "candidate_text": item["text"],
                    "duplicate_evidence_ids": sorted(
                        evidence_id
                        for evidence_id in set(evidence_ids)
                        if evidence_ids.count(evidence_id) > 1
                    ),
                }
            )

        matched_exclusion = next(
            (rule for rule in excluded if _matches_forbidden(item, rule)),
            None,
        )
        if matched_exclusion is not None:
            policy_violations.append(
                {
                    "candidate_index": candidate_index,
                    "candidate_text": item["text"],
                    "excluded_id": matched_exclusion.get("id"),
                    "reason": matched_exclusion.get("reason"),
                    "source_claim_id": item["source_claim_id"],
                    "semantic_type": item["semantic_type"],
                }
            )
            continue

        if item["benchmark_meaning"] is None:
            extras.append(
                {
                    "candidate_index": candidate_index,
                    "candidate_text": item["text"],
                    "source_claim_id": item["source_claim_id"],
                    "semantic_type": item["semantic_type"],
                    "reason": "missing_structured_meaning",
                }
            )
            continue

        group = (item["source_claim_id"], item["semantic_type"])
        if group not in required_groups and group not in admissible_groups:
            extras.append(
                {
                    "candidate_index": candidate_index,
                    "candidate_text": item["text"],
                    "source_claim_id": item["source_claim_id"],
                    "semantic_type": item["semantic_type"],
                    "reason": "not_in_required_or_admissible_fixture_group",
                }
            )
            continue
        candidates_by_group.setdefault(group, []).append((candidate_index, item))

    alignments: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    duplicate_required_candidates: list[dict[str, Any]] = []
    assigned_candidate_indices: set[int] = set()

    for group, gold_items in required_groups.items():
        candidates = candidates_by_group.get(group, [])
        required_source_text = (
            _claim_effective_text(claims[group[0]])
            if validated_grounding_policy is not None
            else None
        )
        assignments, leftovers = _align_group(
            gold_items,
            candidates,
            source_text=required_source_text,
            grounding_policy=validated_grounding_policy,
        )
        group_assigned_indices = {
            candidate_index
            for candidate_index, _candidate in assignments.values()
        }
        for candidate_index, candidate in leftovers:
            extras.append(
                {
                    "candidate_index": candidate_index,
                    "candidate_text": candidate["text"],
                    "source_claim_id": candidate["source_claim_id"],
                    "semantic_type": candidate["semantic_type"],
                    "reason": "unassigned_candidate_in_required_group",
                }
            )
        for gold in gold_items:
            gold_id = str(gold["id"])
            expected = _meaning(gold["meaning"])
            assigned = assignments.get(gold_id)
            if assigned is None:
                missing.append(
                    {
                        "gold_id": gold["id"],
                        "source_claim_id": gold["source_claim_id"],
                        "semantic_type": gold["semantic_type"],
                        "facet": expected["facet"],
                        "canonical_text": gold["canonical_text"],
                    }
                )
                continue
            candidate_index, candidate = assigned
            assigned_candidate_indices.add(candidate_index)
            comparison = _compare_meaning_grounded(
                expected,
                candidate["benchmark_meaning"],
                source_text=required_source_text,
                grounding_policy=validated_grounding_policy,
            )
            required_ids = set(map(str, gold["minimal_evidence_ids"]))
            selected_ids = set(map(str, candidate["evidence_ids"]))
            provenance_sufficient = required_ids.issubset(selected_ids)
            exact_minimal = selected_ids == required_ids

            if comparison["status"] in {
                "ambiguous",
                "contradicted",
                "grounding_failed",
                "grounded_unresolved",
                "overclaimed",
            }:
                entailment_status = comparison["status"]
            elif not provenance_sufficient:
                entailment_status = "insufficient_evidence"
            else:
                entailment_status = "entailed"

            exact_duplicates = [
                index
                for index, other in candidates
                if index != candidate_index
                and _compare_meaning(expected, other["benchmark_meaning"])["status"]
                == "match"
            ]
            if exact_duplicates:
                duplicate_required_candidates.append(
                    {
                        "gold_id": gold_id,
                        "selected_candidate_index": candidate_index,
                        "duplicate_candidate_indices": sorted(exact_duplicates),
                    }
                )

            conflicting_duplicate_indices = [
                index
                for index, other in candidates
                if index != candidate_index
                and index not in group_assigned_indices
                and _essential_identity_matches(
                    expected,
                    other["benchmark_meaning"],
                )
                and _compare_meaning(
                    expected,
                    other["benchmark_meaning"],
                )["status"]
                == "contradicted"
            ]

            alignments.append(
                {
                    "gold_id": gold["id"],
                    "candidate_index": candidate_index,
                    "source_claim_id": gold["source_claim_id"],
                    "semantic_type": gold["semantic_type"],
                    "facet": expected["facet"],
                    "canonical_text": gold["canonical_text"],
                    "candidate_text": candidate["text"],
                    "expected_meaning": expected,
                    "candidate_meaning": candidate["benchmark_meaning"],
                    "meaning_comparison": comparison,
                    "minimal_evidence_ids": list(gold["minimal_evidence_ids"]),
                    "candidate_evidence_ids": list(candidate["evidence_ids"]),
                    "missing_required_evidence_ids": sorted(
                        required_ids - selected_ids
                    ),
                    "extra_evidence_ids": sorted(selected_ids - required_ids),
                    "provenance_sufficient": provenance_sufficient,
                    "exact_minimal_evidence": exact_minimal,
                    "evidence_jaccard": _jaccard(required_ids, selected_ids),
                    "entailment_status": entailment_status,
                    "conflicting_duplicate_candidate_indices": sorted(
                        conflicting_duplicate_indices
                    ),
                }
            )

    admissible_hits: list[dict[str, Any]] = []
    duplicate_admissible_candidates: list[dict[str, Any]] = []
    for group, gold_items in admissible_groups.items():
        candidates = candidates_by_group.get(group, [])
        admissible_source_text = (
            _claim_effective_text(claims[group[0]])
            if validated_grounding_policy is not None
            else None
        )
        assignments, leftovers = _align_group(
            gold_items,
            candidates,
            source_text=admissible_source_text,
            grounding_policy=validated_grounding_policy,
        )
        for candidate_index, candidate in leftovers:
            extras.append(
                {
                    "candidate_index": candidate_index,
                    "candidate_text": candidate["text"],
                    "source_claim_id": candidate["source_claim_id"],
                    "semantic_type": candidate["semantic_type"],
                    "reason": "unassigned_candidate_in_admissible_group",
                }
            )
        for gold in gold_items:
            gold_id = str(gold["id"])
            assigned = assignments.get(gold_id)
            if assigned is None:
                continue
            candidate_index, candidate = assigned
            expected = _meaning(gold["meaning"])
            comparison = _compare_meaning_grounded(
                expected,
                candidate["benchmark_meaning"],
                source_text=admissible_source_text,
                grounding_policy=validated_grounding_policy,
            )
            required_ids = set(map(str, gold["minimal_evidence_ids"]))
            selected_ids = set(map(str, candidate["evidence_ids"]))
            provenance = required_ids.issubset(selected_ids)
            if comparison["status"] == "match" and provenance:
                status = "review_only_supported"
            elif comparison["status"] == "match":
                status = "insufficient_evidence"
            else:
                status = comparison["status"]
            exact_duplicates = [
                index
                for index, other in candidates
                if index != candidate_index
                and _compare_meaning(expected, other["benchmark_meaning"])["status"]
                == "match"
            ]
            if exact_duplicates:
                duplicate_admissible_candidates.append(
                    {
                        "gold_id": gold_id,
                        "selected_candidate_index": candidate_index,
                        "duplicate_candidate_indices": sorted(exact_duplicates),
                    }
                )
            admissible_hits.append(
                {
                    "candidate_index": candidate_index,
                    "gold_id": gold["id"],
                    "status": status,
                    "meaning_comparison": comparison,
                    "provenance_sufficient": provenance,
                    "exact_minimal_evidence": selected_ids == required_ids,
                }
            )

    # De-duplicate extras by candidate index/reason if the same leftover was seen twice.
    deduped_extras: list[dict[str, Any]] = []
    seen_extra: set[tuple[int, str]] = set()
    for item in extras:
        key = (int(item["candidate_index"]), str(item["reason"]))
        if key not in seen_extra:
            seen_extra.add(key)
            deduped_extras.append(item)
    extras = deduped_extras

    statuses = [item["entailment_status"] for item in alignments]
    critical_contradiction_indices = {
        int(item["candidate_index"])
        for item in alignments
        if item["entailment_status"] == "contradicted"
    }
    critical_contradiction_indices.update(
        int(index)
        for item in alignments
        for index in item["conflicting_duplicate_candidate_indices"]
    )
    critical_contradictions = len(critical_contradiction_indices)
    aligned = len(alignments)
    sufficient = sum(item["provenance_sufficient"] for item in alignments)
    provenance_insufficient = aligned - sufficient
    nonminimal_sufficient = sum(
        item["provenance_sufficient"] and not item["exact_minimal_evidence"]
        for item in alignments
    )
    admissible_issues = [
        item for item in admissible_hits
        if item["status"] != "review_only_supported"
    ]

    blocking_reasons: list[str] = []
    if missing:
        blocking_reasons.append(f"missing_required={len(missing)}")
    if provenance_insufficient:
        blocking_reasons.append(
            f"required_provenance_insufficient={provenance_insufficient}"
        )
    if critical_contradictions:
        blocking_reasons.append(
            f"critical_contradictions={critical_contradictions}"
        )
    if statuses.count("ambiguous"):
        blocking_reasons.append(
            f"ambiguous_required={statuses.count('ambiguous')}"
        )
    if statuses.count("overclaimed"):
        blocking_reasons.append(
            f"overclaimed_required={statuses.count('overclaimed')}"
        )
    if statuses.count("grounded_unresolved"):
        blocking_reasons.append(
            "grounded_unresolved_required="
            f"{statuses.count('grounded_unresolved')}"
        )
    if statuses.count("grounding_failed"):
        blocking_reasons.append(
            f"grounding_failed_required={statuses.count('grounding_failed')}"
        )
    if policy_violations:
        blocking_reasons.append(
            "forbidden_inference_policy_violations="
            f"{len(policy_violations)}"
        )
    if extras:
        blocking_reasons.append(
            f"unexpected_extra_candidates={len(extras)}"
        )
    if duplicate_required_candidates:
        blocking_reasons.append(
            "duplicate_required_candidates="
            f"{len(duplicate_required_candidates)}"
        )
    if duplicate_evidence_candidates:
        blocking_reasons.append(
            "duplicate_evidence_candidates="
            f"{len(duplicate_evidence_candidates)}"
        )
    if nonminimal_sufficient:
        blocking_reasons.append(
            "nonminimal_sufficient_evidence_sets="
            f"{nonminimal_sufficient}"
        )
    if admissible_issues:
        blocking_reasons.append(
            f"admissible_output_issues={len(admissible_issues)}"
        )
    if duplicate_admissible_candidates:
        blocking_reasons.append(
            "duplicate_admissible_candidates="
            f"{len(duplicate_admissible_candidates)}"
        )
    if candidate_contract_violations:
        blocking_reasons.append(
            "candidate_contract_violations="
            f"{len(candidate_contract_violations)}"
        )
    if global_exact_duplicate_candidates:
        blocking_reasons.append(
            "global_exact_duplicate_candidates="
            f"{len(global_exact_duplicate_candidates)}"
        )
    if semantic_role_violations:
        blocking_reasons.append(
            "semantic_role_violations="
            f"{len(semantic_role_violations)}"
        )

    required_count = len(required)
    return {
        "schema_version": "2.3.3-grounded-alignment-v1.1",
        "candidate_label": label,
        "candidate_count": emitted_candidate_count,
        "scoreable_candidate_count": len(proposals),
        "meaning_contract": {
            "natural_language_parsing_in_core": False,
            "candidate_required_fields": ["relation", "arguments"],
            "candidate_facet_required": False,
            "candidate_facet_used_for_alignment": False,
            "golden_facet_role": "reporting_only",
            "alignment_group": ["source_claim_id", "semantic_type"],
            "alignment_relation_priority": "exact relation required",
            "argument_grounding_policy_sha256": (
                GROUNDING_POLICY_V1_1_SHA256
                if validated_grounding_policy is not None
                else None
            ),
            "essential_arguments": "exact scalar comparison",
            "numeric_comparison": "Decimal-normalized numeric equality",
            "unit_conversion": False,
            "unexpected_arguments": "blocking overclaim",
            "provider_candidate_errors_fatal": False,
            "benchmark_asset_errors_fatal": True,
        },
        "candidate_contract": {
            "provided": validated_contract is not None,
            "ontology_version": (
                validated_contract.get("ontology_version")
                if validated_contract is not None
                else None
            ),
            "violation_count": len(candidate_contract_violations),
            "violations": candidate_contract_violations,
            "unscoreable_candidate_count": len(unscoreable_candidates),
            "unscoreable_candidates": unscoreable_candidates,
            "policy": (
                "provider-output defects are scored and gate-blocking; "
                "fixture/export/contract corruption remains fatal"
            ),
        },
        "strict_coverage": {
            "required": required_count,
            "detected": aligned,
            "missing": len(missing),
            "rate": round(aligned / required_count, 6) if required_count else 1.0,
        },
        "provenance": {
            "aligned": aligned,
            "sufficient": sufficient,
            "insufficient": provenance_insufficient,
            "rate": round(sufficient / aligned, 6) if aligned else 1.0,
            "exact_minimal_evidence_sets": sum(
                item["exact_minimal_evidence"] for item in alignments
            ),
            "nonminimal_sufficient_evidence_sets": nonminimal_sufficient,
        },
        "entailment_polarity": {
            "entailed": statuses.count("entailed"),
            "contradicted": statuses.count("contradicted"),
            "ambiguous": statuses.count("ambiguous"),
            "overclaimed": statuses.count("overclaimed"),
            "grounded_unresolved": statuses.count("grounded_unresolved"),
            "grounding_failed": statuses.count("grounding_failed"),
            "insufficient_evidence": statuses.count("insufficient_evidence"),
            "critical_contradictions": critical_contradictions,
        },
        "admissible": {
            "fixture_count": len(admissible),
            "detected_unique": len(admissible_hits),
            "emitted": len(admissible_hits),
            "supported_review_only": sum(
                item["status"] == "review_only_supported"
                for item in admissible_hits
            ),
            "issues": admissible_issues,
            "duplicates": duplicate_admissible_candidates,
            "detections": admissible_hits,
        },
        "policy_violations": policy_violations,
        "argument_grounding": {
            "enabled": validated_grounding_policy is not None,
            "policy_sha256": (
                GROUNDING_POLICY_V1_1_SHA256
                if validated_grounding_policy is not None
                else None
            ),
            "candidate_diagnostics": argument_grounding_diagnostics,
            "semantic_role_violation_count": len(semantic_role_violations),
            "semantic_role_violations": semantic_role_violations,
        },
        "global_exact_duplicate_candidates": global_exact_duplicate_candidates,
        "unexpected_extra_candidates": extras,
        "duplicate_required_candidates": duplicate_required_candidates,
        "duplicate_evidence_candidates": duplicate_evidence_candidates,
        "benchmark_gate": {
            "pass": not blocking_reasons,
            "blocking_reasons": blocking_reasons,
        },
        "provider_certification": {
            "certified": False,
            "reason": "benchmark_suite_not_provider_certification",
        },
        "missing_required": missing,
        "alignments": sorted(alignments, key=lambda item: str(item["gold_id"])),
        "scientific_correctness_measured": False,
    }
