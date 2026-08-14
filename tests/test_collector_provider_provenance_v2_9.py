from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition.provider_provenance_v2_9 import (
    CLAIM_SCOPED_PROVENANCE_POLICY_V2_9_CANONICAL_SHA256,
    admit_provider_candidates_v2_9,
    build_provider_schema_v2_9,
    build_source_scope_branches_v2_9,
    deduplicate_proposals_v2_9,
    evidence_owner_index_v2_9,
    load_provenance_policy_v2_9,
    normalize_wire_proposal_v2_9,
    source_scope_decision_v2_9,
)

ROOT = Path(__file__).resolve().parent
POLICY_PATH = (
    ROOT
    / "fixtures"
    / "collector_semantic_v2_9"
    / "CLAIM_SCOPED_PROVENANCE_POLICY_V2_9.json"
)


def test_frozen_v2_9_policy_loads_with_expected_canonical_sha() -> None:
    policy = load_provenance_policy_v2_9(POLICY_PATH)

    assert policy["policy_version"] == "2.9"
    assert CLAIM_SCOPED_PROVENANCE_POLICY_V2_9_CANONICAL_SHA256 == (
        "4c9ab21e6824031092868fafccd910f9f2ec203b650f898f141231490c8bdfc0"
    )
    assert policy["principles"]["automatic_scientific_acceptance"] is False


def _source_request() -> dict[str, object]:
    return {
        "source_claims": [
            {
                "claim_id": "claim-1",
                "effective_text": "fish could produce a robust state",
                "evidence": [
                    {
                        "evidence_id": "ev-1",
                        "text": "fish could produce",
                    },
                    {
                        "evidence_id": "ev-2",
                        "text": "robust state",
                    },
                ],
            },
            {
                "claim_id": "claim-2",
                "effective_text": "goldfish costs five euros",
                "evidence": [
                    {
                        "evidence_id": "ev-3",
                        "text": "goldfish costs five euros",
                    }
                ],
            },
        ]
    }


def _v2_8_provider_schema() -> dict[str, object]:
    def branch(
        semantic_type: str,
        relation: str,
        argument_keys: list[str],
    ) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "c": {
                    "type": "string",
                    "enum": ["claim-1", "claim-2"],
                },
                "t": {
                    "type": "string",
                    "enum": [semantic_type],
                },
                "e": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["ev-1", "ev-2", "ev-3"],
                    },
                },
                "m": {
                    "type": "object",
                    "properties": {
                        "r": {
                            "const": relation,
                        },
                        "a": {
                            "type": "object",
                            "properties": {
                                key: {"type": "string"}
                                for key in argument_keys
                            },
                            "required": argument_keys,
                            "additionalProperties": False,
                        },
                    },
                    "required": ["r", "a"],
                    "additionalProperties": False,
                },
            },
            "required": ["c", "t", "e", "m"],
            "additionalProperties": False,
        }

    return {
        "type": "object",
        "properties": {
            "p": {
                "type": "array",
                "items": {
                    "oneOf": [
                        branch(
                            "causal_inference",
                            "could_produce_state",
                            ["subject", "state"],
                        ),
                        branch(
                            "measurement_trend",
                            "decreased",
                            ["analyte", "temperature_scope"],
                        ),
                    ]
                },
            }
        },
        "required": ["p"],
        "additionalProperties": False,
    }


def _registry_v2_8() -> dict[str, object]:
    return {
        "relations": {
            "could_produce_state": {
                "semantic_type_contract_state":
                    "constrained_existing_v2_7",
                "semantic_types_allowed": ["causal_inference"],
            },
            "decreased": {
                "semantic_type_contract_state":
                    "constrained_reviewed_singleton_v2_8",
                "semantic_types_allowed": ["measurement_trend"],
            },
            "tolerates": {
                "semantic_type_contract_state": "unresolved_blocked",
                "semantic_types_allowed": [],
            },
        }
    }


def _valid_wire_proposal() -> dict[str, object]:
    return {
        "s": {
            "c": "claim-1",
            "e": ["ev-1", "ev-2"],
        },
        "x": {
            "t": "causal_inference",
            "m": {
                "r": "could_produce_state",
                "a": {
                    "subject": "fish",
                    "state": "robust state",
                },
            },
        },
    }


def test_source_scope_branches_are_claim_local() -> None:
    branches = build_source_scope_branches_v2_9(
        _source_request()
    )

    assert len(branches) == 2
    assert branches[0]["properties"]["c"]["const"] == "claim-1"
    assert branches[0]["properties"]["e"]["items"]["enum"] == [
        "ev-1",
        "ev-2",
    ]
    assert branches[1]["properties"]["c"]["const"] == "claim-2"
    assert branches[1]["properties"]["e"]["items"]["enum"] == ["ev-3"]


def test_provider_schema_is_factorized_without_cartesian_product() -> None:
    schema, metadata = build_provider_schema_v2_9(
        _source_request(),
        _v2_8_provider_schema(),
    )

    item = schema["properties"]["p"]["items"]

    assert len(item["properties"]["s"]["oneOf"]) == 2
    assert len(item["properties"]["x"]["oneOf"]) == 2
    assert metadata["cartesian_branch_count_avoided"] == 4
    assert metadata["factorized_branch_count"] == 4
    assert schema["properties"]["p"]["maxItems"] == 40


