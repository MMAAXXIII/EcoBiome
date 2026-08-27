from __future__ import annotations

from pathlib import Path
from typing import Any

from ecobiome.knowledge_persistence.active_foundation_v1 import (
    ResolvedScientificFoundationV1,
)
from ecobiome.reasoning import nitrogen_vertical_runtime_v1 as runtime
from ecobiome.ui import local_api


class _FakeExplanation:
    def render_text(self) -> str:
        return "Technical explanation."


class _FakeHumanExplanation:
    canonical_sha256 = "1" * 64

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "test-human",
            "title": "Why",
            "introduction": "Test",
            "abstraction_note": "Test",
            "model_limit": "No rate model",
            "processes": [],
        }


class _FakeDemonstration:
    canonical_sha256 = "0" * 64
    auditable_explanation = _FakeExplanation()

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "test",
            "demo_id": "fake",
            "model_boundary": {
                "extent_is_explicit_input": True,
                "kinetic_or_rate_model_present": False,
                "dt_or_elapsed_time_prediction_present": False,
                "forecast_claim": False,
            },
        }


def _resolved(
    tmp_path: Path,
) -> ResolvedScientificFoundationV1:
    return ResolvedScientificFoundationV1(
        resolution_mode="active_snapshot",
        database_path=tmp_path / "foundation.sqlite3",
        database_sha256="9" * 64,
        schema_version=6,
        schema_design_sha256=(
            runtime.SCIENTIFIC_FOUNDATION_V6_DESIGN_SHA256
        ),
        snapshot_manifest_path=tmp_path / "snapshot-manifest.json",
        snapshot_manifest_file_sha256="2" * 64,
        snapshot_manifest_payload_sha256="3" * 64,
        pointer_payload_sha256="4" * 64,
        activation_authorization_payload_sha256="5" * 64,
        runtime_policy_payload_sha256="5" * 64,
    )


def test_default_nitrogen_payload_uses_resolver_read_target(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    resolved = _resolved(tmp_path)
    monkeypatch.delenv(
        local_api.NITROGEN_SCIENTIFIC_FOUNDATION_ENV,
        raising=False,
    )
    monkeypatch.setattr(
        local_api,
        "resolve_default_scientific_foundation_v1",
        lambda: resolved,
    )
    monkeypatch.setattr(
        local_api,
        "build_resolved_g7a_nitrogen_vertical_demonstration_v1",
        lambda value: _FakeDemonstration(),
    )
    monkeypatch.setattr(
        local_api,
        "build_human_readable_nitrogen_explanation_v1",
        lambda artifact: _FakeHumanExplanation(),
    )

    payload = local_api._nitrogen_demo_payload()
    assert payload["scientific_foundation_sha256"] == (
        resolved.database_sha256
    )
    assert payload["scientific_foundation_resolution_mode"] == (
        "active_snapshot"
    )
    assert payload["non_predictive"] is True


def test_explicit_legacy_override_does_not_call_active_resolver(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    target = tmp_path / "legacy.sqlite3"
    monkeypatch.setenv(
        local_api.NITROGEN_SCIENTIFIC_FOUNDATION_ENV,
        str(target),
    )

    def fail_if_called() -> object:
        raise AssertionError(
            "active resolver must not be called"
        )

    monkeypatch.setattr(
        local_api,
        "resolve_default_scientific_foundation_v1",
        fail_if_called,
    )
    monkeypatch.setattr(
        local_api,
        "build_frozen_g7a_nitrogen_vertical_demonstration_v1",
        lambda path: _FakeDemonstration(),
    )
    monkeypatch.setattr(
        local_api,
        "build_human_readable_nitrogen_explanation_v1",
        lambda artifact: _FakeHumanExplanation(),
    )

    payload = local_api._nitrogen_demo_payload()
    assert payload["scientific_foundation_sha256"] == (
        runtime.SCIENTIFIC_FOUNDATION_V6_SHA256
    )
    assert payload["scientific_foundation_resolution_mode"] == (
        "explicit_legacy_override"
    )
