from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from ecobiome.knowledge_acquisition.semantic_benchmark import (
    evaluate_semantic_benchmark,
    infer_candidate_facets,
    infer_candidate_relation,
)

FIXTURES = Path(__file__).parent / "fixtures" / "collector_semantic_v2_2"


def _load(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _reports() -> tuple[dict[str, Any], dict[str, Any]]:
    fixture = _load("GOLDEN_REFERENCE_V2_1.json")
    semantic_export = _load("SEMANTIC_EXPORT.json")
    qwen = evaluate_semantic_benchmark(
        _load("OLLAMA_QWEN36_CANDIDATE.json"),
        fixture,
        semantic_export,
        label="ollama-qwen3.6-live-v2",
    )
    lexical = evaluate_semantic_benchmark(
        _load("LEXICAL_BASELINE.json"),
        fixture,
        semantic_export,
        label="lexical-baseline-v1",
    )
    return qwen, lexical


def test_golden_v2_1_fixture_contract_and_reviewed_evidence() -> None:
    fixture = _load("GOLDEN_REFERENCE_V2_1.json")
    required = {
        item["id"]: item
        for item in fixture["required_propositions"]
    }

    assert len(required) == 13
    assert len(fixture["admissible_propositions"]) == 3
    assert len(fixture["excluded_propositions"]) == 1

    assert required["medaka-g2r-02"]["minimal_evidence_segment_indices"] == [
        37,
        38,
    ]
    assert required["medaka-g2r-07"]["minimal_evidence_segment_indices"] == [
        43,
        44,
    ]
    assert required["medaka-g2r-11"]["minimal_evidence_segment_indices"] == [
        56,
        57,
        58,
    ]

    excluded = fixture["excluded_propositions"][0]
    assert excluded["semantic_type"] == "ph_tolerance"
    assert excluded["reason"] == "forbidden_cross_claim_join_required"


def test_qwen_v2_2_regression_report_is_strictly_blocked() -> None:
    qwen, _ = _reports()

    assert qwen["strict_coverage"] == {
        "required": 13,
        "detected": 12,
        "missing": 1,
        "rate": 0.923077,
    }
    assert qwen["provenance"]["sufficient"] == 5
    assert qwen["provenance"]["insufficient"] == 7
    assert qwen["entailment_polarity"] == {
        "entailed": 4,
        "contradicted": 4,
        "ambiguous": 0,
        "insufficient_evidence": 4,
        "critical_contradictions": 4,
    }
    assert qwen["admissible"]["detected_unique"] == 3
    assert qwen["policy_violations"] == []
    assert qwen["benchmark_gate"] == {
        "pass": False,
        "blocking_reasons": [
            "missing_required=1",
            "required_provenance_insufficient=7",
            "critical_contradictions=4",
        ],
    }
    assert qwen["provider_certification"]["certified"] is False
    assert [item["gold_id"] for item in qwen["missing_required"]] == [
        "medaka-g2r-04"
    ]


def test_qwen_four_oral_polarity_inversions_remain_blocking() -> None:
    qwen, _ = _reports()
    alignments = {
        item["gold_id"]: item
        for item in qwen["alignments"]
    }

    for gold_id in (
        "medaka-g2r-08",
        "medaka-g2r-09",
        "medaka-g2r-10",
        "medaka-g2r-11",
    ):
        assert alignments[gold_id]["candidate_relation"] == (
            "does_not_tolerate"
        )
        assert alignments[gold_id]["entailment_status"] == "contradicted"


def test_qwen_incomplete_evidence_is_not_credited_as_entailment() -> None:
    qwen, _ = _reports()
    alignments = {
        item["gold_id"]: item
        for item in qwen["alignments"]
    }

    for gold_id in (
        "medaka-g2r-02",
        "medaka-g2r-03",
        "medaka-g2r-12",
        "medaka-g2r-13",
    ):
        item = alignments[gold_id]
        assert item["provenance_sufficient"] is False
        assert item["entailment_status"] == "insufficient_evidence"


def test_lexical_baseline_v2_2_regression_report_is_strictly_blocked() -> None:
    _, lexical = _reports()

    assert lexical["strict_coverage"] == {
        "required": 13,
        "detected": 13,
        "missing": 0,
        "rate": 1.0,
    }
    assert lexical["provenance"]["sufficient"] == 7
    assert lexical["provenance"]["insufficient"] == 6
    assert lexical["entailment_polarity"] == {
        "entailed": 7,
        "contradicted": 0,
        "ambiguous": 0,
        "insufficient_evidence": 6,
        "critical_contradictions": 0,
    }
    assert lexical["benchmark_gate"] == {
        "pass": False,
        "blocking_reasons": [
            "required_provenance_insufficient=6",
            "forbidden_inference_policy_violations=1",
        ],
    }
    assert len(lexical["policy_violations"]) == 1
    assert lexical["policy_violations"][0]["semantic_type"] == "ph_tolerance"
    assert lexical["provider_certification"]["certified"] is False


def test_relation_inference_has_no_positive_default() -> None:
    assert infer_candidate_relation(
        "temperature_tolerance",
        "La source indique que ce poisson craint le chaud.",
    ) == "does_not_tolerate"
    assert infer_candidate_relation(
        "temperature_tolerance",
        "Il craint ni le chaud, ni le froid.",
    ) == "tolerates"
    assert infer_candidate_relation(
        "temperature_tolerance",
        "La source affirme que ce poisson résiste au froid.",
    ) == "tolerates"
    assert infer_candidate_relation(
        "robustness",
        "La source parle de ce poisson.",
    ) == "unknown"
    assert infer_candidate_relation(
        "habitat",
        "La source mentionne des rizières.",
    ) == "unknown"


def test_multiple_facets_are_exposed_as_non_atomic() -> None:
    assert infer_candidate_facets(
        "temperature_tolerance",
        "Ce poisson supporte le froid et le chaud.",
    ) == ("cold", "heat")
    assert infer_candidate_facets(
        "habitat",
        "Ce poisson vit en rizière et en estuaire.",
    ) == ("rice_fields", "marine_estuary")


def test_non_atomic_candidate_blocks_benchmark_gate() -> None:
    fixture = _load("GOLDEN_REFERENCE_V2_1.json")
    semantic_export = _load("SEMANTIC_EXPORT.json")
    candidate = copy.deepcopy(_load("OLLAMA_QWEN36_CANDIDATE.json"))

    candidate["proposals"].append(
        {
            "source_claim_id": (
                "0449acf7-8dba-43c9-8990-fe811b7f4f2a"
            ),
            "source_claim_effective_text_sha256": (
                "0" * 64
            ),
            "text": "La source dit que ce poisson vit en rizière et en estuaire.",
            "semantic_type": "habitat",
            "evidence_ids": [
                "0d5a923e-193f-41c5-b7c8-32ff3fc42f44"
            ],
            "qualifiers": {"benchmark_only": True},
        }
    )

    report = evaluate_semantic_benchmark(
        candidate,
        fixture,
        semantic_export,
        label="non-atomic-regression",
    )

    assert report["benchmark_gate"]["pass"] is False
    assert "unexpected_extra_candidates=1" in (
        report["benchmark_gate"]["blocking_reasons"]
    )
    assert report["unexpected_extra_candidates"][-1]["reason"] == (
        "non_atomic_multiple_facets"
    )
