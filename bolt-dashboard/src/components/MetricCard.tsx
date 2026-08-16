import { TrendingUp } from 'lucide-react';
import type { Metric } from '@/lib/types';
import { METRICS, getMetricStatus } from '@/lib/types';
import { Sparkline } from './Sparkline';

interface MetricCardProps {
  metric: Metric;
  currentValue: number;
  data: number[];
  unit?: string;
  onAddMeasurement?: (metric: Metric) => void;
  onOpenGlossary?: (metric: Metric) => void;
  onOpenDetails?: (metric: Metric) => void;
}

export function MetricCard({
  metric,
  currentValue,
  data,
  unit,
  onAddMeasurement,
  onOpenGlossary,
  onOpenDetails,
}: MetricCardProps) {
  const info = METRICS[metric];
  const status = getMetricStatus(metric, currentValue);
  const contextual = info.contextual === true;
  const statusColor = contextual
    ? 'text-slate-200'
    : status === 'stable'
      ? 'text-teal-300'
      : status === 'warning'
        ? 'text-amber-300'
        : 'text-coral-400';
  const borderColor = contextual
    ? 'border-l-slate-600'
    : status === 'stable'
      ? 'border-l-teal-500'
      : status === 'warning'
        ? 'border-l-amber-500'
        : 'border-l-coral-500';

  return (
    <div className={`kpi-card border-l-4 ${borderColor}`}>
      <div className="flex items-start justify-between gap-2 mb-1">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{info.label}</p>
        <div className="flex items-center gap-1">
          {onAddMeasurement && (
            <button
              type="button"
              onClick={() => onAddMeasurement(metric)}
              title={`Ajouter une mesure de ${info.label}`}
              aria-label={`Ajouter une mesure de ${info.label}`}
              className="w-7 h-7 rounded-full border border-night-600 text-teal-300 hover:border-teal-500/60 hover:bg-teal-500/10 inline-flex items-center justify-center font-bold text-base leading-none"
            >
              +
            </button>
          )}
          {onOpenGlossary && (
            <button
              type="button"
              onClick={() => onOpenGlossary(metric)}
              title={`Ouvrir ${info.label} dans le lexique`}
              aria-label={`Ouvrir ${info.label} dans le lexique`}
              className="w-7 h-7 rounded-full border border-night-600 text-teal-300 hover:border-teal-500/60 hover:bg-teal-500/10 inline-flex items-center justify-center font-bold text-xs"
            >
              ?
            </button>
          )}
          {onOpenDetails && (
            <button
              type="button"
              onClick={() => onOpenDetails(metric)}
              title={`Voir l’évolution détaillée de ${info.label}`}
              aria-label={`Voir l’évolution détaillée de ${info.label}`}
              className="w-7 h-7 rounded-full border border-night-600 text-slate-400 hover:text-white hover:border-night-500 inline-flex items-center justify-center"
            >
              <TrendingUp className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
      <div className="flex items-end justify-between gap-2">
        <div>
          <p className={`font-display font-bold text-2xl ${statusColor}`}>
            {currentValue.toFixed(2)}
            <span className="text-sm text-slate-500 font-normal ml-1">{unit ?? info.unit}</span>
          </p>
          <p className="text-xs text-slate-500 mt-0.5">
            {contextual
              ? 'Interprétation selon espèces et contexte'
              : `Repère générique : ${info.ideal[0]}–${info.ideal[1]}${info.unit}`}
          </p>
        </div>
        <div className="flex-shrink-0">
          <Sparkline metric={metric} data={data} />
        </div>
      </div>
    </div>
  );
}
