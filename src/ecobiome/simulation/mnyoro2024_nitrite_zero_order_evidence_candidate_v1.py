"""Dormant evidence-only nitrite zero-order candidate from Mnyoro et al. 2024.

RATE-5L deliberately does not implement a RateModelV1, RateParameterV1, or
RateEvaluationV1.  The exact numeric nitrite zero-order constant is preserved
from the associated SSRN preprint, while the peer-reviewed final publication
is represented only as publication-continuity evidence because the exact
numeric value has not been independently verified in the final article body.

This module never evaluates a numerical ecosystem rate, integrates over time,
mutates EcosystemStateV1, invokes MaterialBalance, or authorizes production
use.  Its applicability assessment is an evidence-context fence only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from ecobiome.knowledge_persistence.serialization import (
    canonical_sha256 as canonical_payload_sha256,
)
from ecobiome.knowledge_persistence.serialization import normalize_decimal

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_PROCESS_ID = "nitrite_oxidation_to_nitrate"
_EVIDENCE_CLASS = "associated_preprint_exact_with_peer_reviewed_final_continuity"

_K0V_NO2_G_N_M3_MEDIA_D = Decimal("139")
_PARAMETER_UNIT = "g NO2-N/m3-media/d"
_PARAMETER_BASIS = "media_volume"
_KINETIC_ORDER = "zero_order"

_EXACT_SOURCE_ROLE = "exact_numeric_parameter_source"
_FINAL_SOURCE_ROLE = "peer_reviewed_publication_continuity"
_EXACT_SOURCE_KIND = "associated_preprint"
_FINAL_SOURCE_KIND = "peer_reviewed_final_publication"
_EXACT_SOURCE_ID = "ssrn-4911049"
_EXACT_SOURCE_SHA256 = (
    "2e9af660d0121c9ace5ec469716400458b4994062f7a3ce97a10589e008063e8"
)
_FINAL_DOI = "10.1016/j.jwpe.2024.106549"

_REQUIRED_WATER_TYPE = "freshwater"
_REQUIRED_BIOFILTER_MODE = "fixed_bed_upflow"
_REQUIRED_CARRIER_MEDIA = "15_mm_commercial_polypropylene_plastic_beads"
_REQUIRED_WATER_VELOCITY_M_H = Decimal("12")
_REQUIRED_MEDIA_MATURITY_CONTEXT = (
    "colonized_after_six_week_startup_tested_during_weeks_7_8"
)

_NO2_ZERO_ORDER_THRESHOLD_MG_N_L = Decimal("1.0")
_TEMPERATURE_MIN_C = Decimal("15.0")
_TEMPERATURE_MAX_C = Decimal("16.8")
_DO_MIN_MG_L = Decimal("9.2")
_DO_MAX_MG_L = Decimal("10.8")
_PH_MIN = Decimal("7.0")
_PH_MAX = Decimal("7.4")

_ALKALINITY_REFERENCE_MEAN_MG_L_CACO3 = Decimal("125")
_ALKALINITY_REFERENCE_SD_MG_L_CACO3 = Decimal("8.6")

DecimalInput = str | int | Decimal


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _optional_nonempty(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _nonempty(value, field_name)


def _optional_sha256(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if not _SHA256_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return normalized


def _decimal(value: DecimalInput, field_name: str) -> str:
    try:
        return normalize_decimal(value)
    except (TypeError, ValueError) as exc:
        raise type(exc)(f"{field_name}: {exc}") from exc


def _typed_decimal(value: DecimalInput) -> dict[str, str]:
    return {"type": "decimal", "value": normalize_decimal(value)}


@dataclass(frozen=True, slots=True)
class Mnyoro2024NitriteEvidenceSourceV1:
    """One source identity without promotion to RateScientificSupportV1."""

    role: str
    source_kind: str
    source_id: str
    source_sha256: str | None
    doi: str | None
    peer_reviewed: bool
    exact_parameter_observed: bool
    notes: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _nonempty(self.role, "role"))
        object.__setattr__(
            self,
            "source_kind",
            _nonempty(self.source_kind, "source_kind"),
        )
        object.__setattr__(self, "source_id", _nonempty(self.source_id, "source_id"))
        object.__setattr__(
            self,
            "source_sha256",
            _optional_sha256(self.source_sha256, "source_sha256"),
        )
        object.__setattr__(self, "doi", _optional_nonempty(self.doi, "doi"))
        if not isinstance(self.peer_reviewed, bool):
            raise TypeError("peer_reviewed must be bool")
        if not isinstance(self.exact_parameter_observed, bool):
            raise TypeError("exact_parameter_observed must be bool")
        object.__setattr__(self, "notes", _nonempty(self.notes, "notes"))

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-mnyoro2024-nitrite-evidence-source-v1",
            "role": self.role,
            "source_kind": self.source_kind,
            "source_id": self.source_id,
            "source_sha256": self.source_sha256,
            "doi": self.doi,
            "peer_reviewed": self.peer_reviewed,
            "exact_parameter_observed": self.exact_parameter_observed,
            "notes": self.notes,
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())


@dataclass(frozen=True, slots=True)
class Mnyoro2024NitriteZeroOrderEvidenceBundleV1:
    """Exact two-source evidence structure adopted for RATE-5L."""

    exact_numeric_parameter_source: Mnyoro2024NitriteEvidenceSourceV1
    peer_reviewed_publication_continuity: Mnyoro2024NitriteEvidenceSourceV1

    def __post_init__(self) -> None:
        exact = self.exact_numeric_parameter_source
        final = self.peer_reviewed_publication_continuity

        if exact.role != _EXACT_SOURCE_ROLE:
            raise ValueError(
                "exact numeric source must use role="
                f"{_EXACT_SOURCE_ROLE!r}; got {exact.role!r}"
            )
        if exact.source_kind != _EXACT_SOURCE_KIND:
            raise ValueError("exact numeric source must be the associated preprint")
        if exact.source_id != _EXACT_SOURCE_ID:
            raise ValueError("exact numeric source must be SSRN 4911049")
        if exact.source_sha256 != _EXACT_SOURCE_SHA256:
            raise ValueError(
                "exact numeric source SHA-256 does not match the reviewed RATE-5L "
                "artifact identity"
            )
        if exact.doi is not None:
            raise ValueError("associated preprint source must not impersonate final DOI")
        if exact.peer_reviewed:
            raise ValueError("associated preprint cannot be marked peer reviewed")
        if not exact.exact_parameter_observed:
            raise ValueError(
                "associated preprint must preserve exact_parameter_observed=True"
            )

        if final.role != _FINAL_SOURCE_ROLE:
            raise ValueError(
                "final publication source must use role="
                f"{_FINAL_SOURCE_ROLE!r}; got {final.role!r}"
            )
        if final.source_kind != _FINAL_SOURCE_KIND:
            raise ValueError("final continuity source must be peer-reviewed publication")
        if final.source_id != _FINAL_DOI or final.doi != _FINAL_DOI:
            raise ValueError("final publication continuity DOI mismatch")
        if final.source_sha256 is not None:
            raise ValueError(
                "final publication body has no frozen RATE-5L artifact SHA-256"
            )
        if not final.peer_reviewed:
            raise ValueError("final publication continuity source must be peer reviewed")
        if final.exact_parameter_observed:
            raise ValueError(
                "final publication continuity must not claim direct observation of "
                "the exact 139 parameter"
            )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-mnyoro2024-nitrite-evidence-bundle-v1",
            "exact_numeric_parameter_source": (
                self.exact_numeric_parameter_source.canonical_payload()
            ),
            "peer_reviewed_publication_continuity": (
                self.peer_reviewed_publication_continuity.canonical_payload()
            ),
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())


@dataclass(frozen=True, slots=True)
class Mnyoro2024NitriteZeroOrderCandidateV1:
    """Dormant evidence candidate; deliberately not a numerical RateModel."""

    evidence: Mnyoro2024NitriteZeroOrderEvidenceBundleV1

    @property
    def parameter_decimal(self) -> Decimal:
        return _K0V_NO2_G_N_M3_MEDIA_D

    @property
    def parameter_unit(self) -> str:
        return _PARAMETER_UNIT

    @property
    def parameter_basis(self) -> str:
        return _PARAMETER_BASIS

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": (
                "ecobiome-g7a-rate-5l-mnyoro2024-nitrite-evidence-candidate-v1"
            ),
            "process_id": _PROCESS_ID,
            "candidate_parameter": {
                "value": _typed_decimal(_K0V_NO2_G_N_M3_MEDIA_D),
                "unit": _PARAMETER_UNIT,
                "basis": _PARAMETER_BASIS,
                "kinetic_order": _KINETIC_ORDER,
            },
            "evidence_class": _EVIDENCE_CLASS,
            "evidence": self.evidence.canonical_payload(),
            "execution_authorized": False,
            "production_authorized": False,
            "assumptions": [
                "dormant_evidence_only",
                "exact_139_parameter_from_associated_non_peer_reviewed_preprint",
                "peer_reviewed_final_publication_used_for_continuity_only",
                "no_RateScientificSupportV1_promotion",
                "no_RateParameterV1_promotion",
                "no_RateEvaluationV1",
                "no_numeric_ecosystem_rate_evaluation",
                "no_state_binding",
                "no_state_mutation",
                "no_rate_to_extent_integration",
                "no_MaterialBalance",
                "no_production_activation",
            ],
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())


@dataclass(frozen=True, slots=True)
class Mnyoro2024NitriteContextV1:
    """Evidence-context facts for conservative, non-executing applicability checks."""

    water_type: str
    biofilter_mode: str
    carrier_media: str
    water_velocity_m_h: DecimalInput
    nitrite_n_mg_l: DecimalInput
    temperature_c: DecimalInput
    dissolved_oxygen_mg_l: DecimalInput
    ph: DecimalInput
    media_maturity_context: str

    def __post_init__(self) -> None:
        for field_name in (
            "water_type",
            "biofilter_mode",
            "carrier_media",
            "media_maturity_context",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonempty(str(getattr(self, field_name)), field_name),
            )
        for field_name in (
            "water_velocity_m_h",
            "nitrite_n_mg_l",
            "temperature_c",
            "dissolved_oxygen_mg_l",
            "ph",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal(getattr(self, field_name), field_name),
            )

        if Decimal(self.water_velocity_m_h) <= 0:
            raise ValueError("water_velocity_m_h must be positive")
        if Decimal(self.nitrite_n_mg_l) < 0:
            raise ValueError("nitrite_n_mg_l cannot be negative")
        if Decimal(self.dissolved_oxygen_mg_l) < 0:
            raise ValueError("dissolved_oxygen_mg_l cannot be negative")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-mnyoro2024-nitrite-context-v1",
            "water_type": self.water_type,
            "biofilter_mode": self.biofilter_mode,
            "carrier_media": self.carrier_media,
            "water_velocity_m_h": _typed_decimal(self.water_velocity_m_h),
            "nitrite_n_mg_l": _typed_decimal(self.nitrite_n_mg_l),
            "temperature_c": _typed_decimal(self.temperature_c),
            "dissolved_oxygen_mg_l": _typed_decimal(self.dissolved_oxygen_mg_l),
            "ph": _typed_decimal(self.ph),
            "media_maturity_context": self.media_maturity_context,
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())


@dataclass(frozen=True, slots=True)
class Mnyoro2024NitriteApplicabilityV1:
    """Evidence-context assessment, intentionally distinct from RateApplicabilityResultV1."""

    status: str
    blocking_reason_codes: tuple[str, ...] = ()
    contextual_notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        status = _nonempty(self.status, "status").lower()
        if status not in {"within_evidence_context", "outside_evidence_context"}:
            raise ValueError(f"unsupported evidence-context status: {self.status!r}")
        object.__setattr__(self, "status", status)

        reasons = tuple(
            _nonempty(item, "blocking_reason_codes")
            for item in self.blocking_reason_codes
        )
        notes = tuple(_nonempty(item, "contextual_notes") for item in self.contextual_notes)
        if status == "within_evidence_context" and reasons:
            raise ValueError("within_evidence_context cannot have blocking reasons")
        if status == "outside_evidence_context" and not reasons:
            raise ValueError("outside_evidence_context requires blocking reasons")
        object.__setattr__(self, "blocking_reason_codes", tuple(sorted(set(reasons))))
        object.__setattr__(self, "contextual_notes", notes)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-mnyoro2024-nitrite-applicability-v1",
            "status": self.status,
            "blocking_reason_codes": list(self.blocking_reason_codes),
            "contextual_notes": list(self.contextual_notes),
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())


def _study_context_notes() -> tuple[str, ...]:
    return (
        "temperature, dissolved-oxygen, and pH fences preserve the reported "
        "study-level RAS envelope; they are not biological tolerance claims",
        "experimental alkalinity reference mean=125 mg/L as CaCO3, SD=8.6; "
        "RATE-5L deliberately defines no alkalinity hard guard",
        "the exact 139 g NO2-N/m3-media/d parameter is preserved from the "
        "associated non-peer-reviewed preprint; the peer-reviewed final "
        "publication establishes continuity only",
    )


def assess_mnyoro2024_nitrite_evidence_context_v1(
    context: Mnyoro2024NitriteContextV1,
) -> Mnyoro2024NitriteApplicabilityV1:
    """Assess source-context compatibility without calculating any ecosystem rate."""

    reasons: list[str] = []

    if context.water_type != _REQUIRED_WATER_TYPE:
        reasons.append("water_type_outside_evidence_context")
    if context.biofilter_mode != _REQUIRED_BIOFILTER_MODE:
        reasons.append("biofilter_mode_outside_evidence_context")
    if context.carrier_media != _REQUIRED_CARRIER_MEDIA:
        reasons.append("carrier_media_outside_evidence_context")
    if context.media_maturity_context != _REQUIRED_MEDIA_MATURITY_CONTEXT:
        reasons.append("media_maturity_context_outside_evidence_context")

    velocity = Decimal(context.water_velocity_m_h)
    if velocity != _REQUIRED_WATER_VELOCITY_M_H:
        reasons.append("water_velocity_outside_exact_study_value")

    nitrite = Decimal(context.nitrite_n_mg_l)
    if nitrite <= _NO2_ZERO_ORDER_THRESHOLD_MG_N_L:
        reasons.append("nitrite_not_above_zero_order_threshold")

    temperature = Decimal(context.temperature_c)
    if temperature < _TEMPERATURE_MIN_C or temperature > _TEMPERATURE_MAX_C:
        reasons.append("temperature_outside_reported_study_envelope")

    dissolved_oxygen = Decimal(context.dissolved_oxygen_mg_l)
    if dissolved_oxygen < _DO_MIN_MG_L or dissolved_oxygen > _DO_MAX_MG_L:
        reasons.append("dissolved_oxygen_outside_reported_study_envelope")

    ph = Decimal(context.ph)
    if ph < _PH_MIN or ph > _PH_MAX:
        reasons.append("ph_outside_reported_study_envelope")

    status = "outside_evidence_context" if reasons else "within_evidence_context"
    return Mnyoro2024NitriteApplicabilityV1(
        status=status,
        blocking_reason_codes=tuple(reasons),
        contextual_notes=_study_context_notes(),
    )
