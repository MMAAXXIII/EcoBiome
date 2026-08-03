import type { WaterBodyStatus } from '@/lib/types';
import { STATUS_LABELS } from '@/lib/types';

export function StatusBadge({ status }: { status: WaterBodyStatus }) {
  if (status === 'stable') return <span className="badge-ok"><span className="w-1.5 h-1.5 rounded-full bg-teal-400" /> {STATUS_LABELS.stable}</span>;
  if (status === 'warning') return <span className="badge-warn"><span className="w-1.5 h-1.5 rounded-full bg-amber-400" /> {STATUS_LABELS.warning}</span>;
  return <span className="badge-crit"><span className="w-1.5 h-1.5 rounded-full bg-coral-400" /> {STATUS_LABELS.critical}</span>;
}

export function StatusDot({ status }: { status: WaterBodyStatus }) {
  const color = status === 'stable' ? 'bg-teal-400' : status === 'warning' ? 'bg-amber-400' : 'bg-coral-400';
  const glow = status === 'stable' ? 'shadow-[0_0_8px_rgba(52,211,164,0.6)]' : status === 'warning' ? 'shadow-[0_0_8px_rgba(251,191,36,0.6)]' : 'shadow-[0_0_8px_rgba(251,113,133,0.6)]';
  return <span className={`inline-block w-2 h-2 rounded-full ${color} ${glow}`} />;
}
