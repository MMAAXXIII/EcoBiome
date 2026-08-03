export type WaterBodyType = 'aquarium' | 'pond' | 'aquaponic';
export type WaterBodyStatus = 'stable' | 'warning' | 'critical';

export interface WaterBody {
  id: string;
  name: string;
  type: WaterBodyType;
  volume_liters: number;
  status: WaterBodyStatus;
  created_at: string;
  updated_at: string;
}

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
  | 'nitrite'
  | 'nitrate'
  | 'oxygen'
  | 'phosphate'
  | 'iron'
  | 'co2'
  | 'gh'
  | 'kh';

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

export interface JournalEntry {
  id: string;
  title: string;
  source: JournalSource;
  source_ref: string;
  tags: string[];
  summary: string;
  content: string;
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

// Metric metadata: label, unit, ideal range, thresholds
export interface MetricInfo {
  key: Metric;
  label: string;
  unit: string;
  ideal: [number, number];
  warning: [number, number];
  critical: [number, number];
  icon: string;
}

export const METRICS: Record<Metric, MetricInfo> = {
  temperature: { key: 'temperature', label: 'Température', unit: '°C', ideal: [24, 27], warning: [22, 29], critical: [20, 31], icon: 'Thermometer' },
  ph: { key: 'ph', label: 'pH', unit: '', ideal: [7.8, 8.4], warning: [7.0, 8.6], critical: [6.5, 9.0], icon: 'Droplet' },
  ammonia: { key: 'ammonia', label: 'Ammonium', unit: 'mg/L', ideal: [0, 0.05], warning: [0.05, 0.25], critical: [0.25, 5], icon: 'Skull' },
  nitrite: { key: 'nitrite', label: 'Nitrites', unit: 'mg/L', ideal: [0, 0.05], warning: [0.05, 0.2], critical: [0.2, 5], icon: 'AlertTriangle' },
  nitrate: { key: 'nitrate', label: 'Nitrates', unit: 'mg/L', ideal: [0, 20], warning: [20, 50], critical: [50, 200], icon: 'FlaskConical' },
  oxygen: { key: 'oxygen', label: 'Oxygène', unit: 'mg/L', ideal: [7, 10], warning: [5, 7], critical: [0, 5], icon: 'Wind' },
  phosphate: { key: 'phosphate', label: 'Phosphate', unit: 'mg/L', ideal: [0, 0.3], warning: [0.3, 1.0], critical: [1.0, 5], icon: 'Atom' },
  iron: { key: 'iron', label: 'Fer', unit: 'mg/L', ideal: [0.05, 0.1], warning: [0.02, 0.2], critical: [0, 0.5], icon: 'Hexagon' },
  co2: { key: 'co2', label: 'CO₂', unit: 'mg/L', ideal: [5, 15], warning: [15, 25], critical: [25, 50], icon: 'Cloud' },
  gh: { key: 'gh', label: 'Dureté GH', unit: '°dH', ideal: [6, 12], warning: [4, 15], critical: [0, 20], icon: 'Mountain' },
  kh: { key: 'kh', label: 'Dureté KH', unit: '°dH', ideal: [5, 10], warning: [3, 12], critical: [0, 15], icon: 'Gem' },
};

export const METRIC_LIST = Object.values(METRICS);

export function getMetricStatus(metric: Metric, value: number): WaterBodyStatus {
  const info = METRICS[metric];
  if (value < info.critical[0] || value > info.critical[1]) return 'critical';
  if (value < info.ideal[0] || value > info.ideal[1]) return 'warning';
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
  stable: 'Stable',
  warning: 'Vigilance',
  critical: 'Critique',
};

export const JOURNAL_SOURCE_LABELS: Record<JournalSource, string> = {
  youtube_transcript: 'Transcription YouTube',
  manual: 'Note manuelle',
  literature: 'Littérature',
};
