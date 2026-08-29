"""Immutable governance provenance for explicit reviewed support attachment.

Scientific support remains a scientific object. This module records the separate
human-governance event that authorized one exact support to be attached to one
exact ProcessEvaluationV1 value.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from ecobiome.knowledge_persistence.contracts import (
    KnowledgeSynthesisRepository,
    ScientificAssertionRepository,
)
from ecobiome.knowledge_persistence.serialization import (
    canonical_json_text,
    canonical_sha256,
)
from ecobiome.simulation.g7a_alignment_instances_v2 import (
    HumanReviewedAlignmentV2SelectionV1,
)
from ecobiome.simulation.process_v1 import (
    ProcessEvaluationV1,
    ProcessScientificSupportV1,
    ScientificAssertionRefV1,
)
from ecobiome.simulation.reviewed_support_attachment_v1 import (
    attach_g7a_reviewed_alignment_v2_support_v1,
)

REVIEWED_SUPPORT_ATTACHMENT_RECEIPT_SCHEMA_VERSION = (
    "ecobiome-reviewed-support-attachment-receipt-v1"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ReviewedSupportAttachmentReceiptV1Error(ValueError):
    """Raised when a reviewed support attachment receipt is inconsistent."""


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ReviewedSupportAttachmentReceiptV1Error(
            f"{field_name} must be non-empty"
        )
    return normalized


def _sha256(value: str, field_name: str) -> str:
    digest = value.strip()
    if not _SHA256_RE.fullmatch(digest):
        raise ReviewedSupportAttachmentReceiptV1Error(
            f"{field_name} must be lowercase SHA-256"
        )
    return digest


def _support_sha256(support: ProcessScientificSupportV1) -> str:
    return canonical_sha256(support.canonical_payload())


@dataclass(frozen=True, slots=True)
class ReviewedSupportAttachmentReceiptV1:
    """Immutable proof of one explicit human-reviewed support attachment."""

    receipt_id: str
    evaluation_id: str
    pending_evaluation_sha256: str
    attached_evaluation_sha256: str
    support_sha256: str
    assertion_ref: ScientificAssertionRefV1
    alignment_policy_sha256: str
    evaluation_scope_sha256: str
    bridge_id: str
    bridge_sha256: str
    selection_sha256: str
    selection_payload_json: str
    automatic_acceptance: bool = False
    automatic_attachment: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "receipt_id",
            _nonempty(self.receipt_id, "receipt_id"),
        )
        object.__setattr__(
            self,
            "evaluation_id",
            _nonempty(self.evaluation_id, "evaluation_id"),
        )
        for field_name in (
            "pending_evaluation_sha256",
            "attached_evaluation_sha256",
            "support_sha256",
            "alignment_policy_sha256",
            "evaluation_scope_sha256",
            "bridge_sha256",
            "selection_sha256",
        ):
            object.__setattr__(
                self,
                field_name,
                _sha256(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "bridge_id",
            _nonempty(self.bridge_id, "bridge_id"),
        )
        if self.pending_evaluation_sha256 == self.attached_evaluation_sha256:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "pending and attached evaluation identities must differ"
            )
        if self.automatic_acceptance:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "automatic_acceptance must remain false"
            )
        if self.automatic_attachment:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "automatic_attachment must remain false"
            )

        try:
            selection_payload = json.loads(self.selection_payload_json)
        except json.JSONDecodeError as exc:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection_payload_json must contain valid JSON"
            ) from exc
        if not isinstance(selection_payload, dict):
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection payload must be an object"
            )
        canonical_selection_json = canonical_json_text(selection_payload)
        object.__setattr__(
            self,
            "selection_payload_json",
            canonical_selection_json,
        )
        if canonical_sha256(selection_payload) != self.selection_sha256:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection_sha256 does not match selection payload"
            )
        if selection_payload.get("schema_version") != (
            "ecobiome-human-reviewed-alignment-v2-selection-v1"
        ):
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection payload schema_version is not supported"
            )
        selection_id = selection_payload.get("selection_id")
        if not isinstance(selection_id, str) or not selection_id.strip():
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection payload requires a non-empty selection_id"
            )
        if selection_payload.get("decision") != "accept":
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection payload decision must be accept"
            )
        if selection_payload.get("review_status") != "reviewed_confirmed":
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection payload review_status must be reviewed_confirmed"
            )
        if selection_payload.get("reviewed_by") != "human":
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection payload reviewed_by must be human"
            )
        if selection_payload.get("automatic_attachment") is not False:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection payload must forbid automatic attachment"
            )

        policy = selection_payload.get("policy")
        if not isinstance(policy, dict):
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection payload policy must be an object"
            )
        if policy.get("canonical_sha256") != self.alignment_policy_sha256:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection policy SHA does not match receipt"
            )
        if policy.get("evaluation_scope_sha256") != self.evaluation_scope_sha256:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection evaluation scope SHA does not match receipt"
            )
        if policy.get("bridge_id") != self.bridge_id:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection bridge_id does not match receipt"
            )
        if policy.get("bridge_sha256") != self.bridge_sha256:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection bridge SHA does not match receipt"
            )
        assertion_payload = policy.get("assertion_ref")
        if assertion_payload != self.assertion_ref.canonical_payload():
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection assertion ref does not match receipt"
            )

    @property
    def selection_payload(self) -> dict[str, object]:
        payload = json.loads(self.selection_payload_json)
        if not isinstance(payload, dict):
            raise TypeError("canonical selection payload must remain an object")
        return payload

    @property
    def selection_id(self) -> str:
        value = self.selection_payload.get("selection_id")
        if not isinstance(value, str) or not value.strip():
            raise ReviewedSupportAttachmentReceiptV1Error(
                "selection payload requires a non-empty selection_id"
            )
        return value.strip()

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": REVIEWED_SUPPORT_ATTACHMENT_RECEIPT_SCHEMA_VERSION,
            "receipt_id": self.receipt_id,
            "evaluation": {
                "evaluation_id": self.evaluation_id,
                "pending_canonical_sha256": self.pending_evaluation_sha256,
                "attached_canonical_sha256": self.attached_evaluation_sha256,
            },
            "scientific_binding": {
                "support_sha256": self.support_sha256,
                "assertion_ref": self.assertion_ref.canonical_payload(),
                "alignment_policy_sha256": self.alignment_policy_sha256,
                "evaluation_scope_sha256": self.evaluation_scope_sha256,
                "bridge_id": self.bridge_id,
                "bridge_sha256": self.bridge_sha256,
            },
            "human_reviewed_selection": {
                "canonical_sha256": self.selection_sha256,
                "payload": self.selection_payload,
            },
            "attachment_mode": "explicit_caller_invocation",
            "automatic_acceptance": False,
            "automatic_attachment": False,
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_sha256(self.canonical_payload())


@dataclass(frozen=True, slots=True)
class ReviewedSupportAttachmentResultV1:
    """Attached evaluation plus its independent governance receipt."""

    evaluation: ProcessEvaluationV1
    receipt: ReviewedSupportAttachmentReceiptV1

    def __post_init__(self) -> None:
        if self.receipt.evaluation_id != self.evaluation.evaluation_id:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "receipt evaluation_id does not match attached evaluation"
            )
        if self.receipt.attached_evaluation_sha256 != self.evaluation.canonical_sha256:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "receipt attached evaluation SHA does not match evaluation"
            )
        supports = {
            _support_sha256(item): item
            for item in self.evaluation.scientific_supports
        }
        support = supports.get(self.receipt.support_sha256)
        if support is None:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "receipt support SHA is not attached to evaluation"
            )
        if support.assertion_ref != self.receipt.assertion_ref:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "receipt assertion ref does not match attached support"
            )
        if support.alignment_policy_sha256 != self.receipt.alignment_policy_sha256:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "receipt policy SHA does not match attached support"
            )
        if support.evaluation_scope_sha256 != self.receipt.evaluation_scope_sha256:
            raise ReviewedSupportAttachmentReceiptV1Error(
                "receipt scope SHA does not match attached support"
            )


def attach_g7a_reviewed_alignment_v2_support_with_receipt_v1(
    evaluation: ProcessEvaluationV1,
    *,
    receipt_id: str,
    selection: HumanReviewedAlignmentV2SelectionV1,
    expected_selection_sha256: str,
    assertions: ScientificAssertionRepository,
    syntheses: KnowledgeSynthesisRepository,
) -> ReviewedSupportAttachmentResultV1:
    """Attach one explicit reviewed G7A support and emit governance proof."""
    attached = attach_g7a_reviewed_alignment_v2_support_v1(
        evaluation,
        selection=selection,
        expected_selection_sha256=expected_selection_sha256,
        assertions=assertions,
        syntheses=syntheses,
    )
    if len(attached.scientific_supports) != 1:
        raise ReviewedSupportAttachmentReceiptV1Error(
            "G7A reviewed attachment must contain exactly one support"
        )
    support = attached.scientific_supports[0]
    policy_payload = selection.policy.canonical_payload()
    if policy_payload.get("automatic_acceptance") is not False:
        raise ReviewedSupportAttachmentReceiptV1Error(
            "selected policy must forbid automatic acceptance"
        )
    if policy_payload.get("automatic_attachment") is not False:
        raise ReviewedSupportAttachmentReceiptV1Error(
            "selected policy must forbid automatic attachment"
        )

    receipt = ReviewedSupportAttachmentReceiptV1(
        receipt_id=receipt_id,
        evaluation_id=evaluation.evaluation_id,
        pending_evaluation_sha256=evaluation.canonical_sha256,
        attached_evaluation_sha256=attached.canonical_sha256,
        support_sha256=_support_sha256(support),
        assertion_ref=support.assertion_ref,
        alignment_policy_sha256=support.alignment_policy_sha256,
        evaluation_scope_sha256=support.evaluation_scope_sha256,
        bridge_id=selection.policy.model_semantic_bridge.bridge_id,
        bridge_sha256=selection.policy.bridge_sha256,
        selection_sha256=selection.canonical_sha256,
        selection_payload_json=canonical_json_text(
            selection.canonical_payload()
        ),
        automatic_acceptance=False,
        automatic_attachment=False,
    )
    return ReviewedSupportAttachmentResultV1(
        evaluation=attached,
        receipt=receipt,
    )
