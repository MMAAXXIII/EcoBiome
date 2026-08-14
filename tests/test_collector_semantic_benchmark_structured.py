from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

import pytest

from ecobiome.knowledge_acquisition.semantic_benchmark_structured import (
    evaluate_structured_semantic_benchmark,
)


def _assets() -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    semantic_export = {
        "source_claims": [
            {
                "claim_id": "c1",
                "evidence": [{"evidence_id": "e1"}],
            },
            {
                "claim_id": "c2",
                "evidence": [{"evidence_id": "e2"}],
            },
        ]
    }
    fixture = {
        "required_propositions": [
            {
                "id": "g1",
                "source_claim_id": "c1",
                "semantic_type": "measurement",
                "canonical_text": "Temperature was 34 degC.",
                "minimal_evidence_ids": ["e1"],
                "meaning": {
                    "facet": "temperature",
                    "relation": "measured",
                    "arguments": {"value": 34, "unit": "degC"},
                    "essential_argument_keys": ["value", "unit"],
                },
            }
        ],
        "admissible_propositions": [],
        "excluded_propositions": [
            {
                "id": "x1",
                "source_claim_id": "c1",
                "semantic_type": "causal",
                "reason": "causal relation forbidden in this tiny fixture",
                "forbidden_meaning": {
                    "facet": "cause",
                    "relation": "caused",
                    "arguments": {
                        "cause": "heat",
                        "effect": "mortality",
                    },
                    "essential_argument_keys": ["cause", "effect"],
                },
            }
        ],
    }
    candidate = {
        "proposals": [
            {
                "source_claim_id": "c1",
                "semantic_type": "measurement",
                "text": "34 degC",
                "evidence_ids": ["e1"],
                "benchmark_meaning": {
                    "relation": "measured",
                    "arguments": {"value": 34, "unit": "degC"},
                },
            }
        ]
    }
    contract = {
        "ontology_version": "tiny-v1",
        "semantic_types": {
            "measurement": "x",
            "causal": "x",
        },
        "relations": {
            "measured": {"argument_keys": ["value", "unit"]},
            "caused": {"argument_keys": ["cause", "effect"]},
        },
        "argument_vocabulary": {
            "value": {"type": "number"},
            "unit": {"type": "string", "enum": ["degC"]},
            "cause": {"type": "string"},
            "effect": {"type": "string"},
        },
    }
    return semantic_export, fixture, candidate, contract


def _evaluate(
    payload: Any,
    *,
    fixture: dict[str, Any] | None = None,
    semantic_export: dict[str, Any] | None = None,
    contract: Any | None = None,
) -> dict[str, Any]:
    base_export, base_fixture, _candidate, base_contract = _assets()
    return evaluate_structured_semantic_benchmark(
        payload,
        fixture if fixture is not None else base_fixture,
        semantic_export if semantic_export is not None else base_export,
        label="tiny",
        candidate_contract=base_contract if contract is None else contract,
    )


