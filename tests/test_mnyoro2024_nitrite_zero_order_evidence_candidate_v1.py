from __future__ import annotations

import inspect
import json
from dataclasses import MISSING, fields
from decimal import Decimal
from pathlib import Path

import pytest

from ecobiome.knowledge_persistence.serialization import canonical_sha256
from ecobiome.simulation import mnyoro2024_nitrite_zero_order_evidence_candidate_v1 as module
from ecobiome.simulation.mnyoro2024_nitrite_zero_order_evidence_candidate_v1 import (
    Mnyoro2024NitriteContextV1,
    Mnyoro2024NitriteEvidenceSourceV1,
    Mnyoro2024NitriteZeroOrderCandidateV1,
    Mnyoro2024NitriteZeroOrderEvidenceBundleV1,
    assess_mnyoro2024_nitrite_evidence_context_v1,
)

_FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "rate_models"
    / "mnyoro2024_nitrite_zero_order_evidence_candidate_v1.json"
)


def _payload() -> dict[str, object]:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _source(row: dict[str, object]) -> Mnyoro2024NitriteEvidenceSourceV1:
    return Mnyoro2024NitriteEvidenceSourceV1(
        role=str(row["role"]),
        source_kind=str(row["source_kind"]),
        source_id=str(row["source_id"]),
        source_sha256=(None if row["sha256"] is None else str(row["sha256"])),
        doi=None if row["doi"] is None else str(row["doi"]),
        peer_reviewed=row["peer_reviewed"],
        exact_parameter_observed=row["exact_parameter_observed"],
        notes=str(row["notes"]),
    )


def _bundle() -> Mnyoro2024NitriteZeroOrderEvidenceBundleV1:
    payload = _payload()
    return Mnyoro2024NitriteZeroOrderEvidenceBundleV1(
        exact_numeric_parameter_source=_source(payload["exact_numeric_source"]),
        peer_reviewed_publication_continuity=_source(
            payload["peer_reviewed_continuity_source"]
        ),
    )


def _candidate() -> Mnyoro2024NitriteZeroOrderCandidateV1:
    return Mnyoro2024NitriteZeroOrderCandidateV1(evidence=_bundle())


def _context(**overrides: str) -> Mnyoro2024NitriteContextV1:
    values = {
        "water_type": "freshwater",
        "biofilter_mode": "fixed_bed_upflow",
        "carrier_media": "15_mm_commercial_polypropylene_plastic_beads",
        "water_velocity_m_h": "12",
        "nitrite_n_mg_l": "5",
        "temperature_c": "16.4",
        "dissolved_oxygen_mg_l": "9.9",
        "ph": "7.2",
        "media_maturity_context": (
            "colonized_after_six_week_startup_tested_during_weeks_7_8"
        ),
    }
    values.update(overrides)
    return Mnyoro2024NitriteContextV1(**values)


def test_fixture_preserves_rate5l_epistemic_boundary() -> None:
    payload = _payload()
    assert payload["persistence"] == "dormant_evidence_only"
    assert payload["execution_authorized"] is False
    assert payload["production_authorized"] is False
    assert payload["process_id"] == "nitrite_oxidation_to_nitrate"
    assert payload["candidate_parameter"] == {
        "value": "139",
        "unit": "g NO2-N/m3-media/d",
        "basis": "media_volume",
        "kinetic_order": "zero_order",
    }
    assert payload["epistemic_class"] == (
        "associated_preprint_exact_with_peer_reviewed_final_continuity"
    )


def test_candidate_numeric_parameter_is_not_caller_configurable() -> None:
    assert [item.name for item in fields(Mnyoro2024NitriteZeroOrderCandidateV1)] == [
        "evidence"
    ]
    candidate = _candidate()
    assert candidate.parameter_decimal == Decimal("139")
    assert candidate.parameter_unit == "g NO2-N/m3-media/d"
    assert candidate.parameter_basis == "media_volume"


def test_candidate_payload_is_canonical_and_explicitly_non_executable() -> None:
    candidate = _candidate()
    payload = candidate.canonical_payload()
    assert payload["candidate_parameter"]["value"] == {
        "type": "decimal",
        "value": "139",
    }
    assert payload["execution_authorized"] is False
    assert payload["production_authorized"] is False
    assert candidate.canonical_sha256 == canonical_sha256(payload)
    reversed_payload = dict(reversed(list(payload.items())))
    assert canonical_sha256(reversed_payload) == candidate.canonical_sha256


