"""Explicit human-reviewed G7A Alignment V2 support attachment boundary.

This module does not select a policy automatically. The caller must provide the
exact human-reviewed selection identity and its expected canonical SHA-256.
Scientific alignment is revalidated against the supplied repositories before
support is attached to the immutable ProcessEvaluationV1 value.
"""

from __future__ import annotations

import re

from ecobiome.knowledge_persistence.contracts import (
    KnowledgeSynthesisRepository,
    ScientificAssertionRepository,
)
from ecobiome.simulation.g7a_alignment_instances_v2 import (
    HumanReviewedAlignmentV2SelectionV1,
)
from ecobiome.simulation.process_v1 import ProcessEvaluationV1
from ecobiome.simulation.scientific_alignment_v1 import (
    ScientificProcessAlignmentV1Error,
    attach_scientific_supports_v1,
)
from ecobiome.simulation.scientific_alignment_v2 import (
    ScientificProcessAlignmentV2Error,
    align_scientific_assertion_to_process_v2,
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ExplicitReviewedSupportAttachmentV1Error(ValueError):
    """Raised when an explicit reviewed Alignment V2 attachment is invalid."""


def attach_g7a_reviewed_alignment_v2_support_v1(
    evaluation: ProcessEvaluationV1,
    *,
    selection: HumanReviewedAlignmentV2SelectionV1,
    expected_selection_sha256: str,
    assertions: ScientificAssertionRepository,
    syntheses: KnowledgeSynthesisRepository,
) -> ProcessEvaluationV1:
    """Explicitly attach one exact human-reviewed G7A Alignment V2 support.

    No policy is discovered or selected from the evaluation. The exact selection
    and its expected canonical identity are caller inputs. The scientific
    assertion is revalidated through Alignment V2 before the existing V1 support
    attachment primitive is used.
    """
    digest = expected_selection_sha256.strip()
    if not _SHA256_RE.fullmatch(digest):
        raise ExplicitReviewedSupportAttachmentV1Error(
            "expected_selection_sha256 must be lowercase SHA-256"
        )
    if selection.canonical_sha256 != digest:
        raise ExplicitReviewedSupportAttachmentV1Error(
            "human-reviewed Alignment V2 selection identity mismatch"
        )
    if selection.decision != "accept":
        raise ExplicitReviewedSupportAttachmentV1Error(
            "Alignment V2 selection is not accepted"
        )
    if selection.review_status != "reviewed_confirmed":
        raise ExplicitReviewedSupportAttachmentV1Error(
            "Alignment V2 selection is not reviewed_confirmed"
        )
    if selection.reviewed_by != "human":
        raise ExplicitReviewedSupportAttachmentV1Error(
            "Alignment V2 selection is not human-reviewed"
        )
    if selection.automatic_attachment:
        raise ExplicitReviewedSupportAttachmentV1Error(
            "automatic attachment must remain disabled"
        )

    policy_payload = selection.policy.canonical_payload()
    if policy_payload.get("automatic_acceptance") is not False:
        raise ExplicitReviewedSupportAttachmentV1Error(
            "Alignment V2 policy must forbid automatic acceptance"
        )
    if policy_payload.get("automatic_attachment") is not False:
        raise ExplicitReviewedSupportAttachmentV1Error(
            "Alignment V2 policy must forbid automatic attachment"
        )

    try:
        support = align_scientific_assertion_to_process_v2(
            evaluation=evaluation,
            assertion_ref=selection.policy.assertion_ref,
            policy=selection.policy,
            assertions=assertions,
            syntheses=syntheses,
        )
        attached = attach_scientific_supports_v1(
            evaluation,
            (support,),
        )
    except (
        ScientificProcessAlignmentV1Error,
        ScientificProcessAlignmentV2Error,
    ) as exc:
        raise ExplicitReviewedSupportAttachmentV1Error(
            "reviewed Alignment V2 support cannot be attached to this evaluation"
        ) from exc

    invariant_fields = (
        "evaluation_id",
        "definition",
        "profile_id",
        "input_state_sha256",
        "output_state_sha256",
        "parameters_json",
        "parameter_bases",
        "deltas",
        "assumptions",
    )
    changed = tuple(
        field_name
        for field_name in invariant_fields
        if getattr(attached, field_name) != getattr(evaluation, field_name)
    )
    if changed:
        raise ExplicitReviewedSupportAttachmentV1Error(
            "scientific support attachment changed deterministic evaluation "
            f"semantics: {changed!r}"
        )

    if attached.support_status != "scientific_alignment_reviewed":
        raise ExplicitReviewedSupportAttachmentV1Error(
            "attached evaluation did not reach scientific_alignment_reviewed"
        )
    if attached.scientific_supports != (support,):
        raise ExplicitReviewedSupportAttachmentV1Error(
            "attached evaluation support identity mismatch"
        )
    if attached.scientific_assertion_refs != (support.assertion_ref,):
        raise ExplicitReviewedSupportAttachmentV1Error(
            "attached evaluation assertion ref identity mismatch"
        )

    return attached
