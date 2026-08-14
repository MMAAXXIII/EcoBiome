from __future__ import annotations

import copy

import pytest

from ecobiome.knowledge_acquisition.semantic_candidate_v2_11 import (
    PROMOTION_REQUIRES_SEMANTIC_RESOLUTION,
    SemanticCandidateV211Error,
    build_semantic_candidate_v2_11,
    build_semantic_candidates_v2_11,
    canonical_semantic_candidate_json_v2_11,
    render_semantic_candidate_review_text_v2_11,
    validate_semantic_candidate_v2_11,
)


def _registry() -> dict[str, object]:
    return {
        "relations": {
            "maintained_at": {
                "argument_keys": ["variable", "value", "unit"],
                "epistemic_class": "study_context_non_result",
                "semantic_type_contract_state": (
                    "historical_golden_reviewed_constrained"
                ),
                "semantic_types_allowed": ["experimental_condition"],
            },
            "studied": {
                "argument_keys": ["life_stage", "species"],
                "epistemic_class": "study_context_non_result",
                "semantic_type_contract_state": (
                    "historical_golden_reviewed_constrained"
                ),
                "semantic_types_allowed": ["study_subject"],
            },
            "lives_in": {
                "argument_keys": ["habitat"],
                "epistemic_class": "assertive_fact",
                "semantic_type_contract_state": "unresolved_blocked",
                "semantic_types_allowed": [],
            },
        },
        "argument_role_semantics": {
            "variable": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "measurable_or_described_variable",
            },
            "value": {
                "grounding_class": "exact_numeric_source_grounded",
                "semantic_domain": "numeric_value",
            },
            "unit": {
                "grounding_class": "controlled_literal_source_grounded",
                "semantic_domain": "controlled_measurement_or_time_unit",
            },
            "life_stage": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "organism_life_stage",
            },
            "species": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "species_identity",
            },
            "habitat": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "habitat_or_ecosystem",
            },
        },
    }


def _temperature_source_request() -> dict[str, object]:
    return {
        "source_claims": [
            {
                "claim_id": "claim-temperature",
                "effective_text": (
                    "Temperature was maintained at 26.5 °C during the trial."
                ),
                "evidence": [
                    {"evidence_id": "ev-2", "text": "26.5 °C"},
                    {"evidence_id": "ev-1", "text": "Temperature"},
                ],
            }
        ]
    }


def _temperature_survivor(
    *,
    unit: str = "degree celsius",
    variable: str = "temperature",
    evidence_ids: list[str] | None = None,
) -> dict[str, object]:
    return {
        "c": "claim-temperature",
        "e": evidence_ids or ["ev-2", "ev-1"],
        "t": "experimental_condition",
        "m": {
            "r": "maintained_at",
            "a": {
                "variable": variable,
                "value": 26.5,
                "unit": unit,
            },
        },
    }


def _contains_native_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_native_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_native_float(item) for item in value)
    return False


def test_v2_11_converts_provider_float_to_exact_decimal_text() -> None:
    candidate = build_semantic_candidate_v2_11(
        _temperature_survivor(),
        _temperature_source_request(),
        _registry(),
    )

    assert _contains_native_float(candidate) is False
    assert candidate["promotion_readiness"] == (
        PROMOTION_REQUIRES_SEMANTIC_RESOLUTION
    )
    assert candidate["automatic_scientific_acceptance"] is False

    arguments = candidate["semantic"]["arguments"]
    by_role = {item["role"]: item for item in arguments}

    assert by_role["value"]["value"] == {
        "kind": "decimal",
        "value": "26.5",
        "source_surface": "26.5",
    }
    assert by_role["unit"]["value"] == {
        "kind": "controlled_literal",
        "value": "celsius",
        "source_surface": "°C",
    }
    assert by_role["variable"]["value"] == {
        "kind": "source_text",
        "canonical_text": "temperature",
        "source_surface": "Temperature",
    }


def test_v2_11_identity_is_provider_alias_and_evidence_order_independent() -> None:
    first = build_semantic_candidate_v2_11(
        _temperature_survivor(
            unit="degree celsius",
            variable="temperature",
            evidence_ids=["ev-2", "ev-1"],
        ),
        _temperature_source_request(),
        _registry(),
    )
    second = build_semantic_candidate_v2_11(
        _temperature_survivor(
            unit="°C",
            variable="Temperature",
            evidence_ids=["ev-1", "ev-2"],
        ),
        _temperature_source_request(),
        _registry(),
    )

    assert first["source"]["evidence_ids"] == ["ev-1", "ev-2"]
    assert second["source"]["evidence_ids"] == ["ev-1", "ev-2"]
    assert (
        first["canonical_candidate_sha256"]
        == second["canonical_candidate_sha256"]
    )


