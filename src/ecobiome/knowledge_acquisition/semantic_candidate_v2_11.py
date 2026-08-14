"""Provider-neutral canonical semantic candidates — EcoBiome V2.11.

V2.11 sits after V2.9 Claim/Evidence admission and deterministic grounding.
It preserves V2.10 relation/type semantics without granting scientific
acceptance. Native floats are forbidden from the canonical candidate payload.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections.abc import Mapping
from typing import Any

from ecobiome.knowledge_acquisition.provider_provenance_v2_9 import (
    CLAIM_SCOPED_PROVENANCE_POLICY_V2_9_CANONICAL_SHA256,
)
from ecobiome.knowledge_acquisition.provider_provenance_v2_9 import (
    canonical_json_sha256 as provider_canonical_json_sha256,
)
from ecobiome.knowledge_acquisition.semantic_grounding import (
    GROUNDING_POLICY_V1_1_SHA256,
    NUMERIC_ROLES,
    OPAQUE_OPEN_TEXT_ROLES_V1_2,
    audit_arguments,
    normalize_space_case,
)
from ecobiome.knowledge_persistence.serialization import (
    canonical_json_text,
    canonical_sha256,
    normalize_decimal,
)

SEMANTIC_CANDIDATE_V2_11_SCHEMA_VERSION = (
    "ecobiome-canonical-semantic-candidate-v2.11"
)
SEMANTIC_CANDIDATE_V2_11_CONTRACT_NAME = (
    "ecobiome-canonical-semantic-candidate"
)
SEMANTIC_CANDIDATE_V2_11_CONTRACT_VERSION = "2.11"
RELATION_TYPE_BASIS_VERSION = "2.10"

PROMOTION_GROUNDING_COMPLETE = "grounding_complete"
PROMOTION_REQUIRES_SEMANTIC_RESOLUTION = "requires_semantic_resolution"

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


class SemanticCandidateV211Error(ValueError):
    """Raised when a V2.11 semantic candidate violates the frozen contract."""


def _require_mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SemanticCandidateV211Error(f"{label} must be an object")
    return value


def _require_nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise SemanticCandidateV211Error(f"{label} must be a non-empty string")
    return unicodedata.normalize("NFC", value)


def _reject_native_floats(value: object, path: str = "candidate") -> None:
    if isinstance(value, float):
        raise SemanticCandidateV211Error(
            f"native float forbidden in canonical V2.11 payload: {path}"
        )
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_native_floats(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_native_floats(item, f"{path}[{index}]")


def _source_text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalized_source_surface(source_text: str, value: str) -> str:
    """Recover a deterministic source surface for an opaque provider value."""
    stripped = value.strip()
    if not stripped:
        raise SemanticCandidateV211Error("opaque source text must be non-empty")

    direct = re.search(re.escape(stripped), source_text, flags=re.IGNORECASE)
    if direct is not None:
        return unicodedata.normalize("NFC", direct.group(0))

    parts = [part for part in re.split(r"\s+", stripped) if part]
    if parts:
        pattern = r"\s+".join(re.escape(part) for part in parts)
        match = re.search(pattern, source_text, flags=re.IGNORECASE)
        if match is not None:
            return unicodedata.normalize("NFC", match.group(0))

    if normalize_space_case(stripped) in normalize_space_case(source_text):
        return unicodedata.normalize("NFC", stripped)

    raise SemanticCandidateV211Error(
        "grounding audit reported source text but no deterministic surface "
        "could be reconstructed"
    )


def _numeric_source_match(record: Mapping[str, Any]) -> Mapping[str, Any]:
    joint = record.get("joint_value_unit_pair")
    if isinstance(joint, Mapping):
        pair_match = joint.get("pair_match")
        if isinstance(pair_match, Mapping):
            value_match = pair_match.get("value_match")
            if isinstance(value_match, Mapping):
                return value_match

    source_match = record.get("source_match")
    if isinstance(source_match, Mapping):
        return source_match

    raise SemanticCandidateV211Error(
        "resolved numeric grounding lacks deterministic source match"
    )


def _unit_source_surface(record: Mapping[str, Any]) -> str:
    joint = record.get("joint_value_unit_pair")
    if isinstance(joint, Mapping):
        pair_match = joint.get("pair_match")
        if isinstance(pair_match, Mapping):
            unit_match = pair_match.get("unit_match")
            if isinstance(unit_match, Mapping):
                surface = unit_match.get("surface")
                if isinstance(surface, str) and surface:
                    return unicodedata.normalize("NFC", surface)

    matches = record.get("source_matches")
    if isinstance(matches, list) and matches:
        first = matches[0]
        if isinstance(first, Mapping):
            surface = first.get("surface")
            if isinstance(surface, str) and surface:
                return unicodedata.normalize("NFC", surface)

    surface = record.get("surface")
    if isinstance(surface, str) and surface:
        return unicodedata.normalize("NFC", surface)

    raise SemanticCandidateV211Error(
        "resolved unit grounding lacks deterministic source surface"
    )


def _decimal_text_from_source_match(
    source_match: Mapping[str, Any],
    canonical_value: object,
) -> str:
    surface = source_match.get("surface")
    method = source_match.get("method")

    if method == "english_number_word":
        if isinstance(canonical_value, bool) or not isinstance(
            canonical_value, int
        ):
            raise SemanticCandidateV211Error(
                "number-word grounding must resolve to an integer"
            )
        return normalize_decimal(canonical_value)

    if not isinstance(surface, str) or not surface:
        raise SemanticCandidateV211Error(
            "numeric literal grounding lacks source surface"
        )
    return normalize_decimal(surface.replace(",", "."))


def _canonical_argument_value(
    *,
    role: str,
    raw_value: object,
    record: Mapping[str, Any],
    source_text: str,
) -> dict[str, object]:
    state = _require_nonempty_string(record.get("state"), f"{role}.state")

    if role in NUMERIC_ROLES:
        if state != "resolved":
            raise SemanticCandidateV211Error(
                f"numeric role must be deterministically resolved: {role}"
            )
        match = _numeric_source_match(record)
        surface = _require_nonempty_string(
            match.get("surface"), f"{role}.source_surface"
        )
        canonical = _decimal_text_from_source_match(
            match,
            record.get("canonical_value"),
        )
        if role == "day":
            try:
                day = int(canonical)
            except ValueError as exc:
                raise SemanticCandidateV211Error(
                    "day must resolve to an integer"
                ) from exc
            if str(day) != canonical:
                raise SemanticCandidateV211Error(
                    "day must resolve to an integer"
                )
            return {
                "kind": "integer",
                "value": day,
                "source_surface": surface,
            }
        return {
            "kind": "decimal",
            "value": canonical,
            "source_surface": surface,
        }

    if role == "unit":
        if state != "resolved":
            raise SemanticCandidateV211Error(
                "unit must be deterministically resolved"
            )
        canonical = _require_nonempty_string(
            record.get("canonical_value"),
            "unit.canonical_value",
        )
        return {
            "kind": "controlled_literal",
            "value": canonical,
            "source_surface": _unit_source_surface(record),
        }

    if role == "temperature_scope":
        if not isinstance(raw_value, str):
            raise SemanticCandidateV211Error(
                "temperature_scope must be a string"
            )
        if state not in {"domain_valid_unresolved", "domain_unknown"}:
            raise SemanticCandidateV211Error(
                "temperature_scope failed typed-domain grounding"
            )
        source_surface = _normalized_source_surface(source_text, raw_value)
        return {
            "kind": "source_text",
            "canonical_text": normalize_space_case(source_surface),
            "source_surface": source_surface,
        }

    if role in OPAQUE_OPEN_TEXT_ROLES_V1_2:
        if not isinstance(raw_value, str):
            raise SemanticCandidateV211Error(
                f"opaque role must be a string: {role}"
            )
        if state != "grounded_opaque_unresolved":
            raise SemanticCandidateV211Error(
                f"opaque role is not source-grounded: {role}"
            )
        source_surface = _normalized_source_surface(source_text, raw_value)
        return {
            "kind": "source_text",
            "canonical_text": normalize_space_case(source_surface),
            "source_surface": source_surface,
        }

    raise SemanticCandidateV211Error(f"unsupported V2.11 role: {role}")


def _candidate_identity_projection(
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    """Return provider-neutral identity fields, excluding display surfaces."""

    def project(value: object) -> object:
        if isinstance(value, Mapping):
            result: dict[str, object] = {}
            for key, item in value.items():
                if key in {
                    "canonical_candidate_sha256",
                    "source_surface",
                }:
                    continue
                result[str(key)] = project(item)
            return result
        if isinstance(value, list):
            return [project(item) for item in value]
        if isinstance(value, tuple):
            return [project(item) for item in value]
        return value

    projected = project(candidate)
    if not isinstance(projected, dict):
        raise SemanticCandidateV211Error("candidate projection must be object")
    return projected


def semantic_candidate_sha256_v2_11(
    candidate: Mapping[str, Any],
) -> str:
    """Return provider-neutral SHA-256 for one canonical semantic candidate."""
    _reject_native_floats(candidate)
    return canonical_sha256(_candidate_identity_projection(candidate))


def _contract_descriptor(registry_v2_10: Mapping[str, Any]) -> dict[str, str]:
    registry_sha = provider_canonical_json_sha256(registry_v2_10)
    descriptor: dict[str, str] = {
        "name": SEMANTIC_CANDIDATE_V2_11_CONTRACT_NAME,
        "version": SEMANTIC_CANDIDATE_V2_11_CONTRACT_VERSION,
        "relation_type_basis_version": RELATION_TYPE_BASIS_VERSION,
        "relation_type_registry_sha256": registry_sha,
        "grounding_policy_sha256": GROUNDING_POLICY_V1_1_SHA256,
        "claim_scoped_provenance_policy_sha256": (
            CLAIM_SCOPED_PROVENANCE_POLICY_V2_9_CANONICAL_SHA256
        ),
    }
    descriptor["canonical_sha256"] = canonical_sha256(descriptor)
    return descriptor


def build_semantic_candidate_v2_11(
    survivor: Mapping[str, Any],
    source_request: Mapping[str, Any],
    registry_v2_10: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one provider-neutral V2.11 candidate from an admitted survivor."""
    if set(survivor) != {"c", "e", "t", "m"}:
        raise SemanticCandidateV211Error(
            "admitted survivor must contain exactly c/e/t/m"
        )

    claim_id = _require_nonempty_string(survivor.get("c"), "survivor.c")
    evidence_ids_raw = survivor.get("e")
    semantic_type = _require_nonempty_string(
        survivor.get("t"),
        "survivor.t",
    )
    meaning = _require_mapping(survivor.get("m"), "survivor.m")
    if set(meaning) != {"r", "a"}:
        raise SemanticCandidateV211Error(
            "survivor.m must contain exactly r/a"
        )

    relation = _require_nonempty_string(meaning.get("r"), "survivor.m.r")
    arguments = _require_mapping(meaning.get("a"), "survivor.m.a")

    source_claims = source_request.get("source_claims")
    if not isinstance(source_claims, list) or not source_claims:
        raise SemanticCandidateV211Error(
            "source_request must contain non-empty source_claims"
        )

    parent: Mapping[str, Any] | None = None
    for raw_claim in source_claims:
        claim = _require_mapping(raw_claim, "source Claim")
        if claim.get("claim_id") == claim_id:
            if parent is not None:
                raise SemanticCandidateV211Error(
                    f"duplicate source Claim ID: {claim_id}"
                )
            parent = claim

    if parent is None:
        raise SemanticCandidateV211Error(
            f"unknown source Claim ID: {claim_id}"
        )

    source_text = _require_nonempty_string(
        parent.get("effective_text"),
        "source Claim effective_text",
    )
    evidence = parent.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise SemanticCandidateV211Error(
            "source Claim must contain non-empty Evidence"
        )

    owned_evidence_ids: set[str] = set()
    for raw_evidence in evidence:
        item = _require_mapping(raw_evidence, "Evidence")
        evidence_id = _require_nonempty_string(
            item.get("evidence_id"),
            "Evidence.evidence_id",
        )
        if evidence_id in owned_evidence_ids:
            raise SemanticCandidateV211Error(
                f"duplicate Evidence ID in source Claim: {evidence_id}"
            )
        owned_evidence_ids.add(evidence_id)

    if not isinstance(evidence_ids_raw, list) or not evidence_ids_raw:
        raise SemanticCandidateV211Error(
            "survivor.e must be a non-empty array"
        )
    if not all(
        isinstance(item, str) and bool(item) for item in evidence_ids_raw
    ):
        raise SemanticCandidateV211Error(
            "survivor.e entries must be non-empty strings"
        )
    if len(evidence_ids_raw) != len(set(evidence_ids_raw)):
        raise SemanticCandidateV211Error(
            "survivor.e must not contain duplicates"
        )
    foreign = sorted(set(evidence_ids_raw) - owned_evidence_ids)
    if foreign:
        raise SemanticCandidateV211Error(
            f"survivor contains foreign Evidence IDs: {foreign}"
        )
    evidence_ids = sorted(evidence_ids_raw)

    relations = _require_mapping(
        registry_v2_10.get("relations"),
        "registry.relations",
    )
    spec = _require_mapping(
        relations.get(relation),
        f"registry relation {relation}",
    )
    if spec.get("semantic_type_contract_state") == "unresolved_blocked":
        raise SemanticCandidateV211Error(
            f"fail-closed relation cannot enter V2.11: {relation}"
        )

    allowed = spec.get("semantic_types_allowed")
    if not isinstance(allowed, list) or semantic_type not in allowed:
        raise SemanticCandidateV211Error(
            "semantic type is not allowed for relation"
        )

    argument_keys = spec.get("argument_keys")
    if not isinstance(argument_keys, list) or not all(
        isinstance(item, str) and item for item in argument_keys
    ):
        raise SemanticCandidateV211Error(
            f"invalid relation argument signature: {relation}"
        )
    if set(arguments) != set(argument_keys):
        raise SemanticCandidateV211Error(
            f"argument signature mismatch for relation: {relation}"
        )

    epistemic_class = _require_nonempty_string(
        spec.get("epistemic_class"),
        f"{relation}.epistemic_class",
    )

    role_semantics = _require_mapping(
        registry_v2_10.get("argument_role_semantics"),
        "registry.argument_role_semantics",
    )

    for role, raw_value in arguments.items():
        if isinstance(raw_value, float) and not math.isfinite(raw_value):
            raise SemanticCandidateV211Error(
                f"non-finite provider numeric value: {role}"
            )

    grounding = audit_arguments(dict(arguments), source_text)
    if grounding.get("blocking"):
        raise SemanticCandidateV211Error(
            "candidate no longer passes deterministic grounding"
        )

    records = _require_mapping(
        grounding.get("records"),
        "grounding.records",
    )
    canonical_arguments: list[dict[str, object]] = []
    unresolved = bool(grounding.get("unresolved"))

    for role in argument_keys:
        semantic = _require_mapping(
            role_semantics.get(role),
            f"argument role semantics {role}",
        )
        grounding_class = _require_nonempty_string(
            semantic.get("grounding_class"),
            f"{role}.grounding_class",
        )
        record = _require_mapping(records.get(role), f"grounding record {role}")
        state = _require_nonempty_string(
            record.get("state"),
            f"{role}.resolution_state",
        )
        value = _canonical_argument_value(
            role=role,
            raw_value=arguments[role],
            record=record,
            source_text=source_text,
        )
        canonical_arguments.append(
            {
                "role": role,
                "grounding_class": grounding_class,
                "resolution_state": state,
                "value": value,
            }
        )

    candidate: dict[str, Any] = {
        "schema_version": SEMANTIC_CANDIDATE_V2_11_SCHEMA_VERSION,
        "contract": _contract_descriptor(registry_v2_10),
        "source": {
            "source_statement_claim_id": claim_id,
            "source_claim_effective_text_sha256": _source_text_sha256(
                source_text
            ),
            "evidence_ids": evidence_ids,
        },
        "semantic": {
            "semantic_type": semantic_type,
            "relation": relation,
            "epistemic_class": epistemic_class,
            "arguments": canonical_arguments,
        },
        "promotion_readiness": (
            PROMOTION_REQUIRES_SEMANTIC_RESOLUTION
            if unresolved
            else PROMOTION_GROUNDING_COMPLETE
        ),
        "automatic_scientific_acceptance": False,
    }
    _reject_native_floats(candidate)
    candidate["canonical_candidate_sha256"] = (
        semantic_candidate_sha256_v2_11(candidate)
    )
    validate_semantic_candidate_v2_11(candidate)
    return candidate



