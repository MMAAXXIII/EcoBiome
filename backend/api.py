"""Local-first application API bridge for the EcoBiome web UI."""

from __future__ import annotations

import json
import os
import shutil
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Literal, cast
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from requests import RequestException

from backend.ecology_n7 import (
    append_operation,
    read_operations,
)
from backend.ecology_n7 import decimal_text as ecology_decimal_text
from backend.ecology_n7 import load_state as load_ecology_state
from backend.ecology_n7 import save_state as save_ecology_state
from backend.feed_catalog_n9 import (
    calculate_feed_load,
    create_manual_product,
    fetch_trusted_product_html,
    parse_product_html,
    product_source_fingerprint,
    public_product,
)
from backend.feed_catalog_n9 import load_catalog as load_feed_catalog
from backend.feed_catalog_n9 import save_catalog as save_feed_catalog
from ecobiome.core.observation.measurement import ScientificMeasurement
from ecobiome.core.observation.observation import AcquisitionMethod, Observation
from ecobiome.core.units import Measurement as UnitMeasurement
from ecobiome.dashboard.builder import build_project_dashboard
from ecobiome.journal import (
    CanonicalProjectEventStoreV1,
    CanonicalProjectEventV1,
    build_canonical_observation_event_v1,
    build_canonical_water_exchange_event_v1,
)
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.knowledge_acquisition.collector_acquire import acquire_source
from ecobiome.knowledge_acquisition.persistence import CollectorStore
from ecobiome.knowledge_persistence.serialization import (
    canonical_json_text,
    normalize_decimal,
)
from ecobiome.simulation.ecosystem_state_v1 import QuantityBasisV1
from ecobiome.simulation.intervention_v1 import WaterExchangeInterventionV1
from ecobiome.workspace.manifest import ProjectManifest
from ecobiome.workspace.project_type import ProjectType
from ecobiome.workspace.workspace import ProjectWorkspace
from ecobiome.world.ecosystem_profile_v1 import (
    BiologicalPopulationV1,
    EcosystemProfileV1,
    EnvironmentZoneV1,
    FunctionalSystemV1,
    PhysicalStructureV1,
    ecosystem_profile_from_mapping_v1,
)

