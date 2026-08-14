from __future__ import annotations

import copy
import json
from pathlib import Path

from ecobiome.knowledge_acquisition.semantic_contract_v2_8 import (
    apply_relation_type_contract_v2_8,
    load_relation_type_contract_v2_8,
    relation_semantic_type_decision_v2_8,
)
from ecobiome.knowledge_acquisition.semantic_grounding import (
    GROUNDING_POLICY_V1_1,
    GROUNDING_POLICY_V1_1_SHA256,
    NUMERIC_ROLES,
    OPAQUE_OPEN_TEXT_ROLES,
    OPAQUE_OPEN_TEXT_ROLES_V1_1,
    OPAQUE_OPEN_TEXT_ROLES_V1_2,
    OPAQUE_OPEN_TEXT_ROLES_V1_2_ADDITIONS,
    audit_arguments,
    canonical_json_sha256,
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
GROUNDING_EXTENSION = (
    ROOT
    / "fixtures"
    / "collector_semantic_v2_8"
    / "SOURCE_GROUNDING_ROLE_EXTENSION_V1_2.json"
)

EXPECTED_V27_SHA256 = (
    "cdc0debb45a5ac4182ff441ff1b7811e2571c03dc02b4bcdcf8b61ebbfd131db"
)

EXPECTED_SINGLETONS = {
    "decreased": ["measurement_trend"],
    "lasted": ["experiment_duration"],
    "not_well_understood": ["knowledge_gap"],
}

EXPECTED_NEW_ROLES = {
    "context",
    "entity_a",
    "entity_b",
    "mechanism",
    "mediator",
    "response",
    "state",
    "subject",
    "target_state",
    "taxon",
    "temporal_scope",
}


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha_file(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v27_registry_remains_frozen() -> None:
    assert _sha_file(V27) == EXPECTED_V27_SHA256


def test_v11_grounding_policy_remains_frozen() -> None:
    assert canonical_json_sha256(GROUNDING_POLICY_V1_1) == (
        GROUNDING_POLICY_V1_1_SHA256
    )
    assert OPAQUE_OPEN_TEXT_ROLES_V1_1 == frozenset(
        OPAQUE_OPEN_TEXT_ROLES
    )


def test_v12_grounding_role_extension_is_exact_and_fail_safe() -> None:
    extension = _load_json(GROUNDING_EXTENSION)

    assert extension["new_role_count"] == 11
    assert set(extension["new_open_text_source_grounded_roles"]) == (
        EXPECTED_NEW_ROLES
    )
    assert OPAQUE_OPEN_TEXT_ROLES_V1_2_ADDITIONS == EXPECTED_NEW_ROLES
    assert OPAQUE_OPEN_TEXT_ROLES_V1_2 == (
        OPAQUE_OPEN_TEXT_ROLES_V1_1 | EXPECTED_NEW_ROLES
    )

    for role in EXPECTED_NEW_ROLES:
        spec = extension["role_specs"][role]
        assert spec["grounding_class"] == "open_text_source_grounded"


def test_v12_all_v27_argument_roles_are_classified() -> None:
    registry = _load_json(V27)
    ontology_roles = set(registry["argument_roles"])
    classified = (
        set(NUMERIC_ROLES)
        | {"unit", "temperature_scope"}
        | set(OPAQUE_OPEN_TEXT_ROLES_V1_2)
    )
    assert ontology_roles == classified
    assert len(ontology_roles) == 45


def test_v12_new_open_text_roles_require_source_surface() -> None:
    for role in sorted(EXPECTED_NEW_ROLES):
        good = audit_arguments({role: "source value"}, "prefix source value suffix")
        assert good["blocking"] is False
        assert good["unresolved"] is True
        assert good["records"][role]["state"] == "grounded_opaque_unresolved"
        assert good["records"][role]["scientifically_scoreable"] is False

        bad = audit_arguments({role: "missing value"}, "different source text")
        assert bad["blocking"] is True
        assert bad["records"][role]["state"] == "ungrounded"
        assert bad["records"][role]["scientifically_scoreable"] is False


def test_v28_relation_type_contract_is_complete_and_fail_closed() -> None:
    contract = load_relation_type_contract_v2_8(V28)
    relations = contract["relations"]

    assert len(relations) == 63

    states: dict[str, int] = {}
    for spec in relations.values():
        state = spec["state"]
        states[state] = states.get(state, 0) + 1
        assert isinstance(spec["semantic_types_allowed"], list)

    assert states == {
        "constrained_existing_v2_7": 18,
        "constrained_reviewed_singleton_v2_8": 3,
        "unresolved_blocked": 42,
    }

    unresolved = [
        relation
        for relation, spec in relations.items()
        if spec["state"] == "unresolved_blocked"
    ]
    assert len(unresolved) == 42
    assert all(
        relations[relation]["semantic_types_allowed"] == []
        for relation in unresolved
    )


def test_v28_three_reviewed_singletons_are_exact() -> None:
    contract = load_relation_type_contract_v2_8(V28)
    actual = {
        relation: spec["semantic_types_allowed"]
        for relation, spec in contract["relations"].items()
        if spec["state"] == "constrained_reviewed_singleton_v2_8"
    }
    assert actual == EXPECTED_SINGLETONS


def test_v28_overlay_does_not_mutate_v27() -> None:
    registry = _load_json(V27)
    frozen = copy.deepcopy(registry)
    contract = load_relation_type_contract_v2_8(V28)

    merged = apply_relation_type_contract_v2_8(registry, contract)

    assert registry == frozen
    assert merged is not registry
    assert len(merged["relations"]) == 63
    assert all(
        isinstance(spec.get("semantic_types_allowed"), list)
        for spec in merged["relations"].values()
    )


def test_v28_decision_allows_reviewed_singletons() -> None:
    registry = _load_json(V27)
    contract = load_relation_type_contract_v2_8(V28)
    merged = apply_relation_type_contract_v2_8(registry, contract)

    for relation, allowed in EXPECTED_SINGLETONS.items():
        decision = relation_semantic_type_decision_v2_8(
            merged,
            relation,
            allowed[0],
        )
        assert decision["accepted"] is True
        assert decision["state"] == "allowed"


def test_v28_decision_rejects_wrong_type_for_reviewed_singleton() -> None:
    registry = _load_json(V27)
    contract = load_relation_type_contract_v2_8(V28)
    merged = apply_relation_type_contract_v2_8(registry, contract)

    decision = relation_semantic_type_decision_v2_8(
        merged,
        "lasted",
        "measurement_trend",
    )
    assert decision["accepted"] is False
    assert decision["state"] == "relation_semantic_type_incompatible"


def test_v28_decision_blocks_unresolved_relation() -> None:
    registry = _load_json(V27)
    contract = load_relation_type_contract_v2_8(V28)
    merged = apply_relation_type_contract_v2_8(registry, contract)

    unresolved_relation = next(
        relation
        for relation, spec in contract["relations"].items()
        if spec["state"] == "unresolved_blocked"
    )

    decision = relation_semantic_type_decision_v2_8(
        merged,
        unresolved_relation,
        str(registry["semantic_types"][0]),
    )
    assert decision == {
        "accepted": False,
        "state": "unresolved_blocked",
        "relation": unresolved_relation,
        "semantic_type": str(registry["semantic_types"][0]),
        "allowed": [],
    }