def test_source_scope_accepts_claim_local_evidence() -> None:
    decision = source_scope_decision_v2_9(
        _source_request(),
        {
            "c": "claim-1",
            "e": ["ev-1", "ev-2"],
        },
    )

    assert decision["accepted"] is True
    assert decision["state"] == "claim_local_evidence"


def test_source_scope_rejects_foreign_parent_evidence() -> None:
    decision = source_scope_decision_v2_9(
        _source_request(),
        {
            "c": "claim-1",
            "e": ["ev-3"],
        },
    )

    assert decision["accepted"] is False
    assert decision["state"] == "foreign_parent_evidence_id"
    assert decision["foreign_evidence_ids"] == ["ev-3"]


def test_source_scope_rejects_unknown_evidence() -> None:
    decision = source_scope_decision_v2_9(
        _source_request(),
        {
            "c": "claim-1",
            "e": ["unknown-evidence"],
        },
    )

    assert decision["accepted"] is False
    assert decision["state"] == "unknown_evidence_id"


def test_duplicate_evidence_ownership_is_rejected() -> None:
    source_request = _source_request()
    second_claim = source_request["source_claims"][1]
    second_claim["evidence"][0]["evidence_id"] = "ev-1"

    with pytest.raises(
        ValueError,
        match="Evidence ID owned by multiple Claims",
    ):
        evidence_owner_index_v2_9(source_request)


def test_wire_adapter_preserves_source_and_semantic_fields() -> None:
    normalized = normalize_wire_proposal_v2_9(
        _valid_wire_proposal()
    )

    assert normalized == {
        "c": "claim-1",
        "e": ["ev-1", "ev-2"],
        "t": "causal_inference",
        "m": {
            "r": "could_produce_state",
            "a": {
                "subject": "fish",
                "state": "robust state",
            },
        },
    }


def test_admission_rejects_foreign_evidence_before_grounding() -> None:
    proposal = _valid_wire_proposal()
    proposal["s"] = {
        "c": "claim-1",
        "e": ["ev-3"],
    }

    result = admit_provider_candidates_v2_9(
        {"p": [proposal]},
        _source_request(),
        _registry_v2_8(),
    )

    assert result["survivor_count"] == 0
    assert result["rejection_stage_counts"] == {
        "source_scope": 1,
    }


def test_admission_rejects_cross_claim_argument_grounding() -> None:
    proposal = _valid_wire_proposal()
    proposal["x"]["m"]["a"] = {
        "subject": "goldfish",
        "state": "five euros",
    }

    result = admit_provider_candidates_v2_9(
        {"p": [proposal]},
        _source_request(),
        _registry_v2_8(),
    )

    assert result["survivor_count"] == 0
    assert result["rejection_stage_counts"] == {
        "claim_local_grounding": 1,
    }


def test_admission_rejects_unresolved_relation() -> None:
    proposal = _valid_wire_proposal()
    proposal["x"] = {
        "t": "temperature_tolerance",
        "m": {
            "r": "tolerates",
            "a": {
                "condition": "cold",
            },
        },
    }

    result = admit_provider_candidates_v2_9(
        {"p": [proposal]},
        _source_request(),
        _registry_v2_8(),
    )

    assert result["survivor_count"] == 0
    assert result["rejection_stage_counts"] == {
        "relation_type": 1,
    }
    assert result["rejected"][0]["state"] == "unresolved_blocked"


def test_admission_deduplicates_exact_survivors() -> None:
    proposal = _valid_wire_proposal()

    result = admit_provider_candidates_v2_9(
        {"p": [proposal, copy.deepcopy(proposal)]},
        _source_request(),
        _registry_v2_8(),
    )

    assert result["survivor_count_before_dedup"] == 2
    assert result["survivor_count"] == 1
    assert result["deduplication"]["removed_duplicate_count"] == 1
    assert result["deduplication"]["duplicate_group_count"] == 1


def test_empty_batch_is_valid_fail_safe_abstention() -> None:
    result = admit_provider_candidates_v2_9(
        {"p": []},
        _source_request(),
        _registry_v2_8(),
    )

    assert result["input_proposal_count"] == 0
    assert result["survivor_count"] == 0
    assert result["rejected_count"] == 0
    assert result["zero_survivors_is_valid_abstention"] is True
    assert result["automatic_scientific_acceptance"] is False


def test_deduplication_is_deterministic_keep_first() -> None:
    proposal = normalize_wire_proposal_v2_9(
        _valid_wire_proposal()
    )
    unique, diagnostics = deduplicate_proposals_v2_9(
        [proposal, copy.deepcopy(proposal)]
    )

    assert unique == [proposal]
    assert diagnostics["input_count"] == 2
    assert diagnostics["unique_count"] == 1
    assert diagnostics["removed_duplicate_count"] == 1
