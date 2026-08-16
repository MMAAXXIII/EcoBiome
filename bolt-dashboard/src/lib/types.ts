export type WaterBodyType = 'aquarium' | 'pond' | 'aquaponic';
export type WaterBodyStatus = 'unknown' | 'stable' | 'warning' | 'critical';

export interface WaterBody {
  id: string;
  name: string;
  type: WaterBodyType;
  /** Backward-compatible nominal capacity. */
  volume_liters: number;
  capacity_liters: number;
  current_volume_liters: number;
  fill_percent: number;
  status: WaterBodyStatus;
  created_at: string;
  updated_at: string;
}


export type EquipmentType =
  | 'water_pump'
  | 'air_pump'
  | 'lighting'
  | 'heater'
  | 'filter'
  | 'co2_system'
  | 'sensor'
  | 'other';

export interface EquipmentItem {
  id: string;
  name: string;
  equipment_type: EquipmentType;
  manufacturer: string;
  model: string;
  power_watts: number | null;
  daily_runtime_hours: number | null;
  in_service_since: string | null;
  flow_lph: number | null;
  measured_flow_lph: number | null;
  spectrum: string;
  color_temperature_k: number | null;
  par_surface_umol_m2_s: number | null;
  par_bottom_umol_m2_s: number | null;
  filter_media: string;
  media_volume_liters: number | null;
  specific_surface_m2_per_l: number | null;
  biofilter_maturity: 'unknown' | 'new' | 'cycling' | 'mature' | 'disturbed';
  tan_capacity_mg_n_day: number | null;
  inoculated: boolean | null;
  last_maintenance_at: string | null;
  notes: string;
  daily_energy_wh: number | null;
  annual_energy_kwh: number | null;
}

export const EQUIPMENT_TYPE_LABELS: Record<EquipmentType, string> = {
  water_pump: 'Pompe à eau',
  air_pump: 'Pompe à air',
  lighting: 'Éclairage',
  heater: 'Chauffage',
  filter: 'Filtration',
  co2_system: 'Système CO₂',
  sensor: 'Capteur / sonde',
  other: 'Autre',
};

export interface LivestockItem {
  id: string;
  common_name: string;
  scientific_name: string;
  count: number;
  male_count: number;
  female_count: number;
  unknown_sex_count: number;
  average_mass_g: number | null;
  biomass_g: number | null;
  life_stage: string;
  notes: string;
  created_at: string;
}

export interface FeedProduct {
  schema_version: string;
  id: string;
  revision: number;
  brand: string;
  name: string;
  variant: string;
  feed_category: string;
  form: string;
  dietary_role: string;
  target_species_text: string;
  feeding_zone: string;
  ingredients_text: string;
  crude_protein_percent: number | null;
  crude_fat_percent: number | null;
  crude_fibre_percent: number | null;
  moisture_percent: number | null;
  crude_ash_percent: number | null;
  phosphorus_percent: number | null;
  energy_kj_kg: number | null;
  additives_text: string;
  feeding_guide_text: string;
  package_mass_g: number | null;
  package_volume_ml: number | null;
  source_url: string;
  manufacturer_url: string;
  source_kind: string;
  source_observed_at: string;
  commercial_price: number | null;
  commercial_currency: string;
  notes: string;
  product_sha256: string;
  source_content_sha256?: string;
}

export interface PlantStockItem {
  id: string;
  common_name: string;
  scientific_name: string;
  count: number | null;
  coverage_percent: number | null;
  notes: string;
  created_at: string;
}

export type WaterSourceType = 'tap' | 'rain' | 'ro' | 'well' | 'mixed' | 'other';

export interface WaterSourceProfile {
  id: string;
  name: string;
  source_type: WaterSourceType;
  temperature_c: number | null;
  ph: number | null;
  kh_dkh: number | null;
  gh_dgh: number | null;
  conductivity_us_cm: number | null;
  nitrate_mg_l: number | null;
  nitrite_mg_l: number | null;
  ammonia_mg_l: number | null;
  phosphate_mg_l: number | null;
  chloride_mg_l: number | null;
  calcium_mg_l: number | null;
  magnesium_mg_l: number | null;
  salinity_g_l: number | null;
  notes: string;
  created_at: string;
}

export interface SubstrateLayer {
  id: string;
  material: string;
  thickness_cm: number | null;
  grain_min_mm: number | null;
  grain_max_mm: number | null;
  organic: boolean;
  notes: string;
  created_at: string;
}

