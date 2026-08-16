import type {
  EcologyOperation,
  LivestockItem,
  Metric,
} from '@/lib/types';

export interface SpeciesReferenceRange {
  metric: 'temperature';
  min: number;
  max: number;
  unit: '°C';
  sourceLabel: string;
  sourceUrl: string;
  evidenceNote: string;
}

export interface SpeciesReferenceProfile {
  scientificName: string;
  commonNames: string[];
  temperature: SpeciesReferenceRange;
}

export interface BiologicalAlert {
  id: string;
  severity: 'warning';
  metric: 'temperature';
  speciesScientificName: string;
  speciesCommonName: string;
  measuredValue: number;
  unit: '°C';
  min: number;
  max: number;
  direction: 'below' | 'above';
  title: string;
  message: string;
  sourceLabel: string;
  sourceUrl: string;
  evidenceNote: string;
}

export interface FeedingVisual {
  foodName: string;
  form: string;
  amountG: number | null;
  occurredAt: string;
  opacity: number;
  particleCount: number;
  remainingMs: number;
}

const FEED_VISIBILITY_MS = 5 * 60 * 1000;

export const SPECIES_REFERENCE_PROFILES: SpeciesReferenceProfile[] = [
  {
    scientificName: 'Mikrogeophagus ramirezi',
    commonNames: ['Ramirezi', 'Ram cichlid', 'Cichlidé nain de Ramirez'],
    temperature: {
      metric: 'temperature',
      min: 27,
      max: 30,
      unit: '°C',
      sourceLabel: 'FishBase — Mikrogeophagus ramirezi',
      sourceUrl: 'https://fishbase.org/summary/Mikrogeophagus_ramirezi.html',
      evidenceNote:
        'Plage écologique de référence publiée par FishBase ; elle ne doit pas être interprétée comme une limite létale universelle.',
    },
  },
  {
    scientificName: 'Oryzias latipes',
    commonNames: ['Medaka', 'Japanese rice fish', 'Poisson-riz japonais'],
    temperature: {
      metric: 'temperature',
      min: 18,
      max: 24,
      unit: '°C',
      sourceLabel: 'FishBase — Oryzias latipes',
      sourceUrl: 'https://www.fishbase.se/summary/Oryzias_latipes.html',
      evidenceNote:
        'Plage écologique de référence publiée par FishBase ; les souches domestiques et l’acclimatation peuvent différer.',
    },
  },
];

function normalizeName(value: string): string {
  return value.trim().toLocaleLowerCase('fr-FR');
}

function findSpeciesProfile(item: LivestockItem): SpeciesReferenceProfile | null {
  const scientific = normalizeName(item.scientific_name);
  const common = normalizeName(item.common_name);

  for (const profile of SPECIES_REFERENCE_PROFILES) {
    if (
      scientific &&
      scientific === normalizeName(profile.scientificName)
    ) {
      return profile;
    }
    if (
      common &&
      profile.commonNames.some((name) => normalizeName(name) === common)
    ) {
      return profile;
    }
  }
  return null;
}

export function evaluateBiologicalAlerts(
  livestock: LivestockItem[],
  latestMeasurements: Partial<Record<Metric, number | null>>,
): BiologicalAlert[] {
  const temperature = latestMeasurements.temperature;
  if (temperature === undefined || temperature === null) {
    return [];
  }

  const alerts: BiologicalAlert[] = [];

  for (const item of livestock) {
    if (item.count <= 0) continue;
    const profile = findSpeciesProfile(item);
    if (!profile) continue;

    const reference = profile.temperature;
    if (temperature >= reference.min && temperature <= reference.max) {
      continue;
    }

    const direction = temperature < reference.min ? 'below' : 'above';
    const commonName = item.common_name.trim() || profile.commonNames[0];

    alerts.push({
      id: `${item.id}:temperature:${direction}`,
      severity: 'warning',
      metric: 'temperature',
      speciesScientificName: profile.scientificName,
      speciesCommonName: commonName,
      measuredValue: temperature,
      unit: reference.unit,
      min: reference.min,
      max: reference.max,
      direction,
      title: `Température ${direction === 'below' ? 'trop basse' : 'trop élevée'} pour ${commonName}`,
      message:
        `${temperature.toFixed(1)} ${reference.unit} mesuré ; plage de référence ` +
        `${reference.min}–${reference.max} ${reference.unit} pour ${profile.scientificName}.`,
      sourceLabel: reference.sourceLabel,
      sourceUrl: reference.sourceUrl,
      evidenceNote: reference.evidenceNote,
    });
  }

  return alerts;
}

function decimalDetail(
  details: Record<string, unknown>,
  key: string,
): number | null {
  const raw = details[key];
  if (typeof raw === 'number' && Number.isFinite(raw)) return raw;
  if (typeof raw === 'string') {
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function productForm(details: Record<string, unknown>): string {
  const snapshot = details.feed_product_snapshot;
  if (
    snapshot &&
    typeof snapshot === 'object' &&
    'form' in snapshot &&
    typeof snapshot.form === 'string'
  ) {
    return snapshot.form;
  }
  return 'unknown';
}

export function getRecentFeedingVisual(
  operations: EcologyOperation[],
  nowMs = Date.now(),
): FeedingVisual | null {
  const feeding = [...operations]
    .filter((operation) => operation.operation_type === 'feeding')
    .sort(
      (left, right) =>
        new Date(right.occurred_at).getTime() -
        new Date(left.occurred_at).getTime(),
    )[0];

  if (!feeding) return null;

  const occurredMs = new Date(feeding.occurred_at).getTime();
  if (!Number.isFinite(occurredMs)) return null;

  const ageMs = Math.max(0, nowMs - occurredMs);
  if (ageMs >= FEED_VISIBILITY_MS) return null;

  const amountG = decimalDetail(feeding.details, 'amount_g_decimal');
  const foodNameRaw = feeding.details.food_name;
  const foodName =
    typeof foodNameRaw === 'string' && foodNameRaw.trim()
      ? foodNameRaw.trim()
      : 'Nourriture';

  const progress = ageMs / FEED_VISIBILITY_MS;
  const opacity = Math.max(0.08, 1 - progress);
  const amountFactor = amountG === null ? 1 : Math.max(0.5, Math.min(2.5, amountG));
  const particleCount = Math.max(6, Math.min(24, Math.round(10 * amountFactor)));

  return {
    foodName,
    form: productForm(feeding.details),
    amountG,
    occurredAt: feeding.occurred_at,
    opacity,
    particleCount,
    remainingMs: FEED_VISIBILITY_MS - ageMs,
  };
}

export function livingTankKnownSpeciesCount(
  livestock: LivestockItem[],
): number {
  return livestock.filter((item) => findSpeciesProfile(item) !== null).length;
}
