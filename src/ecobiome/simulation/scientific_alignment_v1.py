"""Fail-closed reviewed ScientificAssertion alignment for N4 process roles."""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, replace
from typing import Any

from ecobiome.knowledge_persistence.contracts import (
    KnowledgeSynthesisRepository,
    ScientificAssertionRepository,
)
from ecobiome.knowledge_persistence.serialization import (
    canonical_json_text,
    canonical_sha256,
)
from ecobiome.simulation.process_v1 import (
    ProcessEvaluationV1,
    ProcessScientificEvaluationScopeV1,
    ProcessScientificSupportV1,
    ScientificAssertionRefV1,
)

ALIGNMENT_POLICY_DESIGN_SHA256 = (
    "a920653c4289d3deab81c2122b1fe05949e57dfd8529c5b507c50062a96db62c"
)
_ALIGNMENT_CLASSES = frozenset(
    {"direct_mechanism_support", "interpretive_mechanism_support"}
)
_MATCH_MODES = frozenset({"contains_exact_required", "exact"})
_ALLOWED_EPISTEMIC_BY_ALIGNMENT = {
    "direct_mechanism_support": frozenset({"explicit_causal_result"}),
    "interpretive_mechanism_support": frozenset({"interpretive_support"}),
}


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


def _canonical_optional_json(
    value: str | None,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ScientificProcessAlignmentV1Error(
            f"{field_name} must contain valid JSON"
        ) from exc
    return canonical_json_text(payload)


@dataclass(frozen=True, slots=True)
class ProcessScientificParticipantRequirementV1:
    """Exact role-sensitive ScientificAssertion participant identity."""

    role: str
    entity_id: str
    entity_revision: int
    occurrence_json: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _nonempty(self.role, "role"))
        object.__setattr__(
            self,
            "entity_id",
            _nonempty(self.entity_id, "entity_id"),
        )
        if (
            isinstance(self.entity_revision, bool)
            or not isinstance(self.entity_revision, int)
            or self.entity_revision < 1
        ):
            raise ScientificProcessAlignmentV1Error(
                "entity_revision must be an integer >= 1"
            )
        object.__setattr__(
            self,
            "occurrence_json",
            _canonical_optional_json(
                self.occurrence_json,
                "occurrence_json",
            ),
        )

    def canonical_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "role": self.role,
            "entity_id": self.entity_id,
            "entity_revision": self.entity_revision,
        }
        if self.occurrence_json is not None:
            payload["occurrence"] = json.loads(self.occurrence_json)
        return payload


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
    evaluation_scope: ProcessScientificEvaluationScopeV1
    required_participants: tuple[
        ProcessScientificParticipantRequirementV1, ...
    ] = ()
    required_qualifiers_json: str = "{}"
    participant_match_mode: str = "exact"
    qualifier_match_mode: str = "exact"
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
            "participant_match_mode",
            "qualifier_match_mode",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonempty(str(getattr(self, field_name)), field_name),
            )
        if not isinstance(self.evaluation_scope, ProcessScientificEvaluationScopeV1):
            raise ScientificProcessAlignmentV1Error(
                "evaluation_scope must be ProcessScientificEvaluationScopeV1"
            )
        if self.evaluation_scope.process_id != self.process_id:
            raise ScientificProcessAlignmentV1Error(
                "evaluation_scope process_id must match policy"
            )
        if self.evaluation_scope.process_version != self.process_version:
            raise ScientificProcessAlignmentV1Error(
                "evaluation_scope process_version must match policy"
            )
        if self.evaluation_scope.role != self.role:
            raise ScientificProcessAlignmentV1Error(
                "evaluation_scope role must match policy"
            )
        if self.alignment_class not in _ALIGNMENT_CLASSES:
            raise ScientificProcessAlignmentV1Error(
                f"unsupported alignment_class: {self.alignment_class!r}"
            )
        allowed_epistemic = _ALLOWED_EPISTEMIC_BY_ALIGNMENT[
            self.alignment_class
        ]
        if self.epistemic_class not in allowed_epistemic:
            raise ScientificProcessAlignmentV1Error(
                "alignment_class cannot increase or reinterpret epistemic strength: "
                f"{self.alignment_class!r} / {self.epistemic_class!r}"
            )
        for field_name in (
            "participant_match_mode",
            "qualifier_match_mode",
        ):
            if getattr(self, field_name) not in _MATCH_MODES:
                raise ScientificProcessAlignmentV1Error(
                    f"unsupported {field_name}: {getattr(self, field_name)!r}"
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

        participants = tuple(self.required_participants)
        if not participants:
            raise ScientificProcessAlignmentV1Error(
                "required_participants must not be empty for mechanism support"
            )
        if len(set(participants)) != len(participants):
            raise ScientificProcessAlignmentV1Error(
                "required_participants must be unique"
            )
        object.__setattr__(
            self,
            "required_participants",
            tuple(
                sorted(
                    participants,
                    key=lambda item: (
                        item.role,
                        item.entity_id,
                        item.entity_revision,
                        item.occurrence_json or "",
                    ),
                )
            ),
        )

        try:
            required_qualifiers = json.loads(self.required_qualifiers_json)
        except json.JSONDecodeError as exc:
            raise ScientificProcessAlignmentV1Error(
                "required_qualifiers_json must contain valid JSON"
            ) from exc
        if not isinstance(required_qualifiers, dict):
            raise ScientificProcessAlignmentV1Error(
                "required_qualifiers_json must decode to an object"
            )
        object.__setattr__(
            self,
            "required_qualifiers_json",
            canonical_json_text(required_qualifiers),
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
            "evaluation_scope": self.evaluation_scope.canonical_payload(),
            "required_participants": [
                item.canonical_payload()
                for item in self.required_participants
            ],
            "required_qualifiers": json.loads(
                self.required_qualifiers_json
            ),
            "participant_match_mode": self.participant_match_mode,
            "qualifier_match_mode": self.qualifier_match_mode,
            "design_basis_sha256": self.design_basis_sha256,
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_sha256(self.canonical_payload())


def _participant_requirements_from_json(
    participants_json: str,
) -> tuple[ProcessScientificParticipantRequirementV1, ...]:
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

    result: list[ProcessScientificParticipantRequirementV1] = []
    for participant in participants:
        if not isinstance(participant, dict):
            raise ScientificProcessAlignmentV1Error(
                "assertion participant must be an object"
            )
        role = participant.get("role")
        entity = participant.get("entity")
        if not isinstance(role, str) or not role.strip():
            raise ScientificProcessAlignmentV1Error(
                "assertion participant role must be non-empty"
            )
        if not isinstance(entity, dict):
            raise ScientificProcessAlignmentV1Error(
                "assertion participant entity must be an object"
            )
        if entity.get("type") != "entity_ref":
            raise ScientificProcessAlignmentV1Error(
                "assertion participant entity must be entity_ref"
            )
        entity_id = entity.get("entity_id")
        revision = entity.get("entity_revision")
        if not isinstance(entity_id, str) or not entity_id.strip():
            raise ScientificProcessAlignmentV1Error(
                "assertion participant entity_id must be non-empty"
            )
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 1
        ):
            raise ScientificProcessAlignmentV1Error(
                "assertion participant entity_revision must be >= 1"
            )
        occurrence_json = (
            None
            if "occurrence" not in participant
            else canonical_json_text(participant["occurrence"])
        )
        result.append(
            ProcessScientificParticipantRequirementV1(
                role=role,
                entity_id=entity_id,
                entity_revision=revision,
                occurrence_json=occurrence_json,
            )
        )
    return tuple(
        sorted(
            result,
            key=lambda item: (
                item.role,
                item.entity_id,
                item.entity_revision,
                item.occurrence_json or "",
            ),
        )
    )


def _require_participant_match(
    *,
    observed: tuple[ProcessScientificParticipantRequirementV1, ...],
    policy: ProcessScientificAlignmentPolicyV1,
) -> None:
    observed_counts = Counter(observed)
    required_counts = Counter(policy.required_participants)

    if policy.participant_match_mode == "exact":
        if observed_counts != required_counts:
            raise ScientificProcessAlignmentV1Error(
                "assertion participants do not exactly match reviewed "
                "role/entity/revision requirements"
            )
        return

    missing = required_counts - observed_counts
    if missing:
        raise ScientificProcessAlignmentV1Error(
            "assertion participants are missing reviewed "
            "role/entity/revision requirements"
        )


def _qualifiers_object(qualifiers_json: str) -> dict[str, object]:
    try:
        qualifiers = json.loads(qualifiers_json)
    except json.JSONDecodeError as exc:
        raise ScientificProcessAlignmentV1Error(
            "assertion qualifiers_json must be valid JSON"
        ) from exc
    if not isinstance(qualifiers, dict):
        raise ScientificProcessAlignmentV1Error(
            "assertion qualifiers_json must decode to an object"
        )
    return qualifiers


def _require_qualifier_match(
    *,
    observed: dict[str, object],
    policy: ProcessScientificAlignmentPolicyV1,
) -> None:
    required = json.loads(policy.required_qualifiers_json)
    if not isinstance(required, dict):
        raise ScientificProcessAlignmentV1Error(
            "policy required qualifiers must remain an object"
        )
    if policy.qualifier_match_mode == "exact":
        if observed != required:
            raise ScientificProcessAlignmentV1Error(
                "assertion qualifiers do not exactly match reviewed policy"
            )
        return

    mismatched = [
        key
        for key, required_value in required.items()
        if key not in observed or observed[key] != required_value
    ]
    if mismatched:
        raise ScientificProcessAlignmentV1Error(
            "assertion qualifiers are missing or conflict with reviewed "
            f"requirements: {sorted(mismatched)!r}"
        )


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


_SCIENTIFIC_ALIGNMENT_NOT_REVIEWED_UNKNOWN = (
    "scientific assertion refs supplied but process-to-assertion alignment "
    "is not reviewed in N4 V1"
)


def _is_stale_alignment_unknown(value: str) -> bool:
    return value.strip() == _SCIENTIFIC_ALIGNMENT_NOT_REVIEWED_UNKNOWN


def _ordered_distinct(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def align_scientific_assertion_to_process_v1(
    *,
    evaluation: ProcessEvaluationV1,
    assertion_ref: ScientificAssertionRefV1,
    policy: ProcessScientificAlignmentPolicyV1,
    assertions: ScientificAssertionRepository,
    syntheses: KnowledgeSynthesisRepository,
) -> ProcessScientificSupportV1:
    """Verify exact V6 identity/review semantics and return reviewed N4 support."""

    definition = evaluation.definition
    if policy.process_id != definition.process_id:
        raise ScientificProcessAlignmentV1Error("policy process_id mismatch")
    if policy.process_version != definition.version:
        raise ScientificProcessAlignmentV1Error("policy process_version mismatch")
    if policy.role not in definition.required_scientific_assertion_roles:
        raise ScientificProcessAlignmentV1Error(
            "policy role is not declared by the process definition"
        )
    try:
        policy.evaluation_scope.require_match(
            process_id=definition.process_id,
            process_version=definition.version,
            role=policy.role,
            parameters=evaluation.parameters_payload,
        )
    except ValueError as exc:
        raise ScientificProcessAlignmentV1Error(
            "evaluation is outside reviewed scientific support scope"
        ) from exc

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

    _require_participant_match(
        observed=_participant_requirements_from_json(
            revision.participants_json
        ),
        policy=policy,
    )
    _require_qualifier_match(
        observed=_qualifiers_object(revision.qualifiers_json),
        policy=policy,
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
        evaluation_scope=policy.evaluation_scope,
        evaluation_scope_sha256=policy.evaluation_scope.canonical_sha256,
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
    for support in supports:
        try:
            support.evaluation_scope.require_match(
                process_id=evaluation.definition.process_id,
                process_version=evaluation.definition.version,
                role=support.role,
                parameters=evaluation.parameters_payload,
            )
        except ValueError as exc:
            raise ScientificProcessAlignmentV1Error(
                "reviewed scientific support does not match evaluation scope"
            ) from exc

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

    filtered_unknowns = tuple(
        item
        for item in evaluation.unknowns
        if not _is_stale_alignment_unknown(item)
    )
    support_warnings = tuple(
        warning
        for support in supports
        for warning in support.warnings
    )
    support_uncertainties = tuple(
        uncertainty
        for support in supports
        for uncertainty in support.uncertainties
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
        warnings=_ordered_distinct(
            evaluation.warnings + support_warnings
        ),
        unknowns=_ordered_distinct(
            filtered_unknowns + support_uncertainties
        ),
    )