export interface EcologyOperation {
  event_id: string;
  occurred_at: string;
  operation_type: string;
  subject_id: string | null;
  details: Record<string, unknown>;
  note: string;
  event_sha256: string;
}

export interface EcologySnapshot {
  livestock: LivestockItem[];
  plants: PlantStockItem[];
  water_sources: WaterSourceProfile[];
  substrate_layers: SubstrateLayer[];
  feed_products: FeedProduct[];
  known_livestock_biomass_g: number;
  operation_count: number;
  feeding_event_count: number;
  derived_indicators: Record<string, unknown>;
  recent_operations: EcologyOperation[];
}

export type ExperienceLevel = 'beginner' | 'intermediate' | 'advanced';

export type GuidanceStatus = 'known' | 'missing' | 'check';

export interface GuidanceItem {
  key: string;
  label: string;
  status: GuidanceStatus;
  required: boolean;
  section: string;
  action: string;
  rationale: string;
  applicability_note: string;
}

export interface GuidanceAction {
  key: string;
  label: string;
  section: string;
  action: string;
  rationale: string;
}

export interface GuidanceSnapshot {
  level: ExperienceLevel;
  is_diagnostic: false;
  message: string;
  known_required_count: number;
  required_count: number;
  items: GuidanceItem[];
  next_actions: GuidanceAction[];
}

export const EXPERIENCE_LEVEL_LABELS: Record<ExperienceLevel, string> = {
  beginner: 'Débutant',
  intermediate: 'Intermédiaire',
  advanced: 'Avancé',
};

export const EXPERIENCE_LEVEL_DESCRIPTIONS: Record<ExperienceLevel, string> = {
  beginner: 'Les informations essentielles restent visibles ; les détails scientifiques sont repliés.',
  intermediate: 'Ajoute charge biologique, minéralisation, oxygène et fonctionnement réel de la filtration.',
  advanced: 'Expose l’ensemble des mesures, paramètres de filtration, lumière et chimie détaillée.',
};

export type OrganismKind = 'plant' | 'bacteria' | 'microfauna' | 'animal';

export interface Organism {
  id: string;
  water_body_id: string;
  name: string;
  kind: OrganismKind;
  population: number;
  health: number;
  created_at: string;
}

export type Metric =
  | 'temperature'
  | 'ph'
  | 'ammonia'
  | 'tan'
  | 'nitrite'
  | 'nitrate'
  | 'oxygen'
  | 'phosphate'
  | 'iron'
  | 'co2'
  | 'gh'
  | 'kh'
  | 'conductivity'
  | 'chloride'
  | 'tss'
  | 'calcium'
  | 'magnesium'
  | 'salinity'
  | 'orp'
  | 'oxygen_saturation'
  | 'water_depth'
  | 'par_surface'
  | 'par_bottom'
  | 'algae_coverage'
  | 'periphyton_coverage';

export interface Measurement {
  id: string;
  water_body_id: string;
  metric: Metric;
  value: number;
  unit: string;
  recorded_at: string;
}

export type DiagnosticStatus = 'healthy' | 'warning' | 'critical';

export interface Diagnostic {
  id: string;
  water_body_id: string;
  status: DiagnosticStatus;
  summary: string;
  root_cause: string;
  confidence: number;
  created_at: string;
}

export type FindingSeverity = 'info' | 'warning' | 'critical';

export interface DiagnosticFinding {
  id: string;
  diagnostic_id: string;
  severity: FindingSeverity;
  metric: string;
  observation: string;
  explanation: string;
  causal_chain: string[];
}

export type JournalSource = 'youtube_transcript' | 'manual' | 'literature';

export type JournalEventKind = 'observation' | 'intervention';

export interface JournalEntry {
  id: string;
  title: string;
  source: JournalSource;
  source_ref: string;
  tags: string[];
  summary: string;
  content: string;
  technical_content: string;
  event_kind: JournalEventKind;
  water_body_name: string;
  created_at: string;
}

export type MediaKind = 'photo' | 'illustration' | 'diagram';

export interface MediaItem {
  id: string;
  water_body_id: string | null;
  title: string;
  kind: MediaKind;
  url: string;
  caption: string;
  created_at: string;
}

export interface MetricInfo {
  key: Metric;
  label: string;
  unit: string;
  ideal: [number, number];
  warning: [number, number];
  critical: [number, number];
  icon: string;
  contextual?: boolean;
}