def test_v2_11_batch_deduplicates_canonical_provider_aliases() -> None:
    admission = {
        "survivor_count": 2,
        "survivors": [
            _temperature_survivor(unit="degree celsius"),
            _temperature_survivor(unit="°C"),
        ],
        "automatic_scientific_acceptance": False,
    }

    batch = build_semantic_candidates_v2_11(
        admission,
        _temperature_source_request(),
        _registry(),
    )

    assert batch["input_survivor_count"] == 2
    assert batch["candidate_count"] == 1
    assert batch["removed_canonical_duplicate_count"] == 1
    assert batch["automatic_scientific_acceptance"] is False


def test_v2_11_opaque_source_roles_remain_unresolved() -> None:
    source = {
        "source_claims": [
            {
                "claim_id": "claim-study",
                "effective_text": "Juvenile zebrafish were studied.",
                "evidence": [
                    {
                        "evidence_id": "ev-study",
                        "text": "Juvenile zebrafish were studied.",
                    }
                ],
            }
        ]
    }
    survivor = {
        "c": "claim-study",
        "e": ["ev-study"],
        "t": "study_subject",
        "m": {
            "r": "studied",
            "a": {
                "life_stage": "juvenile",
                "species": "zebrafish",
            },
        },
    }

    candidate = build_semantic_candidate_v2_11(
        survivor,
        source,
        _registry(),
    )

    assert candidate["promotion_readiness"] == (
        PROMOTION_REQUIRES_SEMANTIC_RESOLUTION
    )
    by_role = {
        item["role"]: item for item in candidate["semantic"]["arguments"]
    }
    assert by_role["life_stage"]["resolution_state"] == (
        "grounded_opaque_unresolved"
    )
    assert by_role["species"]["resolution_state"] == (
        "grounded_opaque_unresolved"
    )


def test_v2_11_renderer_is_deterministic_and_non_generative() -> None:
    candidate = build_semantic_candidate_v2_11(
        _temperature_survivor(),
        _temperature_source_request(),
        _registry(),
    )

    assert render_semantic_candidate_review_text_v2_11(candidate) == (
        'maintained_at(variable="Temperature", value=26.5, unit="celsius")'
    )


def test_v2_11_canonical_json_contains_no_native_float() -> None:
    candidate = build_semantic_candidate_v2_11(
        _temperature_survivor(),
        _temperature_source_request(),
        _registry(),
    )

    text = canonical_semantic_candidate_json_v2_11(candidate)

    assert '"value":"26.5"' in text
    assert '"automatic_scientific_acceptance":false' in text


def test_v2_11_rejects_fail_closed_relation() -> None:
    source = {
        "source_claims": [
            {
                "claim_id": "claim-habitat",
                "effective_text": "Zebrafish lives in streams.",
                "evidence": [
                    {"evidence_id": "ev-habitat", "text": "streams"}
                ],
            }
        ]
    }
    survivor = {
        "c": "claim-habitat",
        "e": ["ev-habitat"],
        "t": "habitat",
        "m": {
            "r": "lives_in",
            "a": {"habitat": "streams"},
        },
    }

    with pytest.raises(SemanticCandidateV211Error, match="fail-closed"):
        build_semantic_candidate_v2_11(
            survivor,
            source,
            _registry(),
        )


def test_v2_11_rejects_argument_signature_drift() -> None:
    survivor = _temperature_survivor()
    survivor["m"]["a"].pop("unit")

    with pytest.raises(
        SemanticCandidateV211Error,
        match="argument signature mismatch",
    ):
        build_semantic_candidate_v2_11(
            survivor,
            _temperature_source_request(),
            _registry(),
        )


def test_v2_11_rejects_foreign_evidence() -> None:
    survivor = _temperature_survivor(
        evidence_ids=["ev-1", "foreign-evidence"]
    )

    with pytest.raises(SemanticCandidateV211Error, match="foreign Evidence"):
        build_semantic_candidate_v2_11(
            survivor,
            _temperature_source_request(),
            _registry(),
        )


def test_v2_11_validator_rejects_native_float_in_canonical_payload() -> None:
    candidate = build_semantic_candidate_v2_11(
        _temperature_survivor(),
        _temperature_source_request(),
        _registry(),
    )
    bad = copy.deepcopy(candidate)
    bad["semantic"]["arguments"][0]["value"]["unexpected"] = 1.5

    with pytest.raises(SemanticCandidateV211Error, match="native float"):
        validate_semantic_candidate_v2_11(bad)


def test_v2_11_validator_detects_identity_tampering() -> None:
    candidate = build_semantic_candidate_v2_11(
        _temperature_survivor(),
        _temperature_source_request(),
        _registry(),
    )
    bad = copy.deepcopy(candidate)
    bad["semantic"]["epistemic_class"] = "tampered"

    with pytest.raises(
        SemanticCandidateV211Error,
        match="canonical_candidate_sha256",
    ):
        validate_semantic_candidate_v2_11(bad)