def _mutate(mutator: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    _export, _fixture, candidate, _contract = _assets()
    payload = copy.deepcopy(candidate)
    mutator(payload["proposals"][0])
    return payload


def _violation_kinds(report: dict[str, Any]) -> list[str]:
    return [
        str(item["kind"])
        for item in report["candidate_contract"]["violations"]
    ]


def _assert_violation(payload: Any, kind: str) -> None:
    report = _evaluate(payload)
    assert kind in _violation_kinds(report)
    assert report["benchmark_gate"]["pass"] is False
    assert any(
        reason.startswith("candidate_contract_violations=")
        for reason in report["benchmark_gate"]["blocking_reasons"]
    )


def test_valid_candidate_passes() -> None:
    _export, _fixture, candidate, _contract = _assets()
    report = _evaluate(copy.deepcopy(candidate))
    assert report["benchmark_gate"]["pass"] is True
    assert report["candidate_contract"]["violation_count"] == 0


def test_payload_not_object_is_nonfatal() -> None:
    _assert_violation([], "candidate_payload_not_object")


def test_proposals_not_list_is_nonfatal() -> None:
    _assert_violation({"proposals": {}}, "proposals_not_list")


def test_proposal_not_object_is_nonfatal() -> None:
    _assert_violation({"proposals": ["bad"]}, "proposal_not_object")


def test_invalid_source_claim_id_is_nonfatal() -> None:
    payload = _mutate(
        lambda proposal: proposal.__setitem__("source_claim_id", None)
    )
    _assert_violation(payload, "invalid_source_claim_id")


def test_unknown_parent_claim_is_nonfatal() -> None:
    payload = _mutate(
        lambda proposal: proposal.__setitem__("source_claim_id", "missing")
    )
    _assert_violation(payload, "unknown_parent_claim")


def test_evidence_not_owned_by_parent_is_nonfatal() -> None:
    payload = _mutate(
        lambda proposal: proposal.__setitem__("evidence_ids", ["e2"])
    )
    _assert_violation(payload, "evidence_not_owned_by_parent")


def test_evidence_ids_not_list_is_nonfatal() -> None:
    payload = _mutate(
        lambda proposal: proposal.__setitem__("evidence_ids", "e1")
    )
    _assert_violation(payload, "evidence_ids_not_list")


def test_invalid_evidence_id_is_nonfatal() -> None:
    payload = _mutate(
        lambda proposal: proposal.__setitem__("evidence_ids", ["e1", 7])
    )
    _assert_violation(payload, "invalid_evidence_id")


def test_invalid_text_remains_scoreable_but_blocks_gate() -> None:
    payload = _mutate(
        lambda proposal: proposal.__setitem__("text", None)
    )
    report = _evaluate(payload)
    assert report["entailment_polarity"]["entailed"] == 1
    assert report["candidate_contract"]["violation_count"] == 1
    assert report["benchmark_gate"]["pass"] is False


def test_missing_structured_meaning_is_nonfatal() -> None:
    payload = _mutate(
        lambda proposal: proposal.__setitem__("benchmark_meaning", None)
    )
    _assert_violation(payload, "missing_structured_meaning")


def test_meaning_not_object_is_nonfatal() -> None:
    payload = _mutate(
        lambda proposal: proposal.__setitem__("benchmark_meaning", "x")
    )
    _assert_violation(payload, "meaning_not_object")


def test_invalid_relation_field_is_nonfatal() -> None:
    payload = _mutate(
        lambda proposal: proposal["benchmark_meaning"].__setitem__(
            "relation",
            None,
        )
    )
    _assert_violation(payload, "invalid_relation_field")


def test_arguments_not_object_is_nonfatal() -> None:
    payload = _mutate(
        lambda proposal: proposal["benchmark_meaning"].__setitem__(
            "arguments",
            [],
        )
    )
    _assert_violation(payload, "arguments_not_object")


def test_unknown_semantic_type_is_contract_violation() -> None:
    payload = _mutate(
        lambda proposal: proposal.__setitem__("semantic_type", "other")
    )
    _assert_violation(payload, "unknown_semantic_type")


def test_unknown_relation_is_contract_violation() -> None:
    payload = _mutate(
        lambda proposal: proposal["benchmark_meaning"].__setitem__(
            "relation",
            "other",
        )
    )
    _assert_violation(payload, "unknown_relation")


def test_argument_keys_mismatch_is_contract_violation() -> None:
    payload = _mutate(
        lambda proposal: proposal["benchmark_meaning"].__setitem__(
            "arguments",
            {"value": 34},
        )
    )
    _assert_violation(payload, "argument_keys_mismatch")


def test_unknown_argument_key_is_contract_violation() -> None:
    payload = _mutate(
        lambda proposal: proposal["benchmark_meaning"].__setitem__(
            "arguments",
            {"value": 34, "unit": "degC", "bogus": "x"},
        )
    )
    _assert_violation(payload, "unknown_argument_key")


def test_argument_type_mismatch_is_contract_violation() -> None:
    payload = _mutate(
        lambda proposal: proposal["benchmark_meaning"].__setitem__(
            "arguments",
            {"value": "34", "unit": "degC"},
        )
    )
    _assert_violation(payload, "argument_type_mismatch")


def test_argument_enum_mismatch_is_contract_violation() -> None:
    payload = _mutate(
        lambda proposal: proposal["benchmark_meaning"].__setitem__(
            "arguments",
            {"value": 34, "unit": "C"},
        )
    )
    _assert_violation(payload, "argument_enum_mismatch")


def test_duplicate_evidence_remains_blocking() -> None:
    payload = _mutate(
        lambda proposal: proposal.__setitem__("evidence_ids", ["e1", "e1"])
    )
    report = _evaluate(payload)
    assert len(report["duplicate_evidence_candidates"]) == 1
    assert report["benchmark_gate"]["pass"] is False


def test_wrong_numeric_value_is_contradicted() -> None:
    payload = _mutate(
        lambda proposal: proposal["benchmark_meaning"].__setitem__(
            "arguments",
            {"value": 35, "unit": "degC"},
        )
    )
    report = _evaluate(payload)
    assert report["entailment_polarity"]["contradicted"] == 1


def test_unexpected_argument_is_overclaimed() -> None:
    payload = _mutate(
        lambda proposal: proposal["benchmark_meaning"].__setitem__(
            "arguments",
            {"value": 34, "unit": "degC", "bogus": "x"},
        )
    )
    report = _evaluate(payload)
    assert report["entailment_polarity"]["overclaimed"] == 1


def test_forbidden_inference_remains_detected() -> None:
    payload = {
        "proposals": [
            {
                "source_claim_id": "c1",
                "semantic_type": "causal",
                "text": "bad causality",
                "evidence_ids": ["e1"],
                "benchmark_meaning": {
                    "relation": "caused",
                    "arguments": {
                        "cause": "heat",
                        "effect": "mortality",
                    },
                },
            }
        ]
    }
    report = _evaluate(payload)
    assert len(report["policy_violations"]) == 1


def test_fixture_corruption_remains_fatal() -> None:
    semantic_export, _fixture, candidate, contract = _assets()
    broken_fixture = {
        "required_propositions": [],
        "admissible_propositions": [],
    }
    with pytest.raises(TypeError):
        evaluate_structured_semantic_benchmark(
            candidate,
            broken_fixture,
            semantic_export,
            label="broken-fixture",
            candidate_contract=contract,
        )


def test_semantic_export_corruption_remains_fatal() -> None:
    _semantic_export, fixture, candidate, contract = _assets()
    with pytest.raises(TypeError):
        evaluate_structured_semantic_benchmark(
            candidate,
            fixture,
            {},
            label="broken-export",
            candidate_contract=contract,
        )


def test_contract_corruption_remains_fatal() -> None:
    semantic_export, fixture, candidate, _contract = _assets()
    with pytest.raises(TypeError):
        evaluate_structured_semantic_benchmark(
            candidate,
            fixture,
            semantic_export,
            label="broken-contract",
            candidate_contract={"semantic_types": []},
        )
