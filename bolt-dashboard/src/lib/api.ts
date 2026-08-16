import type {
  Diagnostic,
  EcologyOperation,
  EcologySnapshot,
  EquipmentItem,
  EquipmentType,
  ExperienceLevel,
  FeedProduct,
  GuidanceSnapshot,
  JournalEntry,
  LivestockItem,
  Measurement,
  MediaItem,
  Organism,
  PlantStockItem,
  SubstrateLayer,
  WaterBody,
  WaterSourceProfile,
  WaterSourceType,
} from '@/lib/types';

const API_BASE = (
  import.meta.env.VITE_ECOBIOME_API_URL ?? 'http://127.0.0.1:8000'
).replace(/\/+$/, '');

async function requestJson<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = text;
    }
  }

  if (!response.ok) {
    const detail =
      typeof payload === 'object' &&
      payload !== null &&
      'detail' in payload
        ? String((payload as { detail: unknown }).detail)
        : String(payload ?? response.statusText);
    throw new Error(detail);
  }

  return payload as T;
}

export interface CreateWaterBodyInput {
  name: string;
  type: 'aquarium' | 'pond';
  volume_liters: number;
}


export interface SetFillLevelInput {
  fill_percent: number;
  observed_at?: string;
  source?: string;
}

export interface WaterExchangeInput {
  removed_volume_liters: number;
  replacement_volume_liters: number;
  water_source_id?: string | null;
  note?: string;
}

export interface WaterExchangeResult {
  event_id: string;
  intervention_id: string;
  occurred_at: string;
  removed_volume_liters: number;
  replacement_volume_liters: number;
  previous_volume_liters: number;
  current_volume_liters: number;
  capacity_liters: number;
  fill_percent: number;
  water_source_id: string | null;
  water_source_name: string | null;
  composition_status: 'unknown' | 'profiled_local';
}

export interface CreateEquipmentInput {
  equipment_type: EquipmentType;
  name: string;
  manufacturer?: string;
  model?: string;
  power_watts?: number | null;
  daily_runtime_hours?: number | null;
  in_service_since?: string | null;
  flow_lph?: number | null;
  measured_flow_lph?: number | null;
  spectrum?: string;
  color_temperature_k?: number | null;
  par_surface_umol_m2_s?: number | null;
  par_bottom_umol_m2_s?: number | null;
  filter_media?: string;
  media_volume_liters?: number | null;
  specific_surface_m2_per_l?: number | null;
  biofilter_maturity?: 'unknown' | 'new' | 'cycling' | 'mature' | 'disturbed';
  tan_capacity_mg_n_day?: number | null;
  inoculated?: boolean | null;
  last_maintenance_at?: string | null;
  notes?: string;
}

export interface AddMeasurementInput {
  metric:
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
  value: number;
  uncertainty?: number;
  confidence?: number;
  observed_at?: string;
  source?: string;
}

export interface CreateLivestockInput {
  common_name: string;
  scientific_name?: string;
  count: number;
  male_count?: number;
  female_count?: number;
  average_mass_g?: number | null;
  life_stage?: string;
  notes?: string;
}

export interface AdjustLivestockInput {
  delta_count: number;
  reason: 'addition' | 'removal' | 'death' | 'correction';
  sex?: 'male' | 'female' | 'unknown';
  note?: string;
}

export interface SetLivestockSexInput {
  male_count: number;
  female_count: number;
  note?: string;
}

export interface CreatePlantInput {
  common_name: string;
  scientific_name?: string;
  count?: number | null;
  coverage_percent?: number | null;
  notes?: string;
}

export interface CreateWaterSourceInput {
  name: string;
  source_type: WaterSourceType;
  temperature_c?: number | null;
  ph?: number | null;
  kh_dkh?: number | null;
  gh_dgh?: number | null;
  conductivity_us_cm?: number | null;
  nitrate_mg_l?: number | null;
  nitrite_mg_l?: number | null;
  ammonia_mg_l?: number | null;
  phosphate_mg_l?: number | null;
  chloride_mg_l?: number | null;
  calcium_mg_l?: number | null;
  magnesium_mg_l?: number | null;
  salinity_g_l?: number | null;
  notes?: string;
}

export interface CreateSubstrateLayerInput {
  material: string;
  thickness_cm: number;
  grain_min_mm?: number | null;
  grain_max_mm?: number | null;
  organic?: boolean;
  notes?: string;
}

