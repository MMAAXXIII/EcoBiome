from __future__ import annotations

import json
from pathlib import Path

from ecobiome.knowledge_acquisition.semantic_epistemic import (
    audit_epistemic_overclaims,
    classify_epistemic_transition,
    coordinated_span_state,
    validate_epistemic_policy,
    validate_registry_v2_6,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "collector_semantic_v2_6"


def _registry():
    return json.loads((FIXTURE_DIR / "SEMANTIC_RELATION_REGISTRY_V2_6.json").read_text())


def _policy():
    return json.loads((FIXTURE_DIR / "COORDINATED_SPAN_EPISTEMIC_POLICY_V1.json").read_text())


def test_frozen_assets_validate() -> None:
    assert validate_registry_v2_6(_registry())["registry_version"] == "2.6-candidate"
    assert validate_epistemic_policy(_policy())["policy_version"] == "1.0-audit-candidate"


def test_coordinated_exposure_is_preserved_unresolved() -> None:
    record = coordinated_span_state(
        "exposure",
        "heat and low oxygen",
        "We investigated heat and low oxygen.",
        _policy(),
    )
    assert record["state"] == "grounded_coordinated_unresolved"
    assert record["scientifically_scoreable"] is False


def test_coordinated_species_is_cardinality_conflict() -> None:
    record = coordinated_span_state(
        "species",
        "species A and species B",
        "We compared species A and species B.",
        _policy(),
    )
    assert record["state"] == "role_cardinality_conflict"


def test_purpose_to_causal_is_blocking_overclaim() -> None:
    transition = classify_epistemic_transition(
        "study_purpose_non_result",
        "explicit_causal_result",
        _policy(),
    )
    assert transition["status"] == "epistemic_overclaim"
    assert transition["blocking"] is True


def test_same_epistemic_class_is_compatible_not_entailment() -> None:
    transition = classify_epistemic_transition(
        "observational",
        "observational",
        _policy(),
    )
    assert transition["status"] == "compatible_same_class"
    assert transition["entailed_by_class_alone"] is False


def test_epistemic_audit_flags_wrong_relation_upgrade() -> None:
    fixture = {
        "required_propositions": [
            {
                "id": "g1",
                "source_claim_id": "c1",
                "semantic_type": "study_purpose",
                "meaning": {
                    "relation": "investigated_effects_on",
                    "arguments": {"exposure": "heat", "outcome": "growth"},
                    "essential_argument_keys": ["exposure", "outcome"],
                },
            }
        ],
        "admissible_propositions": [],
    }
    candidate = {
        "proposals": [
            {
                "source_claim_id": "c1",
                "semantic_type": "study_purpose",
                "benchmark_meaning": {
                    "relation": "caused_decrease",
                    "arguments": {"exposure": "heat", "variable": "growth"},
                },
            }
        ]
    }
    audit = audit_epistemic_overclaims(candidate, fixture, _registry(), _policy())
    assert audit["violation_count"] == 1
    assert audit["violations"][0]["status"] == "epistemic_overclaim"
