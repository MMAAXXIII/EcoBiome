"""Human review gate for canonical Semantic Candidates V2.11."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from typing import Any

from ecobiome.knowledge_acquisition.semantic_candidate_v2_11 import (
    render_semantic_candidate_review_text_v2_11,
    validate_semantic_candidate_v2_11,
)
from ecobiome.knowledge_persistence.contracts import (
    SemanticCandidateReviewEventsRow,
)
from ecobiome.knowledge_persistence.serialization import canonical_sha256

CANDIDATE_REVIEW_POLICY_NAME = "ecobiome-semantic-candidate-human-review"
CANDIDATE_REVIEW_POLICY_VERSION = "1"
CANDIDATE_REVIEW_POLICY_DESCRIPTOR: dict[str, object] = {
    "accept_allows_next_gate": True,
    "append_only": True,
    "automatic_scientific_acceptance": False,
    "candidate_contract_version": "2.11",
    "correct_requires_distinct_replacement_candidate": True,
    "decisions": ["accept", "correct", "reject"],
    "latest_review_order": ["reviewed_at", "id"],
    "name": CANDIDATE_REVIEW_POLICY_NAME,
    "reject_blocks_projection": True,
    "replacement_requires_own_accept": True,
    "review_text_renderer": "render_semantic_candidate_review_text_v2_11",
    "version": CANDIDATE_REVIEW_POLICY_VERSION,
}
CANDIDATE_REVIEW_POLICY_SHA256 = (
    "cb68231ccb26d398ce3c42c9cae33c8470325390b8e3c524f9d9a1b5a1bc8f61"
)

if canonical_sha256(CANDIDATE_REVIEW_POLICY_DESCRIPTOR) != (
    CANDIDATE_REVIEW_POLICY_SHA256
):
    raise RuntimeError("Semantic Candidate review policy identity mismatch")


class SemanticCandidateReviewV1Error(ValueError):
    """Raised when Candidate review cannot authorize the next scientific gate."""


def build_semantic_candidate_review_event_v1(
    candidate: Mapping[str, Any],
    *,
    event_id: str,
    semantic_candidate_id: str,
    decision: str,
    reviewer: str,
    reviewed_at: str,
    rationale: str = "",
    review_metadata_json: str = "{}",
    replacement_candidate_id: str | None = None,
    replacement_candidate_sha256: str | None = None,
) -> SemanticCandidateReviewEventsRow:
    validate_semantic_candidate_v2_11(candidate)
    if decision not in {"accept", "correct", "reject"}:
        raise SemanticCandidateReviewV1Error(
            f"Unsupported Candidate review decision: {decision!r}"
        )
    if not reviewer.strip():
        raise SemanticCandidateReviewV1Error("Candidate reviewer must be non-empty")
    candidate_sha = str(candidate["canonical_candidate_sha256"])
    review_text = render_semantic_candidate_review_text_v2_11(candidate)
    if decision == "correct":
        if (
            replacement_candidate_id is None
            or replacement_candidate_sha256 is None
            or replacement_candidate_id == semantic_candidate_id
        ):
            raise SemanticCandidateReviewV1Error(
                "Candidate correction requires a distinct replacement candidate"
            )
    elif replacement_candidate_id is not None or replacement_candidate_sha256 is not None:
        raise SemanticCandidateReviewV1Error(
            "accept/reject reviews cannot carry a replacement candidate"
        )
    return SemanticCandidateReviewEventsRow(
        id=event_id,
        semantic_candidate_id=semantic_candidate_id,
        semantic_candidate_sha256=candidate_sha,
        decision=decision,
        reviewer=reviewer,
        review_text=review_text,
        review_text_sha256=hashlib.sha256(
            review_text.encode("utf-8")
        ).hexdigest(),
        rationale=rationale,
        review_metadata_json=review_metadata_json,
        review_policy_name=CANDIDATE_REVIEW_POLICY_NAME,
        review_policy_version=CANDIDATE_REVIEW_POLICY_VERSION,
        review_policy_sha256=CANDIDATE_REVIEW_POLICY_SHA256,
        replacement_candidate_id=replacement_candidate_id,
        replacement_candidate_sha256=replacement_candidate_sha256,
        reviewed_at=reviewed_at,
    )


def require_candidate_acceptance_v1(
    candidate: Mapping[str, Any],
    events: Sequence[SemanticCandidateReviewEventsRow],
) -> dict[str, str]:
    validate_semantic_candidate_v2_11(candidate)
    candidate_sha = str(candidate["canonical_candidate_sha256"])
    if not events:
        raise SemanticCandidateReviewV1Error(
            "semantic Candidate requires at least one human review event"
        )
    expected_text = render_semantic_candidate_review_text_v2_11(candidate)
    ordered = sorted(events, key=lambda item: (item.reviewed_at, item.id))
    for event in ordered:
        if event.semantic_candidate_sha256 != candidate_sha:
            raise SemanticCandidateReviewV1Error(
                "Candidate review event is bound to a different candidate SHA"
            )
        if (
            event.review_policy_name != CANDIDATE_REVIEW_POLICY_NAME
            or event.review_policy_version != CANDIDATE_REVIEW_POLICY_VERSION
            or event.review_policy_sha256 != CANDIDATE_REVIEW_POLICY_SHA256
        ):
            raise SemanticCandidateReviewV1Error(
                "Candidate review policy identity mismatch"
            )
        if event.review_text != expected_text:
            raise SemanticCandidateReviewV1Error(
                "Candidate review text does not match deterministic renderer"
            )
        if hashlib.sha256(event.review_text.encode("utf-8")).hexdigest() != (
            event.review_text_sha256
        ):
            raise SemanticCandidateReviewV1Error(
                "Candidate review text SHA mismatch"
            )
        if not event.reviewer.strip():
            raise SemanticCandidateReviewV1Error(
                "Candidate review requires a non-empty reviewer"
            )
    latest = ordered[-1]
    if latest.decision != "accept":
        raise SemanticCandidateReviewV1Error(
            f"latest semantic Candidate review is {latest.decision!r}, not 'accept'"
        )
    return {
        "review_id": latest.id,
        "reviewer": latest.reviewer,
        "reviewed_at": latest.reviewed_at,
        "review_policy_sha256": latest.review_policy_sha256,
    }
