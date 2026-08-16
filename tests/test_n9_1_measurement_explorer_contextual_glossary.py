"""Contract tests for N9.1 measurement exploration and contextual glossary UX."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_measurement_cards_and_history_offer_add_glossary_and_detail_actions() -> None:
    metric_card = _read("bolt-dashboard/src/components/MetricCard.tsx")
    water_bodies = _read("bolt-dashboard/src/views/WaterBodiesView.tsx")

    assert "onAddMeasurement" in metric_card
    assert "onOpenGlossary" in metric_card
    assert "onOpenDetails" in metric_card
    assert "Ajouter une mesure de ${info.label}" in metric_card
    assert "Ouvrir ${info.label} dans le lexique" in metric_card
    assert ">\n              ?\n            </button>" in metric_card
    assert "Voir l’évolution détaillée" in metric_card

    assert "onOpenGlossaryForMetric" in water_bodies
    assert "openMeasurementFormForMetric" in water_bodies
    assert "initialMetric={measurementMetric}" in water_bodies
    assert "valueInputRef.current?.focus()" in water_bodies
    assert "setSelectedMetricDetail" in water_bodies
    assert "<th className=\"text-right p-3 font-medium\">Actions</th>" in water_bodies
    assert "MeasurementExplorerView" in water_bodies


def test_contextual_glossary_deep_link_opens_the_matching_entry() -> None:
    app = _read("bolt-dashboard/src/App.tsx")
    glossary_view = _read("bolt-dashboard/src/views/ScientificGlossaryView.tsx")
    glossary = _read("bolt-dashboard/src/lib/scientificGlossary.ts")

    assert "getGlossaryEntryForMetric" in app
    assert "navigateToGlossaryMetric" in app
    assert "initialEntryId={glossaryEntryId}" in app
    assert "setActiveView('glossary')" in app

    assert "initialEntryId" in glossary_view
    assert "setOpenId(initialEntryId)" in glossary_view
    assert "scrollIntoView" in glossary_view
    assert "id={`glossary-${entry.id}`}" in glossary_view

    assert "id: 'iron'" in glossary
    assert "metric: 'iron'" in glossary
    assert "id: 'algae_coverage'" in glossary
    assert "metric: 'algae_coverage'" in glossary
    assert "par_bottom: 'par'" in glossary


def test_measurement_explorer_supports_periods_and_one_comparison_series() -> None:
    explorer = _read("bolt-dashboard/src/views/MeasurementExplorerView.tsx")

    for label in ("7 jours", "1 mois", "3 mois", "1 an", "Tout"):
        assert label in explorer
    assert "Comparer avec" in explorer
    assert "Aucune superposition" in explorer
    assert "primaryMetric" in explorer
    assert "comparisonMetric" in explorer
    assert "axe gauche" in explorer
    assert "axe droit" in explorer
    assert "sharedScale" in explorer
    assert "onAddMeasurement" in explorer
    assert "Ajouter une mesure" in explorer


def test_chart_is_history_only_and_does_not_claim_causality() -> None:
    explorer = _read("bolt-dashboard/src/views/MeasurementExplorerView.tsx")

    assert "Les points proviennent uniquement de mesures réellement enregistrées" in explorer
    assert "ne démontre pas une relation causale" in explorer
    assert "filterMeasurementsByRange" in explorer
    assert "buildMetricSeries" in explorer
    assert "summarizeSeries" in explorer
    assert "fetch(" not in explorer
    assert "addMeasurement(" not in explorer
