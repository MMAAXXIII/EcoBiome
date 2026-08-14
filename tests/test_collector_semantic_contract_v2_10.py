from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition.semantic_contract_v2_8 import (
    apply_relation_type_contract_v2_8,
    load_relation_type_contract_v2_8,
)
from ecobiome.knowledge_acquisition.semantic_contract_v2_10 import (
    CONTRACT_DELTA_V2_10_STATE,
    apply_relation_type_delta_v2_10,
    load_relation_type_delta_v2_10,
    validate_relation_type_delta_v2_10,
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

BLOCKED = {
    "derived_from_arithmetic",
    "does_not_live_in",
    "does_not_occur_in",
    "does_not_originate_from",
    "does_not_tolerate",
    "easy_to_keep",
    "effective_against",
    "evaluative_conclusion",
    "forbidden_join",
    "is_not_robust",
    "is_robust",
    "lives_in",
    "not_easy_to_keep",
    "not_effective_against",
    "occurs_in",
    "originates_from",
    "purpose_not_result",
    "tolerates",
}


def _merged_v2_8() -> dict[str, object]:
    registry = validate_registry_v2_7(
        json.loads(V27.read_text(encoding="utf-8"))
    )
    contract = load_relation_type_contract_v2_8(V28)
    return apply_relation_type_contract_v2_8(registry, contract)


def test_v2_10_delta_projects_45_resolved_18_blocked() -> None:
    registry_v2_8 = _merged_v2_8()
    before = copy.deepcopy(registry_v2_8)
    delta = load_relation_type_delta_v2_10(V210)

    registry_v2_10 = apply_relation_type_delta_v2_10(
        registry_v2_8,
        delta,
    )

    relations = registry_v2_10["relations"]
    resolved = {
        relation
        for relation, spec in relations.items()
        if spec["semantic_type_contract_state"] != "unresolved_blocked"
    }
    blocked = set(relations) - resolved

    assert len(resolved) == 45
    assert blocked == BLOCKED
    assert registry_v2_8 == before


def test_v2_10_exactly_24_relations_gain_reviewed_state() -> None:
    registry_v2_8 = _merged_v2_8()
    delta = load_relation_type_delta_v2_10(V210)
    registry_v2_10 = apply_relation_type_delta_v2_10(
        registry_v2_8,
        delta,
    )

    reviewed = {
        relation
        for relation, spec in registry_v2_10["relations"].items()
        if spec["semantic_type_contract_state"] == CONTRACT_DELTA_V2_10_STATE
    }

    assert reviewed == set(delta["candidate_resolutions"])
    assert len(reviewed) == 24


def test_v2_10_multi_type_relations_are_preserved() -> None:
    registry_v2_10 = apply_relation_type_delta_v2_10(
        _merged_v2_8(),
        load_relation_type_delta_v2_10(V210),
    )
    relations = registry_v2_10["relations"]

    assert relations["adversely_affects"]["semantic_types_allowed"] == [
        "health_effect",
        "knowledge_gap",
    ]
    assert relations["poses_significant_threat_to"][
        "semantic_types_allowed"
    ] == [
        "industry_impact",
        "risk_factor",
    ]
    assert relations["used_system"]["semantic_types_allowed"] == [
        "experimental_condition",
        "study_context",
    ]


def test_v2_10_rejects_overlap_between_resolved_and_blocked() -> None:
    delta = load_relation_type_delta_v2_10(V210)
    bad = copy.deepcopy(delta)
    bad["remain_unresolved_blocked"][0] = next(
        iter(bad["candidate_resolutions"])
    )

    with pytest.raises(ValueError, match="overlap"):
        validate_relation_type_delta_v2_10(bad)


def test_v2_10_rejects_argument_signature_mutation() -> None:
    delta = load_relation_type_delta_v2_10(V210)
    bad = copy.deepcopy(delta)
    bad["candidate_resolutions"]["studied"]["argument_keys"] = ["species"]

    with pytest.raises(ValueError, match="argument_keys"):
        apply_relation_type_delta_v2_10(_merged_v2_8(), bad)


def test_v2_10_rejects_unknown_semantic_type() -> None:
    delta = load_relation_type_delta_v2_10(V210)
    bad = copy.deepcopy(delta)
    bad["candidate_resolutions"]["studied"]["semantic_types_allowed"] = [
        "not-a-real-semantic-type"
    ]

    with pytest.raises(ValueError, match="unknown semantic type"):
        apply_relation_type_delta_v2_10(_merged_v2_8(), bad)
