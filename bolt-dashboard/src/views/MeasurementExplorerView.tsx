import { useMemo, useState } from 'react';
import { ArrowLeft, BookOpen, CalendarRange, Plus, TrendingUp } from 'lucide-react';
import { METRIC_LIST, METRICS, type Measurement, type Metric, type WaterBody } from '@/lib/types';

export type MeasurementRange = '7d' | '30d' | '90d' | '1y' | 'all';

const RANGE_OPTIONS: Array<{ key: MeasurementRange; label: string; days: number | null }> = [
  { key: '7d', label: '7 jours', days: 7 },
  { key: '30d', label: '1 mois', days: 30 },
  { key: '90d', label: '3 mois', days: 90 },
  { key: '1y', label: '1 an', days: 365 },
  { key: 'all', label: 'Tout', days: null },
];

interface MeasurementExplorerViewProps {
  waterBody: WaterBody;
  measurements: Measurement[];
  primaryMetric: Metric;
  onBack: () => void;
  onAddMeasurement: (metric: Metric) => void;
  onOpenGlossary: (metric: Metric) => void;
}

interface SeriesPoint {
  timestamp: number;
  value: number;
}

interface SeriesSummary {
  count: number;
  latest: number | null;
  minimum: number | null;
  maximum: number | null;
  average: number | null;
}

