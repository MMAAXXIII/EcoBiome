from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition.semantic_relation_registry import (
    build_source_independent_wire_schema,
    canonical_payload_sha256,
    validate_compact_payload,
    validate_compact_proposal,
    validate_meaning,
    validate_registry,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "collector_semantic_v2_4"
REGISTRY_PATH = FIXTURE_ROOT / "SEMANTIC_RELATION_REGISTRY_V2_4_CANDIDATE.json"
SCHEMA_PATH = FIXTURE_ROOT / "SOURCE_INDEPENDENT_WIRE_SCHEMA_V2_4.json"

EXPECTED_REGISTRY_FILE_SHA256 = "2b70544231e7d7e37a859ffaa7fa09630be5977ffb02c443be1273a1d87a4889"
EXPECTED_SCHEMA_FILE_SHA256 = "dfb9fecc743673e0c576366b2c8998496a1b33e2d5208484f0c9b567b24c19a0"
EXPECTED_REGISTRY_CANONICAL_SHA256 = "b35c944ff26739222d26af1feb31e2634693be6e7b32369dee090afbfd36980a"
EXPECTED_SCHEMA_CANONICAL_SHA256 = "d7365f5b68806046e85dc0e5f8a007b658100281c45c2d83966f997aad8ae8a8"


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _registry() -> dict[str, object]:
    return _load(REGISTRY_PATH)


def _schema() -> dict[str, object]:
    return _load(SCHEMA_PATH)


def test_frozen_v24_artifacts_match_reviewed_audit_hashes() -> None:
    assert hashlib.sha256(REGISTRY_PATH.read_bytes()).hexdigest() == (
        EXPECTED_REGISTRY_FILE_SHA256
    )
    assert hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest() == (
        EXPECTED_SCHEMA_FILE_SHA256
    )
    assert canonical_payload_sha256(_registry()) == EXPECTED_REGISTRY_CANONICAL_SHA256
    assert canonical_payload_sha256(_schema()) == EXPECTED_SCHEMA_CANONICAL_SHA256


def test_registry_counts_and_source_independent_role_policy() -> None:
    registry = validate_registry(_registry())
    assert len(registry["semantic_types"]) == 35
    assert len(registry["argument_roles"]) == 34
    assert len(registry["relations"]) == 45
    assert all("enum" not in spec for spec in registry["argument_roles"].values())


def test_generated_schema_is_exact_frozen_audit_schema() -> None:
    generated = build_source_independent_wire_schema(_registry())
    assert generated == _schema()
    branches = generated["properties"]["p"]["items"]["properties"]["m"]["oneOf"]
    assert len(branches) == 45


@pytest.mark.parametrize(
    "meaning",
    [
        {
            "r": "maintained_at",
            "a": {"variable": "dissolved_oxygen", "value": 7.5, "unit": "mg/L"},
        },
        {
            "r": "studied",
            "a": {"life_stage": "adult", "species": "Oryzias_latipes"},
        },
        {
            "r": "had_level",
            "a": {"label": "T1", "day": 3, "analyte": "nitrate", "level": "moderate"},
        },
        {"r": "occurs_in", "a": {"location": "Patagonia"}},
    ],
)
def test_unseen_source_values_are_allowed_when_structure_is_valid(
    meaning: dict[str, object],
) -> None:
    assert validate_meaning(meaning, _registry()) == []


@pytest.mark.parametrize(
    "meaning,kind",
    [
        (
            {
                "r": "co_occurred_with",
                "a": {"event_a": "x", "event_b": "y", "comparator": "z"},
            },
            "argument_keys_mismatch",
        ),
        (
            {"r": "maintained_at", "a": {"variable": "pH", "value": 7.0}},
            "argument_keys_mismatch",
        ),
        (
            {"r": "sampled_on_day", "a": {"day": "7"}},
            "invalid_argument_type",
        ),
        (
            {"r": "occurs_in", "a": {"location": "France", "extra": "x"}},
            "argument_keys_mismatch",
        ),
        (
            {"r": "invented_relation", "a": {}},
            "unsupported_relation",
        ),
    ],
)
def test_structural_provider_defects_are_scoreable(
    meaning: dict[str, object],
    kind: str,
) -> None:
    issues = validate_meaning(meaning, _registry())
    assert any(issue["kind"] == kind for issue in issues)


def test_valid_compact_proposal_passes() -> None:
    proposal = {
        "c": "claim-1",
        "t": "measurement_trend",
        "e": ["evidence-1"],
        "m": {
            "r": "decreased",
            "a": {"analyte": "ammonia", "temperature_scope": "both_conditions"},
        },
    }
    assert validate_compact_proposal(proposal, _registry()) == []


def test_compact_provider_defects_do_not_raise() -> None:
    payload = {
        "p": [
            {
                "c": "claim-1",
                "t": "measurement_trend",
                "e": ["evidence-1"],
                "m": {
                    "r": "decreased",
                    "a": {"analyte": "ammonia", "comparator": "wrong-role"},
                },
            },
            {
                "c": "claim-2",
                "t": "unknown-semantic-type",
                "e": ["evidence-2"],
                "m": {"r": "sampled_on_day", "a": {"day": "7"}},
            },
        ]
    }
    report = validate_compact_payload(payload, _registry())
    assert report["candidate_count"] == 2
    assert report["conforming_count"] == 0
    assert report["violation_count"] == 2


def test_registry_corruption_remains_fatal() -> None:
    registry = _registry()
    registry["argument_roles"]["location"]["enum"] = ["France"]
    with pytest.raises(ValueError, match="must not contain an enum"):
        validate_registry(registry)
