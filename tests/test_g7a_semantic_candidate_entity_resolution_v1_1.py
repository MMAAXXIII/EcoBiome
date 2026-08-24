from __future__ import annotations

import json
from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition.semantic_candidate_entity_resolution_v1 import (
    build_semantic_candidate_entity_resolution_event_v1,
)
from ecobiome.knowledge_acquisition.semantic_candidate_entity_resolution_v1_1 import (
    ENTITY_RESOLUTION_POLICY_DESCRIPTOR_V1_1,
    ENTITY_RESOLUTION_POLICY_SHA256,
    build_semantic_candidate_entity_resolution_event_v1_1,
    require_reviewed_entity_resolutions_v1_1,
)
from ecobiome.knowledge_acquisition.semantic_candidate_v2_11 import (
    SemanticCandidateV211Error,
)
from ecobiome.knowledge_acquisition.semantic_candidate_v2_12 import (
    build_semantic_candidate_v2_12,
)
from ecobiome.knowledge_acquisition.semantic_contract_v2_8 import (
    apply_relation_type_contract_v2_8,
    load_relation_type_contract_v2_8,
)
from ecobiome.knowledge_acquisition.semantic_contract_v2_10 import (
    apply_relation_type_delta_v2_10,
    load_relation_type_delta_v2_10,
)
from ecobiome.knowledge_acquisition.semantic_contract_v2_12 import (
    apply_directional_nitrogen_contract_v2_12,
)
from ecobiome.knowledge_acquisition.semantic_robustness_v2_7 import (
    validate_registry_v2_7,
)

ROOT = Path(__file__).resolve().parent
V27 = ROOT / "fixtures/collector_semantic_v2_7/SEMANTIC_RELATION_REGISTRY_V2_7.json"
V28 = (
    ROOT
    / "fixtures/collector_semantic_v2_8/SEMANTIC_RELATION_TYPE_CONTRACT_V2_8.json"
)
V210 = (
    ROOT
    / "fixtures/collector_semantic_v2_10/SEMANTIC_RELATION_TYPE_DELTA_V2_10.json"
)

TEXT = (
    "Within 2 weeks of this incubation experiment, N. inopinata oxidized "
    "the initially provided 1 mM NH4+ to approximately 90% NO3−."
)


def _registry() -> dict[str, object]:
    base = validate_registry_v2_7(json.loads(V27.read_text(encoding="utf-8")))
    typed = apply_relation_type_contract_v2_8(
        base,
        load_relation_type_contract_v2_8(V28),
    )
    delta = apply_relation_type_delta_v2_10(
        typed,
        load_relation_type_delta_v2_10(V210),
    )
    return apply_directional_nitrogen_contract_v2_12(delta)


def _candidate() -> dict[str, object]:
    return build_semantic_candidate_v2_12(
        {
            "c": "claim-test-nitrogen-oxidation",
            "e": ["evidence-test"],
            "t": "nitrogen_oxidation",
            "m": {
                "r": "nitrogen_oxidized_from_to",
                "a": {
                    "source_material": "NH4+",
                    "target_material": "NO3−",
                    "process_agent": "N. inopinata",
                },
            },
        },
        {
            "source_claims": [
                {
                    "claim_id": "claim-test-nitrogen-oxidation",
                    "effective_text": TEXT,
                    "evidence": [{"evidence_id": "evidence-test", "text": TEXT}],
                }
            ]
        },
        _registry(),
    )


def test_v11_policy_is_exactly_v212_and_fail_closed() -> None:
    assert ENTITY_RESOLUTION_POLICY_SHA256 == (
        "82f4ebbd6b785224eb1fa2c85c659f8a9ba5cbdbb8d8e3175191688cf5eb4dd6"
    )
    assert ENTITY_RESOLUTION_POLICY_DESCRIPTOR_V1_1[
        "candidate_contract_version"
    ] == "2.12"
    assert ENTITY_RESOLUTION_POLICY_DESCRIPTOR_V1_1["mapping_statuses"] == [
        "exact",
        "synonym",
    ]
    assert ENTITY_RESOLUTION_POLICY_DESCRIPTOR_V1_1["source_anchor"][
        "surface_comparison"
    ] == "unicode_nfc_exact_case_sensitive"


def test_legacy_v1_remains_closed_for_v212_candidate() -> None:
    candidate = _candidate()
    with pytest.raises(SemanticCandidateV211Error):
        build_semantic_candidate_entity_resolution_event_v1(
            candidate,
            event_id="legacy-event",
            semantic_candidate_id="candidate-test",
            role="source_material",
            entity_name_usage_id="usage-test",
            entity_id="entity-pubchem-cid-223",
            entity_revision=1,
            mapping_status="exact",
            decision="accept",
            reviewer="human",
            reviewed_at="2026-08-23T20:40:00+00:00",
        )


def test_v11_builds_and_reconstructs_exact_and_synonym_mappings() -> None:
    candidate = _candidate()
    events = [
        build_semantic_candidate_entity_resolution_event_v1_1(
            candidate,
            event_id="resolution-source",
            semantic_candidate_id="candidate-test",
            role="source_material",
            entity_name_usage_id="usage-source",
            entity_id="entity-pubchem-cid-223",
            entity_revision=1,
            mapping_status="exact",
            decision="accept",
            reviewer="human",
            reviewed_at="2026-08-23T20:40:00+00:00",
        ),
        build_semantic_candidate_entity_resolution_event_v1_1(
            candidate,
            event_id="resolution-target",
            semantic_candidate_id="candidate-test",
            role="target_material",
            entity_name_usage_id="usage-target",
            entity_id="entity-pubchem-cid-943",
            entity_revision=1,
            mapping_status="exact",
            decision="accept",
            reviewer="human",
            reviewed_at="2026-08-23T20:40:00+00:00",
        ),
        build_semantic_candidate_entity_resolution_event_v1_1(
            candidate,
            event_id="resolution-agent",
            semantic_candidate_id="candidate-test",
            role="process_agent",
            entity_name_usage_id="usage-agent",
            entity_id="entity-ncbitaxon-1715989",
            entity_revision=1,
            mapping_status="synonym",
            decision="accept",
            reviewer="human",
            reviewed_at="2026-08-23T20:40:00+00:00",
        ),
    ]
    reviewed = require_reviewed_entity_resolutions_v1_1(
        candidate,
        semantic_candidate_id="candidate-test",
        events=events,
        required_roles=["source_material", "target_material", "process_agent"],
    )
    assert reviewed["source_material"].mapping_status == "exact"
    assert reviewed["target_material"].entity_id == "entity-pubchem-cid-943"
    assert reviewed["process_agent"].mapping_status == "synonym"
    assert all(
        item.mapping_review_status == "reviewed_confirmed"
        for item in reviewed.values()
    )