def test_parameter_value_unit_and_basis_are_identity_bearing() -> None:
    payload = _candidate().canonical_payload()
    original_sha = canonical_sha256(payload)
    for key, value in (
        ("value", {"type": "decimal", "value": "140"}),
        ("unit", "g NO2-N/m2/d"),
        ("basis", "surface_area"),
    ):
        changed = json.loads(json.dumps(payload))
        changed["candidate_parameter"][key] = value
        assert canonical_sha256(changed) != original_sha


def test_exact_source_sha_is_frozen() -> None:
    payload = _payload()
    row = dict(payload["exact_numeric_source"])
    row["sha256"] = "0" * 64
    exact = _source(row)
    with pytest.raises(ValueError, match="source SHA-256"):
        Mnyoro2024NitriteZeroOrderEvidenceBundleV1(
            exact_numeric_parameter_source=exact,
            peer_reviewed_publication_continuity=(
                _bundle().peer_reviewed_publication_continuity
            ),
        )


def test_final_doi_is_frozen() -> None:
    payload = _payload()
    row = dict(payload["peer_reviewed_continuity_source"])
    row["source_id"] = "10.0000/not-the-reviewed-doi"
    row["doi"] = "10.0000/not-the-reviewed-doi"
    final = _source(row)
    with pytest.raises(ValueError, match="DOI mismatch"):
        Mnyoro2024NitriteZeroOrderEvidenceBundleV1(
            exact_numeric_parameter_source=_bundle().exact_numeric_parameter_source,
            peer_reviewed_publication_continuity=final,
        )


def test_preprint_cannot_be_promoted_to_peer_reviewed() -> None:
    payload = _payload()
    row = dict(payload["exact_numeric_source"])
    row["peer_reviewed"] = True
    with pytest.raises(ValueError, match="cannot be marked peer reviewed"):
        Mnyoro2024NitriteZeroOrderEvidenceBundleV1(
            exact_numeric_parameter_source=_source(row),
            peer_reviewed_publication_continuity=(
                _bundle().peer_reviewed_publication_continuity
            ),
        )


def test_preprint_must_preserve_exact_parameter_observation() -> None:
    payload = _payload()
    row = dict(payload["exact_numeric_source"])
    row["exact_parameter_observed"] = False
    with pytest.raises(ValueError, match="exact_parameter_observed=True"):
        Mnyoro2024NitriteZeroOrderEvidenceBundleV1(
            exact_numeric_parameter_source=_source(row),
            peer_reviewed_publication_continuity=(
                _bundle().peer_reviewed_publication_continuity
            ),
        )


def test_final_publication_cannot_claim_unverified_exact_parameter() -> None:
    payload = _payload()
    row = dict(payload["peer_reviewed_continuity_source"])
    row["exact_parameter_observed"] = True
    with pytest.raises(ValueError, match="must not claim direct observation"):
        Mnyoro2024NitriteZeroOrderEvidenceBundleV1(
            exact_numeric_parameter_source=_bundle().exact_numeric_parameter_source,
            peer_reviewed_publication_continuity=_source(row),
        )


def test_context_has_no_hidden_defaults() -> None:
    for item in fields(Mnyoro2024NitriteContextV1):
        assert item.default is MISSING
        assert item.default_factory is MISSING


def test_baseline_context_is_within_evidence_context() -> None:
    result = assess_mnyoro2024_nitrite_evidence_context_v1(_context())
    assert result.status == "within_evidence_context"
    assert result.blocking_reason_codes == ()
    assert any("alkalinity" in note for note in result.contextual_notes)
    assert any("no alkalinity hard guard" in note for note in result.contextual_notes)


@pytest.mark.parametrize(
    ("nitrite", "expected_status"),
    [
        ("1.000001", "within_evidence_context"),
        ("1.0", "outside_evidence_context"),
        ("0.999999", "outside_evidence_context"),
        ("0", "outside_evidence_context"),
    ],
)
def test_zero_order_threshold_is_strict(nitrite: str, expected_status: str) -> None:
    result = assess_mnyoro2024_nitrite_evidence_context_v1(
        _context(nitrite_n_mg_l=nitrite)
    )
    assert result.status == expected_status
    if expected_status == "outside_evidence_context":
        assert "nitrite_not_above_zero_order_threshold" in result.blocking_reason_codes


def test_negative_nitrite_is_invalid_context() -> None:
    with pytest.raises(ValueError, match="nitrite_n_mg_l cannot be negative"):
        _context(nitrite_n_mg_l="-0.1")