export interface FeedingInput {
  feed_product_id?: string | null;
  food_name?: string;
  amount_g: number;
  protein_percent?: number | null;
  target_population_ids?: string[];
  consumed_percent?: number | null;
  occurred_at?: string;
  note?: string;
}

export interface CreateFeedProductInput {
  brand?: string;
  name: string;
  variant?: string;
  feed_category?: string;
  form?: string;
  dietary_role?: string;
  target_species_text?: string;
  feeding_zone?: string;
  ingredients_text?: string;
  crude_protein_percent?: number | null;
  crude_fat_percent?: number | null;
  crude_fibre_percent?: number | null;
  moisture_percent?: number | null;
  crude_ash_percent?: number | null;
  phosphorus_percent?: number | null;
  additives_text?: string;
  feeding_guide_text?: string;
  source_url?: string;
  notes?: string;
}

export interface TopUpInput {
  volume_liters: number;
  water_source_id?: string | null;
  occurred_at?: string;
  note?: string;
}

export interface EcosystemOperationInput {
  operation_type:
    | 'filter_maintenance'
    | 'power_outage'
    | 'additive'
    | 'fertilization'
    | 'bacteria_addition'
    | 'co2_change'
    | 'water_treatment'
    | 'siphoning'
    | 'plant_pruning'
    | 'substrate_maintenance'
    | 'medication'
    | 'other';
  label: string;
  quantity?: number | null;
  unit?: string;
  occurred_at?: string;
  note?: string;
}

export interface CollectorRepresentation {
  id: string;
  logical_key: string;
  representation_kind: string;
  language: string;
  segment_count: number;
  duplicate: boolean;
}

export interface CollectorAcquireResult {
  adapter: {
    name: string;
    version: string;
  };
  source: {
    id: string;
    source_type: string;
    canonical_locator: string;
    title: string;
    author: string;
    language: string;
  };
  job: {
    id: string;
    status: string;
  };
  representations: CollectorRepresentation[];
  diagnostics: Array<{
    severity: string;
    code: string;
    message: string;
  }>;
}

export interface CollectorPendingItem {
  target_type: 'passage' | 'claim';
  target_id: string;
  text: string;
  passage_index?: number | null;
  [key: string]: unknown;
}

export interface CollectorStatus {
  [key: string]: unknown;
}

export function getWaterBodies(): Promise<WaterBody[]> {
  return requestJson<WaterBody[]>('/api/water-bodies');
}

