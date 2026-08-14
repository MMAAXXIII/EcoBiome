from __future__ import annotations

import json
from pathlib import Path

from ecobiome.knowledge_acquisition.semantic_robustness_v2_7 import (
    audit_provider_provenance_v1_1,
    classify_epistemic_transition_v2_7,
    constrain_provider_output_schema_v1_1,
    coordinated_span_state_multilingual,
    relation_epistemic_class_v2_7,
    validate_legacy_epistemic_coverage_policy,
    validate_multilingual_coordination_policy,
    validate_provider_provenance_policy,
    validate_registry_v2_7,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "collector_semantic_v2_7"


def _load(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_v2_7_assets_validate_and_cover_all_relations() -> None:
    registry = validate_registry_v2_7(
        _load("SEMANTIC_RELATION_REGISTRY_V2_7.json")
    )
    coordination = validate_multilingual_coordination_policy(
        _load("MULTILINGUAL_COORDINATION_POLICY_V1_1.json")
    )
    epistemic = validate_legacy_epistemic_coverage_policy(
        _load("LEGACY_EPISTEMIC_COVERAGE_V1.json")
    )
    provenance = validate_provider_provenance_policy(
        _load("PROVIDER_PROVENANCE_CONSTRAINT_V1_1.json")
    )

    assert len(registry["relations"]) == 63
    assert len(epistemic["all_relation_epistemic_class"]) == 63
    assert coordination["automatic_split"] is False
    assert provenance["automatic_scientific_acceptance"] is False


def test_french_and_english_coordination_are_detected_without_credit() -> None:
    policy = _load("MULTILINGUAL_COORDINATION_POLICY_V1_1.json")

    french = coordinated_span_state_multilingual(
        "condition",
        "ni le chaud, ni le froid",
        "Il ne supporte ni le chaud, ni le froid.",
        policy,
        language="fr",
    )
    english = coordinated_span_state_multilingual(
        "condition",
        "heat or low oxygen",
        "The exposure was heat or low oxygen.",
        policy,
        language="en-US",
    )

    assert french["state"] == "grounded_coordinated_unresolved"
    assert french["scientifically_scoreable"] is False
    assert french["coordinated"] is True

    assert english["state"] == "grounded_coordinated_unresolved"
    assert english["scientifically_scoreable"] is False
    assert english["coordinated"] is True


def test_unknown_language_does_not_invent_coordination() -> None:
    policy = _load("MULTILINGUAL_COORDINATION_POLICY_V1_1.json")

    result = coordinated_span_state_multilingual(
        "condition",
        "x y z",
        "The source says x y z.",
        policy,
        language="zz",
    )

    assert result["language_supported"] is False
    assert result["coordinated"] is False
    assert result["state"] == "grounded_scalar_unresolved"


def test_legacy_epistemic_classes_are_machine_readable() -> None:
    registry = _load("SEMANTIC_RELATION_REGISTRY_V2_7.json")

    assert relation_epistemic_class_v2_7(
        registry,
        "effective_against",
    ) == "capacity_or_trait"
    assert relation_epistemic_class_v2_7(
        registry,
        "studied",
    ) == "study_context_non_result"
    assert relation_epistemic_class_v2_7(
        registry,
        "caused",
    ) == "explicit_causal_result"
    assert relation_epistemic_class_v2_7(
        registry,
        "not_well_understood",
    ) == "knowledge_state"


def test_epistemic_strength_upgrade_is_blocked() -> None:
    policy = _load("LEGACY_EPISTEMIC_COVERAGE_V1.json")

    result = classify_epistemic_transition_v2_7(
        "study_context_non_result",
        "explicit_causal_result",
        policy,
    )

    assert result["status"] == "epistemic_overclaim"
    assert result["blocking"] is True
    assert result["entailed_by_class_alone"] is False


def _source_request() -> dict[str, object]:
    return {
        "source_claims": [
            {
                "claim_id": "c1",
                "evidence": [
                    {"evidence_id": "e1"},
                    {"evidence_id": "e2"},
                ],
            },
            {
                "claim_id": "c2",
                "evidence": [
                    {"evidence_id": "e3"},
                ],
            },
        ],
    }


def _schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "p": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "c": {"type": "string"},
                        "e": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "t": {"type": "string"},
                        "m": {"type": "object"},
                    },
                },
            },
        },
    }


def test_provider_schema_gets_finite_claim_and_evidence_enums() -> None:
    policy = _load("PROVIDER_PROVENANCE_CONSTRAINT_V1_1.json")

    constrained = constrain_provider_output_schema_v1_1(
        _schema(),
        _source_request(),
        policy,
    )

    proposal = constrained["properties"]["p"]["items"]["properties"]
    assert proposal["c"]["enum"] == ["c1", "c2"]
    assert proposal["e"]["items"]["enum"] == ["e1", "e2", "e3"]
    assert proposal["e"]["minItems"] == 1
    assert proposal["e"]["uniqueItems"] is True


def test_provider_provenance_blocks_unknown_and_foreign_evidence() -> None:
    policy = _load("PROVIDER_PROVENANCE_CONSTRAINT_V1_1.json")

    compact = {
        "p": [
            {"c": "c1", "e": ["invented"], "t": "x", "m": {}},
            {"c": "c1", "e": ["e3"], "t": "x", "m": {}},
            {"c": "c2", "e": ["e3"], "t": "x", "m": {}},
        ],
    }

    audit = audit_provider_provenance_v1_1(
        compact,
        _source_request(),
        policy,
    )

    reasons = [item["reason"] for item in audit["violations"]]
    assert "unknown_evidence_id" in reasons
    assert "foreign_parent_evidence_id" in reasons
    assert audit["blocking"] is True
