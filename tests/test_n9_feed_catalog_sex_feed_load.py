"""Targeted N9 tests for feed products, sex structure and feed-load accounting."""
from __future__ import annotations

from uuid import UUID

import pytest
from fastapi import HTTPException

from backend.api import (
    AdjustLivestockRequest,
    CreateLivestockRequest,
    CreateWaterBodyRequest,
    FeedingRequest,
    SetLivestockSexRequest,
    add_livestock,
    adjust_livestock,
    get_ecology,
    list_feed_products,
    list_measurements,
    record_feeding,
    set_livestock_sex_distribution,
)
from backend.feed_catalog_n9 import parse_product_html


def _project(tmp_path, monkeypatch) -> UUID:
    monkeypatch.setenv("ECOBIOME_LOCAL_DATA_DIR", str(tmp_path / "runtime"))
    from backend.api import create_water_body

    created = create_water_body(
        CreateWaterBodyRequest(
            name="Bassin N9 250 L",
            type="pond",
            volume_liters=250.0,
        )
    )
    return UUID(str(created["id"]))


def test_starter_feed_catalog_and_feed_load_are_structured(tmp_path, monkeypatch) -> None:
    project_id = _project(tmp_path, monkeypatch)

    products = list_feed_products()
    tetramin = next(item for item in products if item["id"] == "feed-tetra-tetramin-flakes")
    assert tetramin["brand"] == "Tetra"
    assert tetramin["name"] == "TetraMin Flakes"
    assert tetramin["form"] == "flakes"
    assert tetramin["crude_protein_percent"] == 46.0
    assert tetramin["crude_fat_percent"] == 11.0
    assert tetramin["crude_fibre_percent"] == 2.0
    assert tetramin["moisture_percent"] == 7.0
    assert "poissons" in str(tetramin["ingredients_text"]).lower()
    assert "tetra.net" in str(tetramin["manufacturer_url"])

    livestock = add_livestock(
        project_id,
        CreateLivestockRequest(
            common_name="Medaka",
            scientific_name="Oryzias latipes",
            count=12,
            male_count=5,
            female_count=4,
            average_mass_g=1.8,
            life_stage="adulte",
        ),
    )
    assert livestock["male_count"] == 5
    assert livestock["female_count"] == 4
    assert livestock["unknown_sex_count"] == 3
    assert livestock["biomass_g"] == pytest.approx(21.6)

    measurements_before = list_measurements(project_id)
    feeding = record_feeding(
        project_id,
        FeedingRequest(
            feed_product_id="feed-tetra-tetramin-flakes",
            amount_g=1.0,
            target_population_ids=[str(livestock["id"])],
            consumed_percent=100.0,
        ),
    )
    details = feeding["details"]
    assert isinstance(details, dict)
    assert details["food_name"] == "TetraMin Flakes"
    snapshot = details["feed_product_snapshot"]
    assert isinstance(snapshot, dict)
    assert snapshot["crude_protein_percent_decimal"] == "46"

    impact = details["feed_load_estimate"]
    assert isinstance(impact, dict)
    assert float(impact["feed_rate_percent_biomass_decimal"]) == pytest.approx(
        100.0 / 21.6
    )
    assert float(impact["protein_g_decimal"]) == pytest.approx(0.46)
    assert float(impact["fat_g_decimal"]) == pytest.approx(0.11)
    assert float(impact["fibre_g_decimal"]) == pytest.approx(0.02)
    assert float(impact["moisture_g_decimal"]) == pytest.approx(0.07)
    assert float(impact["dry_matter_g_decimal"]) == pytest.approx(0.93)
    assert float(impact["estimated_protein_nitrogen_mg_decimal"]) == pytest.approx(73.6)
    assert float(impact["tan_n_upper_bound_delta_mg_l_decimal"]) == pytest.approx(0.2944)
    assert float(impact["nitrate_as_no3_upper_bound_delta_mg_l_decimal"]) == pytest.approx(
        (73.6 * 62.0 / 14.0) / 250.0
    )
    assert float(impact["nitrification_o2_upper_bound_delta_mg_l_decimal"]) == pytest.approx(
        (73.6 * 4.57) / 250.0
    )
    assert float(
        impact["nitrification_alkalinity_upper_bound_delta_mg_l_caco3_decimal"]
    ) == pytest.approx((73.6 * 7.14) / 250.0)
    assert impact["expected_effect_status"] == (
        "requires_species_feed_digestibility_and_retention_coefficients"
    )

    assert list_measurements(project_id) == measurements_before

    ecology = get_ecology(project_id)
    assert ecology["feeding_event_count"] == 1
    assert len(ecology["feed_products"]) >= 1


def test_livestock_sex_distribution_is_explicit_and_adjustable(tmp_path, monkeypatch) -> None:
    project_id = _project(tmp_path, monkeypatch)
    livestock = add_livestock(
        project_id,
        CreateLivestockRequest(
            common_name="Medaka",
            count=10,
            male_count=3,
            female_count=4,
            average_mass_g=1.5,
        ),
    )
    population_id = str(livestock["id"])

    updated = set_livestock_sex_distribution(
        project_id,
        population_id,
        SetLivestockSexRequest(male_count=4, female_count=5),
    )
    assert updated["count"] == 10
    assert updated["male_count"] == 4
    assert updated["female_count"] == 5
    assert updated["unknown_sex_count"] == 1

    added = adjust_livestock(
        project_id,
        population_id,
        AdjustLivestockRequest(
            delta_count=1,
            reason="addition",
            sex="female",
        ),
    )
    assert added["count"] == 11
    assert added["female_count"] == 6
    assert added["unknown_sex_count"] == 1

    death = adjust_livestock(
        project_id,
        population_id,
        AdjustLivestockRequest(
            delta_count=-1,
            reason="death",
            sex="male",
        ),
    )
    assert death["count"] == 10
    assert death["male_count"] == 3
    assert death["female_count"] == 6
    assert death["unknown_sex_count"] == 1

    with pytest.raises(HTTPException):
        set_livestock_sex_distribution(
            project_id,
            population_id,
            SetLivestockSexRequest(male_count=8, female_count=8),
        )


def test_product_page_parser_extracts_factual_feed_fields() -> None:
    html = """
    <html><body>
      <h1>Tetra Pond Sticks</h1>
      <section>
        <h2>Composition</h2>
        <p>Ingrédients : céréales, extraits de protéines végétales, poisson et sous-produits de poisson, huiles et graisses, minéraux, algues, levures.</p>
        <h3>Constituants analytiques</h3>
        <table>
          <tr><td>protéines brutes</td><td>29.0 %</td></tr>
          <tr><td>matières grasses brutes</td><td>4.0 %</td></tr>
          <tr><td>cellulose brute</td><td>2.0 %</td></tr>
          <tr><td>humidité</td><td>7.0 %</td></tr>
        </table>
        <h3>Quantités recommandées</h3>
        <p>Distribuez de petites quantités adaptées à la consommation des poissons.</p>
        <h3>Avis</h3>
      </section>
    </body></html>
    """
    product = parse_product_html(
        html,
        "https://www.zooplus.fr/shop/poissons/example/77553",
        product_id="feed-test",
    )
    assert product["name"] == "Tetra Pond Sticks"
    assert product["brand"] == "Tetra"
    assert product["form"] == "sticks"
    assert product["dietary_role"] == "unknown"
    assert product["crude_protein_percent_decimal"] == "29"
    assert product["crude_fat_percent_decimal"] == "4"
    assert product["crude_fibre_percent_decimal"] == "2"
    assert product["moisture_percent_decimal"] == "7"
    assert "céréales" in str(product["ingredients_text"])