def build_semantic_candidates_v2_11(
    admission: Mapping[str, Any],
    source_request: Mapping[str, Any],
    registry_v2_10: Mapping[str, Any],
) -> dict[str, Any]:
    """Canonicalize and deduplicate all survivors from one V2.9 admission."""
    if admission.get("automatic_scientific_acceptance") is not False:
        raise SemanticCandidateV211Error(
            "admission must explicitly deny automatic scientific acceptance"
        )
    survivors = admission.get("survivors")
    if not isinstance(survivors, list):
        raise SemanticCandidateV211Error(
            "admission.survivors must be an array"
        )

    expected_count = admission.get("survivor_count")
    if (
        isinstance(expected_count, bool)
        or not isinstance(expected_count, int)
        or expected_count != len(survivors)
    ):
        raise SemanticCandidateV211Error(
            "admission survivor_count does not match survivors"
        )

    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    removed = 0

    for raw_survivor in survivors:
        survivor = _require_mapping(raw_survivor, "admission survivor")
        candidate = build_semantic_candidate_v2_11(
            survivor,
            source_request,
            registry_v2_10,
        )
        identity = candidate["canonical_candidate_sha256"]
        if identity in seen:
            removed += 1
            continue
        seen.add(identity)
        unique.append(candidate)

    return {
        "schema_version": "ecobiome-semantic-candidate-batch-v2.11",
        "input_survivor_count": len(survivors),
        "candidate_count": len(unique),
        "removed_canonical_duplicate_count": removed,
        "candidates": unique,
        "zero_candidates_is_valid_abstention": True,
        "automatic_scientific_acceptance": False,
    }