app = FastAPI(title="EcoBiome Local API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

_PROJECT_METADATA_SCHEMA = "ecobiome-local-project-v1"
_LOCAL_BRIDGE_VERSION = "n9"
_WATER_ZONE_ID = "water"
_EQUIPMENT_SCHEMA_V1 = "ecobiome-user-equipment-v1"
_POPULATION_SCHEMA_V1 = "ecobiome-user-population-v1"

_WATER_VOLUME_VARIABLE = ScientificVariable(
    identifier="hydrology.water_volume",
    name="Water volume",
    description="Current water volume of the tracked aquatic environment.",
    unit="L",
    display_unit="L",
    category="hydrology",
)

_METRIC_CONFIG: dict[str, tuple[ScientificVariable, str, str]] = {
    "temperature": (
        ScientificVariable(
            identifier="water.temperature",
            name="Water temperature",
            description="Observed water temperature.",
            unit="degC",
            display_unit="°C",
            category="physical",
        ),
        "degC",
        "°C",
    ),
    "ph": (
        ScientificVariable(
            identifier="water.ph",
            name="pH",
            description="Observed water pH.",
            unit="dimensionless",
            display_unit="",
            category="chemistry",
        ),
        "dimensionless",
        "",
    ),
    "ammonia": (
        ScientificVariable(
            identifier="water.ammonia",
            name="Ammonia / ammonium",
            description="Observed ammonia or ammonium concentration.",
            unit="mg/L",
            display_unit="mg/L",
            category="chemistry",
        ),
        "mg/L",
        "mg/L",
    ),
    "tan": (
        ScientificVariable(
            identifier="water.total_ammonia_nitrogen",
            name="Total ammonia nitrogen",
            description="Observed total ammonia nitrogen (TAN) concentration.",
            unit="mg N/L",
            display_unit="mg N/L",
            category="chemistry",
        ),
        "mg N/L",
        "mg N/L",
    ),
    "nitrite": (
        ScientificVariable(
            identifier="water.nitrite",
            name="Nitrite",
            description="Observed nitrite concentration.",
            unit="mg/L",
            display_unit="mg/L",
            category="chemistry",
        ),
        "mg/L",
        "mg/L",
    ),
    "nitrate": (
        ScientificVariable(
            identifier="water.nitrate",
            name="Nitrate",
            description="Observed nitrate concentration.",
            unit="mg/L",
            display_unit="mg/L",
            category="chemistry",
        ),
        "mg/L",
        "mg/L",
    ),
    "oxygen": (
        ScientificVariable(
            identifier="water.dissolved_oxygen",
            name="Dissolved oxygen",
            description="Observed dissolved oxygen concentration.",
            unit="mg/L",
            display_unit="mg/L",
            category="chemistry",
        ),
        "mg/L",
        "mg/L",
    ),
    "phosphate": (
        ScientificVariable(
            identifier="water.phosphate",
            name="Phosphate",
            description="Observed phosphate concentration.",
            unit="mg/L",
            display_unit="mg/L",
            category="chemistry",
        ),
        "mg/L",
        "mg/L",
    ),
    "iron": (
        ScientificVariable(
            identifier="water.iron",
            name="Iron",
            description="Observed dissolved iron concentration.",
            unit="mg/L",
            display_unit="mg/L",
            category="chemistry",
        ),
        "mg/L",
        "mg/L",
    ),
    "co2": (
        ScientificVariable(
            identifier="water.co2",
            name="Carbon dioxide",
            description="Observed dissolved carbon dioxide concentration.",
            unit="mg/L",
            display_unit="mg/L",
            category="chemistry",
        ),
        "mg/L",
        "mg/L",
    ),
    "gh": (
        ScientificVariable(
            identifier="water.total_hardness_as_caco3",
            name="General hardness as CaCO3",
            description="Observed general hardness expressed as calcium carbonate equivalent.",
            unit="mg/L",
            display_unit="°dGH",
            category="chemistry",
        ),
        "mg/L",
        "°dGH",
    ),
    "kh": (
        ScientificVariable(
            identifier="water.alkalinity_as_caco3",
            name="Carbonate hardness / alkalinity as CaCO3",
            description="Observed alkalinity expressed as calcium carbonate equivalent.",
            unit="mg/L",
            display_unit="°dKH",
            category="chemistry",
        ),
        "mg/L",
        "°dKH",
    ),
    "conductivity": (
        ScientificVariable(
            identifier="water.conductivity",
            name="Electrical conductivity",
            description="Observed electrical conductivity of the water.",
            unit="microsiemens / centimeter",
            display_unit="µS/cm",
            category="chemistry",
        ),
        "microsiemens / centimeter",
        "µS/cm",
    ),
    "chloride": (
        ScientificVariable(
            identifier="water.chloride",
            name="Chloride",
            description="Observed chloride concentration.",
            unit="mg/L",
            display_unit="mg/L",
            category="chemistry",
        ),
        "mg/L",
        "mg/L",
    ),
    "tss": (
        ScientificVariable(
            identifier="water.total_suspended_solids",
            name="Total suspended solids",
            description="Observed total suspended solids concentration.",
            unit="mg/L",
            display_unit="mg/L",
            category="physical",
        ),
        "mg/L",
        "mg/L",
    ),
    "calcium": (
        ScientificVariable(
            identifier="water.calcium",
            name="Calcium",
            description="Observed dissolved calcium concentration.",
            unit="mg/L",
            display_unit="mg/L",
            category="chemistry",
        ),
        "mg/L",
        "mg/L",
    ),
    "magnesium": (
        ScientificVariable(
            identifier="water.magnesium",
            name="Magnesium",
            description="Observed dissolved magnesium concentration.",
            unit="mg/L",
            display_unit="mg/L",
            category="chemistry",
        ),
        "mg/L",
        "mg/L",
    ),
    "salinity": (
        ScientificVariable(
            identifier="water.salinity",
            name="Salinity",
            description="Observed salinity expressed as mass concentration.",
            unit="g/L",
            display_unit="g/L",
            category="chemistry",
        ),
        "g/L",
        "g/L",
    ),
    "orp": (
        ScientificVariable(
            identifier="water.oxidation_reduction_potential",
            name="Oxidation-reduction potential",
            description="Observed oxidation-reduction potential.",
            unit="mV",
            display_unit="mV",
            category="chemistry",
        ),
        "mV",
        "mV",
    ),
    "oxygen_saturation": (
        ScientificVariable(
            identifier="water.oxygen_saturation",
            name="Dissolved oxygen saturation",
            description="Observed dissolved oxygen saturation reported by the instrument.",
            unit="percent",
            display_unit="%",
            category="chemistry",
        ),
        "percent",
        "%",
    ),
    "water_depth": (
        ScientificVariable(
            identifier="hydrology.water_depth",
            name="Water depth",
            description="Observed water-column depth.",
            unit="cm",
            display_unit="cm",
            category="hydrology",
        ),
        "cm",
        "cm",
    ),
    "par_surface": (
        ScientificVariable(
            identifier="light.par_surface",
            name="PAR at water surface",
            description="Observed photosynthetically active radiation at the water surface.",
            unit="micromole / meter ** 2 / second",
            display_unit="µmol/m²/s",
            category="light",
        ),
        "micromole / meter ** 2 / second",
        "µmol/m²/s",
    ),
    "par_bottom": (
        ScientificVariable(
            identifier="light.par_bottom",
            name="PAR at bottom",
            description="Observed photosynthetically active radiation near the bottom/substrate.",
            unit="micromole / meter ** 2 / second",
            display_unit="µmol/m²/s",
            category="light",
        ),
        "micromole / meter ** 2 / second",
        "µmol/m²/s",
    ),
    "algae_coverage": (
        ScientificVariable(
            identifier="biology.algae_coverage",
            name="Visible algae coverage",
            description="User-observed visible algae coverage of tracked surfaces.",
            unit="percent",
            display_unit="%",
            category="biology",
        ),
        "percent",
        "%",
    ),
    "periphyton_coverage": (
        ScientificVariable(
            identifier="biology.periphyton_coverage",
            name="Periphyton coverage",
            description="User-observed periphyton/biofilm coverage of tracked surfaces.",
            unit="percent",
            display_unit="%",
            category="biology",
        ),
        "percent",
        "%",
    ),
}
_METRIC_INPUT_TO_CANONICAL_FACTOR = {
    "gh": 17.848,
    "kh": 17.848,
}
_METRIC_CANONICAL_TO_DISPLAY_FACTOR = {
    key: 1.0 / value for key, value in _METRIC_INPUT_TO_CANONICAL_FACTOR.items()
}
_VARIABLE_TO_METRIC = {
    config[0].identifier: metric
    for metric, config in _METRIC_CONFIG.items()
}


class CreateWaterBodyRequest(BaseModel):
    """Create one local aquatic project backed by an N4 profile."""

    name: str = Field(min_length=1, max_length=120)
    type: Literal["aquarium", "pond"]
    volume_liters: float = Field(gt=0, le=10_000_000)


class SetFillLevelRequest(BaseModel):
    """Record the current fill level as a canonical water-volume observation."""

    fill_percent: float = Field(ge=0, le=100)
    observed_at: datetime | None = None
    source: str = Field(default="ecobiome-ui-fill-level", min_length=1, max_length=120)


class WaterExchangeRequest(BaseModel):
    """Record one user-reported N4/N5 water-exchange intervention."""

    removed_volume_liters: float = Field(ge=0, le=10_000_000)
    replacement_volume_liters: float = Field(ge=0, le=10_000_000)
    water_source_id: str | None = Field(default=None, max_length=128)
    note: str = Field(default="", max_length=1000)


class CreateEquipmentRequest(BaseModel):
    """Add one durable equipment entry to the N4 ecosystem profile."""

    equipment_type: Literal[
        "water_pump",
        "air_pump",
        "lighting",
        "heater",
        "filter",
        "co2_system",
        "sensor",
        "other",
    ]
    name: str = Field(min_length=1, max_length=160)
    manufacturer: str = Field(default="", max_length=160)
    model: str = Field(default="", max_length=160)
    power_watts: float | None = Field(default=None, ge=0, le=100_000)
    daily_runtime_hours: float | None = Field(default=None, ge=0, le=24)
    in_service_since: date | None = None
    flow_lph: float | None = Field(default=None, gt=0, le=100_000_000)
    measured_flow_lph: float | None = Field(default=None, gt=0, le=100_000_000)
    spectrum: str = Field(default="", max_length=500)
    color_temperature_k: float | None = Field(default=None, gt=0, le=100_000)
    par_surface_umol_m2_s: float | None = Field(default=None, ge=0, le=100_000)
    par_bottom_umol_m2_s: float | None = Field(default=None, ge=0, le=100_000)
    filter_media: str = Field(default="", max_length=500)
    media_volume_liters: float | None = Field(default=None, ge=0, le=1_000_000)
    specific_surface_m2_per_l: float | None = Field(default=None, ge=0, le=1_000_000)
    biofilter_maturity: Literal["unknown", "new", "cycling", "mature", "disturbed"] = "unknown"
    tan_capacity_mg_n_day: float | None = Field(default=None, ge=0, le=1_000_000_000)
    inoculated: bool | None = None
    last_maintenance_at: date | None = None
    notes: str = Field(default="", max_length=4000)


class CreateLivestockRequest(BaseModel):
    """Register one animal population and its current biological load."""

    common_name: str = Field(min_length=1, max_length=160)
    scientific_name: str = Field(default="", max_length=200)
    count: int = Field(ge=0, le=10_000_000)
    male_count: int = Field(default=0, ge=0, le=10_000_000)
    female_count: int = Field(default=0, ge=0, le=10_000_000)
    average_mass_g: float | None = Field(default=None, ge=0, le=1_000_000)
    life_stage: str = Field(default="", max_length=120)
    notes: str = Field(default="", max_length=2000)


class AdjustLivestockRequest(BaseModel):
    """Adjust current animal count while preserving append-only history."""

    delta_count: int = Field(ge=-10_000_000, le=10_000_000)
    reason: Literal["addition", "removal", "death", "correction"]
    sex: Literal["male", "female", "unknown"] = "unknown"
    note: str = Field(default="", max_length=2000)


class SetLivestockSexRequest(BaseModel):
    """Set the currently known male/female distribution without changing abundance."""

    male_count: int = Field(ge=0, le=10_000_000)
    female_count: int = Field(ge=0, le=10_000_000)
    note: str = Field(default="", max_length=2000)


class CreatePlantRequest(BaseModel):
    """Register one plant population and current coverage information."""

    common_name: str = Field(min_length=1, max_length=160)
    scientific_name: str = Field(default="", max_length=200)
    count: int | None = Field(default=None, ge=0, le=10_000_000)
    coverage_percent: float | None = Field(default=None, ge=0, le=100)
    notes: str = Field(default="", max_length=2000)


class CreateWaterSourceRequest(BaseModel):
    """Create one reusable replacement/top-up water profile."""

    name: str = Field(min_length=1, max_length=160)
    source_type: Literal["tap", "rain", "ro", "well", "mixed", "other"] = "tap"
    temperature_c: float | None = Field(default=None, ge=-5, le=80)
    ph: float | None = Field(default=None, ge=0, le=14)
    kh_dkh: float | None = Field(default=None, ge=0, le=100)
    gh_dgh: float | None = Field(default=None, ge=0, le=100)
    conductivity_us_cm: float | None = Field(default=None, ge=0, le=1_000_000)
    nitrate_mg_l: float | None = Field(default=None, ge=0, le=1_000_000)
    nitrite_mg_l: float | None = Field(default=None, ge=0, le=1_000_000)
    ammonia_mg_l: float | None = Field(default=None, ge=0, le=1_000_000)
    phosphate_mg_l: float | None = Field(default=None, ge=0, le=1_000_000)
    chloride_mg_l: float | None = Field(default=None, ge=0, le=1_000_000)
    calcium_mg_l: float | None = Field(default=None, ge=0, le=1_000_000)
    magnesium_mg_l: float | None = Field(default=None, ge=0, le=1_000_000)
    salinity_g_l: float | None = Field(default=None, ge=0, le=1_000)
    notes: str = Field(default="", max_length=2000)


class CreateSubstrateLayerRequest(BaseModel):
    """Add one ordered substrate layer description."""

    material: str = Field(min_length=1, max_length=200)
    thickness_cm: float = Field(gt=0, le=1000)
    grain_min_mm: float | None = Field(default=None, ge=0, le=10_000)
    grain_max_mm: float | None = Field(default=None, ge=0, le=10_000)
    organic: bool = False
    notes: str = Field(default="", max_length=2000)


class FeedingRequest(BaseModel):
    """Record one structured feeding event with a frozen feed-product snapshot."""

    feed_product_id: str | None = Field(default=None, max_length=200)
    food_name: str = Field(default="", max_length=200)
    amount_g: float = Field(gt=0, le=100_000)
    protein_percent: float | None = Field(default=None, ge=0, le=100)
    target_population_ids: list[str] = Field(default_factory=list, max_length=1000)
    consumed_percent: float | None = Field(default=None, ge=0, le=100)
    occurred_at: datetime | None = None
    note: str = Field(default="", max_length=2000)


class CreateFeedProductRequest(BaseModel):
    """Create one structured feed product manually."""

    brand: str = Field(default="", max_length=160)
    name: str = Field(min_length=1, max_length=240)
    variant: str = Field(default="", max_length=160)
    feed_category: str = Field(default="prepared_dry", max_length=80)
    form: str = Field(default="other", max_length=80)
    dietary_role: str = Field(default="unknown", max_length=80)
    target_species_text: str = Field(default="", max_length=1000)
    feeding_zone: str = Field(default="unknown", max_length=80)
    ingredients_text: str = Field(default="", max_length=8000)
    crude_protein_percent: float | None = Field(default=None, ge=0, le=100)
    crude_fat_percent: float | None = Field(default=None, ge=0, le=100)
    crude_fibre_percent: float | None = Field(default=None, ge=0, le=100)
    moisture_percent: float | None = Field(default=None, ge=0, le=100)
    crude_ash_percent: float | None = Field(default=None, ge=0, le=100)
    phosphorus_percent: float | None = Field(default=None, ge=0, le=100)
    additives_text: str = Field(default="", max_length=8000)
    feeding_guide_text: str = Field(default="", max_length=4000)
    source_url: str = Field(default="", max_length=2000)
    notes: str = Field(default="", max_length=4000)


class ImportFeedProductRequest(BaseModel):
    """Import structured factual fields from a trusted product URL."""

    url: str = Field(min_length=1, max_length=2000)


class TopUpRequest(BaseModel):
    """Record evaporation replacement separately from a water exchange."""

    volume_liters: float = Field(gt=0, le=10_000_000)
    water_source_id: str | None = Field(default=None, max_length=128)
    occurred_at: datetime | None = None
    note: str = Field(default="", max_length=2000)


class EcosystemOperationRequest(BaseModel):
    """Record a structured operational disturbance or maintenance action."""

    operation_type: Literal[
        "filter_maintenance",
        "power_outage",
        "additive",
        "fertilization",
        "bacteria_addition",
        "co2_change",
        "water_treatment",
        "siphoning",
        "plant_pruning",
        "substrate_maintenance",
        "medication",
        "other",
    ]
    label: str = Field(min_length=1, max_length=200)
    quantity: float | None = None
    unit: str = Field(default="", max_length=40)
    occurred_at: datetime | None = None
    note: str = Field(default="", max_length=2000)


class AddMeasurementRequest(BaseModel):
    """Append one user measurement as a canonical N5 observation."""

    metric: Literal[
        "temperature",
        "ph",
        "ammonia",
        "tan",
        "nitrite",
        "nitrate",
        "oxygen",
        "phosphate",
        "iron",
        "co2",
        "gh",
        "kh",
        "conductivity",
        "chloride",
        "tss",
        "calcium",
        "magnesium",
        "salinity",
        "orp",
        "oxygen_saturation",
        "water_depth",
        "par_surface",
        "par_bottom",
        "algae_coverage",
        "periphyton_coverage",
    ]
    value: float
    uncertainty: float = Field(default=0.0, ge=0)
    confidence: float = Field(default=1.0, ge=0, le=1)
    observed_at: datetime | None = None
    source: str = Field(default="ecobiome-ui", min_length=1, max_length=120)


class CollectorAcquireRequest(BaseModel):
    """Run one deterministic Collector acquisition."""

    source: str = Field(min_length=1, max_length=4096)
    language: str = Field(default="", max_length=32)
    languages: list[str] = Field(default_factory=list, max_length=16)
    maximum_input_bytes: int = Field(default=8 * 1024 * 1024, gt=0)
    maximum_passage_characters: int = Field(default=1500, ge=200, le=20_000)


class CollectorProposeClaimsRequest(BaseModel):
    """Propose source-statement Claims for one representation."""

    representation_id: str = Field(min_length=1, max_length=128)
    limit: int = Field(default=50, ge=1, le=500)
    maximum_claim_characters: int = Field(default=350, ge=50, le=4000)


class CollectorReviewRequest(BaseModel):
    """Record one append-only Collector human-review decision."""

    target_type: Literal["passage", "claim"]
    target_id: str = Field(min_length=1, max_length=128)
    decision: Literal["accept", "reject"]
    reviewer: str = Field(default="ecobiome-ui-user", max_length=120)
    rationale: str = Field(default="", max_length=4000)


def _runtime_root() -> Path:
    configured = os.getenv("ECOBIOME_LOCAL_DATA_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".ecobiome").resolve()


def _projects_root() -> Path:
    return _runtime_root() / "projects"


def _project_dir(project_id: UUID) -> Path:
    return _projects_root() / str(project_id)


def _metadata_path(project_id: UUID) -> Path:
    return _project_dir(project_id) / "metadata.json"


def _profile_path(project_id: UUID) -> Path:
    return _project_dir(project_id) / "profile.json"


def _journal_path(project_id: UUID) -> Path:
    return _project_dir(project_id) / "journal" / "events.jsonl"


def _collector_database_path() -> Path:
    return _runtime_root() / "collector" / "collector.sqlite"


def _write_json_atomic(path: Path, payload: object, *, canonical: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    if canonical:
        text = canonical_json_text(payload)
    else:
        text = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    temporary.write_text(text + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def _load_metadata(project_id: UUID) -> dict[str, object]:
    path = _metadata_path(project_id)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("project metadata must be a JSON object")
    if value.get("schema_version") != _PROJECT_METADATA_SCHEMA:
        raise ValueError("unsupported local project metadata schema")
    if value.get("project_id") != str(project_id):
        raise ValueError("project metadata identity mismatch")
    return value


def _load_profile(project_id: UUID) -> EcosystemProfileV1:
    path = _profile_path(project_id)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("project profile must be a JSON object")
    profile = ecosystem_profile_from_mapping_v1(raw)
    if profile.id != str(project_id):
        raise ValueError("project profile identity mismatch")
    return profile


def _project_store(project_id: UUID) -> CanonicalProjectEventStoreV1:
    _load_metadata(project_id)
    _load_profile(project_id)
    return CanonicalProjectEventStoreV1(_journal_path(project_id))


def _water_volume_from_event(event: CanonicalProjectEventV1) -> float | None:
    if event.event_type.value != "observation":
        return None
    payload = event.canonical_payload
    quantity = payload.get("quantity")
    if not isinstance(quantity, dict):
        return None
    if quantity.get("variable_id") != _WATER_VOLUME_VARIABLE.identifier:
        return None
    typed_value = quantity.get("value")
    if not isinstance(typed_value, dict):
        return None
    raw_value = typed_value.get("value")
    if not isinstance(raw_value, str):
        return None
    return float(raw_value)


def _water_exchange_delta_liters(
    event: CanonicalProjectEventV1,
) -> float | None:
    if event.event_type.value != "intervention":
        return None
    payload = event.canonical_payload
    intervention = payload.get("intervention")
    if not isinstance(intervention, dict):
        return None
    if intervention.get("schema_version") != "ecobiome-water-exchange-intervention-v1":
        return None

    def value_liters(field_name: str) -> float:
        value_with_unit = intervention.get(field_name)
        if not isinstance(value_with_unit, dict):
            raise TypeError(f"{field_name} must be an object")
        if value_with_unit.get("unit") != "L":
            raise ValueError(f"{field_name} must use canonical unit L")
        typed = value_with_unit.get("value")
        if not isinstance(typed, dict):
            raise TypeError(f"{field_name}.value must be a typed decimal")
        raw = typed.get("value")
        if not isinstance(raw, str):
            raise TypeError(f"{field_name}.value.value must be a string")
        return float(raw)

    removed = value_liters("removed_volume")
    replacement = value_liters("replacement_volume")
    return replacement - removed


def _initial_volume_liters(project_id: UUID) -> float:
    for event in _project_store(project_id).all():
        value = _water_volume_from_event(event)
        if value is not None:
            return value
    raise ValueError("project has no canonical water-volume observation")


def _nominal_capacity_liters(project_id: UUID) -> float:
    profile = _load_profile(project_id)
    for structure in profile.structures:
        if structure.id != "container":
            continue
        properties = json.loads(structure.properties_json)
        raw = properties.get("capacity_liters_decimal")
        if isinstance(raw, str):
            capacity = float(raw)
            if capacity > 0:
                return capacity
    # N6 V1 compatibility: the initial observation represented the intended capacity.
    return _initial_volume_liters(project_id)


def _current_volume_liters(project_id: UUID) -> float:
    current: float | None = None
    for event in _project_store(project_id).all():
        observed = _water_volume_from_event(event)
        if observed is not None:
            current = observed
            continue
        delta = _water_exchange_delta_liters(event)
        if delta is not None:
            if current is None:
                raise ValueError("water exchange precedes any water-volume observation")
            current += delta
    if current is None:
        raise ValueError("project has no canonical water-volume observation")
    return current


def _water_body_payload(project_id: UUID) -> dict[str, object]:
    metadata = _load_metadata(project_id)
    profile = _load_profile(project_id)
    created_at = metadata.get("created_at")
    if not isinstance(created_at, str):
        raise TypeError("project metadata created_at must be a string")
    events = _project_store(project_id).all()
    updated_at = (
        max(event.occurred_at for event in events).isoformat()
        if events
        else created_at
    )
    capacity_liters = _nominal_capacity_liters(project_id)
    current_volume_liters = _current_volume_liters(project_id)
    fill_percent = (current_volume_liters / capacity_liters) * 100.0
    return {
        "id": str(project_id),
        "name": profile.label,
        "type": profile.profile_kind,
        # Backward-compatible field: from N6.1 onward this is nominal capacity.
        "volume_liters": capacity_liters,
        "capacity_liters": capacity_liters,
        "current_volume_liters": current_volume_liters,
        "fill_percent": fill_percent,
        "status": "unknown",
        "created_at": created_at,
        "updated_at": updated_at,
    }


def _iter_project_ids() -> tuple[UUID, ...]:
    root = _projects_root()
    if not root.exists():
        return ()
    result: list[UUID] = []
    for entry in sorted(root.iterdir(), key=lambda item: item.name):
        if not entry.is_dir():
            continue
        try:
            result.append(UUID(entry.name))
        except ValueError:
            continue
    return tuple(result)


def _build_profile(
    *,
    project_id: UUID,
    name: str,
    kind: Literal["aquarium", "pond"],
    capacity_liters: float,
) -> EcosystemProfileV1:
    structure_type = "aquarium_tank" if kind == "aquarium" else "pond_basin"
    return EcosystemProfileV1(
        id=str(project_id),
        profile_kind=kind,
        label=name.strip(),
        structures=(
            PhysicalStructureV1(
                id="container",
                structure_type=structure_type,
                label=name.strip(),
                properties_json=canonical_json_text(
                    {
                        "capacity_liters_decimal": normalize_decimal(
                            str(capacity_liters)
                        ),
                        "capacity_unit": "L",
                    }
                ),
            ),
        ),
        zones=(
            EnvironmentZoneV1(
                id=_WATER_ZONE_ID,
                zone_type="water_column",
                label="Water column",
                hosted_by_structure_id="container",
            ),
        ),
    )


def _append_observation(
    *,
    project_id: UUID,
    variable: ScientificVariable,
    value: float,
    unit: str,
    uncertainty: float,
    confidence: float,
    observed_at: datetime,
    source: str,
) -> dict[str, object]:
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")
    observation = Observation(
        source=source,
        variable=variable,
        value=ScientificMeasurement(
            quantity=UnitMeasurement(value=value, unit=unit),
            uncertainty=uncertainty,
        ),
        acquisition_method=AcquisitionMethod.HUMAN,
        confidence=confidence,
        observed_at=observed_at,
    )
    event = build_canonical_observation_event_v1(
        project_id=project_id,
        observation=observation,
        zone_id=_WATER_ZONE_ID,
    )
    _project_store(project_id).append(event)
    return event.canonical_payload


def _measurement_payloads(project_id: UUID) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for event in _project_store(project_id).all():
        if event.event_type.value != "observation":
            continue
        payload = event.canonical_payload
        quantity = payload.get("quantity")
        if not isinstance(quantity, dict):
            continue
        variable_id = quantity.get("variable_id")
        if not isinstance(variable_id, str):
            continue
        metric = _VARIABLE_TO_METRIC.get(variable_id)
        if metric is None:
            continue
        typed_value = quantity.get("value")
        if not isinstance(typed_value, dict):
            continue
        raw_value = typed_value.get("value")
        if not isinstance(raw_value, str):
            continue
        _variable, _canonical_unit, display_unit = _METRIC_CONFIG[metric]
        display_factor = _METRIC_CANONICAL_TO_DISPLAY_FACTOR.get(metric, 1.0)
        result.append(
            {
                "id": str(event.event_id),
                "water_body_id": str(project_id),
                "metric": metric,
                "value": float(raw_value) * display_factor,
                "unit": display_unit,
                "recorded_at": event.occurred_at.isoformat(),
            }
        )
    result.sort(key=lambda item: str(item["recorded_at"]))
    return result


def _replace_profile(project_id: UUID, profile: EcosystemProfileV1) -> None:
    if profile.id != str(project_id):
        raise ValueError("replacement profile identity mismatch")
    _write_json_atomic(
        _profile_path(project_id),
        profile.canonical_payload(),
        canonical=True,
    )


def _equipment_payload(system: FunctionalSystemV1) -> dict[str, object] | None:
    properties = json.loads(system.properties_json)
    if properties.get("schema_version") != _EQUIPMENT_SCHEMA_V1:
        return None

    def optional_decimal(name: str) -> float | None:
        raw = properties.get(name)
        return float(raw) if isinstance(raw, str) else None

    power_watts = optional_decimal("power_watts_decimal")
    runtime_hours = optional_decimal("daily_runtime_hours_decimal")
    daily_energy_wh = (
        power_watts * runtime_hours
        if power_watts is not None and runtime_hours is not None
        else None
    )
    annual_energy_kwh = (
        daily_energy_wh * 365.0 / 1000.0
        if daily_energy_wh is not None
        else None
    )
    return {
        "id": system.id,
        "name": system.label,
        "equipment_type": properties.get("equipment_type", "other"),
        "manufacturer": properties.get("manufacturer", ""),
        "model": properties.get("model", ""),
        "power_watts": power_watts,
        "daily_runtime_hours": runtime_hours,
        "in_service_since": properties.get("in_service_since"),
        "flow_lph": optional_decimal("flow_lph_decimal"),
        "measured_flow_lph": optional_decimal("measured_flow_lph_decimal"),
        "spectrum": properties.get("spectrum", ""),
        "color_temperature_k": optional_decimal("color_temperature_k_decimal"),
        "par_surface_umol_m2_s": optional_decimal("par_surface_umol_m2_s_decimal"),
        "par_bottom_umol_m2_s": optional_decimal("par_bottom_umol_m2_s_decimal"),
        "filter_media": properties.get("filter_media", ""),
        "media_volume_liters": optional_decimal("media_volume_liters_decimal"),
        "specific_surface_m2_per_l": optional_decimal("specific_surface_m2_per_l_decimal"),
        "biofilter_maturity": properties.get("biofilter_maturity", "unknown"),
        "tan_capacity_mg_n_day": optional_decimal("tan_capacity_mg_n_day_decimal"),
        "inoculated": properties.get("inoculated"),
        "last_maintenance_at": properties.get("last_maintenance_at"),
        "notes": properties.get("notes", ""),
        "daily_energy_wh": daily_energy_wh,
        "annual_energy_kwh": annual_energy_kwh,
    }


def _list_equipment_payloads(project_id: UUID) -> list[dict[str, object]]:
    profile = _load_profile(project_id)
    result: list[dict[str, object]] = []
    for system in profile.functional_systems:
        payload = _equipment_payload(system)
        if payload is not None:
            result.append(payload)
    result.sort(key=lambda item: (str(item["equipment_type"]), str(item["name"])))
    return result



def _ecology_state(project_id: UUID) -> dict[str, object]:
    _load_metadata(project_id)
    _load_profile(project_id)
    return load_ecology_state(_project_dir(project_id))


def _ecology_items(state: dict[str, object], field: str) -> list[dict[str, object]]:
    raw = state.get(field)
    if not isinstance(raw, list):
        raise TypeError(f"ecology state {field} must be an array")
    result: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise TypeError(f"ecology state {field} entries must be objects")
        result.append(cast(dict[str, object], item))
    return result


def _optional_decimal_float(item: dict[str, object], field: str) -> float | None:
    raw = item.get(field)
    return float(raw) if isinstance(raw, str) else None


def _livestock_payload(item: dict[str, object]) -> dict[str, object]:
    count_raw = item.get("count_decimal")
    if not isinstance(count_raw, str):
        raise TypeError("livestock count_decimal must be a string")
    count = int(float(count_raw))
    male_raw = item.get("male_count_decimal")
    female_raw = item.get("female_count_decimal")
    male_count = int(float(male_raw)) if isinstance(male_raw, str) else 0
    female_count = int(float(female_raw)) if isinstance(female_raw, str) else 0
    if male_count + female_count > count:
        raise ValueError("known male/female counts cannot exceed total abundance")
    unknown_sex_count = count - male_count - female_count
    average_mass_g = _optional_decimal_float(item, "average_mass_g_decimal")
    biomass_g = count * average_mass_g if average_mass_g is not None else None
    return {
        "id": item.get("id"),
        "common_name": item.get("common_name", ""),
        "scientific_name": item.get("scientific_name", ""),
        "count": count,
        "male_count": male_count,
        "female_count": female_count,
        "unknown_sex_count": unknown_sex_count,
        "average_mass_g": average_mass_g,
        "biomass_g": biomass_g,
        "life_stage": item.get("life_stage", ""),
        "notes": item.get("notes", ""),
        "created_at": item.get("created_at"),
    }


def _plant_payload(item: dict[str, object]) -> dict[str, object]:
    return {
        "id": item.get("id"),
        "common_name": item.get("common_name", ""),
        "scientific_name": item.get("scientific_name", ""),
        "count": (
            int(float(cast(str, item["count_decimal"])))
            if isinstance(item.get("count_decimal"), str)
            else None
        ),
        "coverage_percent": _optional_decimal_float(item, "coverage_percent_decimal"),
        "notes": item.get("notes", ""),
        "created_at": item.get("created_at"),
    }


def _water_source_payload(item: dict[str, object]) -> dict[str, object]:
    return {
        "id": item.get("id"),
        "name": item.get("name", ""),
        "source_type": item.get("source_type", "other"),
        "temperature_c": _optional_decimal_float(item, "temperature_c_decimal"),
        "ph": _optional_decimal_float(item, "ph_decimal"),
        "kh_dkh": _optional_decimal_float(item, "kh_dkh_decimal"),
        "gh_dgh": _optional_decimal_float(item, "gh_dgh_decimal"),
        "conductivity_us_cm": _optional_decimal_float(item, "conductivity_us_cm_decimal"),
        "nitrate_mg_l": _optional_decimal_float(item, "nitrate_mg_l_decimal"),
        "nitrite_mg_l": _optional_decimal_float(item, "nitrite_mg_l_decimal"),
        "ammonia_mg_l": _optional_decimal_float(item, "ammonia_mg_l_decimal"),
        "phosphate_mg_l": _optional_decimal_float(item, "phosphate_mg_l_decimal"),
        "chloride_mg_l": _optional_decimal_float(item, "chloride_mg_l_decimal"),
        "calcium_mg_l": _optional_decimal_float(item, "calcium_mg_l_decimal"),
        "magnesium_mg_l": _optional_decimal_float(item, "magnesium_mg_l_decimal"),
        "salinity_g_l": _optional_decimal_float(item, "salinity_g_l_decimal"),
        "notes": item.get("notes", ""),
        "created_at": item.get("created_at"),
    }


def _substrate_payload(item: dict[str, object]) -> dict[str, object]:
    return {
        "id": item.get("id"),
        "material": item.get("material", ""),
        "thickness_cm": _optional_decimal_float(item, "thickness_cm_decimal"),
        "grain_min_mm": _optional_decimal_float(item, "grain_min_mm_decimal"),
        "grain_max_mm": _optional_decimal_float(item, "grain_max_mm_decimal"),
        "organic": bool(item.get("organic", False)),
        "notes": item.get("notes", ""),
        "created_at": item.get("created_at"),
    }


def _ecology_snapshot(project_id: UUID) -> dict[str, object]:
    state = _ecology_state(project_id)
    livestock = [_livestock_payload(item) for item in _ecology_items(state, "livestock")]
    plants = [_plant_payload(item) for item in _ecology_items(state, "plants")]
    water_sources = [
        _water_source_payload(item) for item in _ecology_items(state, "water_sources")
    ]
    substrate_layers = [
        _substrate_payload(item) for item in _ecology_items(state, "substrate_layers")
    ]
    known_biomass = sum(
        cast(float, item["biomass_g"])
        for item in livestock
        if isinstance(item.get("biomass_g"), (float, int))
    )
    operations = read_operations(_project_dir(project_id), str(project_id))
    feeding_events = [
        event for event in operations if event.get("operation_type") == "feeding"
    ]
    measurements = _measurement_payloads(project_id)
    latest_by_metric: dict[str, float] = {}
    for measurement in measurements:
        metric = measurement.get("metric")
        value = measurement.get("value")
        if isinstance(metric, str) and isinstance(value, (int, float)):
            latest_by_metric[metric] = float(value)
    derived_indicators: dict[str, object] = {}
    temperature_c = latest_by_metric.get("temperature")
    ph_value = latest_by_metric.get("ph")
    tan_mg_n_l = latest_by_metric.get("tan")
    salinity_g_l = latest_by_metric.get("salinity")
    if temperature_c is not None and ph_value is not None and tan_mg_n_l is not None:
        if salinity_g_l is None or salinity_g_l <= 0.5:
            pka = 0.09018 + (2729.92 / (temperature_c + 273.2))
            fraction = 1.0 / (1.0 + (10.0 ** (pka - ph_value)))
            derived_indicators["un_ionized_ammonia"] = {
                "nh3_n_mg_l": tan_mg_n_l * fraction,
                "fraction": fraction,
                "method": "Emerson et al. 1975 zero-salinity equilibrium approximation",
                "inputs": {
                    "tan_mg_n_l": tan_mg_n_l,
                    "ph": ph_value,
                    "temperature_c": temperature_c,
                },
                "applicability": "freshwater_zero_salinity_approximation",
            }
        else:
            derived_indicators["un_ionized_ammonia"] = {
                "available": False,
                "reason": (
                    "zero-salinity Emerson approximation is not applied to "
                    "measured saline water"
                ),
            }
    feed_products = [
        public_product(item) for item in load_feed_catalog(_runtime_root())
    ]
    return {
        "livestock": livestock,
        "plants": plants,
        "water_sources": water_sources,
        "substrate_layers": substrate_layers,
        "feed_products": feed_products,
        "known_livestock_biomass_g": known_biomass,
        "operation_count": len(operations),
        "feeding_event_count": len(feeding_events),
        "derived_indicators": derived_indicators,
        "recent_operations": [
            _operation_public_payload(event) for event in operations[-20:]
        ][::-1],
    }


ExperienceLevel = Literal["beginner", "intermediate", "advanced"]


def _guidance_snapshot(
    project_id: UUID,
    level: ExperienceLevel,
) -> dict[str, object]:
    """Return progressive data-completeness guidance without diagnosing health."""
    ecology = _ecology_snapshot(project_id)
    measurements = _measurement_payloads(project_id)
    measured_metrics = {
        str(item["metric"])
        for item in measurements
        if isinstance(item.get("metric"), str)
    }
    equipment = _list_equipment_payloads(project_id)
    filters = [item for item in equipment if item.get("equipment_type") == "filter"]
    lights = [item for item in equipment if item.get("equipment_type") == "lighting"]
    livestock = cast(list[dict[str, object]], ecology["livestock"])
    plants = cast(list[dict[str, object]], ecology["plants"])
    water_sources = cast(list[dict[str, object]], ecology["water_sources"])
    substrate_layers = cast(list[dict[str, object]], ecology["substrate_layers"])
    feeding_count = int(cast(int, ecology["feeding_event_count"]))

    items: list[dict[str, object]] = []

    def add(
        key: str,
        label: str,
        *,
        known: bool,
        required: bool,
        section: str,
        action: str,
        rationale: str,
        applicability_note: str = "",
    ) -> None:
        status = "known" if known else ("missing" if required else "check")
        items.append(
            {
                "key": key,
                "label": label,
                "status": status,
                "required": required,
                "section": section,
                "action": action,
                "rationale": rationale,
                "applicability_note": applicability_note,
            }
        )

    for metric, label, rationale in (
        ("temperature", "Température de l’eau", "Base nécessaire pour interpréter la physiologie et plusieurs équilibres chimiques."),
        ("ph", "pH", "Le pH structure l’interprétation de la chimie de l’eau, notamment la fraction NH₃ du TAN."),
        ("nitrite", "Nitrites", "Les nitrites permettent de suivre un intermédiaire critique du cycle de l’azote."),
        ("nitrate", "Nitrates", "Les nitrates renseignent sur l’accumulation azotée et l’équilibre entre production et export."),
        ("kh", "Alcalinité / KH", "Le KH renseigne sur la réserve alcaline et la stabilité du système carbonate/pH."),
    ):
        add(
            f"metric:{metric}",
            label,
            known=metric in measured_metrics,
            required=True,
            section="measurements",
            action="measure",
            rationale=rationale,
        )

    add(
        "water-source",
        "Au moins un profil d’eau de remplacement",
        known=bool(water_sources),
        required=True,
        section="water",
        action="add-water-source",
        rationale="Les changements d’eau ne sont interprétables que si l’eau entrante est décrite.",
    )
    add(
        "livestock-inventory",
        "Faune du milieu",
        known=bool(livestock),
        required=False,
        section="life",
        action="add-livestock",
        rationale="La charge biologique animale est un déterminant majeur des flux d’oxygène, de matière organique et d’azote.",
        applicability_note="À renseigner si le milieu contient des animaux.",
    )
    add(
        "filtration-inventory",
        "Filtration / circulation",
        known=bool(filters),
        required=False,
        section="equipment",
        action="add-filter",
        rationale="Le débit et la biofiltration structurent le traitement de la charge azotée.",
        applicability_note="À renseigner si le milieu utilise une filtration technique.",
    )
    add(
        "plant-inventory",
        "Végétation",
        known=bool(plants),
        required=False,
        section="life",
        action="add-plant",
        rationale="La végétation modifie les flux de nutriments, de carbone et d’oxygène.",
        applicability_note="À renseigner si des plantes sont présentes.",
    )

    if level in {"intermediate", "advanced"}:
        for metric, label, required, rationale in (
            ("gh", "Dureté GH", True, "Le GH complète la description minérale de l’eau et son contexte osmorégulatoire."),
            ("conductivity", "Conductivité", True, "La conductivité aide à suivre la minéralisation globale et ses dérives."),
            ("tan", "Azote ammoniacal total (TAN)", bool(livestock), "Le TAN est nécessaire pour quantifier la charge ammoniacale et estimer NH₃ avec pH et température."),
            ("oxygen", "Oxygène dissous", bool(livestock), "L’oxygène relie respiration animale, activité microbienne et fonctionnement du biofiltre."),
        ):
            add(
                f"metric:{metric}",
                label,
                known=metric in measured_metrics,
                required=required,
                section="measurements",
                action="measure",
                rationale=rationale,
                applicability_note=("Particulièrement utile lorsque des animaux sont présents." if not required else ""),
            )

        if livestock:
            add(
                "livestock-mass",
                "Masse moyenne des populations animales",
                known=all(item.get("average_mass_g") is not None for item in livestock),
                required=True,
                section="life",
                action="complete-livestock",
                rationale="L’effectif seul ne suffit pas à estimer une biomasse et donc une charge biologique.",
            )
            add(
                "feeding-history",
                "Historique de nourrissage",
                known=feeding_count > 0,
                required=True,
                section="life",
                action="record-feeding",
                rationale="La nourriture distribuée est une entrée majeure de matière organique et d’azote.",
            )
            add(
                "feed-catalog",
                "Aliment(s) caractérisé(s)",
                known=bool(cast(list[dict[str, object]], ecology["feed_products"])),
                required=True,
                section="life",
                action="add-feed-product",
                rationale="La composition de l’aliment est nécessaire pour relier la masse distribuée aux apports de protéines, d’azote et de matière organique.",
            )

        if filters:
            add(
                "filter-measured-flow",
                "Débit réel de filtration",
                known=all(item.get("measured_flow_lph") is not None for item in filters),
                required=True,
                section="equipment",
                action="complete-filter",
                rationale="Le débit constructeur ne remplace pas le débit réellement obtenu dans l’installation.",
            )
            add(
                "biofilter-maturity",
                "Maturité biologique du filtre",
                known=all(item.get("biofilter_maturity") not in {None, "", "unknown"} for item in filters),
                required=True,
                section="equipment",
                action="complete-filter",
                rationale="Un biofiltre neuf, en cyclage, mature ou perturbé n’a pas la même capacité fonctionnelle.",
            )

        if water_sources:
            source_complete = any(
                all(source.get(field) is not None for field in ("ph", "kh_dkh", "gh_dgh", "conductivity_us_cm"))
                for source in water_sources
            )
            add(
                "water-source-core-chemistry",
                "Chimie de base d’un profil d’eau",
                known=source_complete,
                required=True,
                section="water",
                action="complete-water-source",
                rationale="pH, KH, GH et conductivité rendent le profil d’eau beaucoup plus interprétable.",
            )

        if substrate_layers:
            add(
                "substrate-grain-size",
                "Granulométrie du substrat",
                known=all(
                    item.get("grain_min_mm") is not None and item.get("grain_max_mm") is not None
                    for item in substrate_layers
                ),
                required=True,
                section="water",
                action="complete-substrate",
                rationale="La granulométrie influence circulation interstitielle, colmatage et gradients redox.",
            )

    if level == "advanced":
        for metric, label, required, rationale in (
            ("tss", "Matières en suspension (TSS)", True, "Les solides renseignent sur la charge organique particulaire et la pression sur la filtration."),
            ("chloride", "Chlorures", True, "Les chlorures sont utiles à l’interprétation du risque nitrite et de la composition ionique."),
            ("calcium", "Calcium", True, "Le calcium affine la caractérisation minérale au-delà du GH global."),
            ("magnesium", "Magnésium", True, "Le magnésium affine la caractérisation minérale au-delà du GH global."),
            ("salinity", "Salinité", True, "La salinité conditionne plusieurs équilibres et la validité de certaines approximations."),
            ("oxygen_saturation", "Saturation en oxygène", bool(livestock), "La saturation complète les mg/L en tenant compte du contexte physico-chimique."),
            ("orp", "Potentiel redox (ORP)", False, "L’ORP est un indicateur avancé, utile surtout dans certains systèmes fortement chargés ou instrumentés."),
            ("algae_coverage", "Couverture algale", False, "Le suivi des algues aide à documenter les compétitions et dérives de production primaire."),
            ("periphyton_coverage", "Couverture de périphyton", False, "Le périphyton constitue une composante fonctionnelle du biofilm et de la production primaire."),
        ):
            add(
                f"metric:{metric}",
                label,
                known=metric in measured_metrics,
                required=required,
                section="measurements",
                action="measure",
                rationale=rationale,
            )

        par_required = bool(plants or lights)
        add(
            "metric:par_surface",
            "PAR en surface",
            known="par_surface" in measured_metrics or any(item.get("par_surface_umol_m2_s") is not None for item in lights),
            required=par_required,
            section="measurements",
            action="measure-light",
            rationale="Le PAR décrit la lumière photosynthétiquement active reçue, contrairement aux watts électriques seuls.",
            applicability_note="Attendu lorsqu’une végétation ou un éclairage est présent.",
        )
        add(
            "metric:par_bottom",
            "PAR au fond",
            known="par_bottom" in measured_metrics or any(item.get("par_bottom_umol_m2_s") is not None for item in lights),
            required=par_required,
            section="measurements",
            action="measure-light",
            rationale="La mesure au fond documente l’atténuation réelle dans la colonne d’eau.",
            applicability_note="Attendu lorsqu’une végétation ou un éclairage est présent.",
        )

        if filters:
            add(
                "filter-media",
                "Média et volume du biofiltre",
                known=all(bool(item.get("filter_media")) and item.get("media_volume_liters") is not None for item in filters),
                required=True,
                section="equipment",
                action="complete-filter",
                rationale="Le type et le volume de média sont nécessaires pour caractériser la capacité biologique potentielle.",
            )
            add(
                "filter-specific-surface",
                "Surface spécifique du média",
                known=all(item.get("specific_surface_m2_per_l") is not None for item in filters),
                required=False,
                section="equipment",
                action="complete-filter",
                rationale="Cette donnée améliore la comparaison des supports mais ne doit pas être inventée si elle n’est pas connue.",
            )
            add(
                "filter-tan-capacity",
                "Capacité TAN mesurée du biofiltre",
                known=all(item.get("tan_capacity_mg_n_day") is not None for item in filters),
                required=False,
                section="equipment",
                action="complete-filter",
                rationale="Une capacité TAN mesurée est très informative, mais EcoBiome ne doit pas l’inventer à partir d’un média commercial.",
            )

    required_items = [item for item in items if item["required"] is True]
    known_required = [item for item in required_items if item["status"] == "known"]
    next_actions = [
        {
            "key": item["key"],
            "label": item["label"],
            "section": item["section"],
            "action": item["action"],
            "rationale": item["rationale"],
        }
        for item in items
        if item["status"] == "missing"
    ][:5]
    return {
        "level": level,
        "is_diagnostic": False,
        "message": (
            "Cette couverture décrit uniquement les informations disponibles pour "
            "raisonner sur le milieu ; elle ne constitue pas un score de santé."
        ),
        "known_required_count": len(known_required),
        "required_count": len(required_items),
        "items": items,
        "next_actions": next_actions,
    }


def _operation_public_payload(event: dict[str, object]) -> dict[str, object]:
    return {
        "event_id": event.get("event_id"),
        "occurred_at": event.get("occurred_at"),
        "operation_type": event.get("operation_type"),
        "subject_id": event.get("subject_id"),
        "details": event.get("details", {}),
        "note": event.get("note", ""),
        "event_sha256": event.get("event_sha256"),
    }


def _save_ecology(project_id: UUID, state: dict[str, object]) -> None:
    save_ecology_state(_project_dir(project_id), state)


def _feed_product_by_id(product_id: str) -> dict[str, object] | None:
    for product in load_feed_catalog(_runtime_root()):
        if product.get("id") == product_id:
            return product
    return None


def _target_biomass_g(
    project_id: UUID,
    population_ids: list[str],
) -> tuple[float | None, list[str]]:
    snapshot = _ecology_snapshot(project_id)
    livestock = cast(list[dict[str, object]], snapshot["livestock"])
    if population_ids:
        wanted = set(population_ids)
        selected = [item for item in livestock if str(item.get("id")) in wanted]
        found = {str(item.get("id")) for item in selected}
        missing = sorted(wanted - found)
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"unknown target population ids: {missing}",
            )
    else:
        selected = livestock
    ids = [str(item["id"]) for item in selected if isinstance(item.get("id"), str)]
    biomasses = [item.get("biomass_g") for item in selected]
    if not selected or any(not isinstance(value, (int, float)) for value in biomasses):
        return None, ids
    return sum(float(cast(float, value)) for value in biomasses), ids


def _record_ecology_operation(
    project_id: UUID,
    operation_type: str,
    details: dict[str, object],
    *,
    note: str = "",
    subject_id: str | None = None,
    occurred_at: datetime | None = None,
) -> dict[str, object]:
    event = append_operation(
        _project_dir(project_id),
        project_id=str(project_id),
        event_id=str(uuid4()),
        occurred_at=occurred_at or datetime.now(UTC),
        operation_type=operation_type,
        details=details,
        note=note,
        subject_id=subject_id,
    )
    return _operation_public_payload(event)


def _population_profile(
    *,
    population_id: str,
    kind: Literal["animal", "plant"],
    common_name: str,
    scientific_name: str,
    life_stage: str = "",
    notes: str = "",
) -> BiologicalPopulationV1:
    properties = {
        "schema_version": _POPULATION_SCHEMA_V1,
        "organism_kind": kind,
        "common_name": common_name.strip(),
        "scientific_name": scientific_name.strip(),
        "life_stage": life_stage.strip(),
        "notes": notes.strip(),
    }
    return BiologicalPopulationV1(
        id=population_id,
        population_type=kind,
        label=common_name.strip(),
        zone_ids=(_WATER_ZONE_ID,),
        properties_json=canonical_json_text(properties),
    )


def _replace_populations(
    project_id: UUID,
    populations: tuple[BiologicalPopulationV1, ...],
) -> None:
    profile = _load_profile(project_id)
    updated = EcosystemProfileV1(
        id=profile.id,
        profile_kind=profile.profile_kind,
        label=profile.label,
        structures=profile.structures,
        zones=profile.zones,
        functional_systems=profile.functional_systems,
        populations=populations,
        material_components=profile.material_components,
        flows=profile.flows,
    )
    _replace_profile(project_id, updated)


def _water_source_name(project_id: UUID, water_source_id: str | None) -> str | None:
    if water_source_id is None:
        return None
    for item in _ecology_items(_ecology_state(project_id), "water_sources"):
        if item.get("id") == water_source_id:
            name = item.get("name")
            return name if isinstance(name, str) else None
    raise HTTPException(status_code=422, detail="unknown water source profile")


def _collector_store() -> CollectorStore:
    database = _collector_database_path()
    database.parent.mkdir(parents=True, exist_ok=True)
    store = CollectorStore(database)
    store.initialize()
    return store




@app.get("/dashboard")
def get_dashboard() -> object:
    """Preserve the pre-N6 workspace dashboard endpoint."""
    root = Path("./workspace")
    if not root.exists():
        manifest = ProjectManifest(
            name="EcoBiome Project",
            description="Workspace auto-généré pour le dashboard",
            project_type=ProjectType.OTHER,
            tags=("ecobiome",),
            attributes=(),
        )
        workspace = ProjectWorkspace.create(
            root=root,
            manifest=manifest,
        )
    else:
        workspace = ProjectWorkspace.open(root=root)
    return build_project_dashboard(workspace)


@app.get("/api/health")
def health() -> dict[str, object]:
    """Return local API identity and runtime storage location."""
    return {
        "status": "ok",
        "service": "ecobiome-local-api",
        "bridge_version": _LOCAL_BRIDGE_VERSION,
        "data_root": str(_runtime_root()),
    }


@app.get("/api/water-bodies")
def list_water_bodies() -> list[dict[str, object]]:
    """List locally persisted aquatic projects."""
    result: list[dict[str, object]] = []
    for project_id in _iter_project_ids():
        try:
            result.append(_water_body_payload(project_id))
        except (OSError, TypeError, ValueError):
            continue
    return result


@app.post("/api/water-bodies", status_code=201)
def create_water_body(request: CreateWaterBodyRequest) -> dict[str, object]:
    """Create an N4 profile and its initial N5 water-volume observation."""
    project_id = uuid4()
    project_dir = _project_dir(project_id)
    if project_dir.exists():
        raise HTTPException(status_code=409, detail="project identity collision")

    now = datetime.now(UTC)
    profile = _build_profile(
        project_id=project_id,
        name=request.name,
        kind=request.type,
        capacity_liters=request.volume_liters,
    )
    metadata = {
        "schema_version": _PROJECT_METADATA_SCHEMA,
        "project_id": str(project_id),
        "created_at": now.isoformat(),
    }

    try:
        project_dir.mkdir(parents=True, exist_ok=False)
        _write_json_atomic(_metadata_path(project_id), metadata)
        _write_json_atomic(
            _profile_path(project_id),
            profile.canonical_payload(),
            canonical=True,
        )
        _append_observation(
            project_id=project_id,
            variable=_WATER_VOLUME_VARIABLE,
            value=request.volume_liters,
            unit="L",
            uncertainty=0.0,
            confidence=1.0,
            observed_at=now,
            source="ecobiome-ui",
        )
    except Exception:
        shutil.rmtree(project_dir, ignore_errors=True)
        raise

    return _water_body_payload(project_id)


@app.post("/api/water-bodies/{project_id}/fill-level")
def set_fill_level(
    project_id: UUID,
    request: SetFillLevelRequest,
) -> dict[str, object]:
    """Record current filling as a canonical N5 water-volume observation."""
    try:
        capacity_liters = _nominal_capacity_liters(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc

    observed_at = request.observed_at or datetime.now(UTC)
    target_volume = capacity_liters * request.fill_percent / 100.0
    try:
        _append_observation(
            project_id=project_id,
            variable=_WATER_VOLUME_VARIABLE,
            value=target_volume,
            unit="L",
            uncertainty=0.0,
            confidence=1.0,
            observed_at=observed_at,
            source=request.source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _water_body_payload(project_id)


@app.post("/api/water-bodies/{project_id}/water-exchanges", status_code=201)
def record_water_exchange(
    project_id: UUID,
    request: WaterExchangeRequest,
) -> dict[str, object]:
    """Persist one user-reported N4 water exchange as a canonical N5 event."""
    try:
        capacity_liters = _nominal_capacity_liters(project_id)
        current_volume = _current_volume_liters(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc

    removed = request.removed_volume_liters
    replacement = request.replacement_volume_liters
    if removed == 0 and replacement == 0:
        raise HTTPException(
            status_code=422,
            detail="water exchange must remove or add a non-zero volume",
        )
    if removed > current_volume:
        raise HTTPException(
            status_code=422,
            detail="removed volume exceeds current water volume",
        )
    final_volume = current_volume - removed + replacement
    if final_volume < 0 or final_volume > capacity_liters:
        raise HTTPException(
            status_code=422,
            detail="resulting water volume must stay between 0 and nominal capacity",
        )

    source_name = _water_source_name(project_id, request.water_source_id)
    occurred_at = datetime.now(UTC)
    event_id = uuid4()
    intervention_id = f"water-exchange-{event_id}"
    note = "user-reported water exchange through EcoBiome UI"
    if source_name is not None:
        note = f"{note}; eau de remplacement : {source_name}"
    if request.note.strip():
        note = f"{note}; {request.note.strip()}"
    intervention = WaterExchangeInterventionV1(
        id=intervention_id,
        water_zone_id=_WATER_ZONE_ID,
        removed_volume_decimal=normalize_decimal(str(removed)),
        removed_volume_unit="L",
        replacement_volume_decimal=normalize_decimal(str(replacement)),
        replacement_volume_unit="L",
        replacement_composition=(),
        basis=QuantityBasisV1(
            kind="user_assumption",
            reference_id=intervention_id,
            note=note,
        ),
    )
    event = build_canonical_water_exchange_event_v1(
        project_id=project_id,
        event_id=event_id,
        intervention=intervention,
        occurred_at=occurred_at,
    )
    _project_store(project_id).append(event)
    return {
        "event_id": str(event.event_id),
        "intervention_id": intervention.id,
        "occurred_at": occurred_at.isoformat(),
        "removed_volume_liters": removed,
        "replacement_volume_liters": replacement,
        "previous_volume_liters": current_volume,
        "current_volume_liters": final_volume,
        "capacity_liters": capacity_liters,
        "fill_percent": (final_volume / capacity_liters) * 100.0,
        "water_source_id": request.water_source_id,
        "water_source_name": source_name,
        "composition_status": (
            "profiled_local" if source_name is not None else "unknown"
        ),
    }


@app.get("/api/water-bodies/{project_id}/equipment")
def list_equipment(project_id: UUID) -> list[dict[str, object]]:
    """List user equipment stored as N4 functional systems."""
    try:
        return _list_equipment_payloads(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc


@app.post("/api/water-bodies/{project_id}/equipment", status_code=201)
def add_equipment(
    project_id: UUID,
    request: CreateEquipmentRequest,
) -> dict[str, object]:
    """Add equipment to the durable N4 project topology/configuration."""
    try:
        profile = _load_profile(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc

    equipment_id = f"equipment-{uuid4().hex}"
    properties: dict[str, object] = {
        "schema_version": _EQUIPMENT_SCHEMA_V1,
        "equipment_type": request.equipment_type,
        "manufacturer": request.manufacturer.strip(),
        "model": request.model.strip(),
        "in_service_since": (
            request.in_service_since.isoformat()
            if request.in_service_since is not None
            else None
        ),
        "spectrum": request.spectrum.strip(),
        "filter_media": request.filter_media.strip(),
        "biofilter_maturity": request.biofilter_maturity,
        "inoculated": request.inoculated,
        "last_maintenance_at": (
            request.last_maintenance_at.isoformat()
            if request.last_maintenance_at is not None
            else None
        ),
        "notes": request.notes.strip(),
    }
    for key, value in (
        ("power_watts_decimal", request.power_watts),
        ("daily_runtime_hours_decimal", request.daily_runtime_hours),
        ("flow_lph_decimal", request.flow_lph),
        ("measured_flow_lph_decimal", request.measured_flow_lph),
        ("color_temperature_k_decimal", request.color_temperature_k),
        ("par_surface_umol_m2_s_decimal", request.par_surface_umol_m2_s),
        ("par_bottom_umol_m2_s_decimal", request.par_bottom_umol_m2_s),
        ("media_volume_liters_decimal", request.media_volume_liters),
        ("specific_surface_m2_per_l_decimal", request.specific_surface_m2_per_l),
        ("tan_capacity_mg_n_day_decimal", request.tan_capacity_mg_n_day),
    ):
        properties[key] = (
            normalize_decimal(str(value)) if value is not None else None
        )

    system = FunctionalSystemV1(
        id=equipment_id,
        system_type=f"equipment_{request.equipment_type}",
        label=request.name.strip(),
        zone_ids=(_WATER_ZONE_ID,),
        properties_json=canonical_json_text(properties),
    )
    updated = EcosystemProfileV1(
        id=profile.id,
        profile_kind=profile.profile_kind,
        label=profile.label,
        structures=profile.structures,
        zones=profile.zones,
        functional_systems=profile.functional_systems + (system,),
        populations=profile.populations,
        material_components=profile.material_components,
        flows=profile.flows,
    )
    _replace_profile(project_id, updated)
    _record_ecology_operation(
        project_id,
        "equipment_added",
        {
            "equipment_id": equipment_id,
            "name": request.name.strip(),
            "equipment_type": request.equipment_type,
        },
        note=request.notes,
        subject_id=equipment_id,
    )
    payload = _equipment_payload(system)
    if payload is None:
        raise RuntimeError("new equipment failed inventory projection")
    return payload


@app.delete("/api/water-bodies/{project_id}/equipment/{equipment_id}")
def delete_equipment(project_id: UUID, equipment_id: str) -> dict[str, str]:
    """Remove one user-equipment functional system from the project profile."""
    try:
        profile = _load_profile(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc

    retained: list[FunctionalSystemV1] = []
    found = False
    for system in profile.functional_systems:
        if system.id == equipment_id and _equipment_payload(system) is not None:
            found = True
            continue
        retained.append(system)
    if not found:
        raise HTTPException(status_code=404, detail="equipment not found")

    updated = EcosystemProfileV1(
        id=profile.id,
        profile_kind=profile.profile_kind,
        label=profile.label,
        structures=profile.structures,
        zones=profile.zones,
        functional_systems=tuple(retained),
        populations=profile.populations,
        material_components=profile.material_components,
        flows=profile.flows,
    )
    _replace_profile(project_id, updated)
    _record_ecology_operation(
        project_id,
        "equipment_removed",
        {"equipment_id": equipment_id},
        subject_id=equipment_id,
    )
    return {"deleted_equipment_id": equipment_id}



@app.get("/api/water-bodies/{project_id}/guidance")
def get_guidance(
    project_id: UUID,
    level: ExperienceLevel = "beginner",
) -> dict[str, object]:
    """Return progressive completeness guidance for the selected UI level."""
    try:
        return _guidance_snapshot(project_id, level)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc


@app.get("/api/water-bodies/{project_id}/ecology")
def get_ecology(project_id: UUID) -> dict[str, object]:
    """Return current biological loads, inputs and recent operational history."""
    try:
        return _ecology_snapshot(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc


@app.post("/api/water-bodies/{project_id}/livestock", status_code=201)
def add_livestock(project_id: UUID, request: CreateLivestockRequest) -> dict[str, object]:
    """Register one animal population without putting dynamic abundance in N4 topology."""
    if request.male_count + request.female_count > request.count:
        raise HTTPException(
            status_code=422,
            detail="male_count + female_count cannot exceed total count",
        )
    try:
        profile = _load_profile(project_id)
        state = _ecology_state(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc

    population_id = f"livestock-{uuid4().hex}"
    population = _population_profile(
        population_id=population_id,
        kind="animal",
        common_name=request.common_name,
        scientific_name=request.scientific_name,
        life_stage=request.life_stage,
        notes=request.notes,
    )
    item: dict[str, object] = {
        "id": population_id,
        "common_name": request.common_name.strip(),
        "scientific_name": request.scientific_name.strip(),
        "count_decimal": ecology_decimal_text(request.count),
        "male_count_decimal": ecology_decimal_text(request.male_count),
        "female_count_decimal": ecology_decimal_text(request.female_count),
        "average_mass_g_decimal": (
            ecology_decimal_text(request.average_mass_g)
            if request.average_mass_g is not None
            else None
        ),
        "life_stage": request.life_stage.strip(),
        "notes": request.notes.strip(),
        "created_at": datetime.now(UTC).isoformat(),
    }
    livestock = _ecology_items(state, "livestock")
    livestock.append(item)
    state["livestock"] = livestock
    _replace_populations(project_id, profile.populations + (population,))
    _save_ecology(project_id, state)
    _record_ecology_operation(
        project_id,
        "livestock_added",
        {
            "population_id": population_id,
            "common_name": request.common_name.strip(),
            "scientific_name": request.scientific_name.strip(),
            "count_decimal": ecology_decimal_text(request.count),
            "male_count_decimal": ecology_decimal_text(request.male_count),
            "female_count_decimal": ecology_decimal_text(request.female_count),
            "unknown_sex_count_decimal": ecology_decimal_text(
                request.count - request.male_count - request.female_count
            ),
            "average_mass_g_decimal": item["average_mass_g_decimal"],
        },
        note=request.notes,
        subject_id=population_id,
    )
    return _livestock_payload(item)


@app.post("/api/water-bodies/{project_id}/livestock/{population_id}/adjust")
def adjust_livestock(
    project_id: UUID,
    population_id: str,
    request: AdjustLivestockRequest,
) -> dict[str, object]:
    """Adjust current animal abundance and record the reason append-only."""
    if request.delta_count == 0:
        raise HTTPException(status_code=422, detail="delta_count must be non-zero")
    try:
        state = _ecology_state(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc
    livestock = _ecology_items(state, "livestock")
    target: dict[str, object] | None = None
    for item in livestock:
        if item.get("id") == population_id:
            target = item
            break
    if target is None:
        raise HTTPException(status_code=404, detail="livestock population not found")
    raw_count = target.get("count_decimal")
    if not isinstance(raw_count, str):
        raise TypeError("livestock count_decimal must be a string")
    previous_count = int(float(raw_count))
    previous_payload = _livestock_payload(target)
    sex_key = {
        "male": "male_count_decimal",
        "female": "female_count_decimal",
        "unknown": None,
    }[request.sex]
    previous_sex_count = (
        int(cast(int, previous_payload["unknown_sex_count"]))
        if sex_key is None
        else int(cast(int, previous_payload[f"{request.sex}_count"]))
    )
    next_sex_count = previous_sex_count + request.delta_count
    next_count = previous_count + request.delta_count
    if next_count < 0:
        raise HTTPException(status_code=422, detail="resulting animal count cannot be negative")
    if next_sex_count < 0:
        raise HTTPException(
            status_code=422,
            detail=f"not enough {request.sex} animals for this adjustment",
        )

    male_count = int(cast(int, previous_payload["male_count"]))
    female_count = int(cast(int, previous_payload["female_count"]))
    unknown_count = int(cast(int, previous_payload["unknown_sex_count"]))
    if request.sex == "male":
        male_count = next_sex_count
    elif request.sex == "female":
        female_count = next_sex_count
    else:
        unknown_count = next_sex_count
    if male_count + female_count + unknown_count != next_count:
        raise ValueError("sex-distribution invariant violated")

    target["count_decimal"] = ecology_decimal_text(next_count)
    target["male_count_decimal"] = ecology_decimal_text(male_count)
    target["female_count_decimal"] = ecology_decimal_text(female_count)
    _save_ecology(project_id, state)
    operation_type = {
        "addition": "livestock_added",
        "removal": "livestock_removed",
        "death": "livestock_death",
        "correction": "livestock_corrected",
    }[request.reason]
    _record_ecology_operation(
        project_id,
        operation_type,
        {
            "population_id": population_id,
            "previous_count_decimal": ecology_decimal_text(previous_count),
            "delta_count_decimal": ecology_decimal_text(request.delta_count),
            "current_count_decimal": ecology_decimal_text(next_count),
            "sex": request.sex,
            "male_count_decimal": ecology_decimal_text(male_count),
            "female_count_decimal": ecology_decimal_text(female_count),
            "unknown_sex_count_decimal": ecology_decimal_text(unknown_count),
            "common_name": target.get("common_name", ""),
        },
        note=request.note,
        subject_id=population_id,
    )
    return _livestock_payload(target)


@app.post("/api/water-bodies/{project_id}/livestock/{population_id}/sex-distribution")
def set_livestock_sex_distribution(
    project_id: UUID,
    population_id: str,
    request: SetLivestockSexRequest,
) -> dict[str, object]:
    """Set known male/female counts and keep the remainder explicitly unsexed."""
    try:
        state = _ecology_state(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc
    livestock = _ecology_items(state, "livestock")
    target = next((item for item in livestock if item.get("id") == population_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="livestock population not found")
    raw_count = target.get("count_decimal")
    if not isinstance(raw_count, str):
        raise TypeError("livestock count_decimal must be a string")
    count = int(float(raw_count))
    if request.male_count + request.female_count > count:
        raise HTTPException(
            status_code=422,
            detail="male_count + female_count cannot exceed total count",
        )
    unknown_count = count - request.male_count - request.female_count
    target["male_count_decimal"] = ecology_decimal_text(request.male_count)
    target["female_count_decimal"] = ecology_decimal_text(request.female_count)
    _save_ecology(project_id, state)
    _record_ecology_operation(
        project_id,
        "livestock_sex_distribution_updated",
        {
            "population_id": population_id,
            "count_decimal": ecology_decimal_text(count),
            "male_count_decimal": ecology_decimal_text(request.male_count),
            "female_count_decimal": ecology_decimal_text(request.female_count),
            "unknown_sex_count_decimal": ecology_decimal_text(unknown_count),
            "common_name": target.get("common_name", ""),
        },
        note=request.note,
        subject_id=population_id,
    )
    return _livestock_payload(target)


@app.delete("/api/water-bodies/{project_id}/livestock/{population_id}")
def delete_livestock(project_id: UUID, population_id: str) -> dict[str, str]:
    """Remove a population from current state while retaining its operation history."""
    try:
        profile = _load_profile(project_id)
        state = _ecology_state(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc
    livestock = _ecology_items(state, "livestock")
    target = next((item for item in livestock if item.get("id") == population_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="livestock population not found")
    state["livestock"] = [item for item in livestock if item.get("id") != population_id]
    populations = tuple(item for item in profile.populations if item.id != population_id)
    _replace_populations(project_id, populations)
    _save_ecology(project_id, state)
    _record_ecology_operation(
        project_id,
        "livestock_population_closed",
        {
            "population_id": population_id,
            "common_name": target.get("common_name", ""),
            "final_count_decimal": target.get("count_decimal"),
        },
        subject_id=population_id,
    )
    return {"deleted_population_id": population_id}


@app.post("/api/water-bodies/{project_id}/plants", status_code=201)
def add_plant(project_id: UUID, request: CreatePlantRequest) -> dict[str, object]:
    """Register one plant population and current coverage."""
    try:
        profile = _load_profile(project_id)
        state = _ecology_state(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc
    population_id = f"plant-{uuid4().hex}"
    population = _population_profile(
        population_id=population_id,
        kind="plant",
        common_name=request.common_name,
        scientific_name=request.scientific_name,
        notes=request.notes,
    )
    item: dict[str, object] = {
        "id": population_id,
        "common_name": request.common_name.strip(),
        "scientific_name": request.scientific_name.strip(),
        "count_decimal": (
            ecology_decimal_text(request.count) if request.count is not None else None
        ),
        "coverage_percent_decimal": (
            ecology_decimal_text(request.coverage_percent)
            if request.coverage_percent is not None
            else None
        ),
        "notes": request.notes.strip(),
        "created_at": datetime.now(UTC).isoformat(),
    }
    plants = _ecology_items(state, "plants")
    plants.append(item)
    state["plants"] = plants
    _replace_populations(project_id, profile.populations + (population,))
    _save_ecology(project_id, state)
    _record_ecology_operation(
        project_id,
        "plant_added",
        {
            "population_id": population_id,
            "common_name": request.common_name.strip(),
            "scientific_name": request.scientific_name.strip(),
            "count_decimal": item["count_decimal"],
            "coverage_percent_decimal": item["coverage_percent_decimal"],
        },
        note=request.notes,
        subject_id=population_id,
    )
    return _plant_payload(item)


@app.delete("/api/water-bodies/{project_id}/plants/{population_id}")
def delete_plant(project_id: UUID, population_id: str) -> dict[str, str]:
    try:
        profile = _load_profile(project_id)
        state = _ecology_state(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc
    plants = _ecology_items(state, "plants")
    target = next((item for item in plants if item.get("id") == population_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="plant population not found")
    state["plants"] = [item for item in plants if item.get("id") != population_id]
    populations = tuple(item for item in profile.populations if item.id != population_id)
    _replace_populations(project_id, populations)
    _save_ecology(project_id, state)
    _record_ecology_operation(
        project_id,
        "plant_removed",
        {"population_id": population_id, "common_name": target.get("common_name", "")},
        subject_id=population_id,
    )
    return {"deleted_population_id": population_id}


@app.post("/api/water-bodies/{project_id}/water-sources", status_code=201)
def add_water_source(project_id: UUID, request: CreateWaterSourceRequest) -> dict[str, object]:
    try:
        state = _ecology_state(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc
    source_id = f"water-source-{uuid4().hex}"
    item: dict[str, object] = {
        "id": source_id,
        "name": request.name.strip(),
        "source_type": request.source_type,
        "temperature_c_decimal": ecology_decimal_text(request.temperature_c) if request.temperature_c is not None else None,
        "ph_decimal": ecology_decimal_text(request.ph) if request.ph is not None else None,
        "kh_dkh_decimal": ecology_decimal_text(request.kh_dkh) if request.kh_dkh is not None else None,
        "gh_dgh_decimal": ecology_decimal_text(request.gh_dgh) if request.gh_dgh is not None else None,
        "conductivity_us_cm_decimal": ecology_decimal_text(request.conductivity_us_cm) if request.conductivity_us_cm is not None else None,
        "nitrate_mg_l_decimal": ecology_decimal_text(request.nitrate_mg_l) if request.nitrate_mg_l is not None else None,
        "nitrite_mg_l_decimal": ecology_decimal_text(request.nitrite_mg_l) if request.nitrite_mg_l is not None else None,
        "ammonia_mg_l_decimal": ecology_decimal_text(request.ammonia_mg_l) if request.ammonia_mg_l is not None else None,
        "phosphate_mg_l_decimal": ecology_decimal_text(request.phosphate_mg_l) if request.phosphate_mg_l is not None else None,
        "chloride_mg_l_decimal": ecology_decimal_text(request.chloride_mg_l) if request.chloride_mg_l is not None else None,
        "calcium_mg_l_decimal": ecology_decimal_text(request.calcium_mg_l) if request.calcium_mg_l is not None else None,
        "magnesium_mg_l_decimal": ecology_decimal_text(request.magnesium_mg_l) if request.magnesium_mg_l is not None else None,
        "salinity_g_l_decimal": ecology_decimal_text(request.salinity_g_l) if request.salinity_g_l is not None else None,
        "notes": request.notes.strip(),
        "created_at": datetime.now(UTC).isoformat(),
    }
    sources = _ecology_items(state, "water_sources")
    sources.append(item)
    state["water_sources"] = sources
    _save_ecology(project_id, state)
    _record_ecology_operation(
        project_id,
        "water_source_added",
        {"water_source_id": source_id, "name": request.name.strip(), "source_type": request.source_type},
        note=request.notes,
        subject_id=source_id,
    )
    return _water_source_payload(item)


@app.delete("/api/water-bodies/{project_id}/water-sources/{source_id}")
def delete_water_source(project_id: UUID, source_id: str) -> dict[str, str]:
    try:
        state = _ecology_state(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc
    sources = _ecology_items(state, "water_sources")
    target = next((item for item in sources if item.get("id") == source_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="water source not found")
    state["water_sources"] = [item for item in sources if item.get("id") != source_id]
    _save_ecology(project_id, state)
    _record_ecology_operation(
        project_id,
        "water_source_removed",
        {"water_source_id": source_id, "name": target.get("name", "")},
        subject_id=source_id,
    )
    return {"deleted_water_source_id": source_id}


@app.post("/api/water-bodies/{project_id}/substrate-layers", status_code=201)
def add_substrate_layer(project_id: UUID, request: CreateSubstrateLayerRequest) -> dict[str, object]:
    if (
        request.grain_min_mm is not None
        and request.grain_max_mm is not None
        and request.grain_min_mm > request.grain_max_mm
    ):
        raise HTTPException(status_code=422, detail="grain_min_mm cannot exceed grain_max_mm")
    try:
        state = _ecology_state(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc
    layer_id = f"substrate-{uuid4().hex}"
    item: dict[str, object] = {
        "id": layer_id,
        "material": request.material.strip(),
        "thickness_cm_decimal": ecology_decimal_text(request.thickness_cm),
        "grain_min_mm_decimal": ecology_decimal_text(request.grain_min_mm) if request.grain_min_mm is not None else None,
        "grain_max_mm_decimal": ecology_decimal_text(request.grain_max_mm) if request.grain_max_mm is not None else None,
        "organic": request.organic,
        "notes": request.notes.strip(),
        "created_at": datetime.now(UTC).isoformat(),
    }
    layers = _ecology_items(state, "substrate_layers")
    layers.append(item)
    state["substrate_layers"] = layers
    _save_ecology(project_id, state)
    _record_ecology_operation(
        project_id,
        "substrate_layer_added",
        {"layer_id": layer_id, "material": request.material.strip(), "thickness_cm_decimal": item["thickness_cm_decimal"]},
        note=request.notes,
        subject_id=layer_id,
    )
    return _substrate_payload(item)


@app.delete("/api/water-bodies/{project_id}/substrate-layers/{layer_id}")
def delete_substrate_layer(project_id: UUID, layer_id: str) -> dict[str, str]:
    try:
        state = _ecology_state(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc
    layers = _ecology_items(state, "substrate_layers")
    target = next((item for item in layers if item.get("id") == layer_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="substrate layer not found")
    state["substrate_layers"] = [item for item in layers if item.get("id") != layer_id]
    _save_ecology(project_id, state)
    _record_ecology_operation(
        project_id,
        "substrate_layer_removed",
        {"layer_id": layer_id, "material": target.get("material", "")},
        subject_id=layer_id,
    )
    return {"deleted_layer_id": layer_id}


@app.get("/api/feed-products")
def list_feed_products() -> list[dict[str, object]]:
    """List the shared local feed-product catalog."""
    return [public_product(item) for item in load_feed_catalog(_runtime_root())]


@app.post("/api/feed-products", status_code=201)
def add_feed_product(request: CreateFeedProductRequest) -> dict[str, object]:
    """Create one structured local feed product."""
    products = load_feed_catalog(_runtime_root())
    product = create_manual_product(
        product_id=f"feed-{uuid4().hex}",
        brand=request.brand,
        name=request.name,
        variant=request.variant,
        feed_category=request.feed_category,
        form=request.form,
        dietary_role=request.dietary_role,
        target_species_text=request.target_species_text,
        feeding_zone=request.feeding_zone,
        ingredients_text=request.ingredients_text,
        crude_protein_percent=request.crude_protein_percent,
        crude_fat_percent=request.crude_fat_percent,
        crude_fibre_percent=request.crude_fibre_percent,
        moisture_percent=request.moisture_percent,
        crude_ash_percent=request.crude_ash_percent,
        phosphorus_percent=request.phosphorus_percent,
        additives_text=request.additives_text,
        feeding_guide_text=request.feeding_guide_text,
        source_url=request.source_url,
        notes=request.notes,
    )
    products.append(product)
    save_feed_catalog(_runtime_root(), products)
    return public_product(product)


@app.post("/api/feed-products/import-url", status_code=201)
def import_feed_product(request: ImportFeedProductRequest) -> dict[str, object]:
    """Import structured factual product data from a trusted product page."""
    try:
        html, final_url = fetch_trusted_product_html(request.url)
        product = parse_product_html(
            html,
            final_url,
            product_id=f"feed-{uuid4().hex}",
        )
    except (RequestException, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    product["source_content_sha256"] = product_source_fingerprint(html)
    products = load_feed_catalog(_runtime_root())
    products.append(product)
    save_feed_catalog(_runtime_root(), products)
    return public_product(product)


@app.post("/api/water-bodies/{project_id}/feeding", status_code=201)
def record_feeding(project_id: UUID, request: FeedingRequest) -> dict[str, object]:
    try:
        _load_profile(project_id)
        current_volume = _current_volume_liters(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc

    product: dict[str, object] | None = None
    if request.feed_product_id:
        product = _feed_product_by_id(request.feed_product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="feed product not found")

    food_name = (
        str(product.get("name", "")).strip()
        if product is not None
        else request.food_name.strip()
    )
    if not food_name:
        raise HTTPException(
            status_code=422,
            detail="feed_product_id or food_name is required",
        )

    target_biomass_g, target_ids = _target_biomass_g(
        project_id,
        request.target_population_ids,
    )
    feed_load = calculate_feed_load(
        amount_g=request.amount_g,
        water_volume_liters=current_volume,
        product=product,
        fallback_protein_percent=request.protein_percent,
        target_biomass_g=target_biomass_g,
        consumed_percent=request.consumed_percent,
    )

    product_snapshot: dict[str, object] | None = None
    if product is not None:
        product_snapshot = {
            "id": product.get("id"),
            "revision": product.get("revision"),
            "brand": product.get("brand"),
            "name": product.get("name"),
            "variant": product.get("variant"),
            "form": product.get("form"),
            "crude_protein_percent_decimal": product.get(
                "crude_protein_percent_decimal"
            ),
            "crude_fat_percent_decimal": product.get("crude_fat_percent_decimal"),
            "crude_fibre_percent_decimal": product.get(
                "crude_fibre_percent_decimal"
            ),
            "moisture_percent_decimal": product.get("moisture_percent_decimal"),
            "phosphorus_percent_decimal": product.get("phosphorus_percent_decimal"),
            "product_sha256": product.get("product_sha256"),
            "source_url": product.get("source_url"),
        }

    details: dict[str, object] = {
        "feed_product_id": request.feed_product_id,
        "food_name": food_name,
        "amount_g_decimal": ecology_decimal_text(request.amount_g),
        "protein_percent_decimal": (
            product.get("crude_protein_percent_decimal")
            if product is not None
            else (
                ecology_decimal_text(request.protein_percent)
                if request.protein_percent is not None
                else None
            )
        ),
        "target_population_ids": target_ids,
        "target_biomass_g_decimal": (
            ecology_decimal_text(target_biomass_g)
            if target_biomass_g is not None
            else None
        ),
        "consumed_percent_decimal": (
            ecology_decimal_text(request.consumed_percent)
            if request.consumed_percent is not None
            else None
        ),
        "feed_product_snapshot": product_snapshot,
        "feed_load_estimate": feed_load,
    }
    return _record_ecology_operation(
        project_id,
        "feeding",
        details,
        note=request.note,
        subject_id=request.feed_product_id,
        occurred_at=request.occurred_at,
    )


@app.post("/api/water-bodies/{project_id}/top-ups", status_code=201)
def record_top_up(project_id: UUID, request: TopUpRequest) -> dict[str, object]:
    try:
        capacity = _nominal_capacity_liters(project_id)
        current = _current_volume_liters(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc
    source_name = _water_source_name(project_id, request.water_source_id)
    final = current + request.volume_liters
    if final > capacity:
        raise HTTPException(status_code=422, detail="top-up exceeds nominal capacity")
    occurred_at = request.occurred_at or datetime.now(UTC)
    source_token = request.water_source_id or "unspecified"
    _append_observation(
        project_id=project_id,
        variable=_WATER_VOLUME_VARIABLE,
        value=final,
        unit="L",
        uncertainty=0.0,
        confidence=1.0,
        observed_at=occurred_at,
        source=f"ecobiome-ui-top-up:{source_token}",
    )
    operation = _record_ecology_operation(
        project_id,
        "top_up",
        {
            "volume_liters_decimal": ecology_decimal_text(request.volume_liters),
            "previous_volume_liters_decimal": ecology_decimal_text(current),
            "current_volume_liters_decimal": ecology_decimal_text(final),
            "water_source_id": request.water_source_id,
            "water_source_name": source_name,
        },
        note=request.note,
        occurred_at=occurred_at,
    )
    operation["water_body"] = _water_body_payload(project_id)
    return operation


@app.post("/api/water-bodies/{project_id}/operations", status_code=201)
def record_ecosystem_operation(
    project_id: UUID,
    request: EcosystemOperationRequest,
) -> dict[str, object]:
    try:
        _load_profile(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc
    details: dict[str, object] = {
        "label": request.label.strip(),
        "quantity_decimal": ecology_decimal_text(request.quantity) if request.quantity is not None else None,
        "unit": request.unit.strip(),
    }
    return _record_ecology_operation(
        project_id,
        request.operation_type,
        details,
        note=request.note,
        occurred_at=request.occurred_at,
    )


@app.get("/api/water-bodies/{project_id}/measurements")
def list_measurements(project_id: UUID) -> list[dict[str, object]]:
    """List canonical N5 measurements projected for the UI."""
    try:
        return _measurement_payloads(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc


@app.post("/api/water-bodies/{project_id}/measurements", status_code=201)
def add_measurement(
    project_id: UUID,
    request: AddMeasurementRequest,
) -> dict[str, object]:
    """Append one user measurement through the N5 canonical seam."""
    try:
        _load_profile(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc

    variable, canonical_unit, display_unit = _METRIC_CONFIG[request.metric]
    observed_at = request.observed_at or datetime.now(UTC)
    canonical_value = request.value * _METRIC_INPUT_TO_CANONICAL_FACTOR.get(
        request.metric,
        1.0,
    )
    try:
        payload = _append_observation(
            project_id=project_id,
            variable=variable,
            value=canonical_value,
            unit=canonical_unit,
            uncertainty=request.uncertainty,
            confidence=request.confidence,
            observed_at=observed_at,
            source=request.source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    observation_id = payload["observation_id"]
    return {
        "id": observation_id,
        "water_body_id": str(project_id),
        "metric": request.metric,
        "value": request.value,
        "unit": display_unit,
        "recorded_at": observed_at.isoformat(),
    }


@app.get("/api/measurements")
def list_all_measurements() -> list[dict[str, object]]:
    """List all canonical N5 measurements across local projects."""
    result: list[dict[str, object]] = []
    for project_id in _iter_project_ids():
        try:
            result.extend(_measurement_payloads(project_id))
        except (OSError, TypeError, ValueError):
            continue
    result.sort(key=lambda item: str(item["recorded_at"]))
    return result


@app.get("/api/water-bodies/{project_id}/organisms")
def list_organisms(project_id: UUID) -> list[dict[str, object]]:
    """Return the N6 placeholder until organism editing is bridged."""
    try:
        _load_profile(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="water body not found") from exc
    return []


@app.get("/api/diagnostics")
def list_diagnostics() -> list[dict[str, object]]:
    """Return no inferred diagnostics until the reasoning bridge is explicit."""
    return []


@app.get("/api/diagnostics/{diagnostic_id}/findings")
def list_diagnostic_findings(diagnostic_id: str) -> list[dict[str, object]]:
    """Return no inferred findings until the reasoning bridge is explicit."""
    del diagnostic_id
    return []


@app.get("/api/media")
def list_media() -> list[dict[str, object]]:
    """Return the N6 placeholder until media persistence is bridged."""
    return []


_JOURNAL_METRIC_TITLES = {
    "temperature": "Mesure de température",
    "ph": "Mesure du pH",
    "ammonia": "Mesure d’ammoniaque / ammonium",
    "tan": "Mesure du TAN",
    "nitrite": "Mesure des nitrites",
    "nitrate": "Mesure des nitrates",
    "oxygen": "Mesure de l’oxygène dissous",
    "phosphate": "Mesure des phosphates",
    "iron": "Mesure du fer",
    "co2": "Mesure du CO₂",
    "gh": "Mesure de la dureté générale (GH)",
    "kh": "Mesure de l’alcalinité / dureté carbonatée (KH)",
    "conductivity": "Mesure de la conductivité",
    "chloride": "Mesure des chlorures",
    "tss": "Mesure des matières en suspension",
    "calcium": "Mesure du calcium",
    "magnesium": "Mesure du magnésium",
    "salinity": "Mesure de la salinité",
    "orp": "Mesure du potentiel redox",
    "oxygen_saturation": "Mesure de la saturation en oxygène",
    "water_depth": "Mesure de la profondeur d’eau",
    "par_surface": "Mesure du PAR en surface",
    "par_bottom": "Mesure du PAR au fond",
    "algae_coverage": "Observation de la couverture algale",
    "periphyton_coverage": "Observation du périphyton",
}

_JOURNAL_METRIC_NOUNS = {
    "temperature": "température de l’eau",
    "ph": "pH",
    "ammonia": "concentration en ammoniaque / ammonium",
    "tan": "azote ammoniacal total (TAN)",
    "nitrite": "concentration en nitrites",
    "nitrate": "concentration en nitrates",
    "oxygen": "concentration en oxygène dissous",
    "phosphate": "concentration en phosphates",
    "iron": "concentration en fer",
    "co2": "concentration en CO₂",
    "gh": "dureté générale (GH)",
    "kh": "alcalinité / dureté carbonatée (KH)",
    "conductivity": "conductivité électrique",
    "chloride": "concentration en chlorures",
    "tss": "matières totales en suspension",
    "calcium": "concentration en calcium",
    "magnesium": "concentration en magnésium",
    "salinity": "salinité",
    "orp": "potentiel d’oxydoréduction",
    "oxygen_saturation": "saturation en oxygène dissous",
    "water_depth": "profondeur d’eau",
    "par_surface": "rayonnement photosynthétiquement actif en surface",
    "par_bottom": "rayonnement photosynthétiquement actif au fond",
    "algae_coverage": "couverture algale visible",
    "periphyton_coverage": "couverture de périphyton",
}


def _journal_fr_number(raw: str) -> str:
    """Render one canonical decimal with French punctuation."""
    return raw.replace(".", ",")


def _journal_fr_float(value: float) -> str:
    """Render a calculated display number without fake precision."""
    raw = f"{value:.2f}".rstrip("0").rstrip(".")
    return _journal_fr_number(raw)


def _journal_typed_decimal(container: object, field_name: str) -> str:
    """Read one canonical typed decimal from a quantity-like object."""
    if not isinstance(container, dict):
        raise TypeError(f"{field_name} must be an object")
    typed_value = container.get("value")
    if not isinstance(typed_value, dict):
        raise TypeError(f"{field_name}.value must be a typed decimal")
    raw_value = typed_value.get("value")
    if not isinstance(raw_value, str):
        raise TypeError(f"{field_name}.value.value must be a string")
    return raw_value


def _journal_technical_content(event: CanonicalProjectEventV1) -> str:
    """Keep canonical identities available without exposing them by default."""
    payload = {
        "event_id": str(event.event_id),
        "project_id": str(event.project_id),
        "event_type": event.event_type.value,
        "occurred_at": event.occurred_at.isoformat(),
        "subject_id": event.subject_id,
        "payload_schema_version": event.payload_schema_version,
        "canonical_payload_sha256": event.canonical_payload_sha256,
        "canonical_event_sha256": event.canonical_event_sha256,
        "canonical_payload": event.canonical_payload,
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )


def _journal_user_note(intervention: dict[str, object]) -> str:
    """Recover the optional user note from the intervention epistemic basis."""
    basis = intervention.get("basis")
    if not isinstance(basis, dict):
        return ""
    note = basis.get("note")
    if not isinstance(note, str):
        return ""
    prefix = "user-reported water exchange through EcoBiome UI"
    normalized = note.strip()
    if normalized == prefix:
        return ""
    if normalized.startswith(prefix + ";"):
        return normalized[len(prefix) + 1 :].strip()
    return normalized



def _operation_detail_text(details: dict[str, object], key: str) -> str:
    value = details.get(key)
    return value if isinstance(value, str) else ""


def _journal_operation_entry(
    *,
    water_body_name: str,
    event: dict[str, object],
) -> dict[str, object]:
    operation_type_raw = event.get("operation_type")
    operation_type = operation_type_raw if isinstance(operation_type_raw, str) else "other"
    details_raw = event.get("details")
    details = cast(dict[str, object], details_raw) if isinstance(details_raw, dict) else {}
    note_raw = event.get("note")
    note = note_raw.strip() if isinstance(note_raw, str) else ""
    title = "Intervention sur le milieu"
    summary = f"Intervention enregistrée pour « {water_body_name} »."
    content = summary

    if operation_type == "feeding":
        food = _operation_detail_text(details, "food_name") or "aliment"
        amount = _operation_detail_text(details, "amount_g_decimal")
        protein = _operation_detail_text(details, "protein_percent_decimal")
        title = "Nourrissage"
        summary = f"{_journal_fr_number(amount)} g de {food} distribués." if amount else f"Nourrissage avec {food}."
        content = (
            f"Un nourrissage a été enregistré pour le milieu « {water_body_name} ». "
            f"{_journal_fr_number(amount)} g de {food} ont été distribués."
            if amount
            else f"Un nourrissage avec {food} a été enregistré pour le milieu « {water_body_name} »."
        )
        if protein:
            content += f" La teneur en protéines renseignée est de {_journal_fr_number(protein)} %."
        target_biomass = _operation_detail_text(details, "target_biomass_g_decimal")
        if target_biomass:
            content += (
                f" La biomasse animale ciblée connue est de "
                f"{_journal_fr_number(target_biomass)} g."
            )
        impact_raw = details.get("feed_load_estimate")
        if isinstance(impact_raw, dict):
            impact = cast(dict[str, object], impact_raw)
            feed_rate = _operation_detail_text(impact, "feed_rate_percent_biomass_decimal")
            protein_n = _operation_detail_text(
                impact,
                "estimated_protein_nitrogen_mg_decimal",
            )
            tan_upper = _operation_detail_text(
                impact,
                "tan_n_upper_bound_delta_mg_l_decimal",
            )
            if feed_rate:
                content += (
                    f" Cela représente {_journal_fr_number(feed_rate)} % de la biomasse "
                    "ciblée connue."
                )
            if protein_n:
                content += (
                    f" L’apport protéique correspond à environ "
                    f"{_journal_fr_number(protein_n)} mg d’azote protéique selon la "
                    "conversion conventionnelle protéines/6,25."
                )
            if tan_upper:
                content += (
                    f" La borne stœchiométrique maximale correspondante serait de "
                    f"{_journal_fr_number(tan_upper)} mg N/L de TAN si tout cet azote "
                    "ingéré était minéralisé immédiatement ; ce n’est pas une prédiction "
                    "de la variation réellement observée."
                )
    elif operation_type in {
        "livestock_added",
        "livestock_removed",
        "livestock_death",
        "livestock_corrected",
        "livestock_population_closed",
        "livestock_sex_distribution_updated",
    }:
        common_name = _operation_detail_text(details, "common_name") or "population animale"
        delta = _operation_detail_text(details, "delta_count_decimal")
        titles = {
            "livestock_added": "Ajout d’animaux",
            "livestock_removed": "Retrait d’animaux",
            "livestock_death": "Mortalité enregistrée",
            "livestock_corrected": "Correction d’effectif animal",
            "livestock_population_closed": "Population animale retirée du suivi",
            "livestock_sex_distribution_updated": "Répartition mâles / femelles mise à jour",
        }
        title = titles[operation_type]
        if delta:
            summary = f"{common_name} : variation de {_journal_fr_number(delta)} individu(s)."
        else:
            count = _operation_detail_text(details, "count_decimal")
            summary = f"{common_name} : {count} individu(s) enregistrés." if count else common_name
        content = f"{title} pour « {water_body_name} ». {summary}"
    elif operation_type in {"plant_added", "plant_removed", "plant_pruning"}:
        common_name = _operation_detail_text(details, "common_name") or _operation_detail_text(details, "label") or "végétation"
        title = {
            "plant_added": "Ajout de plantes",
            "plant_removed": "Retrait de plantes",
            "plant_pruning": "Taille des plantes",
        }[operation_type]
        summary = common_name
        content = f"{title} dans le milieu « {water_body_name} » : {common_name}."
    elif operation_type == "top_up":
        volume = _operation_detail_text(details, "volume_liters_decimal")
        current = _operation_detail_text(details, "current_volume_liters_decimal")
        source = _operation_detail_text(details, "water_source_name")
        title = "Complément d’eau après évaporation"
        summary = f"{_journal_fr_number(volume)} L ajoutés" if volume else "Complément d’eau enregistré"
        if source:
            summary += f" depuis « {source} »"
        summary += "."
        content = f"Un complément d’eau a été enregistré pour le milieu « {water_body_name} ». {summary}"
        if current:
            content += f" Le volume d’eau après ajout est de {_journal_fr_number(current)} L."
        content += " Cette action est distinguée d’un changement d’eau : aucun volume d’eau du milieu n’a été retiré."
    elif operation_type in {"equipment_added", "equipment_removed"}:
        name = _operation_detail_text(details, "name") or "matériel"
        title = "Matériel ajouté" if operation_type == "equipment_added" else "Matériel retiré"
        summary = name
        content = f"{title} pour le milieu « {water_body_name} » : {name}."
    elif operation_type in {"water_source_added", "water_source_removed"}:
        name = _operation_detail_text(details, "name") or "profil d’eau"
        title = "Profil d’eau créé" if operation_type == "water_source_added" else "Profil d’eau retiré"
        summary = name
        content = f"{title} pour le milieu « {water_body_name} » : {name}."
    elif operation_type in {"substrate_layer_added", "substrate_layer_removed", "substrate_maintenance"}:
        material = _operation_detail_text(details, "material") or _operation_detail_text(details, "label") or "substrat"
        title = {
            "substrate_layer_added": "Couche de substrat ajoutée",
            "substrate_layer_removed": "Couche de substrat retirée",
            "substrate_maintenance": "Entretien du substrat",
        }[operation_type]
        summary = material
        content = f"{title} dans le milieu « {water_body_name} » : {material}."
    elif operation_type in {
        "fertilization",
        "bacteria_addition",
        "co2_change",
        "water_treatment",
        "siphoning",
    }:
        title = {
            "fertilization": "Fertilisation",
            "bacteria_addition": "Ajout de bactéries",
            "co2_change": "Modification du CO₂",
            "water_treatment": "Traitement de l’eau",
            "siphoning": "Siphonnage du fond",
        }[operation_type]
        label = _operation_detail_text(details, "label") or title
        summary = label
        content = (
            f"{title} enregistré pour le milieu « {water_body_name} » : {label}."
        )
    elif operation_type == "filter_maintenance":
        title = "Entretien de la filtration"
        summary = _operation_detail_text(details, "label") or "Entretien du filtre enregistré."
        content = f"Un entretien de la filtration a été enregistré pour « {water_body_name} » : {summary}."
    elif operation_type == "power_outage":
        title = "Coupure ou arrêt électrique"
        summary = _operation_detail_text(details, "label") or "Arrêt électrique enregistré."
        content = f"Une interruption électrique a été enregistrée pour « {water_body_name} » : {summary}."
    elif operation_type in {"additive", "medication"}:
        title = "Ajout d’un produit" if operation_type == "additive" else "Traitement / médicament"
        label = _operation_detail_text(details, "label") or "produit non précisé"
        quantity = _operation_detail_text(details, "quantity_decimal")
        unit = _operation_detail_text(details, "unit")
        summary = label
        if quantity:
            summary += f" — {_journal_fr_number(quantity)} {unit}".rstrip()
        content = f"{title} dans le milieu « {water_body_name} » : {summary}."
    else:
        label = _operation_detail_text(details, "label")
        if label:
            summary = label
            content = f"Une intervention a été enregistrée pour « {water_body_name} » : {label}."

    if note:
        content += f"\n\nNote de l’utilisateur : {note}."
    occurred_at = event.get("occurred_at")
    event_id = event.get("event_id")
    source_ref = event.get("subject_id") or event_id
    return {
        "id": str(event_id),
        "title": title,
        "source": "manual",
        "source_ref": str(source_ref),
        "tags": ["n7", "intervention", operation_type],
        "summary": summary,
        "content": content,
        "technical_content": json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True),
        "event_kind": "intervention",
        "water_body_name": water_body_name,
        "created_at": str(occurred_at),
    }


@app.get("/api/journal")
def list_journal() -> list[dict[str, object]]:
    """Project canonical N5 events as a human-readable French journal."""
    entries: list[dict[str, object]] = []
    for project_id in _iter_project_ids():
        try:
            profile = _load_profile(project_id)
            capacity_liters = _nominal_capacity_liters(project_id)
            events = _project_store(project_id).all()
        except (OSError, TypeError, ValueError):
            continue

        current_volume_liters: float | None = None
        for event in events:
            payload = event.canonical_payload
            event_kind = event.event_type.value
            title = "Événement scientifique"
            summary = f"Événement enregistré pour « {profile.label} »."
            content = summary
            tags: list[str] = ["n5", event_kind]

            if event_kind == "observation":
                quantity = payload.get("quantity")
                if not isinstance(quantity, dict):
                    raise TypeError("observation quantity must be an object")
                variable_id = quantity.get("variable_id")
                if not isinstance(variable_id, str):
                    raise TypeError("observation variable_id must be a string")
                raw_value = _journal_typed_decimal(quantity, "quantity")
                value = float(raw_value)
                source = payload.get("source")
                source_text = source if isinstance(source, str) else ""
                unit = quantity.get("unit")
                unit_text = unit if isinstance(unit, str) else ""
                display_value = _journal_fr_number(raw_value)

                if variable_id == _WATER_VOLUME_VARIABLE.identifier:
                    current_volume_liters = value
                    if source_text.startswith("ecobiome-ui-top-up:"):
                        # The N7 operation carries the human-readable top-up entry;
                        # keep the N5 volume observation as the canonical state fact.
                        continue
                    fill_percent = (
                        value / capacity_liters * 100.0
                        if capacity_liters > 0
                        else 0.0
                    )
                    fill_text = _journal_fr_float(fill_percent)
                    if source_text == "ecobiome-ui":
                        title = "Mise en eau initiale"
                        summary = (
                            f"Volume initial : {display_value} L "
                            f"({fill_text} % de la capacité)."
                        )
                        content = (
                            f"Le milieu « {profile.label} » a été enregistré avec "
                            f"un volume d’eau initial de {display_value} L. "
                            f"Sa capacité nominale est de "
                            f"{_journal_fr_float(capacity_liters)} L, soit un "
                            f"remplissage de {fill_text} %."
                        )
                        tags.append("mise-en-eau")
                    else:
                        title = "Ajustement du niveau d’eau"
                        summary = (
                            f"Niveau d’eau : {display_value} L, soit "
                            f"{fill_text} % de la capacité."
                        )
                        content = (
                            f"Le niveau d’eau du milieu « {profile.label} » a été "
                            f"ajusté à {display_value} L. Cela correspond à "
                            f"{fill_text} % de sa capacité nominale de "
                            f"{_journal_fr_float(capacity_liters)} L."
                        )
                        tags.append("niveau-eau")
                else:
                    metric = _VARIABLE_TO_METRIC.get(variable_id)
                    if metric is not None:
                        title = _JOURNAL_METRIC_TITLES[metric]
                        noun = _JOURNAL_METRIC_NOUNS[metric]
                        _variable, _canonical_unit, display_unit = (
                            _METRIC_CONFIG[metric]
                        )
                        display_numeric = value * _METRIC_CANONICAL_TO_DISPLAY_FACTOR.get(
                            metric,
                            1.0,
                        )
                        formatted = (
                            f"{_journal_fr_float(display_numeric)} {display_unit}".strip()
                        )
                        summary = f"{noun.capitalize()} : {formatted}."
                        content = (
                            f"Une mesure de {noun} a été enregistrée pour le milieu "
                            f"« {profile.label} ». La valeur observée est de "
                            f"{formatted}. Cette observation a été saisie "
                            f"manuellement dans EcoBiome."
                        )
                        tags.extend(("mesure", metric))
                    else:
                        title = "Observation scientifique"
                        formatted = f"{display_value} {unit_text}".strip()
                        summary = (
                            f"{variable_id} : {formatted} pour « {profile.label} »."
                        )
                        content = (
                            f"Une observation de « {variable_id} » a été enregistrée "
                            f"pour le milieu « {profile.label} », avec une valeur de "
                            f"{formatted}."
                        )
                        tags.append("observation")

            elif event_kind == "intervention":
                intervention = payload.get("intervention")
                if not isinstance(intervention, dict):
                    raise TypeError("intervention payload must be an object")
                if (
                    intervention.get("schema_version")
                    == "ecobiome-water-exchange-intervention-v1"
                ):
                    removed = _journal_typed_decimal(
                        intervention.get("removed_volume"),
                        "removed_volume",
                    )
                    replacement = _journal_typed_decimal(
                        intervention.get("replacement_volume"),
                        "replacement_volume",
                    )
                    removed_value = float(removed)
                    replacement_value = float(replacement)
                    previous_volume = current_volume_liters
                    if current_volume_liters is not None:
                        current_volume_liters = (
                            current_volume_liters
                            - removed_value
                            + replacement_value
                        )
                    title = "Changement d’eau"
                    summary = (
                        f"{_journal_fr_number(removed)} L retirés, "
                        f"{_journal_fr_number(replacement)} L ajoutés."
                    )
                    paragraphs = [
                        (
                            f"Un changement d’eau a été enregistré pour le milieu "
                            f"« {profile.label} » : "
                            f"{_journal_fr_number(removed)} L ont été retirés puis "
                            f"{_journal_fr_number(replacement)} L d’eau ont été "
                            f"ajoutés."
                        )
                    ]
                    if (
                        previous_volume is not None
                        and current_volume_liters is not None
                    ):
                        if abs(previous_volume - current_volume_liters) < 1e-12:
                            paragraphs.append(
                                "Le volume total est resté à "
                                f"{_journal_fr_float(current_volume_liters)} L."
                            )
                        else:
                            paragraphs.append(
                                "Le volume d’eau est passé de "
                                f"{_journal_fr_float(previous_volume)} L à "
                                f"{_journal_fr_float(current_volume_liters)} L."
                            )
                        fill_percent = (
                            current_volume_liters / capacity_liters * 100.0
                            if capacity_liters > 0
                            else 0.0
                        )
                        summary = (
                            f"{summary[:-1]} — volume actuel "
                            f"{_journal_fr_float(current_volume_liters)} L "
                            f"({_journal_fr_float(fill_percent)} %)."
                        )
                    user_note = _journal_user_note(intervention)
                    if user_note:
                        paragraphs.append(f"Note de l’utilisateur : {user_note}.")
                    composition = intervention.get("replacement_composition")
                    if isinstance(composition, list) and not composition:
                        paragraphs.append(
                            "La composition de l’eau de remplacement n’a pas été "
                            "renseignée. EcoBiome conserve donc l’intervention, "
                            "mais ne déduit pas automatiquement son effet sur la "
                            "chimie de l’eau."
                        )
                    content = "\n\n".join(paragraphs)
                    tags.extend(("changement-eau", "entretien"))

            entries.append(
                {
                    "id": str(event.event_id),
                    "title": title,
                    "source": "manual",
                    "source_ref": event.subject_id,
                    "tags": tags,
                    "summary": summary,
                    "content": content,
                    "technical_content": _journal_technical_content(event),
                    "event_kind": event_kind,
                    "water_body_name": profile.label,
                    "created_at": event.occurred_at.isoformat(),
                }
            )
        try:
            operations = read_operations(_project_dir(project_id), str(project_id))
        except (OSError, TypeError, ValueError):
            operations = []
        entries.extend(
            _journal_operation_entry(
                water_body_name=profile.label,
                event=operation,
            )
            for operation in operations
        )
    entries.sort(key=lambda item: str(item["created_at"]), reverse=True)
    return entries


@app.get("/api/collector/status")
def collector_status() -> dict[str, int]:
    """Return the durable Collector summary."""
    return _collector_store().summary()


@app.post("/api/collector/acquire")
def collector_acquire(request: CollectorAcquireRequest) -> dict[str, object]:
    """Acquire one source through the existing deterministic Collector registry."""
    languages = tuple(item.strip() for item in request.languages if item.strip())
    if len(set(languages)) != len(languages):
        raise HTTPException(
            status_code=422,
            detail="languages must not contain duplicates",
        )
    store = _collector_store()
    try:
        run = acquire_source(
            source=request.source,
            database=store.database_path,
            language=request.language.strip(),
            preferred_languages=languages,
            maximum_input_bytes=request.maximum_input_bytes,
            maximum_passage_characters=request.maximum_passage_characters,
        )
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result_representations = {
        representation.logical_key: representation
        for representation in run.result.representations
    }
    representations: list[dict[str, object]] = []
    for persisted in run.receipt.representations:
        drafted = result_representations[persisted.logical_key]
        representations.append(
            {
                "id": str(persisted.representation_id),
                "logical_key": persisted.logical_key,
                "representation_kind": drafted.representation_kind,
                "language": drafted.language,
                "segment_count": len(persisted.segment_ids),
                "duplicate": persisted.duplicate,
            }
        )

    return {
        "adapter": {
            "name": run.adapter_name,
            "version": run.adapter_version,
        },
        "source": {
            "id": str(run.receipt.source_id),
            "source_type": run.result.canonical_source.source_type,
            "canonical_locator": run.result.canonical_source.canonical_locator,
            "title": run.result.canonical_source.title,
            "author": run.result.canonical_source.author,
            "language": run.result.canonical_source.language,
        },
        "job": {
            "id": str(run.receipt.job_id),
            "status": run.result.outcome,
        },
        "representations": representations,
        "diagnostics": [
            {
                "severity": item.severity,
                "code": item.code,
                "message": item.message,
            }
            for item in run.result.diagnostics
        ],
    }


@app.get("/api/collector/pending")
def collector_pending(limit: int = 50) -> list[dict[str, object]]:
    """List Collector items waiting for human review."""
    bounded_limit = min(max(limit, 1), 500)
    return [
        dict(item)
        for item in _collector_store().list_pending_reviews(
            limit=bounded_limit
        )
    ]


@app.post("/api/collector/propose-claims")
def collector_propose_claims(
    request: CollectorProposeClaimsRequest,
) -> dict[str, object]:
    """Create pending source-statement Claims from one representation."""
    store = _collector_store()
    try:
        receipt = store.propose_source_statement_claims(
            representation_id=request.representation_id,
            limit=request.limit,
            maximum_claim_characters=request.maximum_claim_characters,
            maximum_window_seconds=15.0,
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "representation_id": str(receipt.representation_id),
        "claim_count": len(receipt.claims),
        "claims": [
            {
                "claim_id": str(item.claim_id),
                "duplicate": item.duplicate,
            }
            for item in receipt.claims
        ],
        "automatic_scientific_acceptance": False,
    }


@app.post("/api/collector/review")
def collector_review(request: CollectorReviewRequest) -> dict[str, object]:
    """Append one human-review decision to the Collector."""
    store = _collector_store()
    try:
        decision_id = store.record_review_decision(
            target_type=request.target_type,
            target_id=request.target_id,
            decision=request.decision,
            reviewer=request.reviewer,
            rationale=request.rationale,
            corrected_text=None,
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "decision_id": str(decision_id),
        "target_type": request.target_type,
        "target_id": request.target_id,
        "decision": request.decision,
    }
