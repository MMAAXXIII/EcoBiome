from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ecobiome.ui import local_api


class _FakeExplanation:
    def render_text(self) -> str:
        return "Explication technique revue."


class _FakeHumanExplanation:
    canonical_sha256 = "1" * 64

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-human-readable-nitrogen-explanation-v1",
            "title": "Pourquoi ?",
            "introduction": "Introduction.",
            "abstraction_note": "Ne pas additionner les vues.",
            "model_limit": "Pas de RateModel.",
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


def test_resolve_nitrogen_foundation_default(monkeypatch: Any) -> None:
    monkeypatch.delenv(local_api.NITROGEN_SCIENTIFIC_FOUNDATION_ENV, raising=False)
    path = local_api.resolve_nitrogen_scientific_foundation_path()
    assert path.name == "scientific-foundation-v6.sqlite3"
    assert "scientific-foundation-v6" in str(path)


def test_resolve_nitrogen_foundation_override(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    target = tmp_path / "foundation.sqlite3"
    monkeypatch.setenv(local_api.NITROGEN_SCIENTIFIC_FOUNDATION_ENV, str(target))
    assert local_api.resolve_nitrogen_scientific_foundation_path() == (
        target.resolve()
    )


def test_nitrogen_demo_api_payload(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        local_api,
        "build_frozen_g7a_nitrogen_vertical_demonstration_v1",
        lambda _path: _FakeDemonstration(),
    )
    monkeypatch.setattr(
        local_api,
        "build_human_readable_nitrogen_explanation_v1",
        lambda _artifact: _FakeHumanExplanation(),
    )
    payload = local_api._nitrogen_demo_payload(Path("unused.sqlite3"))
    assert payload["status"] == "reviewed_scenario"
    assert payload["artifact_sha256"] == "0" * 64
    assert payload["non_predictive"] is True
    assert payload["technical_explanation"] == "Explication technique revue."
    assert payload["explanation"] == "Explication technique revue."
    human = payload["human_explanation"]
    assert isinstance(human, dict)
    assert human["canonical_sha256"] == "1" * 64
    assert human["title"] == "Pourquoi ?"


def test_nitrogen_demo_payload_rejects_predictive_boundary(
    monkeypatch: Any,
) -> None:
    class _PredictiveFake(_FakeDemonstration):
        def canonical_payload(self) -> dict[str, object]:
            payload = super().canonical_payload()
            payload["model_boundary"] = {
                "extent_is_explicit_input": True,
                "kinetic_or_rate_model_present": True,
                "dt_or_elapsed_time_prediction_present": False,
                "forecast_claim": False,
            }
            return payload

    monkeypatch.setattr(
        local_api,
        "build_frozen_g7a_nitrogen_vertical_demonstration_v1",
        lambda _path: _PredictiveFake(),
    )
    with pytest.raises(RuntimeError, match="non-predictive"):
        local_api._nitrogen_demo_payload(Path("unused.sqlite3"))