export function MeasurementExplorerView({
  waterBody,
  measurements,
  primaryMetric,
  onBack,
  onAddMeasurement,
  onOpenGlossary,
}: MeasurementExplorerViewProps) {
  const [range, setRange] = useState<MeasurementRange>('30d');
  const [comparisonMetric, setComparisonMetric] = useState<Metric | ''>('');

  const filteredMeasurements = useMemo(
    () => filterMeasurementsByRange(measurements, range),
    [measurements, range],
  );
  const primarySeries = useMemo(
    () => buildMetricSeries(filteredMeasurements, primaryMetric),
    [filteredMeasurements, primaryMetric],
  );
  const comparisonSeries = useMemo(
    () => comparisonMetric ? buildMetricSeries(filteredMeasurements, comparisonMetric) : [],
    [comparisonMetric, filteredMeasurements],
  );
  const availableComparisons = useMemo(
    () => METRIC_LIST.filter((info) => (
      info.key !== primaryMetric && measurements.some((item) => item.metric === info.key)
    )),
    [measurements, primaryMetric],
  );

  const primaryInfo = METRICS[primaryMetric];
  const comparisonInfo = comparisonMetric ? METRICS[comparisonMetric] : null;
  const primarySummary = summarizeSeries(primarySeries);
  const comparisonSummary = summarizeSeries(comparisonSeries);

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <button
        type="button"
        onClick={onBack}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Retour aux paramètres de {waterBody.name}
      </button>

      <div className="flex flex-col xl:flex-row xl:items-start xl:justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-500">Vue détaillée</p>
          <h1 className="font-display font-bold text-white text-2xl mt-1">{primaryInfo.label}</h1>
          <p className="text-sm text-slate-400 mt-1">
            Évolution des mesures enregistrées dans {waterBody.name}.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => onAddMeasurement(primaryMetric)}
            className="rounded-xl bg-teal-500 text-night-950 px-3 py-2 text-sm font-semibold hover:bg-teal-400 flex items-center gap-2 w-fit"
          >
            <Plus className="w-4 h-4" />
            Ajouter une mesure
          </button>
          <button
            type="button"
            onClick={() => onOpenGlossary(primaryMetric)}
            className="rounded-xl bg-night-800 border border-night-600 px-3 py-2 text-sm text-slate-200 hover:text-white flex items-center gap-2 w-fit"
          >
            <span className="w-5 h-5 rounded-full border border-teal-500/50 text-teal-300 inline-flex items-center justify-center font-bold">?</span>
            Comprendre {primaryInfo.label}
          </button>
        </div>
      </div>

      <div className="surface p-4 space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-wider text-slate-500 flex items-center gap-2">
              <CalendarRange className="w-4 h-4" /> Période affichée
            </p>
            <div className="flex flex-wrap gap-2 mt-2">
              {RANGE_OPTIONS.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => setRange(option.key)}
                  className={`rounded-xl px-3 py-1.5 text-xs border transition-colors ${
                    range === option.key
                      ? 'bg-teal-500/15 border-teal-500/30 text-teal-300'
                      : 'border-night-700 text-slate-400 hover:text-white'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <label className="block min-w-[260px]">
            <span className="text-xs uppercase tracking-wider text-slate-500">Comparer avec</span>
            <select
              value={comparisonMetric}
              onChange={(event) => setComparisonMetric(event.target.value as Metric | '')}
              className="w-full mt-2 rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white outline-none focus:border-teal-500/60"
            >
              <option value="">Aucune superposition</option>
              {availableComparisons.map((info) => (
                <option key={info.key} value={info.key}>{info.label}</option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <SeriesSummaryCard metric={primaryMetric} summary={primarySummary} />
        {comparisonMetric && (
          <SeriesSummaryCard metric={comparisonMetric} summary={comparisonSummary} secondary />
        )}
      </div>

      <div className="surface p-4 md:p-5 space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
          <div>
            <h2 className="section-title flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-teal-400" /> Courbe d’évolution
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              L’axe horizontal représente le temps. Les points proviennent uniquement de mesures réellement enregistrées.
            </p>
          </div>
          {comparisonInfo && primaryInfo.unit !== comparisonInfo.unit && (
            <p className="text-xs text-amber-300 max-w-xl">
              Deux unités différentes : axe gauche = {primaryInfo.unit || 'sans unité'}, axe droit = {comparisonInfo.unit || 'sans unité'}.
              La superposition compare surtout la chronologie des variations, pas leur amplitude numérique directe.
            </p>
          )}
        </div>

        <MeasurementComparisonChart
          primaryMetric={primaryMetric}
          primarySeries={primarySeries}
          comparisonMetric={comparisonMetric || null}
          comparisonSeries={comparisonSeries}
        />
      </div>

      {comparisonMetric && (
        <div className="surface p-4 border border-night-700/60">
          <p className="text-sm text-slate-300 flex items-start gap-2">
            <BookOpen className="w-4 h-4 text-teal-400 mt-0.5 flex-shrink-0" />
            Une concordance visuelle entre deux courbes ne démontre pas une relation causale. Elle sert à repérer des co-variations à examiner avec le contexte, le journal des interventions et les mécanismes décrits dans le lexique.
          </p>
        </div>
      )}
    </div>
  );
}

function SeriesSummaryCard({
  metric,
  summary,
  secondary = false,
}: {
  metric: Metric;
  summary: SeriesSummary;
  secondary?: boolean;
}) {
  const info = METRICS[metric];
  const border = secondary ? 'border-sky-500/30' : 'border-teal-500/30';
  return (
    <div className={`surface p-4 border ${border}`}>
      <p className="text-xs uppercase tracking-wider text-slate-500">{info.label}</p>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-3 text-sm">
        <SummaryValue label="Dernière" value={summary.latest} unit={info.unit} />
        <SummaryValue label="Minimum" value={summary.minimum} unit={info.unit} />
        <SummaryValue label="Maximum" value={summary.maximum} unit={info.unit} />
        <SummaryValue label="Moyenne" value={summary.average} unit={info.unit} />
        <SummaryValue label="Mesures" value={summary.count} unit="" digits={0} />
      </div>
    </div>
  );
}

function SummaryValue({
  label,
  value,
  unit,
  digits = 2,
}: {
  label: string;
  value: number | null;
  unit: string;
  digits?: number;
}) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-mono text-white mt-1">
        {value === null ? '—' : value.toFixed(digits)}
        {value !== null && unit ? <span className="text-slate-500 ml-1">{unit}</span> : null}
      </p>
    </div>
  );
}

function MeasurementComparisonChart({
  primaryMetric,
  primarySeries,
  comparisonMetric,
  comparisonSeries,
}: {
  primaryMetric: Metric;
  primarySeries: SeriesPoint[];
  comparisonMetric: Metric | null;
  comparisonSeries: SeriesPoint[];
}) {
  const width = 960;
  const height = 360;
  const margin = { top: 28, right: 82, bottom: 52, left: 82 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;

  const allTimes = [...primarySeries, ...comparisonSeries].map((point) => point.timestamp);
  if (allTimes.length === 0) {
    return (
      <div className="min-h-[300px] flex items-center justify-center rounded-xl bg-night-900/40 border border-night-700 text-sm text-slate-500">
        Aucune mesure dans cette période.
      </div>
    );
  }

  const timeMin = Math.min(...allTimes);
  const timeMax = Math.max(...allTimes);
  const primaryExtent = paddedExtent(primarySeries.map((point) => point.value));
  const comparisonInfo = comparisonMetric ? METRICS[comparisonMetric] : null;
  const hasComparisonData = Boolean(comparisonMetric && comparisonSeries.length > 0);
  const sharedScale = Boolean(
    hasComparisonData && comparisonInfo && METRICS[primaryMetric].unit === comparisonInfo.unit,
  );
  const rawComparisonExtent = hasComparisonData
    ? paddedExtent(comparisonSeries.map((point) => point.value))
    : primaryExtent;
  const comparisonExtent = sharedScale
    ? mergeExtents(primaryExtent, rawComparisonExtent)
    : rawComparisonExtent;
  const effectivePrimaryExtent = sharedScale ? comparisonExtent : primaryExtent;

  const xFor = (timestamp: number) => {
    if (timeMax === timeMin) return margin.left + plotWidth / 2;
    return margin.left + ((timestamp - timeMin) / (timeMax - timeMin)) * plotWidth;
  };
  const yFor = (value: number, extent: [number, number]) => {
    const [minimum, maximum] = extent;
    return margin.top + (1 - (value - minimum) / (maximum - minimum)) * plotHeight;
  };
  const pathFor = (series: SeriesPoint[], extent: [number, number]) => series
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${xFor(point.timestamp).toFixed(2)} ${yFor(point.value, extent).toFixed(2)}`)
    .join(' ');

  const primaryPath = pathFor(primarySeries, effectivePrimaryExtent);
  const comparisonPath = comparisonMetric ? pathFor(comparisonSeries, comparisonExtent) : '';
  const ticks = buildTimeTicks(timeMin, timeMax, 5);
  const leftTicks = buildValueTicks(effectivePrimaryExtent, 5);
  const rightTicks = hasComparisonData && !sharedScale ? buildValueTicks(comparisonExtent, 5) : [];

  return (
    <div className="overflow-x-auto">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`Évolution de ${METRICS[primaryMetric].label}${comparisonMetric ? ` comparée à ${METRICS[comparisonMetric].label}` : ''}`}
        className="w-full min-w-[720px] h-auto"
      >
        <rect x={margin.left} y={margin.top} width={plotWidth} height={plotHeight} fill="rgba(15,23,42,0.35)" rx="10" />

        {leftTicks.map((tick) => {
          const y = yFor(tick, effectivePrimaryExtent);
          return (
            <g key={`left-${tick}`}>
              <line x1={margin.left} x2={width - margin.right} y1={y} y2={y} stroke="rgba(100,116,139,0.16)" strokeWidth="1" />
              <text x={margin.left - 10} y={y + 4} textAnchor="end" fontSize="11" fill="#94a3b8">{formatAxisValue(tick)}</text>
            </g>
          );
        })}

        {rightTicks.map((tick) => {
          const y = yFor(tick, comparisonExtent);
          return (
            <text key={`right-${tick}`} x={width - margin.right + 10} y={y + 4} textAnchor="start" fontSize="11" fill="#7dd3fc">
              {formatAxisValue(tick)}
            </text>
          );
        })}

        {ticks.map((tick) => {
          const x = xFor(tick);
          return (
            <g key={`time-${tick}`}>
              <line x1={x} x2={x} y1={margin.top} y2={height - margin.bottom} stroke="rgba(100,116,139,0.10)" strokeWidth="1" />
              <text x={x} y={height - margin.bottom + 24} textAnchor="middle" fontSize="11" fill="#64748b">
                {formatDateTick(tick, timeMax - timeMin)}
              </text>
            </g>
          );
        })}

        {primaryPath && (
          <path d={primaryPath} fill="none" stroke="#2dd4bf" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        )}
        {primarySeries.map((point) => (
          <circle key={`p-${point.timestamp}-${point.value}`} cx={xFor(point.timestamp)} cy={yFor(point.value, effectivePrimaryExtent)} r="3" fill="#2dd4bf">
            <title>{`${new Date(point.timestamp).toLocaleString('fr-FR')} — ${point.value} ${METRICS[primaryMetric].unit}`}</title>
          </circle>
        ))}

        {comparisonMetric && comparisonPath && (
          <path d={comparisonPath} fill="none" stroke="#38bdf8" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        )}
        {comparisonMetric && comparisonSeries.map((point) => (
          <circle key={`c-${point.timestamp}-${point.value}`} cx={xFor(point.timestamp)} cy={yFor(point.value, comparisonExtent)} r="3" fill="#38bdf8">
            <title>{`${new Date(point.timestamp).toLocaleString('fr-FR')} — ${point.value} ${METRICS[comparisonMetric].unit}`}</title>
          </circle>
        ))}

        <text x={margin.left} y={17} fontSize="12" fill="#5eead4">
          {METRICS[primaryMetric].label} · {METRICS[primaryMetric].unit || 'sans unité'}
        </text>
        {comparisonMetric && (
          <text x={width - margin.right} y={17} textAnchor="end" fontSize="12" fill="#7dd3fc">
            {METRICS[comparisonMetric].label} · {METRICS[comparisonMetric].unit || 'sans unité'}
          </text>
        )}
      </svg>
    </div>
  );
}

