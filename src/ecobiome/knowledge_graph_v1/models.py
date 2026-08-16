"""N10 V1 scientific-knowledge graph domain contracts.

This module is deliberately persistence-neutral. Collector Source/Passage/Claim/Evidence
rows remain the provenance source of truth; N10 adds strict logical/read-model objects
without creating a parallel SQLite schema.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from typing import ClassVar

from ecobiome.knowledge_persistence.serialization import (
    canonical_json_text,
    canonical_sha256,
)

_REVIEW_STATUSES = frozenset({"pending", "accepted", "rejected", "superseded"})
_IDENTIFICATION_LEVELS = frozenset(
    {"exact_taxon", "probable_taxon", "genus", "biological_group", "unknown"}
)
_RELATION_STANCES = frozenset({"supports", "contradicts"})
_CLAIM_RELATION_TYPES = frozenset(
    {"corroborates", "contradicts", "refines", "duplicates"}
)
_SCOPE_OVERLAPS = frozenset({"full", "partial", "none", "unknown"})
_DEPENDENCY_TYPES = frozenset(
    {
        "independent",
        "derived_from",
        "syndicated_from",
        "duplicate_of",
        "possibly_dependent",
        "unknown",
    }
)
_USAGE_PERMISSIONS = frozenset({"allowed", "disallowed", "unknown"})
_LICENSE_VERIFICATION = frozenset({"verified", "unverified", "rejected"})
_FACTOR_STATES = frozenset({"concordant", "non_concordant", "missing", "unknown"})
_OBSERVATION_TRENDS = frozenset({"appearing", "increasing", "stable", "regressing", "unknown"})


def _nonempty(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must be non-empty")
    return normalized


def _optional_nonempty(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    return _nonempty(value, label)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_sha256(value: str, label: str) -> str:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def _review_status(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in _REVIEW_STATUSES:
        raise ValueError(f"unsupported review status: {value!r}")
    return normalized


def _decimal_text(value: str | None, label: str, *, minimum: Decimal | None = None, maximum: Decimal | None = None) -> str | None:
    if value is None:
        return None
    raw = _nonempty(value, label)
    try:
        number = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a decimal value") from exc
    if not number.is_finite():
        raise ValueError(f"{label} must be finite")
    if minimum is not None and number < minimum:
        raise ValueError(f"{label} must be >= {minimum}")
    if maximum is not None and number > maximum:
        raise ValueError(f"{label} must be <= {maximum}")
    return format(number, "f")


def _json_object_text(value: str, label: str) -> str:
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON") from exc
    if not isinstance(decoded, dict):
        raise TypeError(f"{label} must decode to an object")
    return canonical_json_text(decoded)


@dataclass(frozen=True, slots=True)
class Evidence:
    id: str
    source_id: str
    passage_id: str
    span_start: int
    span_end: int
    evidence_text: str
    evidence_sha256: str
    evidence_type: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _nonempty(self.id, "evidence id"))
        object.__setattr__(self, "source_id", _nonempty(self.source_id, "source_id"))
        object.__setattr__(self, "passage_id", _nonempty(self.passage_id, "passage_id"))
        if self.span_start < 0 or self.span_end <= self.span_start:
            raise ValueError("Evidence span must satisfy 0 <= start < end")
        text = _nonempty(self.evidence_text, "evidence_text")
        if _sha256_text(text) != self.evidence_sha256:
            raise ValueError("Evidence SHA-256 does not match exact evidence_text")
        object.__setattr__(self, "evidence_text", text)
        object.__setattr__(self, "evidence_sha256", _require_sha256(self.evidence_sha256, "evidence_sha256"))
        object.__setattr__(self, "evidence_type", _nonempty(self.evidence_type, "evidence_type"))

    @property
    def canonical_sha256(self) -> str:
        return canonical_sha256(self.canonical_payload())

    def canonical_payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "passage_id": self.passage_id,
            "span_start": self.span_start,
            "span_end": self.span_end,
            "evidence_text": self.evidence_text,
            "evidence_sha256": self.evidence_sha256,
            "evidence_type": self.evidence_type,
        }


@dataclass(frozen=True, slots=True)
class ApplicabilityScope:
    id: str
    medium: str | None = None
    system_type: str | None = None
    environment: str | None = None
    temperature_min: str | None = None
    temperature_max: str | None = None
    temperature_unit: str | None = None
    taxon: str | None = None
    life_stage: str | None = None
    geography: str | None = None
    temporal_scope: str | None = None
    additional_constraints_json: str = "{}"

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _nonempty(self.id, "scope id"))
        for field_name in (
            "medium",
            "system_type",
            "environment",
            "taxon",
            "life_stage",
            "geography",
            "temporal_scope",
        ):
            object.__setattr__(self, field_name, _optional_nonempty(getattr(self, field_name), field_name))
        minimum = _decimal_text(self.temperature_min, "temperature_min")
        maximum = _decimal_text(self.temperature_max, "temperature_max")
        if minimum is not None and maximum is not None and Decimal(maximum) < Decimal(minimum):
            raise ValueError("temperature_max must be >= temperature_min")
        unit = _optional_nonempty(self.temperature_unit, "temperature_unit")
        if (minimum is None) != (maximum is None):
            raise ValueError("temperature range requires both minimum and maximum")
        if minimum is not None and unit is None:
            raise ValueError("temperature range requires temperature_unit")
        if minimum is None and unit is not None:
            raise ValueError("temperature_unit requires a temperature range")
        object.__setattr__(self, "temperature_min", minimum)
        object.__setattr__(self, "temperature_max", maximum)
        object.__setattr__(self, "temperature_unit", unit)
        object.__setattr__(
            self,
            "additional_constraints_json",
            _json_object_text(self.additional_constraints_json, "additional_constraints_json"),
        )

    @property
    def is_unspecified(self) -> bool:
        constraints = json.loads(self.additional_constraints_json)
        assert isinstance(constraints, dict)
        return (
            self.medium is None
            and self.system_type is None
            and self.environment is None
            and self.temperature_min is None
            and self.taxon is None
            and self.life_stage is None
            and self.geography is None
            and self.temporal_scope is None
            and not constraints
        )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "medium": self.medium,
            "system_type": self.system_type,
            "environment": self.environment,
            "temperature": (
                None
                if self.temperature_min is None
                else {
                    "min": self.temperature_min,
                    "max": self.temperature_max,
                    "unit": self.temperature_unit,
                }
            ),
            "taxon": self.taxon,
            "life_stage": self.life_stage,
            "geography": self.geography,
            "temporal_scope": self.temporal_scope,
            "additional_constraints": json.loads(self.additional_constraints_json),
            # Critical semantics: absent dimensions mean unknown, not universal.
            "missing_dimensions_mean_unknown": True,
        }


@dataclass(frozen=True, slots=True)
class Claim:
    id: str
    passage_id: str
    source_text: str
    subject_surface: str
    predicate_key: str
    object_surface: str | None
    subject_object_id: str | None
    object_object_id: str | None
    value_type: str
    scalar_value: str | None
    text_value: str | None
    lower_bound: str | None
    upper_bound: str | None
    unit_key: str | None
    applicability_scope_id: str | None
    extraction_method: str
    extraction_confidence: str | None
    created_at: str
    source_span_start: int | None = None
    source_span_end: int | None = None
    review_status: str = "pending"

    def __post_init__(self) -> None:
        for name in ("id", "passage_id", "source_text", "subject_surface", "predicate_key", "value_type", "extraction_method", "created_at"):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))
        for name in ("object_surface", "subject_object_id", "object_object_id", "text_value", "unit_key", "applicability_scope_id"):
            object.__setattr__(self, name, _optional_nonempty(getattr(self, name), name))
        if (self.source_span_start is None) != (self.source_span_end is None):
            raise ValueError("Claim source span requires both start and end")
        if self.source_span_start is not None:
            assert self.source_span_end is not None
            if self.source_span_start < 0 or self.source_span_end <= self.source_span_start:
                raise ValueError("Claim source span must satisfy 0 <= start < end")
        scalar = _decimal_text(self.scalar_value, "scalar_value")
        lower = _decimal_text(self.lower_bound, "lower_bound")
        upper = _decimal_text(self.upper_bound, "upper_bound")
        if lower is not None and upper is not None and Decimal(upper) < Decimal(lower):
            raise ValueError("upper_bound must be >= lower_bound")
        confidence = _decimal_text(
            self.extraction_confidence,
            "extraction_confidence",
            minimum=Decimal(0),
            maximum=Decimal(1),
        )
        object.__setattr__(self, "scalar_value", scalar)
        object.__setattr__(self, "lower_bound", lower)
        object.__setattr__(self, "upper_bound", upper)
        object.__setattr__(self, "extraction_confidence", confidence)
        object.__setattr__(self, "review_status", _review_status(self.review_status))
        # Numeric values are data, never implicit operational thresholds.
        if self.value_type == "threshold":
            raise ValueError("numeric claims must not auto-declare an operational threshold")

    def with_review_status(self, status: str) -> Claim:
        return replace(self, review_status=_review_status(status))

    def canonical_payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "passage_id": self.passage_id,
            "source_span_start": self.source_span_start,
            "source_span_end": self.source_span_end,
            "source_text": self.source_text,
            "subject_surface": self.subject_surface,
            "predicate_key": self.predicate_key,
            "object_surface": self.object_surface,
            "subject_object_id": self.subject_object_id,
            "object_object_id": self.object_object_id,
            "value_type": self.value_type,
            "scalar_value": self.scalar_value,
            "text_value": self.text_value,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "unit_key": self.unit_key,
            "applicability_scope_id": self.applicability_scope_id,
            "extraction_method": self.extraction_method,
            "extraction_confidence": self.extraction_confidence,
            "created_at": self.created_at,
            "review_status": self.review_status,
            "operational_threshold": False,
        }


@dataclass(frozen=True, slots=True)
class ClaimEvidence:
    claim_id: str
    evidence_id: str
    evidence_order: int
    role: str
    created_at: str

    def __post_init__(self) -> None:
        for name in ("claim_id", "evidence_id", "role", "created_at"):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))
        if self.evidence_order < 0:
            raise ValueError("evidence_order must be >= 0")


@dataclass(frozen=True, slots=True)
class ClaimReviewEvent:
    id: str
    claim_id: str
    decision: str
    reviewer: str
    rationale: str
    reviewed_at: str

    _DECISIONS: ClassVar[frozenset[str]] = frozenset({"accept", "reject", "supersede", "reopen"})

    def __post_init__(self) -> None:
        for name in ("id", "claim_id", "reviewer", "rationale", "reviewed_at"):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))
        decision = self.decision.strip().lower()
        if decision not in self._DECISIONS:
            raise ValueError(f"unsupported Claim review decision: {self.decision!r}")
        object.__setattr__(self, "decision", decision)


@dataclass(frozen=True, slots=True)
class KnowledgeObject:
    id: str
    object_type: str
    canonical_label: str
    canonical_key: str
    created_at: str

    def __post_init__(self) -> None:
        for name in ("id", "object_type", "canonical_label", "canonical_key", "created_at"):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class LivingEntity:
    knowledge_object_id: str
    identification_level: str
    taxon_name: str | None = None
    taxon_rank: str | None = None
    taxon_identifier: str | None = None
    taxonomy_source: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "knowledge_object_id", _nonempty(self.knowledge_object_id, "knowledge_object_id"))
        level = self.identification_level.strip().lower()
        if level not in _IDENTIFICATION_LEVELS:
            raise ValueError(f"unsupported identification_level: {self.identification_level!r}")
        object.__setattr__(self, "identification_level", level)
        for name in ("taxon_name", "taxon_rank", "taxon_identifier", "taxonomy_source"):
            object.__setattr__(self, name, _optional_nonempty(getattr(self, name), name))
        if level == "exact_taxon" and self.taxon_name is None:
            raise ValueError("exact_taxon requires taxon_name")


@dataclass(frozen=True, slots=True)
class Morphotype:
    knowledge_object_id: str
    morphology: str
    color: str
    texture: str
    typical_location: str
    differential_features: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("knowledge_object_id", "morphology", "color", "texture", "typical_location"):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))
        features = tuple(_nonempty(item, "differential_feature") for item in self.differential_features)
        object.__setattr__(self, "differential_features", features)


@dataclass(frozen=True, slots=True)
class EcosystemObservable:
    knowledge_object_id: str
    observable_category: str
    default_quantification_mode: str

    def __post_init__(self) -> None:
        for name in ("knowledge_object_id", "observable_category", "default_quantification_mode"):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class ScientificConcept:
    knowledge_object_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "knowledge_object_id", _nonempty(self.knowledge_object_id, "knowledge_object_id"))


@dataclass(frozen=True, slots=True)
class Process:
    knowledge_object_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "knowledge_object_id", _nonempty(self.knowledge_object_id, "knowledge_object_id"))


@dataclass(frozen=True, slots=True)
class KnowledgeRelation:
    id: str
    subject_object_id: str
    predicate_key: str
    object_object_id: str | None
    scalar_value: str | None
    text_value: str | None
    unit_key: str | None
    applicability_scope_id: str | None
    created_at: str

    def __post_init__(self) -> None:
        for name in ("id", "subject_object_id", "predicate_key", "created_at"):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))
        for name in ("object_object_id", "text_value", "unit_key", "applicability_scope_id"):
            object.__setattr__(self, name, _optional_nonempty(getattr(self, name), name))
        object.__setattr__(self, "scalar_value", _decimal_text(self.scalar_value, "scalar_value"))
        value_count = sum(
            item is not None for item in (self.object_object_id, self.scalar_value, self.text_value)
        )
        if value_count != 1:
            raise ValueError("KnowledgeRelation requires exactly one object/scalar/text value")


@dataclass(frozen=True, slots=True)
class RelationClaimLink:
    relation_id: str
    claim_id: str
    stance: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relation_id", _nonempty(self.relation_id, "relation_id"))
        object.__setattr__(self, "claim_id", _nonempty(self.claim_id, "claim_id"))
        stance = self.stance.strip().lower()
        if stance not in _RELATION_STANCES:
            raise ValueError(f"unsupported relation Claim stance: {self.stance!r}")
        object.__setattr__(self, "stance", stance)


@dataclass(frozen=True, slots=True)
class ClaimRelation:
    id: str
    claim_a_id: str
    claim_b_id: str
    relation_type: str
    scope_overlap: str
    applicability_scope_id: str | None
    review_status: str
    created_at: str

    def __post_init__(self) -> None:
        for name in ("id", "claim_a_id", "claim_b_id", "created_at"):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))
        if self.claim_a_id == self.claim_b_id:
            raise ValueError("ClaimRelation requires two distinct Claims")
        relation_type = self.relation_type.strip().lower()
        if relation_type not in _CLAIM_RELATION_TYPES:
            raise ValueError(f"unsupported Claim relation_type: {self.relation_type!r}")
        overlap = self.scope_overlap.strip().lower()
        if overlap not in _SCOPE_OVERLAPS:
            raise ValueError(f"unsupported scope_overlap: {self.scope_overlap!r}")
        object.__setattr__(self, "relation_type", relation_type)
        object.__setattr__(self, "scope_overlap", overlap)
        object.__setattr__(self, "applicability_scope_id", _optional_nonempty(self.applicability_scope_id, "applicability_scope_id"))
        object.__setattr__(self, "review_status", _review_status(self.review_status))


@dataclass(frozen=True, slots=True)
class SourceDependency:
    id: str
    source_a_id: str
    source_b_id: str
    dependency_type: str
    review_status: str
    detection_method: str
    detection_confidence: str | None
    created_at: str

    def __post_init__(self) -> None:
        for name in ("id", "source_a_id", "source_b_id", "detection_method", "created_at"):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))
        if self.source_a_id == self.source_b_id:
            raise ValueError("SourceDependency requires two distinct sources")
        dependency = self.dependency_type.strip().lower()
        if dependency not in _DEPENDENCY_TYPES:
            raise ValueError(f"unsupported dependency_type: {self.dependency_type!r}")
        object.__setattr__(self, "dependency_type", dependency)
        object.__setattr__(self, "review_status", _review_status(self.review_status))
        object.__setattr__(
            self,
            "detection_confidence",
            _decimal_text(
                self.detection_confidence,
                "detection_confidence",
                minimum=Decimal(0),
                maximum=Decimal(1),
            ),
        )

    @property
    def counts_as_independent(self) -> bool:
        return self.dependency_type == "independent" and self.review_status == "accepted"


@dataclass(frozen=True, slots=True)
class ObservationLocation:
    id: str
    ecosystem_id: str
    location_key: str
    label: str

    def __post_init__(self) -> None:
        for name in ("id", "ecosystem_id", "location_key", "label"):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class EcosystemObservation:
    id: str
    ecosystem_id: str
    observable_object_id: str
    observed_at: str
    quantification_mode: str
    numeric_value: str | None = None
    ordinal_value: str | None = None
    unit_key: str | None = None
    location_id: str | None = None
    trend: str = "unknown"
    notes: str = ""

    def __post_init__(self) -> None:
        for name in ("id", "ecosystem_id", "observable_object_id", "observed_at", "quantification_mode"):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))
        object.__setattr__(self, "numeric_value", _decimal_text(self.numeric_value, "numeric_value"))
        object.__setattr__(self, "ordinal_value", _optional_nonempty(self.ordinal_value, "ordinal_value"))
        object.__setattr__(self, "unit_key", _optional_nonempty(self.unit_key, "unit_key"))
        object.__setattr__(self, "location_id", _optional_nonempty(self.location_id, "location_id"))
        trend = self.trend.strip().lower()
        if trend not in _OBSERVATION_TRENDS:
            raise ValueError(f"unsupported observation trend: {self.trend!r}")
        object.__setattr__(self, "trend", trend)
        if (self.numeric_value is None) == (self.ordinal_value is None):
            raise ValueError("observation requires exactly one numeric or ordinal value")


@dataclass(frozen=True, slots=True)
class BioindicatorFactorAssessment:
    id: str
    assessment_id: str
    factor_key: str
    state: str
    observed_value: str | None
    relation_id: str | None
    rationale: str

    def __post_init__(self) -> None:
        for name in ("id", "assessment_id", "factor_key", "rationale"):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))
        state = self.state.strip().lower()
        if state not in _FACTOR_STATES:
            raise ValueError(f"unsupported factor assessment state: {self.state!r}")
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "observed_value", _optional_nonempty(self.observed_value, "observed_value"))
        object.__setattr__(self, "relation_id", _optional_nonempty(self.relation_id, "relation_id"))
        if state == "missing" and self.observed_value is not None:
            raise ValueError("missing factor must not carry an observed value")
        if state in {"concordant", "non_concordant"} and self.relation_id is None:
            raise ValueError("concordant/non_concordant factor requires a reviewed relation anchor")


@dataclass(frozen=True, slots=True)
class BioindicatorAssessment:
    id: str
    ecosystem_id: str
    observation_id: str
    evaluability: str
    evidence_strength: str
    data_completeness: str
    generated_at: str

    CORRELATION_WARNING: ClassVar[str] = "compatibility/correlation does not establish causality"

    def __post_init__(self) -> None:
        for name in (
            "id",
            "ecosystem_id",
            "observation_id",
            "evaluability",
            "evidence_strength",
            "data_completeness",
            "generated_at",
        ):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class ImageAsset:
    id: str
    source_url: str
    image_url: str
    creator: str
    title: str
    license: str
    license_url: str
    attribution: str
    retrieved_at: str
    sha256: str
    usage_permission: str
    verification_status: str

    def __post_init__(self) -> None:
        for name in (
            "id",
            "source_url",
            "image_url",
            "creator",
            "title",
            "license",
            "license_url",
            "attribution",
            "retrieved_at",
        ):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))
        object.__setattr__(self, "sha256", _require_sha256(self.sha256, "image sha256"))
        permission = self.usage_permission.strip().lower()
        verification = self.verification_status.strip().lower()
        if permission not in _USAGE_PERMISSIONS:
            raise ValueError(f"unsupported usage_permission: {self.usage_permission!r}")
        if verification not in _LICENSE_VERIFICATION:
            raise ValueError(f"unsupported verification_status: {self.verification_status!r}")
        object.__setattr__(self, "usage_permission", permission)
        object.__setattr__(self, "verification_status", verification)

    @property
    def attachable(self) -> bool:
        return self.usage_permission == "allowed" and self.verification_status == "verified"


@dataclass(frozen=True, slots=True)
class KnowledgeObjectImage:
    knowledge_object_id: str
    image_asset_id: str
    role: str = "illustration"
    display_order: int = 0

    def __post_init__(self) -> None:
        for name in ("knowledge_object_id", "image_asset_id", "role"):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name))
        if self.display_order < 0:
            raise ValueError("display_order must be >= 0")
