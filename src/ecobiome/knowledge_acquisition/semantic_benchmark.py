"""Deterministic semantic benchmark evaluation for reviewed Collector fixtures.

This module is deliberately fixture-aware. It measures benchmark coverage,
provenance, and obvious entailment/polarity failures for curated semantic
fixtures. It does not measure scientific correctness and cannot certify a
production semantic provider by itself.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

_WORD_RE = re.compile(r"[0-9A-Za-z]+")


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    ascii_text = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return " ".join(_WORD_RE.findall(ascii_text))


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
        effective_text = claim.get("effective_text")
        evidence = claim.get("evidence")
        if not isinstance(claim_id, str) or not isinstance(effective_text, str):
            raise TypeError("source claim identity/text is malformed")
        if not isinstance(evidence, list):
            raise TypeError("source claim evidence must be a list")
        if claim_id in result:
            raise ValueError(f"duplicate source claim id: {claim_id}")
        result[claim_id] = claim
    return result


def _evidence_by_segment(claim: dict[str, Any]) -> dict[int, dict[str, Any]]:
    evidence = claim.get("evidence")
    if not isinstance(evidence, list):
        raise TypeError("source claim evidence must be a list")

    result: dict[int, dict[str, Any]] = {}
    for item in evidence:
        if not isinstance(item, dict):
            raise TypeError("evidence item must be an object")
        segment = item.get("segment_index")
        evidence_id = item.get("evidence_id")
        text = item.get("text")
        if (
            not isinstance(segment, int)
            or not isinstance(evidence_id, str)
            or not isinstance(text, str)
        ):
            raise TypeError("evidence fields are malformed")
        if segment in result:
            raise ValueError(f"duplicate evidence segment index: {segment}")
        result[segment] = item
    return result


def _evidence_by_id(claim: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in _evidence_by_segment(claim).values():
        evidence_id = str(item["evidence_id"])
        if evidence_id in result:
            raise ValueError(f"duplicate evidence id: {evidence_id}")
        result[evidence_id] = item
    return result


def _fixture_arrays(
    fixture: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(fixture, dict):
        raise TypeError("fixture must be an object")

    values: list[list[dict[str, Any]]] = []
    for key in (
        "required_propositions",
        "admissible_propositions",
        "excluded_propositions",
    ):
        raw = fixture.get(key)
        if not isinstance(raw, list) or not all(
            isinstance(item, dict) for item in raw
        ):
            raise TypeError(f"fixture {key} must be a list of objects")
        values.append(raw)

    required, admissible, excluded = values
    return required, admissible, excluded


def infer_candidate_facets(
    semantic_type: str,
    text: str,
) -> tuple[str, ...]:
    """Return every reviewed fixture facet explicitly present in candidate text.

    More than one returned facet means the candidate is non-atomic for this
    benchmark contract.
    """

    normalized = _normalize(text)
    facets: list[str] = []

    if semantic_type == "geographic_origin":
        if "asie" in normalized and "japon" in normalized:
            facets.append("asia_japan")
    elif semantic_type == "geographic_distribution":
        has_europe = "europe" in normalized
        has_north = "nord" in normalized
        has_france = "france" in normalized
        if has_north and has_europe:
            facets.append("northern_europe")
        elif has_europe:
            facets.append("europe")
        if has_france:
            facets.append("france")
    elif semantic_type == "habitat":
        if "rizi" in normalized or "resi" in normalized:
            facets.append("rice_fields")
        if "estua" in normalized or "estuaire" in normalized:
            facets.append("marine_estuary")
    elif semantic_type == "robustness":
        facets.append("generic_robustness")
    elif semantic_type == "ph_tolerance":
        facets.append("ph_variation")
    elif semantic_type == "husbandry":
        facets.append("easy_to_keep")
    elif semantic_type == "mosquito_control":
        facets.append("mosquito_control")
    elif semantic_type == "temperature_tolerance":
        if "froid" in normalized:
            facets.append("cold")
        if "chaud" in normalized:
            facets.append("heat")
    elif semantic_type == "volume_tolerance":
        if "petit" in normalized:
            facets.append("small_volume")
        if "grand" in normalized:
            facets.append("large_volume")

    return tuple(dict.fromkeys(facets))


def _tolerance_relation(text: str) -> str:
    normalized = _normalize(text)
    padded = f" {normalized} "

    negative_patterns = (
        " ne supporte pas ",
        " ne tolere pas ",
        " ne resiste pas ",
        " ne peut pas vivre ",
        " n supporte pas ",
        " n tolere pas ",
    )
    if any(pattern in padded for pattern in negative_patterns):
        return "does_not_tolerate"

    if " craint " in padded or " redoute " in padded:
        if " craint ni " in padded or " redoute ni " in padded:
            return "tolerates"
        if " ne craint pas " in padded or " ne redoute pas " in padded:
            return "tolerates"
        return "does_not_tolerate"

    if any(
        marker in normalized
        for marker in ("support", "toler", "resist")
    ):
        return "tolerates"
    if "peut vivre" in normalized or "peuvent vivre" in normalized:
        return "tolerates"
    return "unknown"


def _generic_relation(semantic_type: str, text: str) -> str:
    normalized = _normalize(text)
    padded = f" {normalized} "

    if semantic_type == "geographic_origin":
        if any(
            pattern in padded
            for pattern in (
                " ne provient pas ",
                " ne vient pas ",
                " n est pas originaire ",
            )
        ):
            return "does_not_originate_from"
        if (
            "provient" in normalized
            or "venu" in normalized
            or "vient de" in normalized
            or "originaire" in normalized
            or "origine" in normalized
        ):
            return "originates_from"
        return "unknown"

    if semantic_type == "geographic_distribution":
        if any(
            pattern in padded
            for pattern in (
                " ne se trouve pas ",
                " n est pas present ",
                " est absent ",
            )
        ):
            return "does_not_occur_in"
        if (
            "se trouve" in normalized
            or "present" in normalized
            or "situe" in normalized
            or "localise" in normalized
        ):
            return "occurs_in"
        return "unknown"

    if semantic_type == "habitat":
        if " ne vit pas " in padded or " n habite pas " in padded:
            return "does_not_live_in"
        if (
            " vit " in padded
            or "habite" in normalized
            or "present" in normalized
        ):
            return "lives_in"
        return "unknown"

    if semantic_type == "robustness":
        if (
            " n est pas robuste " in padded
            or " pas robuste " in padded
            or " fragile " in padded
        ):
            return "is_not_robust"
        if (
            "robust" in normalized
            or "costaud" in normalized
            or "resilient" in normalized
        ):
            return "is_robust"
        return "unknown"

    if semantic_type == "husbandry":
        if " n est pas facile " in padded or " difficile " in padded:
            return "not_easy_to_keep"
        if "facile" in normalized or "simple" in normalized:
            return "easy_to_keep"
        return "unknown"

    if semantic_type == "mosquito_control":
        if (
            " n est pas efficace " in padded
            or " inefficace " in padded
            or " ne lutte pas " in padded
        ):
            return "not_effective_against"
        if (
            "efficace" in normalized
            or "lutte" in normalized
            or "redoutable" in normalized
        ):
            return "effective_against"
        return "unknown"

    if semantic_type == "ph_tolerance":
        return _tolerance_relation(text)

    return "unknown"


def infer_candidate_relation(semantic_type: str, text: str) -> str:
    """Infer an explicit benchmark relation without positive defaults."""

    if semantic_type in {"temperature_tolerance", "volume_tolerance"}:
        return _tolerance_relation(text)
    return _generic_relation(semantic_type, text)


def _is_opposite(expected: str, actual: str) -> bool:
    opposite_pairs = {
        ("tolerates", "does_not_tolerate"),
        ("originates_from", "does_not_originate_from"),
        ("occurs_in", "does_not_occur_in"),
        ("lives_in", "does_not_live_in"),
        ("is_robust", "is_not_robust"),
        ("easy_to_keep", "not_easy_to_keep"),
        ("effective_against", "not_effective_against"),
    }
    return (expected, actual) in opposite_pairs


def _proposals(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise TypeError("candidate payload must be an object")
    raw = payload.get("proposals")
    if not isinstance(raw, list):
        raise TypeError("candidate proposals must be a list")

    result: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise TypeError("candidate proposal must be an object")
        for field in (
            "source_claim_id",
            "semantic_type",
            "text",
            "evidence_ids",
        ):
            if field not in item:
                raise ValueError(f"candidate proposal lacks field: {field}")
        if not isinstance(item["source_claim_id"], str):
            raise TypeError("candidate source_claim_id is malformed")
        if (
            not isinstance(item["semantic_type"], str)
            or not isinstance(item["text"], str)
        ):
            raise TypeError("candidate semantic fields are malformed")
        if not isinstance(item["evidence_ids"], list) or not all(
            isinstance(evidence_id, str)
            for evidence_id in item["evidence_ids"]
        ):
            raise TypeError("candidate evidence_ids are malformed")
        result.append(item)
    return result


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 1.0
    return round(len(left & right) / len(union), 6)


def evaluate_semantic_benchmark(
    candidate_payload: Any,
    fixture: Any,
    semantic_export: Any,
    *,
    label: str,
) -> dict[str, Any]:
    """Evaluate one candidate batch against one reviewed semantic fixture."""

    batch = _proposals(candidate_payload)
    claims = _source_claim_index(semantic_export)
    required, admissible, excluded = _fixture_arrays(fixture)

    required_by_key: dict[
        tuple[str, str, str],
        dict[str, Any],
    ] = {}
    admissible_by_key: dict[
        tuple[str, str, str],
        dict[str, Any],
    ] = {}

    for target, index in (
        (required, required_by_key),
        (admissible, admissible_by_key),
    ):
        for item in target:
            meaning = item.get("meaning")
            if not isinstance(meaning, dict):
                raise TypeError("fixture meaning must be an object")
            facet = meaning.get("facet")
            relation = meaning.get("relation")
            if not isinstance(facet, str) or not isinstance(relation, str):
                raise TypeError("fixture meaning facet/relation is malformed")
            claim_id = item.get("source_claim_id")
            semantic_type = item.get("semantic_type")
            if not isinstance(claim_id, str) or not isinstance(
                semantic_type,
                str,
            ):
                raise TypeError("fixture semantic key is malformed")
            key = (claim_id, semantic_type, facet)
            if key in index:
                raise ValueError(f"duplicate fixture semantic key: {key}")
            index[key] = item

    excluded_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for item in excluded:
        claim_id = item.get("source_claim_id")
        semantic_type = item.get("semantic_type")
        reason = item.get("reason")
        if (
            not isinstance(claim_id, str)
            or not isinstance(semantic_type, str)
            or not isinstance(reason, str)
        ):
            raise TypeError("excluded fixture proposition is malformed")
        excluded_key = (claim_id, semantic_type)
        if excluded_key in excluded_by_key:
            raise ValueError(
                f"duplicate excluded fixture key: {excluded_key}"
            )
        excluded_by_key[excluded_key] = item

    candidate_index: dict[
        tuple[str, str, str],
        list[tuple[int, dict[str, Any], str]],
    ] = {}
    extras: list[dict[str, Any]] = []
    policy_violations: list[dict[str, Any]] = []
    admissible_hits: list[dict[str, Any]] = []
    duplicate_evidence_candidates: list[dict[str, Any]] = []

    for candidate_number, item in enumerate(batch):
        claim_id = str(item["source_claim_id"])
        semantic_type = str(item["semantic_type"])
        candidate_text = str(item["text"])

        if claim_id not in claims:
            raise ValueError(
                f"candidate {candidate_number} references unknown parent claim"
            )

        owned_evidence = _evidence_by_id(claims[claim_id])
        evidence_ids = [str(value) for value in item["evidence_ids"]]
        for evidence_id in evidence_ids:
            if evidence_id not in owned_evidence:
                raise ValueError(
                    "candidate "
                    f"{candidate_number} evidence {evidence_id} "
                    "is not owned by its parent claim"
                )

        if len(set(evidence_ids)) != len(evidence_ids):
            duplicate_evidence_candidates.append(
                {
                    "candidate_index": candidate_number,
                    "candidate_text": candidate_text,
                    "duplicate_evidence_ids": sorted(
                        evidence_id
                        for evidence_id in set(evidence_ids)
                        if evidence_ids.count(evidence_id) > 1
                    ),
                }
            )

        excluded_key = (claim_id, semantic_type)
        if excluded_key in excluded_by_key:
            policy_violations.append(
                {
                    "candidate_index": candidate_number,
                    "candidate_text": candidate_text,
                    "semantic_type": semantic_type,
                    "source_claim_id": claim_id,
                    "reason": excluded_by_key[excluded_key]["reason"],
                }
            )
            continue

        facets = infer_candidate_facets(semantic_type, candidate_text)
        if not facets:
            extras.append(
                {
                    "candidate_index": candidate_number,
                    "candidate_text": candidate_text,
                    "semantic_type": semantic_type,
                    "source_claim_id": claim_id,
                    "reason": "unmapped_semantic_facet",
                }
            )
            continue

        if len(facets) > 1:
            extras.append(
                {
                    "candidate_index": candidate_number,
                    "candidate_text": candidate_text,
                    "semantic_type": semantic_type,
                    "source_claim_id": claim_id,
                    "facets": list(facets),
                    "reason": "non_atomic_multiple_facets",
                }
            )
            continue

        facet = facets[0]
        key = (claim_id, semantic_type, facet)
        relation = infer_candidate_relation(semantic_type, candidate_text)

        if key in admissible_by_key:
            gold = admissible_by_key[key]
            required_ids = {
                str(evidence_id)
                for evidence_id in gold["minimal_evidence_ids"]
            }
            selected_ids = set(evidence_ids)
            expected_relation = str(gold["meaning"]["relation"])

            if _is_opposite(expected_relation, relation):
                status = "contradicted"
            elif relation == "unknown" or relation != expected_relation:
                status = "ambiguous"
            elif not required_ids.issubset(selected_ids):
                status = "insufficient_reviewed_fragments"
            else:
                status = "review_only_supported"

            admissible_hits.append(
                {
                    "candidate_index": candidate_number,
                    "gold_id": gold["id"],
                    "facet": facet,
                    "candidate_text": candidate_text,
                    "expected_relation": expected_relation,
                    "candidate_relation": relation,
                    "status": status,
                    "reviewed_fragments_present": required_ids.issubset(
                        selected_ids
                    ),
                    "candidate_evidence_ids": evidence_ids,
                }
            )
            continue

        if key not in required_by_key:
            extras.append(
                {
                    "candidate_index": candidate_number,
                    "candidate_text": candidate_text,
                    "semantic_type": semantic_type,
                    "source_claim_id": claim_id,
                    "facet": facet,
                    "reason": "not_in_required_or_admissible_fixture",
                }
            )
            continue

        candidate_index.setdefault(key, []).append(
            (candidate_number, item, relation)
        )

    alignments: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    duplicate_required_keys: list[dict[str, Any]] = []

    for gold in required:
        meaning = gold["meaning"]
        key = (
            str(gold["source_claim_id"]),
            str(gold["semantic_type"]),
            str(meaning["facet"]),
        )
        matches = candidate_index.get(key, [])

        if not matches:
            missing.append(
                {
                    "gold_id": gold["id"],
                    "source_claim_id": gold["source_claim_id"],
                    "semantic_type": gold["semantic_type"],
                    "facet": meaning["facet"],
                    "canonical_text": gold["canonical_text"],
                }
            )
            continue

        if len(matches) > 1:
            duplicate_required_keys.append(
                {
                    "gold_id": gold["id"],
                    "candidate_indices": [
                        index
                        for index, _, _ in matches
                    ],
                }
            )

        required_ids = {
            str(evidence_id)
            for evidence_id in gold["minimal_evidence_ids"]
        }
        expected_relation = str(meaning["relation"])

        candidate_number, item, relation = matches[0]
        selected_ids_for_rank = {
            str(evidence_id)
            for evidence_id in item["evidence_ids"]
        }
        best_rank = (
            int(required_ids.issubset(selected_ids_for_rank)),
            int(relation == expected_relation),
            -candidate_number,
        )
        for candidate_entry in matches[1:]:
            entry_index, entry_candidate, entry_relation = candidate_entry
            entry_selected_ids = {
                str(evidence_id)
                for evidence_id in entry_candidate["evidence_ids"]
            }
            entry_rank = (
                int(required_ids.issubset(entry_selected_ids)),
                int(entry_relation == expected_relation),
                -entry_index,
            )
            if entry_rank > best_rank:
                candidate_number = entry_index
                item = entry_candidate
                relation = entry_relation
                best_rank = entry_rank
        selected_ids = {
            str(evidence_id)
            for evidence_id in item["evidence_ids"]
        }
        provenance_sufficient = required_ids.issubset(selected_ids)
        exact_minimal = selected_ids == required_ids

        if _is_opposite(expected_relation, relation):
            status = "contradicted"
        elif relation == "unknown" or relation != expected_relation:
            status = "ambiguous"
        elif not provenance_sufficient:
            status = "insufficient_evidence"
        else:
            status = "entailed"

        contradictory_duplicates = sorted(
            index
            for index, _, duplicate_relation in matches
            if _is_opposite(expected_relation, duplicate_relation)
        )

        alignments.append(
            {
                "gold_id": gold["id"],
                "candidate_index": candidate_number,
                "source_claim_id": gold["source_claim_id"],
                "semantic_type": gold["semantic_type"],
                "facet": meaning["facet"],
                "expected_relation": expected_relation,
                "candidate_relation": relation,
                "canonical_text": gold["canonical_text"],
                "candidate_text": item["text"],
                "minimal_evidence_ids": list(
                    gold["minimal_evidence_ids"]
                ),
                "minimal_evidence_segment_indices": list(
                    gold["minimal_evidence_segment_indices"]
                ),
                "candidate_evidence_ids": list(item["evidence_ids"]),
                "missing_required_evidence_ids": sorted(
                    required_ids - selected_ids
                ),
                "extra_evidence_ids": sorted(
                    selected_ids - required_ids
                ),
                "provenance_sufficient": provenance_sufficient,
                "exact_minimal_evidence": exact_minimal,
                "evidence_jaccard": _jaccard(
                    required_ids,
                    selected_ids,
                ),
                "entailment_status": status,
                "contradictory_duplicate_candidate_indices": (
                    contradictory_duplicates
                ),
            }
        )

    statuses = [
        str(item["entailment_status"])
        for item in alignments
    ]
    aligned = len(alignments)
    sufficient = sum(
        bool(item["provenance_sufficient"])
        for item in alignments
    )
    provenance_insufficient = aligned - sufficient
    all_contradictory_indices = {
        index
        for item in alignments
        for index in item["contradictory_duplicate_candidate_indices"]
    }
    critical_contradictions = len(all_contradictory_indices)
    contradictions = statuses.count("contradicted")
    ambiguous = statuses.count("ambiguous")
    nonminimal_sufficient = sum(
        bool(item["provenance_sufficient"])
        and not bool(item["exact_minimal_evidence"])
        for item in alignments
    )

    admissible_by_gold: dict[str, list[dict[str, Any]]] = {}
    for item in admissible_hits:
        admissible_by_gold.setdefault(
            str(item["gold_id"]),
            [],
        ).append(item)

    duplicate_admissible_keys = [
        {
            "gold_id": gold_id,
            "candidate_indices": [
                int(item["candidate_index"])
                for item in hits
            ],
        }
        for gold_id, hits in sorted(admissible_by_gold.items())
        if len(hits) > 1
    ]
    admissible_issues = [
        item
        for item in admissible_hits
        if item["status"] != "review_only_supported"
    ]

    blocking_reasons: list[str] = []
    if missing:
        blocking_reasons.append(f"missing_required={len(missing)}")
    if provenance_insufficient:
        blocking_reasons.append(
            "required_provenance_insufficient="
            f"{provenance_insufficient}"
        )
    if critical_contradictions:
        blocking_reasons.append(
            f"critical_contradictions={critical_contradictions}"
        )
    if ambiguous:
        blocking_reasons.append(f"ambiguous_required={ambiguous}")
    if policy_violations:
        blocking_reasons.append(
            "forbidden_inference_policy_violations="
            f"{len(policy_violations)}"
        )
    if extras:
        blocking_reasons.append(
            f"unexpected_extra_candidates={len(extras)}"
        )
    if duplicate_required_keys:
        blocking_reasons.append(
            f"duplicate_required_keys={len(duplicate_required_keys)}"
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
    if duplicate_admissible_keys:
        blocking_reasons.append(
            "duplicate_admissible_keys="
            f"{len(duplicate_admissible_keys)}"
        )

    required_count = len(required)

    return {
        "schema_version": "2.2",
        "candidate_label": label,
        "candidate_count": len(batch),
        "metric_definition": {
            "strict_coverage": (
                "required fixture atoms structurally detected by parent "
                "Claim + semantic_type + semantic facet"
            ),
            "provenance": (
                "candidate Evidence set must contain the explicit reviewed "
                "minimal Evidence set"
            ),
            "entailment_polarity": (
                "deterministic fixture-aware relation comparison; obvious "
                "negation/opposite relation is blocking"
            ),
            "admissible": (
                "elliptical/fragmentary source-local readings are "
                "review-only and excluded from strict recall denominator"
            ),
            "excluded": (
                "candidate extraction of forbidden fixture readings is a "
                "policy violation"
            ),
            "benchmark_gate": (
                "strict single-fixture gate; does not certify a production "
                "provider"
            ),
        },
        "strict_coverage": {
            "required": required_count,
            "detected": aligned,
            "missing": len(missing),
            "rate": (
                round(aligned / required_count, 6)
                if required_count
                else 1.0
            ),
        },
        "provenance": {
            "aligned": aligned,
            "sufficient": sufficient,
            "insufficient": provenance_insufficient,
            "rate": (
                round(sufficient / aligned, 6)
                if aligned
                else 1.0
            ),
            "exact_minimal_evidence_sets": sum(
                bool(item["exact_minimal_evidence"])
                for item in alignments
            ),
            "nonminimal_sufficient_evidence_sets": nonminimal_sufficient,
        },
        "entailment_polarity": {
            "entailed": statuses.count("entailed"),
            "contradicted": contradictions,
            "ambiguous": ambiguous,
            "insufficient_evidence": statuses.count(
                "insufficient_evidence"
            ),
            "critical_contradictions": critical_contradictions,
        },
        "admissible": {
            "fixture_count": len(admissible),
            "detected_unique": len(admissible_by_gold),
            "emitted": len(admissible_hits),
            "supported_review_only": sum(
                item["status"] == "review_only_supported"
                for item in admissible_hits
            ),
            "issues": admissible_issues,
            "duplicates": duplicate_admissible_keys,
            "detections": admissible_hits,
        },
        "policy_violations": policy_violations,
        "unexpected_extra_candidates": extras,
        "duplicate_required_keys": duplicate_required_keys,
        "duplicate_evidence_candidates": duplicate_evidence_candidates,
        "benchmark_gate": {
            "pass": not blocking_reasons,
            "blocking_reasons": blocking_reasons,
        },
        "provider_certification": {
            "certified": False,
            "reason": (
                "single_fixture_not_sufficient_for_"
                "production_provider_certification"
            ),
        },
        "missing_required": missing,
        "alignments": alignments,
        "scientific_correctness_measured": False,
    }
