"""Auditable ecosystem explanation envelope with governance provenance.

The scientific explanation trace remains unchanged. This additive envelope binds
that trace to exact ProcessEvaluationV1 identities and to explicit human-reviewed
support-attachment receipts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ecobiome.knowledge_persistence.serialization import canonical_sha256
from ecobiome.reasoning.ecosystem_explanation_v1 import (
    EcosystemExplanationTraceV1,
    build_ecosystem_explanation_v1,
)
from ecobiome.simulation.ecosystem_state_v1 import EcosystemStateV1
from ecobiome.simulation.process_v1 import (
    ProcessEvaluationV1,
    ProcessScientificSupportV1,
)
from ecobiome.simulation.reviewed_support_attachment_receipt_v1 import (
    ReviewedSupportAttachmentReceiptV1,
)

AUDITABLE_ECOSYSTEM_EXPLANATION_SCHEMA_VERSION = (
    "ecobiome-auditable-ecosystem-explanation-v1"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AuditableEcosystemExplanationV1Error(ValueError):
    """Raised when explanation governance provenance is incomplete or invalid."""


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise AuditableEcosystemExplanationV1Error(
            f"{field_name} must be non-empty"
        )
    return normalized


def _sha256(value: str, field_name: str) -> str:
    digest = value.strip()
    if not _SHA256_RE.fullmatch(digest):
        raise AuditableEcosystemExplanationV1Error(
            f"{field_name} must be lowercase SHA-256"
        )
    return digest


def _support_sha256(support: ProcessScientificSupportV1) -> str:
    return canonical_sha256(support.canonical_payload())


@dataclass(frozen=True, slots=True)
class ProcessEvaluationIdentityV1:
    evaluation_id: str
    canonical_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evaluation_id",
            _nonempty(self.evaluation_id, "evaluation_id"),
        )
        object.__setattr__(
            self,
            "canonical_sha256",
            _sha256(self.canonical_sha256, "canonical_sha256"),
        )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "evaluation_id": self.evaluation_id,
            "canonical_sha256": self.canonical_sha256,
        }


@dataclass(frozen=True, slots=True)
class AuditableEcosystemExplanationV1:
    """Core explanation plus exact evaluation and attachment provenance."""

    explanation_trace: EcosystemExplanationTraceV1
    process_evaluation_identities: tuple[ProcessEvaluationIdentityV1, ...]
    reviewed_support_attachment_receipts: tuple[
        ReviewedSupportAttachmentReceiptV1, ...
    ]

    def __post_init__(self) -> None:
        identities = tuple(self.process_evaluation_identities)
        expected_ids = self.explanation_trace.process_evaluation_refs
        observed_ids = tuple(item.evaluation_id for item in identities)
        if observed_ids != expected_ids:
            raise AuditableEcosystemExplanationV1Error(
                "process evaluation identities must exactly match trace order"
            )
        if len(set(observed_ids)) != len(observed_ids):
            raise AuditableEcosystemExplanationV1Error(
                "process evaluation identities must be unique"
            )
        identity_by_id = {
            item.evaluation_id: item
            for item in identities
        }

        support_by_evaluation: dict[
            str, dict[str, ProcessScientificSupportV1]
        ] = {}
        for step in self.explanation_trace.causal_steps:
            bucket = support_by_evaluation.setdefault(
                step.process_evaluation_id,
                {},
            )
            for support in step.scientific_supports:
                bucket[_support_sha256(support)] = support

        expected_receipt_pairs = {
            (evaluation_id, support_sha)
            for evaluation_id, supports in support_by_evaluation.items()
            for support_sha in supports
        }
        receipts = tuple(self.reviewed_support_attachment_receipts)
        receipt_pairs: set[tuple[str, str]] = set()
        receipt_ids: set[str] = set()
        receipt_shas: set[str] = set()
        for receipt in receipts:
            if receipt.receipt_id in receipt_ids:
                raise AuditableEcosystemExplanationV1Error(
                    "attachment receipt ids must be unique"
                )
            receipt_ids.add(receipt.receipt_id)
            if receipt.canonical_sha256 in receipt_shas:
                raise AuditableEcosystemExplanationV1Error(
                    "attachment receipt identities must be unique"
                )
            receipt_shas.add(receipt.canonical_sha256)

            identity = identity_by_id.get(receipt.evaluation_id)
            if identity is None:
                raise AuditableEcosystemExplanationV1Error(
                    "attachment receipt references evaluation outside trace"
                )
            if receipt.attached_evaluation_sha256 != identity.canonical_sha256:
                raise AuditableEcosystemExplanationV1Error(
                    "attachment receipt evaluation SHA does not match trace identity"
                )
            bound_support = support_by_evaluation.get(
                receipt.evaluation_id,
                {},
            ).get(receipt.support_sha256)
            if bound_support is None:
                raise AuditableEcosystemExplanationV1Error(
                    "attachment receipt support is not bound to its trace evaluation"
                )
            if bound_support.assertion_ref != receipt.assertion_ref:
                raise AuditableEcosystemExplanationV1Error(
                    "attachment receipt assertion does not match trace support"
                )
            if (
                bound_support.alignment_policy_sha256
                != receipt.alignment_policy_sha256
            ):
                raise AuditableEcosystemExplanationV1Error(
                    "attachment receipt policy does not match trace support"
                )
            if (
                bound_support.evaluation_scope_sha256
                != receipt.evaluation_scope_sha256
            ):
                raise AuditableEcosystemExplanationV1Error(
                    "attachment receipt scope does not match trace support"
                )
            pair = (receipt.evaluation_id, receipt.support_sha256)
            if pair in receipt_pairs:
                raise AuditableEcosystemExplanationV1Error(
                    "one trace support cannot have duplicate attachment receipts"
                )
            receipt_pairs.add(pair)

        if receipt_pairs != expected_receipt_pairs:
            raise AuditableEcosystemExplanationV1Error(
                "reviewed support attachment receipts must exactly cover trace supports"
            )

        object.__setattr__(
            self,
            "process_evaluation_identities",
            identities,
        )
        order = {
            evaluation_id: index
            for index, evaluation_id in enumerate(expected_ids)
        }
        object.__setattr__(
            self,
            "reviewed_support_attachment_receipts",
            tuple(
                sorted(
                    receipts,
                    key=lambda item: (
                        order[item.evaluation_id],
                        item.support_sha256,
                        item.receipt_id,
                    ),
                )
            ),
        )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": AUDITABLE_ECOSYSTEM_EXPLANATION_SCHEMA_VERSION,
            "explanation_trace": self.explanation_trace.canonical_payload(),
            "process_evaluation_identities": [
                item.canonical_payload()
                for item in self.process_evaluation_identities
            ],
            "reviewed_support_attachment_receipts": [
                item.canonical_payload()
                for item in self.reviewed_support_attachment_receipts
            ],
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_sha256(self.canonical_payload())

    def render_text(self) -> str:
        lines = [
            self.explanation_trace.render_text(),
            "",
            "Provenance d'attachement revue:",
        ]
        for receipt in self.reviewed_support_attachment_receipts:
            lines.append(
                "- "
                f"{receipt.evaluation_id}: receipt={receipt.receipt_id}; "
                f"selection={receipt.selection_id}; "
                f"selection_sha256={receipt.selection_sha256}; "
                f"bridge_sha256={receipt.bridge_sha256}."
            )
        return "\n".join(lines)


def build_auditable_ecosystem_explanation_v1(
    starting_state: EcosystemStateV1,
    ending_state: EcosystemStateV1,
    evaluations: tuple[ProcessEvaluationV1, ...],
    *,
    reviewed_support_attachment_receipts: tuple[
        ReviewedSupportAttachmentReceiptV1, ...
    ],
    observation_refs: tuple[str, ...] = (),
    intervention_refs: tuple[str, ...] = (),
) -> AuditableEcosystemExplanationV1:
    """Build an auditable envelope without changing the core explanation trace."""
    trace = build_ecosystem_explanation_v1(
        starting_state,
        ending_state,
        evaluations,
        observation_refs=observation_refs,
        intervention_refs=intervention_refs,
    )
    identities = tuple(
        ProcessEvaluationIdentityV1(
            evaluation_id=item.evaluation_id,
            canonical_sha256=item.canonical_sha256,
        )
        for item in evaluations
    )
    return AuditableEcosystemExplanationV1(
        explanation_trace=trace,
        process_evaluation_identities=identities,
        reviewed_support_attachment_receipts=(
            reviewed_support_attachment_receipts
        ),
    )
