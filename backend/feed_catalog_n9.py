"""N9 structured fish-feed catalog and conservative feed-load calculations."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ecobiome.knowledge_persistence.serialization import (
    canonical_json_text,
    canonical_sha256,
    normalize_decimal,
)

FEED_CATALOG_SCHEMA_V1 = "ecobiome-feed-catalog-v1"
FEED_PRODUCT_SCHEMA_V1 = "ecobiome-feed-product-v1"
FEED_LOAD_METHOD_V1 = "ecobiome-feed-load-stoichiometric-v1"

_MAX_HTML_BYTES = 2_000_000
_MAX_REDIRECTS = 3
_TRUSTED_FEED_HOSTS = frozenset(
    {
        "zooplus.fr",
        "www.zooplus.fr",
        "tetra.net",
        "www.tetra.net",
    }
)

_ANALYTICAL_LABELS = {
    "crude_protein_percent_decimal": (
        "protéines brutes",
        "proteines brutes",
        "crude protein",
    ),
    "crude_fat_percent_decimal": (
        "matières grasses brutes",
        "matieres grasses brutes",
        "crude fat",
        "oils and fats",
    ),
    "crude_fibre_percent_decimal": (
        "cellulose brute",
        "fibres brutes",
        "fibres alimentaires",
        "crude fibre",
        "crude fiber",
    ),
    "moisture_percent_decimal": (
        "humidité",
        "humidite",
        "moisture",
        "moisture content",
    ),
    "crude_ash_percent_decimal": (
        "cendres brutes",
        "crude ash",
        "ash",
    ),
    "phosphorus_percent_decimal": (
        "phosphore",
        "phosphorus",
    ),
}

_FORM_KEYWORDS = (
    ("flakes", ("flocon", "flakes")),
    ("micro_granules", ("micro gran", "microgran")),
    ("granules", ("granul", "granules")),
    ("pellets", ("pellet",)),
    ("sticks", ("stick", "bâtonnet", "batonnet")),
    ("tablets", ("comprim", "tablet")),
    ("wafers", ("wafer", "disque")),
    ("chips", ("chips",)),
    ("powder", ("poudre", "powder")),
    ("gel", ("gelée", "gelee", "gel ")),
    ("freeze_dried", ("lyophilis", "freeze-dried", "freeze dried")),
    ("frozen", ("congel", "frozen")),
    ("live", ("vivant", "live food")),
)


def _catalog_path(runtime_root: Path) -> Path:
    return runtime_root / "catalog" / "feed_products.json"


def _starter_tetramin() -> dict[str, object]:
    product: dict[str, object] = {
        "schema_version": FEED_PRODUCT_SCHEMA_V1,
        "id": "feed-tetra-tetramin-flakes",
        "revision": 1,
        "brand": "Tetra",
        "name": "TetraMin Flakes",
        "variant": "1 000 mL",
        "feed_category": "prepared_dry",
        "form": "flakes",
        "dietary_role": "complete",
        "target_species_text": "poissons d’ornement; aquarium communautaire",
        "feeding_zone": "surface_to_midwater",
        "ingredients_text": (
            "poissons et sous-produits de poissons, céréales, extraits de protéines "
            "végétales, levures, huiles et graisses, sous-produits d’origine végétale, "
            "mollusques et crustacés, algues, minéraux"
        ),
        "crude_protein_percent_decimal": "46",
        "crude_fat_percent_decimal": "11",
        "crude_fibre_percent_decimal": "2",
        "moisture_percent_decimal": "7",
        "crude_ash_percent_decimal": None,
        "phosphorus_percent_decimal": None,
        "energy_kj_kg_decimal": None,
        "additives_text": "vitamine D3 1848 IU/kg; acide citrique 293 mg/kg",
        "feeding_guide_text": (
            "Aliment complet quotidien; distribuer une quantité adaptée à la consommation "
            "des poissons."
        ),
        "package_mass_g_decimal": None,
        "package_volume_ml_decimal": "1000",
        "source_url": (
            "https://www.zooplus.fr/shop/poissons/type_nourriture_poissons/"
            "nourriture_flocons_poissons/flocons_tetra/15277?activeVariant=15277.2"
        ),
        "manufacturer_url": "https://www.tetra.net/en-eu/products/tetramin-flakes",
        "source_kind": "manufacturer_plus_retailer",
        "source_observed_at": "2026-08-16T00:00:00+00:00",
        "commercial_price_decimal": None,
        "commercial_currency": "",
        "notes": (
            "Starter catalog entry grounded in the manufacturer analytical constituents. "
            "Commercial price is intentionally not frozen into the scientific identity."
        ),
    }
    product["product_sha256"] = _product_sha(product)
    return product


def _product_sha(product: dict[str, object]) -> str:
    payload = {
        key: value
        for key, value in product.items()
        if key not in {
            "product_sha256",
            "source_content_sha256",
            "commercial_price_decimal",
            "commercial_currency",
        }
    }
    return canonical_sha256(payload)


def load_catalog(runtime_root: Path) -> list[dict[str, object]]:
    path = _catalog_path(runtime_root)
    if not path.exists():
        return [_starter_tetramin()]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("feed catalog must be a JSON object")
    if payload.get("schema_version") != FEED_CATALOG_SCHEMA_V1:
        raise ValueError("unsupported feed catalog schema")
    products = payload.get("products")
    if not isinstance(products, list):
        raise TypeError("feed catalog products must be an array")
    result: list[dict[str, object]] = []
    for item in products:
        if not isinstance(item, dict):
            raise TypeError("feed catalog product must be an object")
        product = cast(dict[str, object], item)
        supplied_sha = product.get("product_sha256")
        if not isinstance(supplied_sha, str) or supplied_sha != _product_sha(product):
            raise ValueError("feed catalog product SHA-256 mismatch")
        result.append(product)
    if not any(item.get("id") == "feed-tetra-tetramin-flakes" for item in result):
        result.insert(0, _starter_tetramin())
    return result


def save_catalog(runtime_root: Path, products: list[dict[str, object]]) -> None:
    for product in products:
        supplied_sha = product.get("product_sha256")
        if not isinstance(supplied_sha, str) or supplied_sha != _product_sha(product):
            raise ValueError("refusing to persist a feed product with invalid SHA-256")
    path = _catalog_path(runtime_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": FEED_CATALOG_SCHEMA_V1,
        "products": products,
    }
    text = canonical_json_text(payload) + "\n"
    temp = path.with_suffix(".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def _decimal_or_none(value: object) -> float | None:
    if isinstance(value, str):
        return float(value)
    return None


def public_product(product: dict[str, object]) -> dict[str, object]:
    result = dict(product)
    for key in (
        "crude_protein_percent_decimal",
        "crude_fat_percent_decimal",
        "crude_fibre_percent_decimal",
        "moisture_percent_decimal",
        "crude_ash_percent_decimal",
        "phosphorus_percent_decimal",
        "energy_kj_kg_decimal",
        "package_mass_g_decimal",
        "package_volume_ml_decimal",
        "commercial_price_decimal",
    ):
        public_key = key.removesuffix("_decimal")
        result[public_key] = _decimal_or_none(product.get(key))
        result.pop(key, None)
    return result


def create_manual_product(
    *,
    product_id: str,
    brand: str,
    name: str,
    variant: str,
    feed_category: str,
    form: str,
    dietary_role: str,
    target_species_text: str,
    feeding_zone: str,
    ingredients_text: str,
    crude_protein_percent: float | None,
    crude_fat_percent: float | None,
    crude_fibre_percent: float | None,
    moisture_percent: float | None,
    crude_ash_percent: float | None,
    phosphorus_percent: float | None,
    additives_text: str,
    feeding_guide_text: str,
    source_url: str,
    notes: str,
) -> dict[str, object]:
    product: dict[str, object] = {
        "schema_version": FEED_PRODUCT_SCHEMA_V1,
        "id": product_id,
        "revision": 1,
        "brand": brand.strip(),
        "name": name.strip(),
        "variant": variant.strip(),
        "feed_category": feed_category.strip() or "other",
        "form": form.strip() or "other",
        "dietary_role": dietary_role.strip() or "unknown",
        "target_species_text": target_species_text.strip(),
        "feeding_zone": feeding_zone.strip() or "unknown",
        "ingredients_text": ingredients_text.strip(),
        "crude_protein_percent_decimal": (
            normalize_decimal(str(crude_protein_percent))
            if crude_protein_percent is not None
            else None
        ),
        "crude_fat_percent_decimal": (
            normalize_decimal(str(crude_fat_percent))
            if crude_fat_percent is not None
            else None
        ),
        "crude_fibre_percent_decimal": (
            normalize_decimal(str(crude_fibre_percent))
            if crude_fibre_percent is not None
            else None
        ),
        "moisture_percent_decimal": (
            normalize_decimal(str(moisture_percent))
            if moisture_percent is not None
            else None
        ),
        "crude_ash_percent_decimal": (
            normalize_decimal(str(crude_ash_percent))
            if crude_ash_percent is not None
            else None
        ),
        "phosphorus_percent_decimal": (
            normalize_decimal(str(phosphorus_percent))
            if phosphorus_percent is not None
            else None
        ),
        "energy_kj_kg_decimal": None,
        "additives_text": additives_text.strip(),
        "feeding_guide_text": feeding_guide_text.strip(),
        "package_mass_g_decimal": None,
        "package_volume_ml_decimal": None,
        "source_url": source_url.strip(),
        "manufacturer_url": "",
        "source_kind": "manual",
        "source_observed_at": datetime.now(UTC).isoformat(),
        "commercial_price_decimal": None,
        "commercial_currency": "",
        "notes": notes.strip(),
    }
    product["product_sha256"] = _product_sha(product)
    return product


def _validate_import_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        raise ValueError("feed product import requires an https URL")
    host = (parsed.hostname or "").lower()
    if host not in _TRUSTED_FEED_HOSTS:
        raise ValueError(
            "unsupported feed source host; N9 V1 accepts zooplus.fr and tetra.net"
        )
    if parsed.username or parsed.password:
        raise ValueError("credentials in feed product URLs are forbidden")
    return parsed.geturl()


def fetch_trusted_product_html(url: str) -> tuple[str, str]:
    current = _validate_import_url(url)
    headers = {
        "User-Agent": "EcoBiome/0.1 feed-product-import (+local scientific catalog)"
    }
    for _ in range(_MAX_REDIRECTS + 1):
        response = requests.get(
            current,
            headers=headers,
            timeout=(4.0, 12.0),
            stream=True,
            allow_redirects=False,
        )
        if response.status_code in {301, 302, 303, 307, 308}:
            location = response.headers.get("Location")
            if not location:
                raise ValueError("feed source redirect is missing Location")
            current = _validate_import_url(urljoin(current, location))
            continue
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type.lower():
            raise ValueError("feed source must return text/html")
        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_content(chunk_size=65536):
            if not chunk:
                continue
            total += len(chunk)
            if total > _MAX_HTML_BYTES:
                raise ValueError("feed source HTML exceeds 2 MB safety limit")
            chunks.append(chunk)
        encoding = response.encoding or "utf-8"
        return b"".join(chunks).decode(encoding, errors="replace"), current
    raise ValueError("too many feed source redirects")


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _jsonld_product(soup: BeautifulSoup) -> dict[str, object]:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        candidates = payload if isinstance(payload, list) else [payload]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            if candidate.get("@type") == "Product":
                return cast(dict[str, object], candidate)
            graph = candidate.get("@graph")
            if isinstance(graph, list):
                for item in graph:
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        return cast(dict[str, object], item)
    return {}


def _percent_from_text(text: str, labels: tuple[str, ...]) -> str | None:
    for label in labels:
        pattern = (
            re.escape(label)
            + r"\s*(?:[:|]\s*)?"
            + r"([0-9]+(?:[.,][0-9]+)?)\s*%"
        )
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return normalize_decimal(match.group(1).replace(",", "."))
    return None


def _infer_form(text: str) -> str:
    lowered = text.lower()
    for form, needles in _FORM_KEYWORDS:
        if any(needle in lowered for needle in needles):
            return form
    return "other"


def parse_product_html(
    html: str,
    source_url: str,
    *,
    product_id: str,
) -> dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")
    text = _normalize_text(soup.get_text(" ", strip=True))
    structured = _jsonld_product(soup)

    h1 = soup.find("h1")
    name = _normalize_text(h1.get_text(" ", strip=True)) if h1 else ""
    if not name:
        structured_name = structured.get("name")
        if isinstance(structured_name, str):
            name = structured_name.strip()
    if not name:
        raise ValueError("could not identify feed product name")

    brand = ""
    structured_brand = structured.get("brand")
    if isinstance(structured_brand, dict):
        brand_name = structured_brand.get("name")
        if isinstance(brand_name, str):
            brand = brand_name.strip()
    elif isinstance(structured_brand, str):
        brand = structured_brand.strip()
    if not brand:
        first = name.split(maxsplit=1)[0]
        if first.lower() in {"tetra", "sera", "jbl", "tropical"}:
            brand = first

    ingredients = ""
    ingredients_match = re.search(
        r"(?:Ingrédients|Ingredients)\s*:?\s*(.*?)\s*"
        r"(?:Constituants analytiques|Analytical constituents|Quantités recommandées|Feeding recommendation|Avis)",
        text,
        flags=re.IGNORECASE,
    )
    if ingredients_match:
        ingredients = _normalize_text(ingredients_match.group(1))

    feeding_guide = ""
    feeding_match = re.search(
        r"(?:Quantités recommandées|Feeding recommendation)\s*:?\s*(.*?)\s*"
        r"(?:Avis|Reviews|Dimensions|$)",
        text,
        flags=re.IGNORECASE,
    )
    if feeding_match:
        feeding_guide = _normalize_text(feeding_match.group(1))[:1200]

    analytics = {
        key: _percent_from_text(text, labels)
        for key, labels in _ANALYTICAL_LABELS.items()
    }

    form = _infer_form(f"{name} {text[:5000]}")
    dietary_role = (
        "complete"
        if re.search(r"\baliment complet\b|\bcomplete feed\b", text, re.IGNORECASE)
        else "unknown"
    )
    feeding_zone = "unknown"
    lowered = text.lower()
    if "flott" in lowered or "float" in lowered:
        feeding_zone = "surface"
    if ("coule" in lowered or "sink" in lowered) and feeding_zone == "surface":
        feeding_zone = "surface_to_bottom"
    elif "coule" in lowered or "sink" in lowered:
        feeding_zone = "bottom"

    commercial_price: str | None = None
    commercial_currency = ""
    offers = structured.get("offers")
    offer: dict[str, object] | None = None
    if isinstance(offers, dict):
        offer = cast(dict[str, object], offers)
    elif isinstance(offers, list) and offers and isinstance(offers[0], dict):
        offer = cast(dict[str, object], offers[0])
    if offer is not None:
        raw_price = offer.get("price")
        if isinstance(raw_price, (str, int)):
            try:
                commercial_price = normalize_decimal(str(raw_price))
            except ValueError:
                commercial_price = None
        currency = offer.get("priceCurrency")
        if isinstance(currency, str):
            commercial_currency = currency.strip().upper()

    product: dict[str, object] = {
        "schema_version": FEED_PRODUCT_SCHEMA_V1,
        "id": product_id,
        "revision": 1,
        "brand": brand,
        "name": name,
        "variant": "",
        "feed_category": "prepared_dry" if form not in {"frozen", "live"} else form,
        "form": form,
        "dietary_role": dietary_role,
        "target_species_text": "",
        "feeding_zone": feeding_zone,
        "ingredients_text": ingredients,
        **analytics,
        "energy_kj_kg_decimal": None,
        "additives_text": "",
        "feeding_guide_text": feeding_guide,
        "package_mass_g_decimal": None,
        "package_volume_ml_decimal": None,
        "source_url": source_url,
        "manufacturer_url": "",
        "source_kind": "web_import",
        "source_observed_at": datetime.now(UTC).isoformat(),
        "commercial_price_decimal": commercial_price,
        "commercial_currency": commercial_currency,
        "notes": (
            "Structured facts extracted from a trusted product page. "
            "Marketing prose is not copied into the scientific catalog."
        ),
    }
    product["product_sha256"] = _product_sha(product)
    return product


def _decimal_from_product(product: dict[str, object], key: str) -> Decimal | None:
    value = product.get(key)
    if isinstance(value, str):
        return Decimal(value)
    return None


def calculate_feed_load(
    *,
    amount_g: float,
    water_volume_liters: float,
    product: dict[str, object] | None,
    fallback_protein_percent: float | None,
    target_biomass_g: float | None,
    consumed_percent: float | None,
) -> dict[str, object]:
    amount = Decimal(str(amount_g))
    volume = Decimal(str(water_volume_liters))
    if amount <= 0 or volume <= 0:
        raise ValueError("feed amount and water volume must be positive")

    protein_percent = (
        _decimal_from_product(product, "crude_protein_percent_decimal")
        if product is not None
        else None
    )
    if protein_percent is None and fallback_protein_percent is not None:
        protein_percent = Decimal(str(fallback_protein_percent))

    consumed_fraction: Decimal | None = None
    if consumed_percent is not None:
        consumed_fraction = Decimal(str(consumed_percent)) / Decimal(100)

    result: dict[str, object] = {
        "method": FEED_LOAD_METHOD_V1,
        "model_kind": "stoichiometric_input_and_upper_bounds_not_observed_prediction",
        "amount_g_decimal": normalize_decimal(amount),
        "water_volume_liters_decimal": normalize_decimal(volume),
        "target_biomass_g_decimal": (
            normalize_decimal(str(target_biomass_g))
            if target_biomass_g is not None
            else None
        ),
        "feed_rate_percent_biomass_decimal": None,
        "consumed_percent_decimal": (
            normalize_decimal(str(consumed_percent))
            if consumed_percent is not None
            else None
        ),
        "ingested_feed_g_decimal": None,
        "uneaten_feed_g_decimal": None,
        "protein_g_decimal": None,
        "fat_g_decimal": None,
        "fibre_g_decimal": None,
        "moisture_g_decimal": None,
        "dry_matter_g_decimal": None,
        "ash_g_decimal": None,
        "phosphorus_mg_decimal": None,
        "phosphate_as_po4_upper_bound_delta_mg_l_decimal": None,
        "estimated_protein_nitrogen_mg_decimal": None,
        "ingested_protein_nitrogen_mg_decimal": None,
        "tan_n_upper_bound_mg_decimal": None,
        "tan_n_upper_bound_delta_mg_l_decimal": None,
        "nitrate_as_no3_upper_bound_delta_mg_l_decimal": None,
        "nitrification_o2_upper_bound_mg_decimal": None,
        "nitrification_o2_upper_bound_delta_mg_l_decimal": None,
        "nitrification_alkalinity_upper_bound_mg_caco3_decimal": None,
        "nitrification_alkalinity_upper_bound_delta_mg_l_caco3_decimal": None,
        "expected_effect_status": "requires_species_feed_digestibility_and_retention_coefficients",
        "assumptions": [
            "crude protein is converted to protein nitrogen using N = crude protein / 6.25",
            "TAN, nitrate, oxygen and alkalinity values are stoichiometric upper bounds, not expected measured changes",
            "actual effects depend on consumption, digestibility, retention/growth, species, life stage, temperature, biofilter and water exchange",
        ],
    }

    if target_biomass_g is not None and target_biomass_g > 0:
        feed_rate = amount / Decimal(str(target_biomass_g)) * Decimal(100)
        result["feed_rate_percent_biomass_decimal"] = normalize_decimal(feed_rate)

    if consumed_fraction is not None:
        ingested = amount * consumed_fraction
        uneaten = amount - ingested
        result["ingested_feed_g_decimal"] = normalize_decimal(ingested)
        result["uneaten_feed_g_decimal"] = normalize_decimal(uneaten)

    if product is not None:
        proximate_fields = {
            "crude_fat_percent_decimal": "fat_g_decimal",
            "crude_fibre_percent_decimal": "fibre_g_decimal",
            "moisture_percent_decimal": "moisture_g_decimal",
            "crude_ash_percent_decimal": "ash_g_decimal",
        }
        for product_key, result_key in proximate_fields.items():
            percent = _decimal_from_product(product, product_key)
            if percent is not None:
                result[result_key] = normalize_decimal(amount * percent / Decimal(100))
        moisture_percent = _decimal_from_product(product, "moisture_percent_decimal")
        if moisture_percent is not None:
            result["dry_matter_g_decimal"] = normalize_decimal(
                amount * (Decimal(100) - moisture_percent) / Decimal(100)
            )
        phosphorus_percent = _decimal_from_product(product, "phosphorus_percent_decimal")
        if phosphorus_percent is not None:
            phosphorus_mg = amount * phosphorus_percent / Decimal(100) * Decimal(1000)
            phosphate_mg = phosphorus_mg * (Decimal("94.9714") / Decimal("30.973761998"))
            result["phosphorus_mg_decimal"] = normalize_decimal(phosphorus_mg)
            result["phosphate_as_po4_upper_bound_delta_mg_l_decimal"] = normalize_decimal(
                phosphate_mg / volume
            )

    if protein_percent is None:
        return result

    protein_g = amount * protein_percent / Decimal(100)
    protein_n_mg = protein_g / Decimal("6.25") * Decimal(1000)
    result["protein_g_decimal"] = normalize_decimal(protein_g)
    result["estimated_protein_nitrogen_mg_decimal"] = normalize_decimal(protein_n_mg)

    if consumed_fraction is None:
        return result

    ingested_n = protein_n_mg * consumed_fraction
    tan_upper = ingested_n
    o2_upper = tan_upper * Decimal("4.57")
    alkalinity_upper = tan_upper * Decimal("7.14")
    nitrate_no3_upper = tan_upper * (Decimal(62) / Decimal(14))

    result["ingested_protein_nitrogen_mg_decimal"] = normalize_decimal(ingested_n)
    result["tan_n_upper_bound_mg_decimal"] = normalize_decimal(tan_upper)
    result["tan_n_upper_bound_delta_mg_l_decimal"] = normalize_decimal(tan_upper / volume)
    result["nitrate_as_no3_upper_bound_delta_mg_l_decimal"] = normalize_decimal(
        nitrate_no3_upper / volume
    )
    result["nitrification_o2_upper_bound_mg_decimal"] = normalize_decimal(o2_upper)
    result["nitrification_o2_upper_bound_delta_mg_l_decimal"] = normalize_decimal(
        o2_upper / volume
    )
    result["nitrification_alkalinity_upper_bound_mg_caco3_decimal"] = normalize_decimal(
        alkalinity_upper
    )
    result["nitrification_alkalinity_upper_bound_delta_mg_l_caco3_decimal"] = (
        normalize_decimal(alkalinity_upper / volume)
    )
    return result


def product_source_fingerprint(html: str) -> str:
    return hashlib.sha256(html.encode("utf-8")).hexdigest()
