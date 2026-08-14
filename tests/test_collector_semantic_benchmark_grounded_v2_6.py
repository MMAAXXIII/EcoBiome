from __future__ import annotations

import json
from pathlib import Path

from ecobiome.knowledge_acquisition.semantic_benchmark_grounded_v2_6 import (
    evaluate_structured_semantic_benchmark_v2_6,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "collector_semantic_v2_6"


def _registry():
    return json.loads((FIXTURE_DIR / "SEMANTIC_RELATION_REGISTRY_V2_6.json").read_text())


def _policy():
    return json.loads((FIXTURE_DIR / "COORDINATED_SPAN_EPISTEMIC_POLICY_V1.json").read_text())


def test_wrapper_blocks_epistemic_upgrade_even_when_base_sees_extra() -> None:
    semantic_export = {
        "source_claims": [
            {
                "claim_id": "c1",
                "effective_text": "We investigated heat effects on growth.",
                "evidence": [{"evidence_id": "e1"}],
            }
        ]
    }
    fixture = {
        "required_propositions": [
            {
                "id": "g1",
                "source_claim_id": "c1",
                "semantic_type": "study_purpose",
                "canonical_text": "Study purpose.",
                "minimal_evidence_ids": ["e1"],
                "meaning": {
                    "facet": "purpose",
                    "relation": "investigated_effects_on",
                    "arguments": {"exposure": "heat", "outcome": "growth"},
                    "essential_argument_keys": ["exposure", "outcome"],
                },
            }
        ],
        "admissible_propositions": [],
        "excluded_propositions": [],
    }
    candidate = {
        "proposals": [
            {
                "source_claim_id": "c1",
                "semantic_type": "study_purpose",
                "text": "Heat caused lower growth.",
                "evidence_ids": ["e1"],
                "benchmark_meaning": {
                    "relation": "caused_decrease",
                    "arguments": {"exposure": "heat", "variable": "growth"},
                },
            }
        ]
    }
    report = evaluate_structured_semantic_benchmark_v2_6(
        candidate,
        fixture,
        semantic_export,
        label="epistemic-upgrade",
        registry_v2_6=_registry(),
        epistemic_policy=_policy(),
    )
    assert report["epistemic_enforcement"]["violation_count"] == 1
    assert "epistemic_overclaims=1" in report["benchmark_gate"]["blocking_reasons"]
    assert report["benchmark_gate"]["pass"] is False


def test_wrapper_preserves_base_result_for_old_relation() -> None:
    semantic_export = {
        "source_claims": [
            {
                "claim_id": "c1",
                "effective_text": "A four-year field experiment was conducted.",
                "evidence": [{"evidence_id": "e1"}],
            }
        ]
    }
    fixture = {
        "required_propositions": [
            {
                "id": "g1",
                "source_claim_id": "c1",
                "semantic_type": "experiment_duration",
                "canonical_text": "Four years.",
                "minimal_evidence_ids": ["e1"],
                "meaning": {
                    "facet": "duration",
                    "relation": "lasted",
                    "arguments": {"value": 4, "unit": "years"},
                    "essential_argument_keys": ["value", "unit"],
                },
            }
        ],
        "admissible_propositions": [],
        "excluded_propositions": [],
    }
    candidate = {
        "proposals": [
            {
                "source_claim_id": "c1",
                "semantic_type": "experiment_duration",
                "text": "four-year",
                "evidence_ids": ["e1"],
                "benchmark_meaning": {
                    "relation": "lasted",
                    "arguments": {"value": 4, "unit": "years"},
                },
            }
        ]
    }
    report = evaluate_structured_semantic_benchmark_v2_6(
        candidate,
        fixture,
        semantic_export,
        label="compat",
        registry_v2_6=_registry(),
        epistemic_policy=_policy(),
    )
    assert report["strict_coverage"]["detected"] == 1
    assert report["entailment_polarity"]["entailed"] == 1
    assert report["epistemic_enforcement"]["violation_count"] == 0
    assert report["coordinated_span"]["role_cardinality_conflict_count"] == 0
    assert report["benchmark_gate"]["pass"] is True