@pytest.mark.parametrize("velocity", ["11.999", "12.001", "10.8", "16.2"])
def test_water_velocity_is_exact_study_value(velocity: str) -> None:
    result = assess_mnyoro2024_nitrite_evidence_context_v1(
        _context(water_velocity_m_h=velocity)
    )
    assert result.status == "outside_evidence_context"
    assert "water_velocity_outside_exact_study_value" in result.blocking_reason_codes


def test_exact_12_m_h_water_velocity_is_accepted() -> None:
    result = assess_mnyoro2024_nitrite_evidence_context_v1(
        _context(water_velocity_m_h="12")
    )
    assert result.status == "within_evidence_context"


@pytest.mark.parametrize(
    (
        "field_name",
        "inside_low",
        "inside_high",
        "outside_low",
        "outside_high",
        "reason",
    ),
    [
        (
            "temperature_c",
            "15.0",
            "16.8",
            "14.999",
            "16.801",
            "temperature_outside_reported_study_envelope",
        ),
        (
            "dissolved_oxygen_mg_l",
            "9.2",
            "10.8",
            "9.199",
            "10.801",
            "dissolved_oxygen_outside_reported_study_envelope",
        ),
        (
            "ph",
            "7.0",
            "7.4",
            "6.999",
            "7.401",
            "ph_outside_reported_study_envelope",
        ),
    ],
)
def test_environmental_study_envelopes_are_inclusive_and_fail_closed(
    field_name: str,
    inside_low: str,
    inside_high: str,
    outside_low: str,
    outside_high: str,
    reason: str,
) -> None:
    for value in (inside_low, inside_high):
        result = assess_mnyoro2024_nitrite_evidence_context_v1(
            _context(**{field_name: value})
        )
        assert result.status == "within_evidence_context"
    for value in (outside_low, outside_high):
        result = assess_mnyoro2024_nitrite_evidence_context_v1(
            _context(**{field_name: value})
        )
        assert result.status == "outside_evidence_context"
        assert reason in result.blocking_reason_codes


@pytest.mark.parametrize(
    ("field_name", "value", "reason"),
    [
        ("water_type", "marine", "water_type_outside_evidence_context"),
        ("biofilter_mode", "moving_bed", "biofilter_mode_outside_evidence_context"),
        (
            "carrier_media",
            "RK_Bioelements_Heavy",
            "carrier_media_outside_evidence_context",
        ),
        (
            "carrier_media",
            "generic_polypropylene_media",
            "carrier_media_outside_evidence_context",
        ),
        (
            "carrier_media",
            "polyurethane_foam",
            "carrier_media_outside_evidence_context",
        ),
        (
            "media_maturity_context",
            "mature_unspecified",
            "media_maturity_context_outside_evidence_context",
        ),
    ],
)
def test_reactor_media_and_maturity_are_not_generalized(
    field_name: str,
    value: str,
    reason: str,
) -> None:
    result = assess_mnyoro2024_nitrite_evidence_context_v1(
        _context(**{field_name: value})
    )
    assert result.status == "outside_evidence_context"
    assert reason in result.blocking_reason_codes


def test_rk_bioelements_heavy_is_explicitly_not_substituted_for_source_media() -> None:
    payload = _payload()
    assert payload["evidence_context"]["carrier_media"] == (
        "15_mm_commercial_polypropylene_plastic_beads"
    )
    encoded = json.dumps(payload, sort_keys=True)
    assert "RK Bioelements Heavy" not in encoded


def test_candidate_payload_contains_no_execution_or_integration_surface() -> None:
    payload = _candidate().canonical_payload()
    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "material_balance",
        "output_state",
        '"dt"',
        '"duration"',
        "elapsed_time",
        "time_step",
        "timestep",
        "rate_decimal",
        '"extent"',
    ):
        assert forbidden not in encoded


def test_module_exposes_no_rate_evaluation_callable() -> None:
    forbidden = []
    for name, value in vars(module).items():
        if inspect.isfunction(value) and name.startswith("evaluate_"):
            forbidden.append(name)
    assert forbidden == []


def test_candidate_does_not_import_generic_rate_model_contracts() -> None:
    source = inspect.getsource(module)
    for forbidden in (
        "RateScientificSupportV1",
        "RateParameterV1",
        "RateModelDefinitionV1",
        "RateEvaluationV1",
        "EcosystemStateV1",
        "MaterialBalance",
    ):
        assert f"import {forbidden}" not in source
        assert f"from ecobiome.simulation.rate_model_v1 import {forbidden}" not in source
