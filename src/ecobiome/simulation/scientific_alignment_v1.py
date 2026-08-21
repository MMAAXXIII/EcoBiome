"""Fail-closed reviewed ScientificAssertion alignment for N4 process roles."""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Any

from ecobiome.knowledge_persistence.contracts import (
    KnowledgeSynthesisRepository,
    ScientificAssertionRepository,
)
from ecobiome.knowledge_persistence.serialization import canonical_sha256
from ecobiome.simulation.process_v1 import (
    ProcessDefinitionV1,
    ProcessEvaluationV1,
    ProcessScientificSupportV1,
    ScientificAssertionRefV1,
)

ALIGNMENT_POLICY_DESIGN_SHA256 = (
    "a920653c4289d3deab81c2122b1fe05949e57dfd8529c5b507c50062a96db62c"
)
_ALIGNMENT_CLASSES = frozenset(
    {"direct_mechanism_support", "interpretive_mechanism_support"}
)


class ScientificProcessAlignmentV1Error(ValueError):
    """Raised when a ScientificAssertion cannot support an N4 process role."""


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ScientificProcessAlignmentV1Error(
            f"{field_name} must be non-empty"
        )
    return normalized


def _ordered_unique(
    values: tuple[str, ...],
    field_name: str,
) -> tuple[str, ...]:
    normalized = tuple(_nonempty(value, field_name) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ScientificProcessAlignmentV1Error(
            f"{field_name} values must be unique"
        )
    return normalized


@dataclass(frozen=True, slots=True)
class ProcessScientificAlignmentPolicyV1:
    """Frozen process-specific matcher built on the reviewed G7A policy design."""

    name: str
    version: str
    process_id: str
    process_version: str
    role: str
    allowed_predicates: tuple[str, ...]
    alignment_class: str
    epistemic_class: str
    required_entity_ids: tuple[str, ...] = ()
    design_basis_sha256: str = ALIGNMENT_POLICY_DESIGN_SHA256

    def __post_init__(self) -> None:
        for field_name in (
            "name",
            "version",
            "process_id",
            "process_version",
            "role",
            "alignment_class",
            "epistemic_class",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonempty(str(getattr(self, field_name)), field_name),
            )
        if self.alignment_class not in _ALIGNMENT_CLASSES:
            raise ScientificProcessAlignmentV1Error(
                f"unsupported alignment_class: {self.alignment_class!r}"
            )
        predicates = _ordered_unique(
            tuple(self.allowed_predicates),
            "allowed_predicates",
        )
        if not predicates:
            raise ScientificProcessAlignmentV1Error(
                "allowed_predicates must not be empty"
            )
        object.__setattr__(self, "allowed_predicates", predicates)
        object.__setattr__(
            self,
            "required_entity_ids",
            _ordered_unique(
                tuple(self.required_entity_ids),
                "required_entity_ids",
            ),
        )
        digest = self.design_basis_sha256.strip()
        if digest != ALIGNMENT_POLICY_DESIGN_SHA256:
            raise ScientificProcessAlignmentV1Error(
                "design_basis_sha256 must equal the audited G7A policy design"
            )
        object.__setattr__(self, "design_basis_sha256", digest)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-process-scientific-alignment-policy-v1",
            "name": self.name,
            "version": self.version,
            "process_id": self.process_id,
            "process_version": self.process_version,
            "role": self.role,
            "allowed_predicates": list(self.allowed_predicates),
            "alignment_class": self.alignment_class,
            "epistemic_class": self.epistemic_class,
            "required_entity_ids": sorted(self.required_entity_ids),
            "design_basis_sha256": self.design_basis_sha256,
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_sha256(self.canonical_payload())


def _entity_ids_from_participants_json(participants_json: str) -> set[str]:
    try:
        participants = json.loads(participants_json)
    except json.JSONDecodeError as exc:
        raise ScientificProcessAlignmentV1Error(
            "assertion participants_json must be valid JSON"
        ) from exc
    if not isinstance(participants, list):
        raise ScientificProcessAlignmentV1Error(
            "assertion participants_json must decode to a list"
        )
    entity_ids: set[str] = set()
    for participant in participants:
        if not isinstance(participant, dict):
            continue
        entity = participant.get("entity")
        if not isinstance(entity, dict):
            continue
        if entity.get("type") != "entity_ref":
            continue
        entity_id = entity.get("entity_id")
        if isinstance(entity_id, str) and entity_id.strip():
            entity_ids.add(entity_id.strip())
    return entity_ids


def _json_messages(raw: str, label: str) -> tuple[str, ...]:
    try:
        value: Any = json.loads(raw)
    except json.JSONDecodeError:
        return (f"{label}: invalid persisted JSON",)
    if value in (None, [], {}, ""):
        return ()
    if isinstance(value, list):
        return tuple(
            (
                f"{label}: {item}"
                if isinstance(item, str)
                else f"{label}: "
                + json.dumps(
                    item,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            for item in value
        )
    if isinstance(value, dict):
        return (
            f"{label}: "
            + json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )
    return (f"{label}: {value}",)


def align_scientific_assertion_to_process_v1(
    *,
    definition: ProcessDefinitionV1,
    assertion_ref: ScientificAssertionRefV1,
    policy: ProcessScientificAlignmentPolicyV1,
    assertions: ScientificAssertionRepository,
    syntheses: KnowledgeSynthesisRepository,
) -> ProcessScientificSupportV1:
    """Verify exact V6 identity/review semantics and return reviewed N4 support."""

    if policy.process_id != definition.process_id:
        raise ScientificProcessAlignmentV1Error("policy process_id mismatch")
    if policy.process_version != definition.version:
        raise ScientificProcessAlignmentV1Error("policy process_version mismatch")
    if policy.role not in definition.required_scientific_assertion_roles:
        raise ScientificProcessAlignmentV1Error(
            "policy role is not declared by the process definition"
        )

    root = assertions.get_assertion(assertion_ref.assertion_id)
    if root is None:
        raise ScientificProcessAlignmentV1Error(
            "scientific assertion root missing"
        )
    if root.retired_at is not None:
        raise ScientificProcessAlignmentV1Error(
            "scientific assertion is retired"
        )

    revision = assertions.get_assertion_revision(
        assertion_ref.assertion_id,
        assertion_ref.assertion_revision,
    )
    if revision is None:
        raise ScientificProcessAlignmentV1Error(
            "scientific assertion revision missing"
        )
    if revision.schema_version != "scientific-assertion-v1.1":
        raise ScientificProcessAlignmentV1Error(
            "scientific assertion schema_version mismatch"
        )
    if (
        revision.canonical_payload_sha256
        != assertion_ref.canonical_payload_sha256
    ):
        raise ScientificProcessAlignmentV1Error(
            "scientific assertion canonical SHA mismatch"
        )

    reverse_matches = assertions.find_by_canonical_payload_sha256(
        assertion_ref.canonical_payload_sha256
    )
    if not any(
        row.assertion_id == assertion_ref.assertion_id
        and row.revision == assertion_ref.assertion_revision
        for row in reverse_matches
    ):
        raise ScientificProcessAlignmentV1Error(
            "canonical SHA reverse lookup does not resolve to the same revision"
        )

    links = assertions.list_assertion_claim_links(
        assertion_ref.assertion_id,
        assertion_ref.assertion_revision,
    )
    eligible_links = tuple(
        link
        for link in links
        if link.stance == "supports"
        and link.scope_alignment == "exact"
        and link.semantic_alignment == "exact"
        and link.reviewed_by is not None
        and bool(link.reviewed_by.strip())
        and link.reviewed_at is not None
        and bool(link.reviewed_at.strip())
    )
    if not eligible_links:
        raise ScientificProcessAlignmentV1Error(
            "no exact reviewed supporting assertion-claim link"
        )

    if revision.predicate not in policy.allowed_predicates:
        raise ScientificProcessAlignmentV1Error(
            "assertion predicate is not allowed by the process-specific policy"
        )

    observed_entity_ids = _entity_ids_from_participants_json(
        revision.participants_json
    )
    missing_entity_ids = set(policy.required_entity_ids) - observed_entity_ids
    if missing_entity_ids:
        raise ScientificProcessAlignmentV1Error(
            "assertion participants are missing required exact entity identities: "
            f"{sorted(missing_entity_ids)!r}"
        )

    synthesis_rows = tuple(
        syntheses.list_for_assertion(
            assertion_ref.assertion_id,
            assertion_ref.assertion_revision,
        )
    )
    latest = (
        max(synthesis_rows, key=lambda row: row.synthesis_revision)
        if synthesis_rows
        else None
    )
    evidence_state = None if latest is None else latest.evidence_state
    warnings = (
        ()
        if latest is None
        else _json_messages(
            latest.conflicts_json,
            "synthesis_conflict",
        )
    )
    uncertainties = (
        ()
        if latest is None
        else _json_messages(
            latest.uncertainties_json,
            "synthesis_uncertainty",
        )
    )

    return ProcessScientificSupportV1(
        role=policy.role,
        assertion_ref=assertion_ref,
        alignment_class=policy.alignment_class,
        epistemic_class=policy.epistemic_class,
        alignment_policy_name=policy.name,
        alignment_policy_version=policy.version,
        alignment_policy_sha256=policy.canonical_sha256,
        evidence_state=evidence_state,
        warnings=warnings,
        uncertainties=uncertainties,
    )


def attach_scientific_supports_v1(
    evaluation: ProcessEvaluationV1,
    supports: tuple[ProcessScientificSupportV1, ...],
) -> ProcessEvaluationV1:
    """Attach reviewed supports without modifying the deterministic evaluator."""

    if not supports:
        raise ScientificProcessAlignmentV1Error(
            "at least one reviewed scientific support is required"
        )
    required_roles = set(
        evaluation.definition.required_scientific_assertion_roles
    )
    if not required_roles:
        raise ScientificProcessAlignmentV1Error(
            "process definition declares no scientific support roles"
        )
    support_roles = {support.role for support in supports}
    undeclared = support_roles - required_roles
    if undeclared:
        raise ScientificProcessAlignmentV1Error(
            f"scientific support contains undeclared roles: {sorted(undeclared)!r}"
        )
    missing = required_roles - support_roles
    if missing:
        raise ScientificProcessAlignmentV1Error(
            f"scientific support is missing required roles: {sorted(missing)!r}"
        )

    support_refs = tuple(
        sorted(
            {support.assertion_ref for support in supports},
            key=lambda ref: (
                ref.assertion_id,
                ref.assertion_revision,
            ),
        )
    )
    existing_refs = tuple(
        sorted(
            set(evaluation.scientific_assertion_refs),
            key=lambda ref: (
                ref.assertion_id,
                ref.assertion_revision,
            ),
        )
    )
    if existing_refs and existing_refs != support_refs:
        raise ScientificProcessAlignmentV1Error(
            "reviewed supports do not match the evaluation assertion refs"
        )

    return replace(
        evaluation,
        support_status="scientific_alignment_reviewed",
        scientific_assertion_refs=support_refs,
        scientific_supports=tuple(
            sorted(
                supports,
                key=lambda item: (
                    item.role,
                    item.assertion_ref.assertion_id,
                    item.assertion_ref.assertion_revision,
                ),
            )
        ),
    )
