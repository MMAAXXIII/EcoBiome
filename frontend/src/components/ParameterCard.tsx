import type { Metric } from '../lib/types';
import { MetricSparkline } from './MetricSparkline';

const statusClasses: Record<Metric['status'], string> = {
  ideal: 'text-emerald-400',
  warning: 'text-amber-300',
  critical: 'text-coral'
};

export function ParameterCard({ label, value, ideal, status, sparkline }: Metric) {
  return (
    <article className="rounded-3xl border border-white/5 bg-white/5 p-5 shadow-panel transition hover:border-ecobiome-accent/20 hover:bg-white/10">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-slate-400">{label}</p>
          <p className="mt-2 text-xl font-semibold text-ecobiome-text">{value}</p>
        </div>
        <span className={`rounded-2xl px-3 py-1 text-xs font-semibold ${statusClasses[status]}`}>
          {status === 'ideal' ? 'Idéal' : status === 'warning' ? 'Alerte' : 'Critique'}
        </span>
      </div>
      <p className="mt-4 text-sm text-slate-400">Idéal: {ideal}</p>
      <div className="mt-4">
        <MetricSparkline points={sparkline} />
      </div>
    </article>
  );
}