export function filterMeasurementsByRange(
  measurements: Measurement[],
  range: MeasurementRange,
  nowMs = Date.now(),
): Measurement[] {
  const option = RANGE_OPTIONS.find((item) => item.key === range);
  if (!option || option.days === null) {
    return [...measurements];
  }
  const cutoff = nowMs - option.days * 24 * 60 * 60 * 1000;
  return measurements.filter((measurement) => new Date(measurement.recorded_at).getTime() >= cutoff);
}

export function buildMetricSeries(measurements: Measurement[], metric: Metric): SeriesPoint[] {
  return measurements
    .filter((measurement) => measurement.metric === metric)
    .map((measurement) => ({
      timestamp: new Date(measurement.recorded_at).getTime(),
      value: measurement.value,
    }))
    .filter((point) => Number.isFinite(point.timestamp) && Number.isFinite(point.value))
    .sort((a, b) => a.timestamp - b.timestamp);
}

export function summarizeSeries(series: SeriesPoint[]): SeriesSummary {
  if (series.length === 0) {
    return { count: 0, latest: null, minimum: null, maximum: null, average: null };
  }
  const values = series.map((point) => point.value);
  const total = values.reduce((sum, value) => sum + value, 0);
  return {
    count: values.length,
    latest: series[series.length - 1].value,
    minimum: Math.min(...values),
    maximum: Math.max(...values),
    average: total / values.length,
  };
}

