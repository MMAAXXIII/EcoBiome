import type { Metric } from '@/lib/types';
import { METRICS, getMetricStatus } from '@/lib/types';
import { Sparkline } from './Sparkline';

interface MetricCardProps {
  metric: Metric;
  currentValue: number;
  data: number[];
  unit?: string;
}

export function MetricCard({ metric, currentValue, data, unit }: MetricCardProps) {
  const info = METRICS[metric];
  const status = getMetricStatus(metric, currentValue);
  const statusColor = status === 'stable' ? 'text-teal-300' : status === 'warning' ? 'text-amber-300' : 'text-coral-400';
  const borderColor = status === 'stable' ? 'border-l-teal-500' : status === 'warning' ? 'border-l-amber-500' : 'border-l-coral-500';

  return (
    <div className={`kpi-card border-l-4 ${borderColor}`}>
      <div className="flex items-start justify-between mb-1">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{info.label}</p>
        </div>
      </div>
      <div className="flex items-end justify-between gap-2">
        <div>
          <p className={`font-display font-bold text-2xl ${statusColor}`}>
            {currentValue.toFixed(2)}
            <span className="text-sm text-slate-500 font-normal ml-1">{unit ?? info.unit}</span>
          </p>
          <p className="text-xs text-slate-500 mt-0.5">
            Idéal: {info.ideal[0]}–{info.ideal[1]}{info.unit}
          </p>
        </div>
        <div className="flex-shrink-0">
          <Sparkline metric={metric} data={data} />
        </div>
      </div>
    </div>
  );
}