export const METRICS: Record<Metric, MetricInfo> = {
  temperature: {
    key: 'temperature',
    label: 'Température (T)',
    unit: '°C',
    ideal: [24, 27],
    warning: [22, 29],
    critical: [20, 31],
    icon: 'Thermometer',
    contextual: true,
  },
  ph: {
    key: 'ph',
    label: 'pH — potentiel hydrogène',
    unit: '',
    ideal: [7.8, 8.4],
    warning: [7.0, 8.6],
    critical: [6.5, 9.0],
    icon: 'Droplet',
    contextual: true,
  },
  ammonia: {
    key: 'ammonia',
    label: 'Ammoniac / ammonium (NH₃ / NH₄⁺) — test déclaré',
    unit: 'mg/L',
    ideal: [0, 0.05],
    warning: [0.05, 0.25],
    critical: [0.25, 5],
    icon: 'Skull',
    contextual: true,
  },
  tan: {
    key: 'tan',
    label: 'Azote ammoniacal total (TAN = NH₃-N + NH₄⁺-N)',
    unit: 'mg N/L',
    ideal: [0, 0],
    warning: [0, 1],
    critical: [0, 1000],
    icon: 'Skull',
    contextual: true,
  },
  nitrite: {
    key: 'nitrite',
    label: 'Nitrites (NO₂⁻)',
    unit: 'mg/L',
    ideal: [0, 0.05],
    warning: [0.05, 0.2],
    critical: [0.2, 5],
    icon: 'AlertTriangle',
    contextual: true,
  },
  nitrate: {
    key: 'nitrate',
    label: 'Nitrates (NO₃⁻)',
    unit: 'mg/L',
    ideal: [0, 20],
    warning: [20, 50],
    critical: [50, 200],
    icon: 'FlaskConical',
    contextual: true,
  },
  oxygen: {
    key: 'oxygen',
    label: 'Oxygène dissous (O₂)',
    unit: 'mg/L',
    ideal: [7, 10],
    warning: [5, 7],
    critical: [0, 5],
    icon: 'Wind',
    contextual: true,
  },
  phosphate: {
    key: 'phosphate',
    label: 'Phosphates (PO₄³⁻)',
    unit: 'mg/L',
    ideal: [0, 0.3],
    warning: [0.3, 1.0],
    critical: [1.0, 5],
    icon: 'Atom',
    contextual: true,
  },
  iron: {
    key: 'iron',
    label: 'Fer (Fe)',
    unit: 'mg/L',
    ideal: [0.05, 0.1],
    warning: [0.02, 0.2],
    critical: [0, 0.5],
    icon: 'Hexagon',
    contextual: true,
  },
  co2: {
    key: 'co2',
    label: 'Dioxyde de carbone (CO₂)',
    unit: 'mg/L',
    ideal: [5, 15],
    warning: [15, 25],
    critical: [25, 50],
    icon: 'Cloud',
    contextual: true,
  },
  gh: {
    key: 'gh',
    label: 'Dureté générale (GH — Ca²⁺ / Mg²⁺)',
    unit: '°dGH',
    ideal: [6, 12],
    warning: [4, 15],
    critical: [0, 20],
    icon: 'Mountain',
    contextual: true,
  },
  kh: {
    key: 'kh',
    label: 'Dureté carbonatée (KH — HCO₃⁻ / CO₃²⁻)',
    unit: '°dKH',
    ideal: [5, 10],
    warning: [3, 12],
    critical: [0, 15],
    icon: 'Gem',
    contextual: true,
  },
  conductivity: {
    key: 'conductivity', label: 'Conductivité électrique (κ)', unit: 'µS/cm',
    ideal: [0, 2000], warning: [0, 5000], critical: [0, 1000000], icon: 'Activity', contextual: true,
  },
  chloride: {
    key: 'chloride', label: 'Chlorures (Cl⁻)', unit: 'mg/L',
    ideal: [0, 500], warning: [0, 2000], critical: [0, 1000000], icon: 'FlaskConical', contextual: true,
  },
  tss: {
    key: 'tss', label: 'Matières en suspension (MES / TSS)', unit: 'mg/L',
    ideal: [0, 50], warning: [0, 200], critical: [0, 1000000], icon: 'Cloud', contextual: true,
  },
  calcium: {
    key: 'calcium', label: 'Calcium (Ca²⁺)', unit: 'mg/L',
    ideal: [0, 500], warning: [0, 2000], critical: [0, 1000000], icon: 'Atom', contextual: true,
  },
  magnesium: {
    key: 'magnesium', label: 'Magnésium (Mg²⁺)', unit: 'mg/L',
    ideal: [0, 500], warning: [0, 2000], critical: [0, 1000000], icon: 'Atom', contextual: true,
  },
  salinity: {
    key: 'salinity', label: 'Salinité (S)', unit: 'g/L',
    ideal: [0, 40], warning: [0, 60], critical: [0, 1000], icon: 'Waves', contextual: true,
  },
  orp: {
    key: 'orp', label: 'Potentiel d’oxydoréduction (ORP / Eh)', unit: 'mV',
    ideal: [-1000, 1000], warning: [-2000, 2000], critical: [-10000, 10000], icon: 'Zap', contextual: true,
  },
  oxygen_saturation: {
    key: 'oxygen_saturation', label: 'Saturation en oxygène (O₂ sat.)', unit: '%',
    ideal: [0, 200], warning: [0, 300], critical: [0, 1000], icon: 'Wind', contextual: true,
  },
  water_depth: {
    key: 'water_depth', label: 'Profondeur d’eau (h)', unit: 'cm',
    ideal: [0, 1000], warning: [0, 5000], critical: [0, 100000], icon: 'Ruler', contextual: true,
  },
  par_surface: {
    key: 'par_surface', label: 'PAR / PPFD — surface', unit: 'µmol photons/m²/s',
    ideal: [0, 5000], warning: [0, 10000], critical: [0, 100000], icon: 'Sun', contextual: true,
  },
  par_bottom: {
    key: 'par_bottom', label: 'PAR / PPFD — fond', unit: 'µmol photons/m²/s',
    ideal: [0, 5000], warning: [0, 10000], critical: [0, 100000], icon: 'Sun', contextual: true,
  },
  algae_coverage: {
    key: 'algae_coverage', label: 'Couverture algale', unit: '%',
    ideal: [0, 100], warning: [0, 100], critical: [0, 100], icon: 'Leaf', contextual: true,
  },
  periphyton_coverage: {
    key: 'periphyton_coverage', label: 'Couverture périphyton', unit: '%',
    ideal: [0, 100], warning: [0, 100], critical: [0, 100], icon: 'Leaf', contextual: true,
  },
};

