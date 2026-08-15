from __future__ import annotations

import hashlib

import pytest

from ecobiome.knowledge_acquisition.semantic_candidate_review_v1 import (
    CANDIDATE_REVIEW_POLICY_SHA256,
    SemanticCandidateReviewV1Error,
    build_semantic_candidate_review_event_v1,
    require_candidate_acceptance_v1,
)
from ecobiome.knowledge_acquisition.semantic_candidate_v2_11 import (
    build_semantic_candidate_v2_11,
    render_semantic_candidate_review_text_v2_11,
)


def _candidate() -> dict[str, object]:
    registry = {
        "relations": {
            "maintained_at": {
                "argument_keys": ["variable", "value", "unit"],
                "epistemic_class": "study_context_non_result",
                "semantic_type_contract_state":
                    "historical_golden_reviewed_constrained",
                "semantic_types_allowed": ["experimental_condition"],
            }
        },
        "argument_role_semantics": {
            "variable": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "measurable_or_described_variable",
            },
            "value": {
                "grounding_class": "exact_numeric_source_grounded",
                "semantic_domain": "numeric_value",
            },
            "unit": {
                "grounding_class": "controlled_literal_source_grounded",
                "semantic_domain": "controlled_measurement_or_time_unit",
            },
        },
    }
    source = {
        "source_claims": [{
            "claim_id": "claim-1",
            "effective_text": "Temperature was maintained at 26.5 °C.",
            "evidence": [{"evidence_id": "ev-1", "text": "26.5 °C"}],
        }]
    }
    survivor = {
        "c": "claim-1",
        "e": ["ev-1"],
        "t": "experimental_condition",
        "m": {
            "r": "maintained_at",
            "a": {
                "variable": "temperature",
                "value": 26.5,
                "unit": "degree celsius",
            },
        },
    }
    return build_semantic_candidate_v2_11(survivor, source, registry)


def test_candidate_review_policy_identity_is_frozen() -> None:
    assert CANDIDATE_REVIEW_POLICY_SHA256 == (
        "cb68231ccb26d398ce3c42c9cae33c8470325390b8e3c524f9d9a1b5a1bc8f61"
    )


def test_candidate_review_event_binds_exact_renderer_and_sha() -> None:
    candidate = _candidate()
    event = build_semantic_candidate_review_event_v1(
        candidate,
        event_id="review-1",
        semantic_candidate_id="candidate-1",
        decision="accept",
        reviewer="human",
        reviewed_at="2026-08-15T09:00:00+00:00",
    )
    expected = render_semantic_candidate_review_text_v2_11(candidate)
    assert event.review_text == expected
    assert event.review_text_sha256 == hashlib.sha256(
        expected.encode("utf-8")
    ).hexdigest()
    trace = require_candidate_acceptance_v1(candidate, [event])
    assert trace["review_id"] == "review-1"


def test_candidate_review_latest_order_is_reviewed_at_then_id() -> None:
    candidate = _candidate()
    accepted = build_semantic_candidate_review_event_v1(
        candidate,
        event_id="a",
        semantic_candidate_id="candidate-1",
        decision="accept",
        reviewer="human",
        reviewed_at="2026-08-15T09:00:00+00:00",
    )
    rejected = build_semantic_candidate_review_event_v1(
        candidate,
        event_id="b",
        semantic_candidate_id="candidate-1",
        decision="reject",
        reviewer="human",
        reviewed_at="2026-08-15T09:00:00+00:00",
    )
    with pytest.raises(SemanticCandidateReviewV1Error, match="'reject'"):
        require_candidate_acceptance_v1(candidate, [accepted, rejected])
