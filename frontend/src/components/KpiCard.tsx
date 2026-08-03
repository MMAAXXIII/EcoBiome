import { ArrowUpRight, AlertTriangle, CheckCircle2 } from 'lucide-react';
import type { KpiCard as KpiCardType } from '../lib/types';

const statusStyles: Record<KpiCardType['status'], string> = {
  stable: 'bg-ecobiome-accent/10 text-ecobiome-accent border-ecobiome-accent/20',
  caution: 'bg-amber-500/10 text-amber-300 border-amber-300/20',
  critical: 'bg-coral/10 text-coral border-coral/20'
};

export function KpiCard({ title, value, status, description }: KpiCardType) {
  const Icon = status === 'critical' ? AlertTriangle : status === 'caution' ? ArrowUpRight : CheckCircle2;

  return (
    <article className="rounded-3xl border border-white/5 bg-white/5 p-5 shadow-panel transition hover:border-ecobiome-accent/20 hover:bg-white/10">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-slate-400">{title}</p>
          <p className="mt-3 text-3xl font-semibold text-ecobiome-text">{value}</p>
        </div>
        <span className={`inline-flex h-12 w-12 items-center justify-center rounded-3xl border ${statusStyles[status]}`}>
          <Icon className="h-5 w-5" />
        </span>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-300">{description}</p>
    </article>
  );
}
