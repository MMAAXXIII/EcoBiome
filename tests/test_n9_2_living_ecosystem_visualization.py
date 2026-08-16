"""Contract tests for N9.2 living ecosystem visualization and biological alerts."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_living_tank_species_registry_is_sourced_and_contextual() -> None:
    source = _read("bolt-dashboard/src/lib/livingTank.ts")

    assert "Mikrogeophagus ramirezi" in source
    assert "Oryzias latipes" in source
    assert "FishBase — Mikrogeophagus ramirezi" in source
    assert "FishBase — Oryzias latipes" in source
    assert "plage écologique de référence" in source.lower()
    assert "limite létale universelle" in source.lower()
    assert "evaluateBiologicalAlerts" in source
    assert "temperature >= reference.min" in source
    assert "temperature <= reference.max" in source


def test_feeding_visual_is_transient_and_comes_from_real_feeding_operations() -> None:
    source = _read("bolt-dashboard/src/lib/livingTank.ts")
    tank = _read("bolt-dashboard/src/components/WaterTankViz.tsx")

    assert "operation.operation_type === 'feeding'" in source
    assert "FEED_VISIBILITY_MS = 5 * 60 * 1000" in source
    assert "getRecentFeedingVisual" in source
    assert "amount_g_decimal" in source
    assert "feed_product_snapshot" in source
    assert "FoodParticles" in tank
    assert "Nourrissage récent" in tank
    assert "Nourriture visible temporairement" in tank


def test_tank_exposes_at_a_glance_biological_warning() -> None:
    tank = _read("bolt-dashboard/src/components/WaterTankViz.tsx")

    assert "evaluateBiologicalAlerts" in tank
    assert "Afficher les alertes biologiques" in tank
    assert "alert.title" in tank
    assert "alert.message" in tank
    assert "alert.sourceUrl" in tank
    assert "!" in tank


def test_overview_connects_real_measurements_populations_and_operations() -> None:
    source = _read("bolt-dashboard/src/views/WaterBodiesView.tsx")

    assert "data: ecology" in source
    assert "refetch: refetchEcology" in source
    assert "latestMeasurements={latest}" in source
    assert "livestock={ecology.livestock}" in source
    assert "recentOperations={ecology.recent_operations}" in source
    assert "if (activeTab === 'overview')" in source
    assert "void refetchEcology();" in source


def test_visualization_does_not_create_measurements_or_mutate_scientific_state() -> None:
    tank = _read("bolt-dashboard/src/components/WaterTankViz.tsx")
    living = _read("bolt-dashboard/src/lib/livingTank.ts")

    assert "addMeasurement" not in tank
    assert "fetch(" not in tank
    assert "addMeasurement" not in living
    assert "fetch(" not in living