export function createWaterBody(
  input: CreateWaterBodyInput,
): Promise<WaterBody> {
  return requestJson<WaterBody>('/api/water-bodies', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function setFillLevel(
  waterBodyId: string,
  input: SetFillLevelInput,
): Promise<WaterBody> {
  return requestJson<WaterBody>(
    `/api/water-bodies/${encodeURIComponent(waterBodyId)}/fill-level`,
    {
      method: 'POST',
      body: JSON.stringify(input),
    },
  );
}

export function recordWaterExchange(
  waterBodyId: string,
  input: WaterExchangeInput,
): Promise<WaterExchangeResult> {
  return requestJson<WaterExchangeResult>(
    `/api/water-bodies/${encodeURIComponent(waterBodyId)}/water-exchanges`,
    {
      method: 'POST',
      body: JSON.stringify(input),
    },
  );
}

export function getEquipment(
  waterBodyId: string,
): Promise<EquipmentItem[]> {
  return requestJson<EquipmentItem[]>(
    `/api/water-bodies/${encodeURIComponent(waterBodyId)}/equipment`,
  );
}

export function addEquipment(
  waterBodyId: string,
  input: CreateEquipmentInput,
): Promise<EquipmentItem> {
  return requestJson<EquipmentItem>(
    `/api/water-bodies/${encodeURIComponent(waterBodyId)}/equipment`,
    {
      method: 'POST',
      body: JSON.stringify(input),
    },
  );
}

export function deleteEquipment(
  waterBodyId: string,
  equipmentId: string,
): Promise<{ deleted_equipment_id: string }> {
  return requestJson(
    `/api/water-bodies/${encodeURIComponent(waterBodyId)}/equipment/${encodeURIComponent(equipmentId)}`,
    { method: 'DELETE' },
  );
}

export function getEcology(waterBodyId: string): Promise<EcologySnapshot> {
  return requestJson<EcologySnapshot>(
    `/api/water-bodies/${encodeURIComponent(waterBodyId)}/ecology`,
  );
}

export function getGuidance(
  waterBodyId: string,
  level: ExperienceLevel,
): Promise<GuidanceSnapshot> {
  return requestJson<GuidanceSnapshot>(
    `/api/water-bodies/${encodeURIComponent(waterBodyId)}/guidance?level=${encodeURIComponent(level)}`,
  );
}

export function addLivestock(waterBodyId: string, input: CreateLivestockInput): Promise<LivestockItem> {
  return requestJson<LivestockItem>(`/api/water-bodies/${encodeURIComponent(waterBodyId)}/livestock`, {
    method: 'POST', body: JSON.stringify(input),
  });
}

export function adjustLivestock(
  waterBodyId: string,
  populationId: string,
  input: AdjustLivestockInput,
): Promise<LivestockItem> {
  return requestJson<LivestockItem>(
    `/api/water-bodies/${encodeURIComponent(waterBodyId)}/livestock/${encodeURIComponent(populationId)}/adjust`,
    { method: 'POST', body: JSON.stringify(input) },
  );
}

export function setLivestockSexDistribution(
  waterBodyId: string,
  populationId: string,
  input: SetLivestockSexInput,
): Promise<LivestockItem> {
  return requestJson<LivestockItem>(
    `/api/water-bodies/${encodeURIComponent(waterBodyId)}/livestock/${encodeURIComponent(populationId)}/sex-distribution`,
    { method: 'POST', body: JSON.stringify(input) },
  );
}

export function deleteLivestock(waterBodyId: string, populationId: string): Promise<{ deleted_population_id: string }> {
  return requestJson(`/api/water-bodies/${encodeURIComponent(waterBodyId)}/livestock/${encodeURIComponent(populationId)}`, { method: 'DELETE' });
}

export function addPlant(waterBodyId: string, input: CreatePlantInput): Promise<PlantStockItem> {
  return requestJson<PlantStockItem>(`/api/water-bodies/${encodeURIComponent(waterBodyId)}/plants`, {
    method: 'POST', body: JSON.stringify(input),
  });
}

export function deletePlant(waterBodyId: string, populationId: string): Promise<{ deleted_population_id: string }> {
  return requestJson(`/api/water-bodies/${encodeURIComponent(waterBodyId)}/plants/${encodeURIComponent(populationId)}`, { method: 'DELETE' });
}

export function addWaterSource(waterBodyId: string, input: CreateWaterSourceInput): Promise<WaterSourceProfile> {
  return requestJson<WaterSourceProfile>(`/api/water-bodies/${encodeURIComponent(waterBodyId)}/water-sources`, {
    method: 'POST', body: JSON.stringify(input),
  });
}

export function deleteWaterSource(waterBodyId: string, sourceId: string): Promise<{ deleted_water_source_id: string }> {
  return requestJson(`/api/water-bodies/${encodeURIComponent(waterBodyId)}/water-sources/${encodeURIComponent(sourceId)}`, { method: 'DELETE' });
}

export function addSubstrateLayer(waterBodyId: string, input: CreateSubstrateLayerInput): Promise<SubstrateLayer> {
  return requestJson<SubstrateLayer>(`/api/water-bodies/${encodeURIComponent(waterBodyId)}/substrate-layers`, {
    method: 'POST', body: JSON.stringify(input),
  });
}

export function deleteSubstrateLayer(waterBodyId: string, layerId: string): Promise<{ deleted_layer_id: string }> {
  return requestJson(`/api/water-bodies/${encodeURIComponent(waterBodyId)}/substrate-layers/${encodeURIComponent(layerId)}`, { method: 'DELETE' });
}

export function getFeedProducts(): Promise<FeedProduct[]> {
  return requestJson<FeedProduct[]>('/api/feed-products');
}

export function addFeedProduct(input: CreateFeedProductInput): Promise<FeedProduct> {
  return requestJson<FeedProduct>('/api/feed-products', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function importFeedProduct(url: string): Promise<FeedProduct> {
  return requestJson<FeedProduct>('/api/feed-products/import-url', {
    method: 'POST',
    body: JSON.stringify({ url }),
  });
}

export function recordFeeding(waterBodyId: string, input: FeedingInput): Promise<EcologyOperation> {
  return requestJson<EcologyOperation>(`/api/water-bodies/${encodeURIComponent(waterBodyId)}/feeding`, {
    method: 'POST', body: JSON.stringify(input),
  });
}

export function recordTopUp(waterBodyId: string, input: TopUpInput): Promise<EcologyOperation & { water_body: WaterBody }> {
  return requestJson(`/api/water-bodies/${encodeURIComponent(waterBodyId)}/top-ups`, {
    method: 'POST', body: JSON.stringify(input),
  });
}

export function recordEcosystemOperation(waterBodyId: string, input: EcosystemOperationInput): Promise<EcologyOperation> {
  return requestJson<EcologyOperation>(`/api/water-bodies/${encodeURIComponent(waterBodyId)}/operations`, {
    method: 'POST', body: JSON.stringify(input),
  });
}

export function getMeasurements(
  waterBodyId: string,
): Promise<Measurement[]> {
  return requestJson<Measurement[]>(
    `/api/water-bodies/${encodeURIComponent(waterBodyId)}/measurements`,
  );
}

export function getAllMeasurements(): Promise<Measurement[]> {
  return requestJson<Measurement[]>('/api/measurements');
}

export function addMeasurement(
  waterBodyId: string,
  input: AddMeasurementInput,
): Promise<Measurement> {
  return requestJson<Measurement>(
    `/api/water-bodies/${encodeURIComponent(waterBodyId)}/measurements`,
    {
      method: 'POST',
      body: JSON.stringify(input),
    },
  );
}

export function getOrganisms(
  waterBodyId: string,
): Promise<Organism[]> {
  return requestJson<Organism[]>(
    `/api/water-bodies/${encodeURIComponent(waterBodyId)}/organisms`,
  );
}

export function getDiagnostics(): Promise<Diagnostic[]> {
  return requestJson<Diagnostic[]>('/api/diagnostics');
}

export function getDiagnosticFindings(
  diagnosticId: string,
): Promise<Array<{
  id: string;
  severity: string;
  metric: string;
  observation: string;
  explanation: string;
  causal_chain: string[];
}>> {
  return requestJson(
    `/api/diagnostics/${encodeURIComponent(diagnosticId)}/findings`,
  );
}

export function getJournal(): Promise<JournalEntry[]> {
  return requestJson<JournalEntry[]>('/api/journal');
}

export function getMedia(): Promise<MediaItem[]> {
  return requestJson<MediaItem[]>('/api/media');
}

export function getCollectorStatus(): Promise<CollectorStatus> {
  return requestJson<CollectorStatus>('/api/collector/status');
}

export function getCollectorPending(
  limit = 50,
): Promise<CollectorPendingItem[]> {
  return requestJson<CollectorPendingItem[]>(
    `/api/collector/pending?limit=${limit}`,
  );
}

export function acquireCollectorSource(input: {
  source: string;
  language?: string;
  languages?: string[];
}): Promise<CollectorAcquireResult> {
  return requestJson<CollectorAcquireResult>('/api/collector/acquire', {
    method: 'POST',
    body: JSON.stringify({
      source: input.source,
      language: input.language ?? '',
      languages: input.languages ?? [],
    }),
  });
}

export function proposeCollectorClaims(
  representationId: string,
): Promise<{
  representation_id: string;
  claim_count: number;
  claims: Array<{ claim_id: string; duplicate: boolean }>;
  automatic_scientific_acceptance: false;
}> {
  return requestJson('/api/collector/propose-claims', {
    method: 'POST',
    body: JSON.stringify({
      representation_id: representationId,
    }),
  });
}

export function reviewCollectorItem(input: {
  target_type: 'passage' | 'claim';
  target_id: string;
  decision: 'accept' | 'reject';
  rationale?: string;
}): Promise<{
  decision_id: string;
  target_type: string;
  target_id: string;
  decision: string;
}> {
  return requestJson('/api/collector/review', {
    method: 'POST',
    body: JSON.stringify({
      ...input,
      reviewer: 'ecobiome-ui-user',
      rationale: input.rationale ?? '',
    }),
  });
}

export async function getApiHealth(): Promise<{
  status: string;
  service: string;
  bridge_version: string;
  data_root: string;
}> {
  return requestJson('/api/health');
}