function paddedExtent(values: number[]): [number, number] {
  if (values.length === 0) return [0, 1];
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  if (minimum === maximum) {
    const delta = Math.max(Math.abs(minimum) * 0.05, 0.5);
    return [minimum - delta, maximum + delta];
  }
  const padding = (maximum - minimum) * 0.08;
  return [minimum - padding, maximum + padding];
}

function mergeExtents(first: [number, number], second: [number, number]): [number, number] {
  return [Math.min(first[0], second[0]), Math.max(first[1], second[1])];
}

function buildTimeTicks(minimum: number, maximum: number, count: number): number[] {
  if (maximum === minimum) return [minimum];
  return Array.from({ length: count }, (_, index) => minimum + (index / (count - 1)) * (maximum - minimum));
}

function buildValueTicks(extent: [number, number], count: number): number[] {
  const [minimum, maximum] = extent;
  return Array.from({ length: count }, (_, index) => maximum - (index / (count - 1)) * (maximum - minimum));
}

function formatAxisValue(value: number): string {
  const absolute = Math.abs(value);
  if (absolute >= 1000) return value.toFixed(0);
  if (absolute >= 100) return value.toFixed(1);
  return value.toFixed(2);
}

function formatDateTick(timestamp: number, spanMs: number): string {
  const date = new Date(timestamp);
  const oneDay = 24 * 60 * 60 * 1000;
  if (spanMs <= 2 * oneDay) {
    return date.toLocaleString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  }
  if (spanMs <= 120 * oneDay) {
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
  }
  return date.toLocaleDateString('fr-FR', { month: 'short', year: '2-digit' });
}