def validate_semantic_candidate_v2_11(
    candidate: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Validate a complete V2.11 candidate and its provider-neutral identity."""
    expected_root = {
        "schema_version",
        "contract",
        "source",
        "semantic",
        "promotion_readiness",
        "automatic_scientific_acceptance",
        "canonical_candidate_sha256",
    }
    if set(candidate) != expected_root:
        raise SemanticCandidateV211Error(
            "unexpected V2.11 candidate root keys"
        )
    if candidate.get("schema_version") != SEMANTIC_CANDIDATE_V2_11_SCHEMA_VERSION:
        raise SemanticCandidateV211Error(
            "unexpected V2.11 schema_version"
        )
    if candidate.get("automatic_scientific_acceptance") is not False:
        raise SemanticCandidateV211Error(
            "V2.11 must not grant automatic scientific acceptance"
        )
    if candidate.get("promotion_readiness") not in {
        PROMOTION_GROUNDING_COMPLETE,
        PROMOTION_REQUIRES_SEMANTIC_RESOLUTION,
    }:
        raise SemanticCandidateV211Error(
            "unsupported V2.11 promotion_readiness"
        )

    _reject_native_floats(candidate)
    canonical_json_text(candidate)

    actual_hash = candidate.get("canonical_candidate_sha256")
    if not isinstance(actual_hash, str) or _HASH_RE.fullmatch(actual_hash) is None:
        raise SemanticCandidateV211Error(
            "canonical_candidate_sha256 must be lowercase SHA-256"
        )
    expected_hash = semantic_candidate_sha256_v2_11(candidate)
    if actual_hash != expected_hash:
        raise SemanticCandidateV211Error(
            "canonical_candidate_sha256 does not match candidate identity"
        )

    contract = _require_mapping(
        candidate.get("contract"),
        "candidate.contract",
    )
    expected_contract_keys = {
        "name",
        "version",
        "relation_type_basis_version",
        "relation_type_registry_sha256",
        "grounding_policy_sha256",
        "claim_scoped_provenance_policy_sha256",
        "canonical_sha256",
    }
    if set(contract) != expected_contract_keys:
        raise SemanticCandidateV211Error(
            "unexpected V2.11 contract descriptor keys"
        )
    if contract.get("name") != SEMANTIC_CANDIDATE_V2_11_CONTRACT_NAME:
        raise SemanticCandidateV211Error(
            "unexpected V2.11 contract name"
        )
    if contract.get("version") != SEMANTIC_CANDIDATE_V2_11_CONTRACT_VERSION:
        raise SemanticCandidateV211Error(
            "unexpected V2.11 contract version"
        )
    if contract.get("relation_type_basis_version") != RELATION_TYPE_BASIS_VERSION:
        raise SemanticCandidateV211Error(
            "unexpected relation/type basis version"
        )
    for key in (
        "relation_type_registry_sha256",
        "grounding_policy_sha256",
        "claim_scoped_provenance_policy_sha256",
        "canonical_sha256",
    ):
        value = contract.get(key)
        if not isinstance(value, str) or _HASH_RE.fullmatch(value) is None:
            raise SemanticCandidateV211Error(
                f"contract {key} must be lowercase SHA-256"
            )
    contract_without_hash = {
        key: value
        for key, value in contract.items()
        if key != "canonical_sha256"
    }
    if contract["canonical_sha256"] != canonical_sha256(contract_without_hash):
        raise SemanticCandidateV211Error(
            "contract canonical_sha256 does not match descriptor"
        )

    source = _require_mapping(candidate.get("source"), "candidate.source")
    if set(source) != {
        "source_statement_claim_id",
        "source_claim_effective_text_sha256",
        "evidence_ids",
    }:
        raise SemanticCandidateV211Error(
            "unexpected V2.11 source descriptor keys"
        )
    _require_nonempty_string(
        source.get("source_statement_claim_id"),
        "candidate.source.source_statement_claim_id",
    )
    evidence_ids = source.get("evidence_ids")
    if (
        not isinstance(evidence_ids, list)
        or not evidence_ids
        or evidence_ids != sorted(set(evidence_ids))
    ):
        raise SemanticCandidateV211Error(
            "candidate Evidence IDs must be sorted and unique"
        )
    source_hash = source.get("source_claim_effective_text_sha256")
    if not isinstance(source_hash, str) or _HASH_RE.fullmatch(source_hash) is None:
        raise SemanticCandidateV211Error(
            "source Claim effective-text hash must be SHA-256"
        )

    semantic = _require_mapping(candidate.get("semantic"), "candidate.semantic")
    if set(semantic) != {
        "semantic_type",
        "relation",
        "epistemic_class",
        "arguments",
    }:
        raise SemanticCandidateV211Error(
            "unexpected V2.11 semantic descriptor keys"
        )
    for key in ("semantic_type", "relation", "epistemic_class"):
        _require_nonempty_string(
            semantic.get(key),
            f"candidate.semantic.{key}",
        )
    arguments = semantic.get("arguments")
    if not isinstance(arguments, list):
        raise SemanticCandidateV211Error(
            "candidate semantic arguments must be an array"
        )
    roles: list[str] = []
    for raw_argument in arguments:
        argument = _require_mapping(raw_argument, "candidate argument")
        if set(argument) != {
            "role",
            "grounding_class",
            "resolution_state",
            "value",
        }:
            raise SemanticCandidateV211Error(
                "unexpected V2.11 argument keys"
            )
        role = _require_nonempty_string(
            argument.get("role"),
            "candidate argument role",
        )
        roles.append(role)
        value = _require_mapping(
            argument.get("value"),
            f"{role}.value",
        )
        kind = value.get("kind")
        if kind not in {
            "decimal",
            "integer",
            "controlled_literal",
            "source_text",
        }:
            raise SemanticCandidateV211Error(
                f"unsupported V2.11 value kind: {kind!r}"
            )
        if kind == "decimal":
            if set(value) != {"kind", "value", "source_surface"}:
                raise SemanticCandidateV211Error(
                    "unexpected decimal candidate value keys"
                )
            if not isinstance(value.get("value"), str):
                raise SemanticCandidateV211Error(
                    "decimal candidate value must be text"
                )
            normalized = normalize_decimal(value["value"])
            if value["value"] != normalized:
                raise SemanticCandidateV211Error(
                    "decimal candidate value is not canonical"
                )
        elif kind == "integer":
            if set(value) != {"kind", "value", "source_surface"}:
                raise SemanticCandidateV211Error(
                    "unexpected integer candidate value keys"
                )
            integer = value.get("value")
            if isinstance(integer, bool) or not isinstance(integer, int):
                raise SemanticCandidateV211Error(
                    "integer candidate value must be int"
                )
        elif kind == "controlled_literal":
            if set(value) != {"kind", "value", "source_surface"}:
                raise SemanticCandidateV211Error(
                    "unexpected controlled-literal value keys"
                )
            _require_nonempty_string(
                value.get("value"),
                "controlled_literal.value",
            )
        elif kind == "source_text":
            if set(value) != {
                "kind",
                "canonical_text",
                "source_surface",
            }:
                raise SemanticCandidateV211Error(
                    "unexpected source-text candidate value keys"
                )
            canonical_text = value.get("canonical_text")
            if not isinstance(canonical_text, str) or not canonical_text:
                raise SemanticCandidateV211Error(
                    "source_text candidate lacks canonical_text"
                )

    if len(roles) != len(set(roles)):
        raise SemanticCandidateV211Error(
            "candidate semantic arguments contain duplicate roles"
        )
    return candidate


def canonical_semantic_candidate_json_v2_11(
    candidate: Mapping[str, Any],
) -> str:
    """Return canonical UTF-8 JSON text for a validated V2.11 candidate."""
    validate_semantic_candidate_v2_11(candidate)
    return canonical_json_text(candidate)


def render_semantic_candidate_review_text_v2_11(
    candidate: Mapping[str, Any],
) -> str:
    """Render one deterministic, non-generative Claim review string."""
    validate_semantic_candidate_v2_11(candidate)
    semantic = _require_mapping(candidate.get("semantic"), "candidate.semantic")
    relation = _require_nonempty_string(
        semantic.get("relation"),
        "candidate.semantic.relation",
    )
    arguments = semantic.get("arguments")
    if not isinstance(arguments, list):
        raise SemanticCandidateV211Error(
            "candidate semantic arguments must be an array"
        )

    rendered: list[str] = []
    for raw_argument in arguments:
        argument = _require_mapping(raw_argument, "candidate argument")
        role = _require_nonempty_string(
            argument.get("role"),
            "candidate argument role",
        )
        value = _require_mapping(argument.get("value"), f"{role}.value")
        kind = value.get("kind")

        if kind == "decimal" or kind == "integer":
            token = str(value["value"])
        elif kind == "controlled_literal":
            token = json.dumps(
                value["value"],
                ensure_ascii=False,
            )
        elif kind == "source_text":
            display = value.get("source_surface", value["canonical_text"])
            token = json.dumps(display, ensure_ascii=False)
        else:
            raise SemanticCandidateV211Error(
                f"unsupported V2.11 value kind: {kind!r}"
            )

        rendered.append(f"{role}={token}")

    return f"{relation}({', '.join(rendered)})"
