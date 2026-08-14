from __future__ import annotations

from typing import Any

from ecobiome.knowledge_acquisition.semantic_benchmark_grounded import (
    evaluate_structured_semantic_benchmark,
)
from ecobiome.knowledge_acquisition.semantic_grounding import (
    GROUNDING_POLICY_V1_1,
)


def _contract() -> dict[str, Any]:
    return {
        "ontology_version": "tiny",
        "semantic_types": ["knowledge_gap", "duration", "trend"],
        "relations": {
            "not_well_understood": {"argument_keys": ["topic"]},
            "adversely_affects": {"argument_keys": ["cause", "target"]},
            "lasted": {"argument_keys": ["value", "unit"]},
            "decreased": {"argument_keys": ["analyte", "temperature_scope"]},
        },
        "argument_vocabulary": {
            "topic": {"type": "string"},
            "cause": {"type": "string"},
            "target": {"type": "string"},
            "value": {"type": "number"},
            "unit": {"type": "string"},
            "analyte": {"type": "string"},
            "temperature_scope": {"type": "string"},
        },
    }


def _export() -> dict[str, Any]:
    return {
        "source_claims": [
            {
                "claim_id": "c1",
                "effective_text": (
                    "How global change drivers interact to affect the resistance "
                    "and functioning of microbial communities is not well understood."
                ),
                "evidence": [{"evidence_id": "e1"}],
            },
            {
                "claim_id": "c2",
                "effective_text": "A four-year field experiment was conducted.",
                "evidence": [{"evidence_id": "e2"}],
            },
        ]
    }


def _knowledge_fixture() -> dict[str, Any]:
    return {
        "required_propositions": [
            {
                "id": "g1",
                "source_claim_id": "c1",
                "semantic_type": "knowledge_gap",
                "canonical_text": "Interaction effects are not well understood.",
                "minimal_evidence_ids": ["e1"],
                "meaning": {
                    "facet": "gap",
                    "relation": "not_well_understood",
                    "arguments": {"topic": "canonical_topic_identifier"},
                    "essential_argument_keys": ["topic"],
                },
            },
            {
                "id": "g2",
                "source_claim_id": "c1",
                "semantic_type": "knowledge_gap",
                "canonical_text": "The gap hinders modeling.",
                "minimal_evidence_ids": ["e1"],
                "meaning": {
                    "facet": "impact",
                    "relation": "adversely_affects",
                    "arguments": {"cause": "gap", "target": "modeling"},
                    "essential_argument_keys": ["cause", "target"],
                },
            },
        ],
        "admissible_propositions": [],
        "excluded_propositions": [],
    }


def _knowledge_candidate() -> dict[str, Any]:
    return {
        "proposals": [
            {
                "source_claim_id": "c1",
                "semantic_type": "knowledge_gap",
                "text": "source-grounded gap",
                "evidence_ids": ["e1"],
                "benchmark_meaning": {
                    "relation": "not_well_understood",
                    "arguments": {
                        "topic": (
                            "How global change drivers interact to affect the "
                            "resistance and functioning of microbial communities"
                        )
                    },
                },
            }
        ]
    }


def test_relation_first_alignment_avoids_false_contradiction() -> None:
    report = evaluate_structured_semantic_benchmark(
        _knowledge_candidate(),
        _knowledge_fixture(),
        _export(),
        label="relation-first",
        candidate_contract=_contract(),
        argument_grounding_policy=GROUNDING_POLICY_V1_1,
    )
    aligned = [
        (item["gold_id"], item["candidate_index"])
        for item in report["alignments"]
    ]
    assert aligned == [("g1", 0)]
    assert report["entailment_polarity"]["contradicted"] == 0
    assert report["entailment_polarity"]["critical_contradictions"] == 0
    assert report["entailment_polarity"]["grounded_unresolved"] == 1
    assert report["strict_coverage"] == {
        "required": 2,
        "detected": 1,
        "missing": 1,
        "rate": 0.5,
    }


def test_grounded_unresolved_receives_no_entailment_credit() -> None:
    report = evaluate_structured_semantic_benchmark(
        _knowledge_candidate(),
        _knowledge_fixture(),
        _export(),
        label="grounded",
        candidate_contract=_contract(),
        argument_grounding_policy=GROUNDING_POLICY_V1_1,
    )
    assert report["entailment_polarity"]["entailed"] == 0
    reasons = report["benchmark_gate"]["blocking_reasons"]
    assert "grounded_unresolved_required=1" in reasons


