from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_physicochemical_labels_keep_symbols_and_units_visible() -> None:
    types = read("bolt-dashboard/src/lib/types.ts")

    expected = (
        "Température (T)",
        "pH — potentiel hydrogène",
        "Oxygène dissous (O₂)",
        "Nitrites (NO₂⁻)",
        "Nitrates (NO₃⁻)",
        "Ammoniac / ammonium (NH₃ / NH₄⁺)",
        "TAN = NH₃-N + NH₄⁺-N",
        "Chlorures (Cl⁻)",
        "Calcium (Ca²⁺)",
        "Magnésium (Mg²⁺)",
        "Phosphates (PO₄³⁻)",
        "Conductivité électrique (κ)",
        "Potentiel d’oxydoréduction (ORP / Eh)",
        "PAR / PPFD — surface",
    )
    for label in expected:
        assert label in types


def test_scientific_glossary_contains_definitions_equations_and_sources() -> None:
    glossary = read("bolt-dashboard/src/lib/scientificGlossary.ts")

    assert "pH = −log₁₀(aH⁺)" in glossary
    assert (
        "Cs(T) = 14,64 − 0,4227T + 0,009937T² − "
        "0,0001575T³ + 0,000001125T⁴"
    ) in glossary
    assert "Sat O₂ (%) = O₂mesuré × 100 / Cs(T)" in glossary
    assert "pKa = 0,09018 + 2729,92 / T(K)" in glossary
    assert "fNH₃ = 1 / (10^(pKa − pH) + 1)" in glossary

    assert "1013 mbar et salinité nulle" in glossary
    assert "'température'" in glossary
    assert "'pression atmosphérique'" in glossary
    assert "'salinité'" in glossary
    assert "KH et alcalinité ne doivent pas être traités comme synonymes exacts" in glossary
    assert "https://mdm.sandre.eaufrance.fr/node/414781" in glossary
    assert "https://goldbook.iupac.org/terms/view/P04524" in glossary
    assert "https://doi.org/10.1139/f75-274" in glossary
    assert "https://www.usgs.gov/tools/dotables" in glossary


def test_glossary_is_reachable_from_main_navigation() -> None:
    app = read("bolt-dashboard/src/App.tsx")
    nav = read("bolt-dashboard/src/lib/nav.ts")
    view = read("bolt-dashboard/src/views/ScientificGlossaryView.tsx")

    assert "ScientificGlossaryView" in app
    assert "activeView === 'glossary'" in app
    assert "| 'glossary'" in nav
    assert "Lexique scientifique" in nav
    assert "Rechercher : oxygène, NH₃, KH, nitrification, PAR…" in view
    assert "Définition" in view
    assert "À quoi ça sert ?" in view
    assert "Relations et calculs" in view
    assert "Points d’attention" in view
    assert "Sources" in view


def test_water_source_form_uses_explicit_chemical_symbols() -> None:
    panel = read("bolt-dashboard/src/views/EcosystemInputsPanel.tsx")

    expected = (
        "Température (T) °C",
        "pH — potentiel hydrogène",
        "KH (HCO₃⁻ / CO₃²⁻) °dKH",
        "GH (Ca²⁺ / Mg²⁺) °dGH",
        "Nitrates (NO₃⁻) mg/L",
        "Nitrites (NO₂⁻) mg/L",
        "Ammoniac / ammonium (NH₃ / NH₄⁺) mg/L",
        "Phosphates (PO₄³⁻) mg/L",
        "Chlorures (Cl⁻) mg/L",
        "Calcium (Ca²⁺) mg/L",
        "Magnésium (Mg²⁺) mg/L",
    )
    for label in expected:
        assert label in panel
