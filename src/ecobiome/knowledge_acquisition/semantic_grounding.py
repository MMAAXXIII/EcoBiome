"""Deterministic source-grounding helpers for EcoBiome semantic benchmarks.

This module implements the frozen Source-Independent Semantic Resolution /
Numeric Grounding Policy V1.1. It deliberately abstains from general semantic
equivalence for open-text arguments.

Grounding proves where a value came from. It does not prove that a free-text
surface is semantically equivalent to a Golden canonical identifier.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

GROUNDING_POLICY_V1_1_SHA256 = (
    "e7c566d78ec3eefbd30b9b424f92e35e25430933921f9a57f1c84efff232b6bf"
)

NUMBER_ONES = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
NUMBER_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

UNIT_ALIASES = {
    "second": "seconds",
    "seconds": "seconds",
    "sec": "seconds",
    "secs": "seconds",
    "s": "seconds",
    "minute": "minutes",
    "minutes": "minutes",
    "min": "minutes",
    "mins": "minutes",
    "hour": "hours",
    "hours": "hours",
    "hr": "hours",
    "hrs": "hours",
    "day": "days",
    "days": "days",
    "d": "days",
    "year": "years",
    "years": "years",
    "yr": "years",
    "yrs": "years",
    "%": "percent",
    "percent": "percent",
    "percentage": "percent",
    "°c": "celsius",
    "celsius": "celsius",
    "degc": "celsius",
    "degree celsius": "celsius",
    "degrees celsius": "celsius",
    "degree c": "celsius",
    "degrees c": "celsius",
    "g": "grams",
    "gram": "grams",
    "grams": "grams",
    "kg": "kilograms",
    "kilogram": "kilograms",
    "kilograms": "kilograms",
    "mg": "milligrams",
    "milligram": "milligrams",
    "milligrams": "milligrams",
    "l": "liters",
    "liter": "liters",
    "liters": "liters",
    "litre": "liters",
    "litres": "liters",
    "ml": "milliliters",
    "milliliter": "milliliters",
    "milliliters": "milliliters",
    "millilitre": "milliliters",
    "millilitres": "milliliters",
}

NUMERIC_ROLES = {
    "value": "numeric_value",
    "day": "day_index",
    "temperature_c": "temperature_celsius",
    "driver_temperature_c": "temperature_celsius",
    "comparator_temperature_c": "temperature_celsius",
}

OPAQUE_OPEN_TEXT_ROLES = {
    "analyte",
    "cause",
    "comparator",
    "condition",
    "event_a",
    "event_b",
    "experiment",
    "exposure",
    "factor",
    "frequency",
    "gene_set",
    "habitat",
    "impact_scope",
    "label",
    "level",
    "life_stage",
    "location",
    "outcome",
    "pathway",
    "process",
    "reference",
    "species",
    "system",
    "target",
    "tissue",
    "topic",
    "variable",
}

# V1.2 closes the role-coverage seam introduced by the V2.7 ontology while
# preserving the frozen V1.1 policy object and its canonical SHA-256 above.
# These roles remain opaque/source-grounded: presence in the source is checked,
# but no semantic equivalence or scientific credit is inferred.
OPAQUE_OPEN_TEXT_ROLES_V1_1 = frozenset(OPAQUE_OPEN_TEXT_ROLES)
OPAQUE_OPEN_TEXT_ROLES_V1_2_ADDITIONS = frozenset(
    {
        "context",
        "entity_a",
        "entity_b",
        "mechanism",
        "mediator",
        "response",
        "state",
        "subject",
        "target_state",
        "taxon",
        "temporal_scope",
    }
)
OPAQUE_OPEN_TEXT_ROLES_V1_2 = frozenset(
    OPAQUE_OPEN_TEXT_ROLES_V1_1 | OPAQUE_OPEN_TEXT_ROLES_V1_2_ADDITIONS
)

# V1.3 adds the four human-adopted G7A directional-nitrogen roles without
# mutating the frozen V1.1 policy identity or the V1.2 role set.
OPAQUE_OPEN_TEXT_ROLES_V1_3_ADDITIONS = frozenset(
    {
        "process_agent",
        "source_material",
        "target_material",
        "target_nitrogen_pool",
    }
)
OPAQUE_OPEN_TEXT_ROLES_V1_3 = frozenset(
    OPAQUE_OPEN_TEXT_ROLES_V1_2 | OPAQUE_OPEN_TEXT_ROLES_V1_3_ADDITIONS
)

TEMPERATURE_POSITIVE_PATTERNS = [
    r"\btemperature\b",
    r"\btemperatures\b",
    r"\bcelsius\b",
    r"°\s*c\b",
    r"\bdegc\b",
    r"\b[+-]?\d+(?:[.,]\d+)?\s*°?\s*c\b",
]
TEMPERATURE_NEGATIVE_CONTEXT_PATTERNS = [
    r"\brain(?:fall)?\b",
    r"\bdrought\b",
    r"\bprecipitation\b",
    r"\bseason(?:al|s)?\b",
    r"\bplant(?:s)?\b",
    r"\bsalinity\b",
    r"\bph\b",
]

GROUNDING_POLICY_V1_1: dict[str, Any] = {
    "authorship_context": {
        "developed_after_fixture_3_observation": True,
        "fixture_3_may_be_used_as_regression_only": True,
        "new_generalization_claim_requires_fixture_4": True,
    },
    "controlled_units": {
        "alias_map": dict(sorted(UNIT_ALIASES.items())),
        "canonical_values": sorted(set(UNIT_ALIASES.values())),
        "single_letter_alias_possessive_guard": True,
    },
    "hardening_changes": [
        "day_index_uses_actual_source_number_surface",
        "single_letter_unit_aliases_exclude_apostrophe_possessives",
        "value_unit_pairs_require_same_local_source_mention",
        "degree_and_degrees_celsius_surface_forms_supported",
    ],
    "numeric_grounding": {
        "accepted_surface_forms": [
            "decimal_or_integer_numeric_literal",
            "english_number_words_zero_to_ninety_nine",
        ],
        "day_context_uses_actual_source_surface": True,
        "temperature_requires_local_celsius_unit": True,
        "value_unit_pairing": {
            "independent_value_and_unit_hits_cannot_be_combined": True,
            "same_local_numeric_unit_mention_required": True,
        },
    },
    "opaque_open_text_policy": {
        "canonical_resolution_available": False,
        "scientific_credit": False,
        "source_grounding_required": True,
    },
    "policy_name": "source-independent-semantic-resolution-numeric-grounding",
    "policy_version": "1.1-hardening-audit-candidate",
    "principles": {
        "ambiguity_produces_no_scientific_credit": True,
        "no_fixture_specific_aliases": True,
        "no_golden_specific_aliases": True,
        "no_llm_or_embedding_resolver": True,
        "semantic_resolution_must_be_deterministic_or_abstain": True,
        "source_grounding_is_not_semantic_equivalence": True,
        "value_unit_pairing_is_joint_not_independent": True,
    },
    "role_resolution_classes": {
        "controlled_literal": {"unit": "measurement_or_time_unit"},
        "exact_numeric": dict(sorted(NUMERIC_ROLES.items())),
        "opaque_source_grounded": sorted(OPAQUE_OPEN_TEXT_ROLES),
        "typed_domain_validator": {
            "temperature_scope": "temperature_condition_or_temperature_set"
        },
    },
    "status": "AUDIT_ONLY_NOT_PRODUCTION",
    "supersedes_policy_canonical_sha256": (
        "94333733c6dd79f517579e56766236c6c87d5d74bacba69d3c4e857d76a3577c"
    ),
    "temperature_scope_validator": {
        "domain_mismatch_is_semantic_contract_violation": True,
        "domain_valid_unresolved_gets_entailment_credit": False,
        "high_confidence_non_temperature_rules": TEMPERATURE_NEGATIVE_CONTEXT_PATTERNS,
        "positive_rules": TEMPERATURE_POSITIVE_PATTERNS,
    },
}


def canonical_json_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_grounding_policy(policy: Any) -> dict[str, Any]:
    """Validate and return the one frozen V1.1 policy accepted by this module."""
    if not isinstance(policy, dict):
        raise TypeError("argument_grounding_policy must be an object")
    actual = canonical_json_sha256(policy)
    if actual != GROUNDING_POLICY_V1_1_SHA256:
        raise ValueError(
            "unsupported argument grounding policy SHA-256: "
            f"{actual}; expected {GROUNDING_POLICY_V1_1_SHA256}"
        )
    return policy


def normalize_space_case(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def normalize_unit_token(text: str) -> str | None:
    return UNIT_ALIASES.get(normalize_space_case(text))


def parse_number_word(token: str) -> int | None:
    value = token.casefold().replace("-", " ").strip()
    parts = value.split()
    if len(parts) == 1:
        if parts[0] in NUMBER_ONES:
            return NUMBER_ONES[parts[0]]
        if parts[0] in NUMBER_TENS:
            return NUMBER_TENS[parts[0]]
        return None
    if (
        len(parts) == 2
        and parts[0] in NUMBER_TENS
        and parts[1] in NUMBER_ONES
        and NUMBER_ONES[parts[1]] < 10
    ):
        return NUMBER_TENS[parts[0]] + NUMBER_ONES[parts[1]]
    return None


def number_mentions(text: str) -> list[dict[str, Any]]:
    mentions: list[dict[str, Any]] = []
    digit_pattern = re.compile(r"(?<!\w)[+-]?\d+(?:[.,]\d+)?(?!\w)")
    for match in digit_pattern.finditer(text):
        raw = match.group(0)
        value = float(raw.replace(",", "."))
        normalized: int | float = int(value) if value.is_integer() else value
        mentions.append(
            {
                "surface": raw,
                "start": match.start(),
                "end": match.end(),
                "value": normalized,
                "method": "numeric_literal",
            }
        )

    tokens = sorted([*NUMBER_ONES, *NUMBER_TENS], key=len, reverse=True)
    alt = "|".join(re.escape(token) for token in tokens)
    pattern = re.compile(
        rf"\b(?:{alt})(?:[-\s](?:{alt}))?\b",
        flags=re.IGNORECASE,
    )
    occupied = [(item["start"], item["end"]) for item in mentions]
    for match in pattern.finditer(text):
        if any(
            not (match.end() <= start or match.start() >= end)
            for start, end in occupied
        ):
            continue
        parsed = parse_number_word(match.group(0))
        if parsed is None:
            continue
        mentions.append(
            {
                "surface": match.group(0),
                "start": match.start(),
                "end": match.end(),
                "value": parsed,
                "method": "english_number_word",
            }
        )
    return sorted(
        mentions,
        key=lambda item: (item["start"], item["end"], str(item["surface"])),
    )


def _safe_alpha_alias_pattern(alias: str) -> re.Pattern[str]:
    if len(alias) == 1:
        return re.compile(
            rf"(?<![\w']){re.escape(alias)}(?!\w)",
            flags=re.IGNORECASE,
        )
    return re.compile(rf"\b{re.escape(alias)}\b", flags=re.IGNORECASE)


def unit_mentions(text: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for alias in sorted(UNIT_ALIASES, key=len, reverse=True):
        canonical = UNIT_ALIASES[alias]
        if re.fullmatch(r"[A-Za-z]+", alias):
            pattern = _safe_alpha_alias_pattern(alias)
        elif re.fullmatch(r"[A-Za-z ]+", alias):
            pattern = re.compile(
                rf"(?<!\w){re.escape(alias)}(?!\w)",
                flags=re.IGNORECASE,
            )
        else:
            pattern = re.compile(re.escape(alias), flags=re.IGNORECASE)

        for match in pattern.finditer(text):
            matches.append(
                {
                    "surface": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "canonical": canonical,
                    "alias": alias,
                }
            )

    matches.sort(
        key=lambda item: (
            item["start"],
            -(item["end"] - item["start"]),
            item["canonical"],
        )
    )
    selected: list[dict[str, Any]] = []
    for item in matches:
        if any(
            not (item["end"] <= other["start"] or item["start"] >= other["end"])
            for other in selected
        ):
            continue
        selected.append(item)

    return sorted(
        selected,
        key=lambda item: (item["start"], item["end"], item["canonical"]),
    )


def nearby_units(
    text: str,
    number: dict[str, Any],
    maximum_gap: int = 4,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for unit in unit_mentions(text):
        if unit["start"] >= number["end"]:
            gap = text[number["end"] : unit["start"]]
        elif unit["end"] <= number["start"]:
            gap = text[unit["end"] : number["start"]]
        else:
            continue
        if len(gap) <= maximum_gap and re.fullmatch(r"[\s\-–—()]*", gap):
            result.append(unit)
    return result


def _day_context_matches(text: str, mention: dict[str, Any]) -> bool:
    prefix = text[max(0, mention["start"] - 16) : mention["start"]]
    return bool(re.search(r"\bday[\s\-]*$", prefix, flags=re.IGNORECASE))


def numeric_role_grounding(
    role: str,
    value: float,
    source_text: str,
    paired_unit: str | None = None,
) -> dict[str, Any]:
    domain = NUMERIC_ROLES.get(role)
    if domain is None:
        raise ValueError(f"unknown numeric role: {role}")

    candidates: list[dict[str, Any]] = []
    for mention in number_mentions(source_text):
        if mention["value"] != value:
            continue
        nearby = nearby_units(source_text, mention)
        units = sorted({str(item["canonical"]) for item in nearby})
        context_ok = True
        reason = "generic_numeric_match"

        if domain == "temperature_celsius":
            context_ok = "celsius" in units
            reason = (
                "celsius_unit_adjacent"
                if context_ok
                else "temperature_role_requires_adjacent_celsius_unit"
            )
        elif domain == "day_index":
            context_ok = _day_context_matches(source_text, mention)
            reason = (
                "day_marker_adjacent"
                if context_ok
                else "day_role_requires_day_marker"
            )

        if paired_unit is not None:
            canonical_unit = normalize_unit_token(paired_unit) or paired_unit
            if canonical_unit not in units:
                context_ok = False
                reason = "paired_unit_not_adjacent"

        candidates.append(
            {
                **mention,
                "nearby_units": nearby,
                "canonical_units": units,
                "context_ok": context_ok,
                "context_reason": reason,
            }
        )

    valid = [item for item in candidates if item["context_ok"]]
    if len(valid) == 1:
        return {
            "state": "resolved",
            "role": role,
            "semantic_domain": domain,
            "canonical_value": value,
            "source_match": valid[0],
            "scientifically_scoreable": True,
        }
    if len(valid) > 1:
        return {
            "state": "ambiguous",
            "role": role,
            "semantic_domain": domain,
            "canonical_value": value,
            "source_matches": valid,
            "scientifically_scoreable": False,
        }
    return {
        "state": "ungrounded",
        "role": role,
        "semantic_domain": domain,
        "canonical_value": value,
        "candidate_matches_rejected_by_context": candidates,
        "scientifically_scoreable": False,
    }


def unit_role_resolution(value: str, source_text: str) -> dict[str, Any]:
    canonical = normalize_unit_token(value)
    if canonical is None:
        return {
            "state": "unsupported_literal",
            "role": "unit",
            "surface": value,
            "scientifically_scoreable": False,
        }
    matches = [
        item for item in unit_mentions(source_text)
        if item["canonical"] == canonical
    ]
    if not matches:
        return {
            "state": "ungrounded",
            "role": "unit",
            "surface": value,
            "canonical_value": canonical,
            "scientifically_scoreable": False,
        }
    return {
        "state": "resolved",
        "role": "unit",
        "surface": value,
        "canonical_value": canonical,
        "source_matches": matches,
        "scientifically_scoreable": True,
    }


def resolve_value_unit_pair(
    value: float,
    unit: str,
    source_text: str,
) -> dict[str, Any]:
    canonical_unit = normalize_unit_token(unit)
    if canonical_unit is None:
        return {
            "state": "unsupported_unit",
            "canonical_value": value,
            "surface_unit": unit,
            "scientifically_scoreable": False,
        }

    pair_matches: list[dict[str, Any]] = []
    for mention in number_mentions(source_text):
        if mention["value"] != value:
            continue
        adjacent = [
            item for item in nearby_units(source_text, mention)
            if item["canonical"] == canonical_unit
        ]
        for unit_match in adjacent:
            pair_matches.append(
                {
                    "value_match": mention,
                    "unit_match": unit_match,
                    "canonical_value": value,
                    "canonical_unit": canonical_unit,
                }
            )

    if len(pair_matches) == 1:
        return {
            "state": "resolved",
            "canonical_value": value,
            "canonical_unit": canonical_unit,
            "pair_match": pair_matches[0],
            "scientifically_scoreable": True,
        }
    if len(pair_matches) > 1:
        return {
            "state": "ambiguous",
            "canonical_value": value,
            "canonical_unit": canonical_unit,
            "pair_matches": pair_matches,
            "scientifically_scoreable": False,
        }
    return {
        "state": "ungrounded_pair",
        "canonical_value": value,
        "canonical_unit": canonical_unit,
        "scientifically_scoreable": False,
    }


def temperature_scope_domain_check(
    value: str,
    source_text: str,
) -> dict[str, Any]:
    normalized_value = normalize_space_case(value)
    normalized_source = normalize_space_case(source_text)
    if not normalized_value or normalized_value not in normalized_source:
        return {
            "state": "ungrounded",
            "role": "temperature_scope",
            "semantic_domain": "temperature_condition_or_temperature_set",
            "scientifically_scoreable": False,
        }

    positive = any(
        re.search(pattern, normalized_value, flags=re.IGNORECASE)
        for pattern in TEMPERATURE_POSITIVE_PATTERNS
    )
    negative = any(
        re.search(pattern, normalized_value, flags=re.IGNORECASE)
        for pattern in TEMPERATURE_NEGATIVE_CONTEXT_PATTERNS
    )
    if positive:
        return {
            "state": "domain_valid_unresolved",
            "role": "temperature_scope",
            "semantic_domain": "temperature_condition_or_temperature_set",
            "surface": value,
            "source_grounded": True,
            "scientifically_scoreable": False,
        }
    if negative:
        return {
            "state": "domain_mismatch",
            "role": "temperature_scope",
            "semantic_domain": "temperature_condition_or_temperature_set",
            "surface": value,
            "source_grounded": True,
            "scientifically_scoreable": False,
        }
    return {
        "state": "domain_unknown",
        "role": "temperature_scope",
        "semantic_domain": "temperature_condition_or_temperature_set",
        "surface": value,
        "source_grounded": True,
        "scientifically_scoreable": False,
    }


def opaque_text_resolution(
    role: str,
    value: str,
    source_text: str,
) -> dict[str, Any]:
    grounded = (
        bool(normalize_space_case(value))
        and normalize_space_case(value) in normalize_space_case(source_text)
    )
    return {
        "state": "grounded_opaque_unresolved" if grounded else "ungrounded",
        "role": role,
        "surface": value,
        "source_grounded": grounded,
        "scientifically_scoreable": False,
    }


def audit_arguments(
    arguments: dict[str, Any],
    source_text: str,
) -> dict[str, Any]:
    """Audit arguments with V1.2 role coverage and V1.1 numeric semantics."""
    records: dict[str, dict[str, Any]] = {}

    # Joint value+unit first; it must not be assembled from unrelated mentions.
    if "value" in arguments and "unit" in arguments:
        value = arguments["value"]
        unit = arguments["unit"]
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isinstance(unit, str)
        ):
            pair = resolve_value_unit_pair(value, unit, source_text)
        else:
            pair = {
                "state": "scalar_type_violation",
                "scientifically_scoreable": False,
            }
        pair_state = str(pair["state"])
        if pair_state == "resolved":
            records["value"] = {
                "role": "value",
                "state": "resolved",
                "canonical_value": pair["canonical_value"],
                "scientifically_scoreable": True,
                "joint_value_unit_pair": pair,
            }
            records["unit"] = {
                "role": "unit",
                "state": "resolved",
                "canonical_value": pair["canonical_unit"],
                "scientifically_scoreable": True,
                "joint_value_unit_pair": pair,
            }
        else:
            records["value"] = {
                "role": "value",
                "state": pair_state,
                "scientifically_scoreable": False,
                "joint_value_unit_pair": pair,
            }
            records["unit"] = {
                "role": "unit",
                "state": pair_state,
                "scientifically_scoreable": False,
                "joint_value_unit_pair": pair,
            }

    for role, value in arguments.items():
        if role in records:
            continue
        if role in NUMERIC_ROLES:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                record = {
                    "role": role,
                    "state": "scalar_type_violation",
                    "scientifically_scoreable": False,
                }
            else:
                record = numeric_role_grounding(role, value, source_text)
        elif role == "unit":
            record = (
                unit_role_resolution(value, source_text)
                if isinstance(value, str)
                else {
                    "role": role,
                    "state": "scalar_type_violation",
                    "scientifically_scoreable": False,
                }
            )
        elif role == "temperature_scope":
            record = (
                temperature_scope_domain_check(value, source_text)
                if isinstance(value, str)
                else {
                    "role": role,
                    "state": "scalar_type_violation",
                    "scientifically_scoreable": False,
                }
            )
        elif role in OPAQUE_OPEN_TEXT_ROLES_V1_2:
            record = (
                opaque_text_resolution(role, value, source_text)
                if isinstance(value, str)
                else {
                    "role": role,
                    "state": "scalar_type_violation",
                    "scientifically_scoreable": False,
                }
            )
        else:
            record = {
                "role": role,
                "state": "unknown_role",
                "scientifically_scoreable": False,
            }
        records[role] = record

    state_counts: dict[str, int] = {}
    for record in records.values():
        state = str(record["state"])
        state_counts[state] = state_counts.get(state, 0) + 1

    blocking_states = {
        "ambiguous",
        "domain_mismatch",
        "scalar_type_violation",
        "ungrounded",
        "ungrounded_pair",
        "unknown_role",
        "unsupported_literal",
        "unsupported_unit",
    }
    unresolved_states = {
        "domain_unknown",
        "domain_valid_unresolved",
        "grounded_opaque_unresolved",
    }

    return {
        "records": records,
        "state_counts": dict(sorted(state_counts.items())),
        "blocking": any(
            str(record["state"]) in blocking_states
            for record in records.values()
        ),
        "unresolved": any(
            str(record["state"]) in unresolved_states
            for record in records.values()
        ),
        "all_scientifically_scoreable": all(
            bool(record.get("scientifically_scoreable"))
            for record in records.values()
        )
        if records
        else True,
    }


def audit_arguments_v1_3(
    arguments: dict[str, Any],
    source_text: str,
) -> dict[str, Any]:
    """Audit arguments with V1.3 role coverage and V1.1 numeric semantics."""
    records: dict[str, dict[str, Any]] = {}

    # Joint value+unit first; it must not be assembled from unrelated mentions.
    if "value" in arguments and "unit" in arguments:
        value = arguments["value"]
        unit = arguments["unit"]
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isinstance(unit, str)
        ):
            pair = resolve_value_unit_pair(value, unit, source_text)
        else:
            pair = {
                "state": "scalar_type_violation",
                "scientifically_scoreable": False,
            }
        pair_state = str(pair["state"])
        if pair_state == "resolved":
            records["value"] = {
                "role": "value",
                "state": "resolved",
                "canonical_value": pair["canonical_value"],
                "scientifically_scoreable": True,
                "joint_value_unit_pair": pair,
            }
            records["unit"] = {
                "role": "unit",
                "state": "resolved",
                "canonical_value": pair["canonical_unit"],
                "scientifically_scoreable": True,
                "joint_value_unit_pair": pair,
            }
        else:
            records["value"] = {
                "role": "value",
                "state": pair_state,
                "scientifically_scoreable": False,
                "joint_value_unit_pair": pair,
            }
            records["unit"] = {
                "role": "unit",
                "state": pair_state,
                "scientifically_scoreable": False,
                "joint_value_unit_pair": pair,
            }

    for role, value in arguments.items():
        if role in records:
            continue
        if role in NUMERIC_ROLES:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                record = {
                    "role": role,
                    "state": "scalar_type_violation",
                    "scientifically_scoreable": False,
                }
            else:
                record = numeric_role_grounding(role, value, source_text)
        elif role == "unit":
            record = (
                unit_role_resolution(value, source_text)
                if isinstance(value, str)
                else {
                    "role": role,
                    "state": "scalar_type_violation",
                    "scientifically_scoreable": False,
                }
            )
        elif role == "temperature_scope":
            record = (
                temperature_scope_domain_check(value, source_text)
                if isinstance(value, str)
                else {
                    "role": role,
                    "state": "scalar_type_violation",
                    "scientifically_scoreable": False,
                }
            )
        elif role in OPAQUE_OPEN_TEXT_ROLES_V1_3:
            record = (
                opaque_text_resolution(role, value, source_text)
                if isinstance(value, str)
                else {
                    "role": role,
                    "state": "scalar_type_violation",
                    "scientifically_scoreable": False,
                }
            )
        else:
            record = {
                "role": role,
                "state": "unknown_role",
                "scientifically_scoreable": False,
            }
        records[role] = record

    state_counts: dict[str, int] = {}
    for record in records.values():
        state = str(record["state"])
        state_counts[state] = state_counts.get(state, 0) + 1

    blocking_states = {
        "ambiguous",
        "domain_mismatch",
        "scalar_type_violation",
        "ungrounded",
        "ungrounded_pair",
        "unknown_role",
        "unsupported_literal",
        "unsupported_unit",
    }
    unresolved_states = {
        "domain_unknown",
        "domain_valid_unresolved",
        "grounded_opaque_unresolved",
    }

    return {
        "records": records,
        "state_counts": dict(sorted(state_counts.items())),
        "blocking": any(
            str(record["state"]) in blocking_states
            for record in records.values()
        ),
        "unresolved": any(
            str(record["state"]) in unresolved_states
            for record in records.values()
        ),
        "all_scientifically_scoreable": all(
            bool(record.get("scientifically_scoreable"))
            for record in records.values()
        )
        if records
        else True,
    }


def resolved_argument_equal(
    role: str,
    actual: Any,
    expected: Any,
    record: dict[str, Any],
) -> bool | None:
    """Return True/False when V1.1 resolves identity, otherwise None."""
    if not record.get("scientifically_scoreable"):
        return None

    canonical = record.get("canonical_value")
    if role == "unit":
        if not isinstance(expected, str):
            return False
        expected_canonical = normalize_unit_token(expected)
        return expected_canonical is not None and canonical == expected_canonical

    if role in NUMERIC_ROLES:
        if isinstance(expected, bool) or not isinstance(expected, (int, float)):
            return False
        return canonical == expected

    return None