def test_same_relation_is_required_for_alignment() -> None:
    candidate = _knowledge_candidate()
    candidate["proposals"][0]["benchmark_meaning"] = {
        "relation": "adversely_affects",
        "arguments": {"cause": "gap", "target": "modeling"},
    }
    report = evaluate_structured_semantic_benchmark(
        candidate,
        _knowledge_fixture(),
        _export(),
        label="relation-required",
        candidate_contract=_contract(),
    )
    assert [item["gold_id"] for item in report["alignments"]] == ["g2"]
    assert report["entailment_polarity"]["contradicted"] == 0
    assert {item["gold_id"] for item in report["missing_required"]} == {"g1"}


def test_numeric_value_unit_pair_can_be_strictly_entailed() -> None:
    fixture = {
        "required_propositions": [
            {
                "id": "duration",
                "source_claim_id": "c2",
                "semantic_type": "duration",
                "canonical_text": "Four years.",
                "minimal_evidence_ids": ["e2"],
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
                "source_claim_id": "c2",
                "semantic_type": "duration",
                "text": "four-year",
                "evidence_ids": ["e2"],
                "benchmark_meaning": {
                    "relation": "lasted",
                    "arguments": {"value": 4, "unit": "years"},
                },
            }
        ]
    }
    report = evaluate_structured_semantic_benchmark(
        candidate,
        fixture,
        _export(),
        label="numeric",
        candidate_contract=_contract(),
        argument_grounding_policy=GROUNDING_POLICY_V1_1,
    )
    assert report["entailment_polarity"]["entailed"] == 1
    assert report["benchmark_gate"]["pass"] is True


def test_temperature_scope_rainfall_is_semantic_role_violation() -> None:
    semantic_export = {
        "source_claims": [
            {
                "claim_id": "c3",
                "effective_text": (
                    "Microbial biomass decreased during scant rainfall periods."
                ),
                "evidence": [{"evidence_id": "e3"}],
            }
        ]
    }
    fixture = {
        "required_propositions": [],
        "admissible_propositions": [],
        "excluded_propositions": [],
    }
    candidate = {
        "proposals": [
            {
                "source_claim_id": "c3",
                "semantic_type": "trend",
                "text": "bad typed proxy",
                "evidence_ids": ["e3"],
                "benchmark_meaning": {
                    "relation": "decreased",
                    "arguments": {
                        "analyte": "microbial biomass",
                        "temperature_scope": "scant rainfall periods",
                    },
                },
            }
        ]
    }
    report = evaluate_structured_semantic_benchmark(
        candidate,
        fixture,
        semantic_export,
        label="role-violation",
        candidate_contract=_contract(),
        argument_grounding_policy=GROUNDING_POLICY_V1_1,
    )
    assert report["argument_grounding"]["semantic_role_violation_count"] == 1
    violation = report["argument_grounding"]["semantic_role_violations"][0]
    assert violation["argument_key"] == "temperature_scope"
    assert violation["state"] == "domain_mismatch"
    assert "semantic_role_violations=1" in report["benchmark_gate"]["blocking_reasons"]


def test_global_exact_duplicate_detection_includes_extras() -> None:
    candidate = _knowledge_candidate()
    candidate["proposals"].append(dict(candidate["proposals"][0]))
    candidate["proposals"][1]["benchmark_meaning"] = dict(
        candidate["proposals"][0]["benchmark_meaning"]
    )
    candidate["proposals"][1]["benchmark_meaning"]["arguments"] = dict(
        candidate["proposals"][0]["benchmark_meaning"]["arguments"]
    )

    report = evaluate_structured_semantic_benchmark(
        candidate,
        _knowledge_fixture(),
        _export(),
        label="duplicates",
        candidate_contract=_contract(),
        argument_grounding_policy=GROUNDING_POLICY_V1_1,
    )
    assert report["global_exact_duplicate_candidates"] == [
        {
            "candidate_index": 1,
            "duplicate_of_candidate_index": 0,
            "identity_sha256": report["global_exact_duplicate_candidates"][0][
                "identity_sha256"
            ],
        }
    ]
    assert "global_exact_duplicate_candidates=1" in report["benchmark_gate"][
        "blocking_reasons"
    ]


def test_no_grounding_policy_preserves_exact_scalar_semantics() -> None:
    fixture = {
        "required_propositions": [
            {
                "id": "duration",
                "source_claim_id": "c2",
                "semantic_type": "duration",
                "canonical_text": "Four years.",
                "minimal_evidence_ids": ["e2"],
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
                "source_claim_id": "c2",
                "semantic_type": "duration",
                "text": "four years",
                "evidence_ids": ["e2"],
                "benchmark_meaning": {
                    "relation": "lasted",
                    "arguments": {"value": 4, "unit": "years"},
                },
            }
        ]
    }
    report = evaluate_structured_semantic_benchmark(
        candidate,
        fixture,
        _export(),
        label="compat",
        candidate_contract=_contract(),
    )
    assert report["entailment_polarity"]["entailed"] == 1
    assert report["argument_grounding"]["enabled"] is False