export const METRIC_LIST = Object.values(METRICS);

export const METRICS_BY_EXPERIENCE_LEVEL: Record<ExperienceLevel, readonly Metric[]> = {
  beginner: ['temperature', 'ph', 'nitrite', 'nitrate', 'kh'],
  intermediate: [
    'temperature', 'ph', 'nitrite', 'nitrate', 'kh', 'gh',
    'tan', 'oxygen', 'conductivity', 'phosphate',
  ],
  advanced: Object.keys(METRICS) as Metric[],
};

export function metricVisibleAtLevel(metric: Metric, level: ExperienceLevel): boolean {
  return METRICS_BY_EXPERIENCE_LEVEL[level].includes(metric);
}

export function getMetricStatus(
  metric: Metric,
  value: number,
): WaterBodyStatus {
  const info = METRICS[metric];
  if (info.contextual) {
    return 'unknown';
  }
  if (value < info.critical[0] || value > info.critical[1]) {
    return 'critical';
  }
  if (value < info.ideal[0] || value > info.ideal[1]) {
    return 'warning';
  }
  return 'stable';
}

export const ORGANISM_KIND_LABELS: Record<OrganismKind, string> = {
  plant: 'Plante',
  bacteria: 'Bactérie',
  microfauna: 'Microfaune',
  animal: 'Animal',
};

export const WATER_BODY_TYPE_LABELS: Record<WaterBodyType, string> = {
  aquarium: 'Aquarium',
  pond: 'Bassin',
  aquaponic: 'Aquaponique',
};

export const STATUS_LABELS: Record<WaterBodyStatus, string> = {
  unknown: 'Non évalué',
  stable: 'Stable',
  warning: 'Vigilance',
  critical: 'Critique',
};

export const JOURNAL_SOURCE_LABELS: Record<JournalSource, string> = {
  youtube_transcript: 'Transcription YouTube',
  manual: 'Note manuelle',
  literature: 'Littérature',
};
