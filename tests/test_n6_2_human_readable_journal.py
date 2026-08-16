"""Targeted N6.2 tests for the human-readable scientific journal."""

from __future__ import annotations

from uuid import UUID

from backend.api import (
    AddMeasurementRequest,
    CreateWaterBodyRequest,
    SetFillLevelRequest,
    WaterExchangeRequest,
    add_measurement,
    create_water_body,
    list_journal,
    record_water_exchange,
    set_fill_level,
)


def test_journal_projects_events_as_readable_french_narratives(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("ECOBIOME_LOCAL_DATA_DIR", str(tmp_path / "runtime"))

    created = create_water_body(
        CreateWaterBodyRequest(
            name="Bassin extérieur 250 L",
            type="pond",
            volume_liters=250.0,
        )
    )
    project_id = UUID(str(created["id"]))

    set_fill_level(
        project_id,
        SetFillLevelRequest(fill_percent=90.0),
    )
    add_measurement(
        project_id,
        AddMeasurementRequest(
            metric="temperature",
            value=22.5,
            uncertainty=0.2,
        ),
    )
    record_water_exchange(
        project_id,
        WaterExchangeRequest(
            removed_volume_liters=20.0,
            replacement_volume_liters=20.0,
            note="Entretien hebdomadaire",
        ),
    )

    entries = list_journal()

    assert [entry["title"] for entry in entries] == [
        "Changement d’eau",
        "Mesure de température",
        "Ajustement du niveau d’eau",
        "Mise en eau initiale",
    ]

    exchange = entries[0]
    assert exchange["event_kind"] == "intervention"
    assert exchange["water_body_name"] == "Bassin extérieur 250 L"
    assert "20 L retirés, 20 L ajoutés" in str(exchange["summary"])
    assert "Le volume total est resté à 225 L." in str(exchange["content"])
    assert "Note de l’utilisateur : Entretien hebdomadaire." in str(
        exchange["content"]
    )
    assert "ne déduit pas automatiquement son effet" in str(exchange["content"])

    measurement = entries[1]
    assert measurement["event_kind"] == "observation"
    assert "22,5 °C" in str(measurement["summary"])
    assert "saisie manuellement dans EcoBiome" in str(measurement["content"])

    fill = entries[2]
    assert "225 L" in str(fill["summary"])
    assert "90 % de la capacité" in str(fill["summary"])

    initial = entries[3]
    assert "250 L" in str(initial["summary"])
    assert "100 % de la capacité" in str(initial["summary"])

    for entry in entries:
        content = str(entry["content"])
        assert '"schema_version"' not in content
        technical = str(entry["technical_content"])
        assert '"canonical_event_sha256"' in technical
        assert '"canonical_payload"' in technical
