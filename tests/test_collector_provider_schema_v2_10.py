from __future__ import annotations

import json
from pathlib import Path

from ecobiome.knowledge_acquisition.provider_provenance_v2_9 import (
    admit_provider_candidates_v2_9,
)
from ecobiome.knowledge_acquisition.provider_schema_v2_10 import (
    build_provider_ontology_v2_10,
    build_provider_schema_v2_10,
)
from ecobiome.knowledge_acquisition.semantic_contract_v2_8 import (
    apply_relation_type_contract_v2_8,
    load_relation_type_contract_v2_8,
)
from ecobiome.knowledge_acquisition.semantic_contract_v2_10 import (
    apply_relation_type_delta_v2_10,
    load_relation_type_delta_v2_10,
)
from ecobiome.knowledge_acquisition.semantic_robustness_v2_7 import (
    validate_registry_v2_7,
)

ROOT = Path(__file__).resolve().parent
V27 = (
    ROOT
    / "fixtures"
    / "collector_semantic_v2_7"
    / "SEMANTIC_RELATION_REGISTRY_V2_7.json"
)
V28 = (
    ROOT
    / "fixtures"
    / "collector_semantic_v2_8"
    / "SEMANTIC_RELATION_TYPE_CONTRACT_V2_8.json"
)
V210 = (
    ROOT
    / "fixtures"
    / "collector_semantic_v2_10"
    / "SEMANTIC_RELATION_TYPE_DELTA_V2_10.json"
)


def _registry_v2_10() -> dict[str, object]:
    base = validate_registry_v2_7(
        json.loads(V27.read_text(encoding="utf-8"))
    )
    v2_8 = apply_relation_type_contract_v2_8(
        base,
        load_relation_type_contract_v2_8(V28),
    )
    return apply_relation_type_delta_v2_10(
        v2_8,
        load_relation_type_delta_v2_10(V210),
    )


def _source_request() -> dict[str, object]:
    return {
        "source_claims": [
            {
                "claim_id": "claim-1",
                "effective_text": "juvenile zebrafish were studied",
                "evidence": [
                    {
                        "evidence_id": "ev-1",
                        "text": "juvenile zebrafish were studied",
                    }
                ],
            },
            {
                "claim_id": "claim-2",
                "effective_text": "ammonia peaked",
                "evidence": [
                    {
                        "evidence_id": "ev-2",
                        "text": "ammonia peaked",
                    }
                ],
            },
        ]
    }


def _relation_from_branch(branch: dict[str, object]) -> str:
    return branch["properties"]["m"]["properties"]["r"]["const"]  # type: ignore[index]


def test_v2_10_provider_schema_is_factorized_2_by_45() -> None:
    schema, metadata = build_provider_schema_v2_10(
        _source_request(),
        _registry_v2_10(),
    )

    assert metadata["source_scope_branch_count"] == 2
    assert metadata["semantic_assertion_branch_count"] == 45
    assert metadata["cartesian_branch_count_avoided"] == 90
    assert metadata["factorized_branch_count"] == 47

    items = schema["properties"]["p"]["items"]
    assert len(items["properties"]["s"]["oneOf"]) == 2
    assert len(items["properties"]["x"]["oneOf"]) == 45


def test_v2_10_provider_schema_exposes_only_resolved_relations() -> None:
    registry = _registry_v2_10()
    schema, _ = build_provider_schema_v2_10(
        _source_request(),
        registry,
    )

    branches = schema["properties"]["p"]["items"]["properties"]["x"]["oneOf"]
    exposed = {
        _relation_from_branch(branch)
        for branch in branches
    }
    expected = {
        relation
        for relation, spec in registry["relations"].items()
        if spec["semantic_type_contract_state"] != "unresolved_blocked"
    }

    assert exposed == expected
    assert "lives_in" not in exposed
    assert "tolerates" not in exposed
    assert "is_robust" not in exposed


def test_v2_10_provider_ontology_matches_resolved_registry() -> None:
    registry = _registry_v2_10()
    ontology = build_provider_ontology_v2_10(registry)

    assert len(ontology["relations"]) == 45
    assert len(ontology["blocked_relation_ids"]) == 18
    assert set(ontology["relations"]).isdisjoint(
        ontology["blocked_relation_ids"]
    )
    assert set(ontology["relations"]) | set(
        ontology["blocked_relation_ids"]
    ) == set(registry["relations"])


def test_v2_9_admission_accepts_new_v2_10_reviewed_relation() -> None:
    source = _source_request()
    registry = _registry_v2_10()

    compact = {
        "p": [
            {
                "s": {
                    "c": "claim-1",
                    "e": ["ev-1"],
                },
                "x": {
                    "t": "study_subject",
                    "m": {
                        "r": "studied",
                        "a": {
                            "life_stage": "juvenile",
                            "species": "zebrafish",
                        },
                    },
                },
            }
        ]
    }

    result = admit_provider_candidates_v2_9(
        compact,
        source,
        registry,
    )

    assert result["survivor_count"] == 1
    assert result["rejected_count"] == 0


def test_v2_9_admission_still_rejects_fail_closed_relation() -> None:
    source = _source_request()
    registry = _registry_v2_10()

    compact = {
        "p": [
            {
                "s": {
                    "c": "claim-1",
                    "e": ["ev-1"],
                },
                "x": {
                    "t": "habitat",
                    "m": {
                        "r": "lives_in",
                        "a": {
                            "organism": "zebrafish",
                            "habitat": "juvenile",
                        },
                    },
                },
            }
        ]
    }

    result = admit_provider_candidates_v2_9(
        compact,
        source,
        registry,
    )

    assert result["survivor_count"] == 0
    assert result["rejection_stage_counts"] == {"relation_type": 1}


def test_v2_10_zero_proposal_abstention_remains_valid() -> None:
    result = admit_provider_candidates_v2_9(
        {"p": []},
        _source_request(),
        _registry_v2_10(),
    )

    assert result["survivor_count"] == 0
    assert result["rejected_count"] == 0
    assert result["zero_survivors_is_valid_abstention"] is True
