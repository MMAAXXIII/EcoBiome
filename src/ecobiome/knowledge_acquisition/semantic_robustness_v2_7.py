"""Source-independent semantic robustness controls for EcoBiome V2.7."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

REGISTRY_V2_7_SHA256 = "f7c2d966a60d5b1f3accbbf60cd94afd7b394e3d1a6bcbe19bd1088fb4819f5b"
MULTILINGUAL_COORDINATION_POLICY_V1_1_SHA256 = (
    "c58ebe6b2b2a2114bfd2cd03a2bec7de0665fc63333356a2f82fa6a87825b872"
)
LEGACY_EPISTEMIC_COVERAGE_V1_SHA256 = (
    "801615c06ac5ce2f40a7938033c89d0fbb139f2483c17996d3a9dc127f1d389b"
)
PROVIDER_PROVENANCE_CONSTRAINT_V1_1_SHA256 = (
    "328a34a1ac913dc99bd2079f6a9f2676795c04a9da56a397c6f7d8a59895cef0"
)


def _canonical_sha(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _validate_object(
    payload: Any,
    *,
    expected_sha: str,
    label: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError(f"{label} must be an object")
    actual = _canonical_sha(payload)
    if actual != expected_sha:
        raise ValueError(f"unexpected {label} SHA: {actual}")
    return payload


def validate_registry_v2_7(registry: Any) -> dict[str, Any]:
    validated = _validate_object(
        registry,
        expected_sha=REGISTRY_V2_7_SHA256,
        label="V2.7 registry",
    )
    relations = validated.get("relations")
    if not isinstance(relations, dict) or len(relations) != 63:
        raise ValueError("V2.7 registry must contain exactly 63 relations")
    missing = [
        relation
        for relation, spec in relations.items()
        if not isinstance(spec, dict)
        or not isinstance(spec.get("epistemic_class"), str)
    ]
    if missing:
        raise ValueError(
            "V2.7 registry relations lack epistemic_class: "
            + ", ".join(sorted(missing))
        )
    return validated


def validate_multilingual_coordination_policy(
    policy: Any,
) -> dict[str, Any]:
    return _validate_object(
        policy,
        expected_sha=MULTILINGUAL_COORDINATION_POLICY_V1_1_SHA256,
        label="multilingual coordination policy V1.1",
    )


def validate_legacy_epistemic_coverage_policy(
    policy: Any,
) -> dict[str, Any]:
    validated = _validate_object(
        policy,
        expected_sha=LEGACY_EPISTEMIC_COVERAGE_V1_SHA256,
        label="legacy epistemic coverage policy V1",
    )
    mapping = validated.get("all_relation_epistemic_class")
    if not isinstance(mapping, dict) or len(mapping) != 63:
        raise ValueError(
            "legacy epistemic coverage policy must map exactly 63 relations"
        )
    return validated


def validate_provider_provenance_policy(
    policy: Any,
) -> dict[str, Any]:
    return _validate_object(
        policy,
        expected_sha=PROVIDER_PROVENANCE_CONSTRAINT_V1_1_SHA256,
        label="provider provenance policy V1.1",
    )


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _language_pack(
    policy: dict[str, Any],
    language: str | None,
) -> dict[str, Any] | None:
    packs = policy.get("language_packs")
    if not isinstance(packs, dict) or not isinstance(language, str):
        return None
    normalized = language.strip().casefold().replace("_", "-")
    primary = normalized.partition("-")[0]
    pack = packs.get(normalized, packs.get(primary))
    return pack if isinstance(pack, dict) else None


def _contains_token(surface: str, token: str) -> bool:
    return bool(
        re.search(
            rf"(?<!\w){re.escape(token.casefold())}(?!\w)",
            surface.casefold(),
            flags=re.UNICODE,
        )
    )


def _coordination_matches(
    surface: str,
    pack: dict[str, Any] | None,
) -> list[str]:
    if pack is None:
        return []

    normalized = _normalize(surface)
    matches: list[str] = []

    single = pack.get("single", [])
    if isinstance(single, list):
        for token in single:
            if isinstance(token, str) and _contains_token(normalized, token):
                matches.append(f"single:{token}")

    paired = pack.get("paired", [])
    if isinstance(paired, list):
        for pair in paired:
            if (
                isinstance(pair, list)
                and len(pair) == 2
                and all(isinstance(item, str) for item in pair)
            ):
                left, right = pair
                if _contains_token(normalized, left) and _contains_token(
                    normalized,
                    right,
                ):
                    matches.append(f"paired:{left}...{right}")

    return sorted(set(matches))


def coordinated_span_state_multilingual(
    role: str,
    surface: str,
    source_text: str,
    policy: Any,
    *,
    language: str | None,
) -> dict[str, Any]:
    validated = validate_multilingual_coordination_policy(policy)
    normalized_surface = _normalize(surface)
    normalized_source = _normalize(source_text)
    grounded = bool(normalized_surface) and normalized_surface in normalized_source

    pack = _language_pack(validated, language)
    matches = _coordination_matches(surface, pack)
    coordinated = bool(matches)

    eligible_roles = validated.get("eligible_roles")
    if not isinstance(eligible_roles, list):
        raise TypeError("coordination policy eligible_roles must be a list")

    if not grounded:
        state = "ungrounded"
    elif not coordinated:
        state = "grounded_scalar_unresolved"
    elif role not in {str(item) for item in eligible_roles}:
        state = str(validated["ineligible_coordinated_state"])
    else:
        state = str(validated["grounded_coordinated_state"])

    return {
        "state": state,
        "role": role,
        "surface": surface,
        "language": language,
        "language_supported": pack is not None,
        "coordination_matches": matches,
        "source_grounded": grounded,
        "coordinated": coordinated,
        "scientifically_scoreable": False,
    }


def relation_epistemic_class_v2_7(
    registry: Any,
    relation: str,
) -> str | None:
    validated = validate_registry_v2_7(registry)
    spec = validated["relations"].get(relation)
    if not isinstance(spec, dict):
        return None
    value = spec.get("epistemic_class")
    return value if isinstance(value, str) else None


def classify_epistemic_transition_v2_7(
    expected_class: str,
    candidate_class: str,
    policy: Any,
) -> dict[str, Any]:
    validated = validate_legacy_epistemic_coverage_policy(policy)

    taxonomy = validated.get("taxonomy")
    if not isinstance(taxonomy, dict):
        raise TypeError("epistemic taxonomy must be an object")
    known = {str(item) for item in taxonomy}

    if expected_class not in known:
        raise ValueError(f"unknown expected epistemic class: {expected_class}")
    if candidate_class not in known:
        raise ValueError(f"unknown candidate epistemic class: {candidate_class}")

    raw_forbidden = validated.get("forbidden_assertion_strength_upgrades")
    if not isinstance(raw_forbidden, list):
        raise TypeError("forbidden assertion-strength upgrades must be a list")
    forbidden = {
        (item["expected"], item["candidate"])
        for item in raw_forbidden
        if isinstance(item, dict)
        and isinstance(item.get("expected"), str)
        and isinstance(item.get("candidate"), str)
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
        "contradicted_by_class_mismatch_alone": False,
    }


def _source_ids(
    source_request: Any,
) -> tuple[list[str], list[str], dict[str, set[str]]]:
    if not isinstance(source_request, dict):
        raise TypeError("source request must be an object")

    source_claims = source_request.get("source_claims")
    if not isinstance(source_claims, list):
        raise TypeError("source_request.source_claims must be a list")

    claim_ids: list[str] = []
    evidence_ids: list[str] = []
    ownership: dict[str, set[str]] = {}

    for claim in source_claims:
        if not isinstance(claim, dict):
            raise TypeError("source request Claim must be an object")
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id:
            raise ValueError("source request Claim lacks claim_id")
        if claim_id in ownership:
            raise ValueError(f"duplicate source Claim ID: {claim_id}")

        raw_evidence = claim.get("evidence")
        if not isinstance(raw_evidence, list) or not raw_evidence:
            raise ValueError(f"source Claim {claim_id} lacks Evidence")

        owned: set[str] = set()
        for item in raw_evidence:
            if not isinstance(item, dict):
                raise TypeError("source request Evidence must be an object")
            evidence_id = item.get("evidence_id")
            if not isinstance(evidence_id, str) or not evidence_id:
                raise ValueError(
                    f"source Claim {claim_id} has invalid Evidence ID"
                )
            if evidence_id in owned:
                raise ValueError(
                    f"source Claim {claim_id} repeats Evidence ID {evidence_id}"
                )
            owned.add(evidence_id)
            evidence_ids.append(evidence_id)

        claim_ids.append(claim_id)
        ownership[claim_id] = owned

    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError(
            "Evidence IDs must be globally unique in the provider batch"
        )

    return claim_ids, evidence_ids, ownership


def constrain_provider_output_schema_v1_1(
    schema: Any,
    source_request: Any,
    policy: Any,
) -> dict[str, Any]:
    validate_provider_provenance_policy(policy)

    if not isinstance(schema, dict):
        raise TypeError("provider schema must be an object")

    claim_ids, evidence_ids, _ = _source_ids(source_request)
    constrained = copy.deepcopy(schema)

    try:
        proposal = constrained["properties"]["p"]["items"]
        properties = proposal["properties"]
        claim_schema = properties["c"]
        evidence_schema = properties["e"]
        evidence_item_schema = evidence_schema["items"]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            "provider schema does not expose compact c/e proposal fields"
        ) from exc

    if not isinstance(claim_schema, dict) or not isinstance(
        evidence_item_schema,
        dict,
    ):
        raise TypeError("provider c/e schemas must be objects")

    claim_schema["enum"] = sorted(claim_ids)
    evidence_item_schema["enum"] = sorted(evidence_ids)
    evidence_schema["minItems"] = 1
    evidence_schema["uniqueItems"] = True

    return constrained


def audit_provider_provenance_v1_1(
    compact_payload: Any,
    source_request: Any,
    policy: Any,
) -> dict[str, Any]:
    validate_provider_provenance_policy(policy)
    claim_ids, evidence_ids, ownership = _source_ids(source_request)
    known_claims = set(claim_ids)
    known_evidence = set(evidence_ids)

    proposals = (
        compact_payload.get("p", [])
        if isinstance(compact_payload, dict)
        else []
    )
    if not isinstance(proposals, list):
        raise TypeError("provider compact payload p must be a list")

    violations: list[dict[str, Any]] = []

    for index, proposal in enumerate(proposals):
        if not isinstance(proposal, dict):
            violations.append(
                {
                    "candidate_index": index,
                    "reason": "proposal_not_object",
                }
            )
            continue

        claim_id = proposal.get("c")
        raw_evidence = proposal.get("e")

        if not isinstance(claim_id, str) or claim_id not in known_claims:
            violations.append(
                {
                    "candidate_index": index,
                    "reason": "unknown_claim_id",
                    "claim_id": claim_id,
                }
            )
            continue

        if (
            not isinstance(raw_evidence, list)
            or not raw_evidence
            or not all(isinstance(item, str) for item in raw_evidence)
        ):
            violations.append(
                {
                    "candidate_index": index,
                    "reason": "invalid_evidence_ids",
                }
            )
            continue

        if len(raw_evidence) != len(set(raw_evidence)):
            violations.append(
                {
                    "candidate_index": index,
                    "reason": "duplicate_evidence_id",
                }
            )

        unknown = [
            item
            for item in raw_evidence
            if item not in known_evidence
        ]
        if unknown:
            violations.append(
                {
                    "candidate_index": index,
                    "reason": "unknown_evidence_id",
                    "evidence_ids": unknown,
                }
            )

        foreign = [
            item
            for item in raw_evidence
            if item in known_evidence
            and item not in ownership[claim_id]
        ]
        if foreign:
            violations.append(
                {
                    "candidate_index": index,
                    "reason": "foreign_parent_evidence_id",
                    "evidence_ids": foreign,
                }
            )

    return {
        "violation_count": len(violations),
        "violations": violations,
        "blocking": bool(violations),
    }
