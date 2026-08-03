import { useState, useMemo } from 'react';
import { useWaterBodies, useMeasurements, useOrganisms, getLatestByMetric, getMetricSeries } from '@/lib/hooks';
import { METRIC_LIST, METRICS, WATER_BODY_TYPE_LABELS, ORGANISM_KIND_LABELS, type WaterBody, type Metric } from '@/lib/types';
import { MetricCard } from '@/components/MetricCard';
import { WaterTankViz } from '@/components/WaterTankViz';
import { StatusBadge, StatusDot } from '@/components/StatusBadge';
import { ORGANISM_ICONS } from '@/lib/nav';
import { ArrowLeft, Leaf, Plus, TrendingUp, Calendar } from 'lucide-react';

interface WaterBodiesViewProps {
  initialWaterBody: WaterBody | null;
  onClearInitial: () => void;
}

export function WaterBodiesView({ initialWaterBody, onClearInitial }: WaterBodiesViewProps) {
  const { data: waterBodies, loading } = useWaterBodies();
  const [selectedId, setSelectedId] = useState<string | null>(initialWaterBody?.id ?? null);

  const selected = useMemo(() => {
    if (waterBodies.length === 0) return null;
    return waterBodies.find((w) => w.id === selectedId) ?? null;
  }, [waterBodies, selectedId]);

  if (loading) {
    return <div className="p-6 space-y-4"><div className="skeleton h-96" /></div>;
  }

  if (selected) {
    return (
      <WaterBodyDetail
        waterBody={selected}
        onBack={() => { setSelectedId(null); onClearInitial(); }}
      />
    );
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">{waterBodies.length} milieux aquatiques suivis</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {waterBodies.map((wb) => (
          <div key={wb.id} onClick={() => setSelectedId(wb.id)} className="cursor-pointer group">
            <WaterTankViz waterBody={wb} fillPercent={65 + Math.floor(wb.volume_liters / 50) % 25} />
          </div>
        ))}

        {/* Add new card */}
        <button className="surface surface-hover p-5 flex flex-col items-center justify-center min-h-[280px] border-dashed border-2 border-night-700 hover:border-teal-500/40 group">
          <div className="w-12 h-12 rounded-xl bg-night-800 group-hover:bg-teal-500/15 flex items-center justify-center transition-colors mb-3">
            <Plus className="w-6 h-6 text-slate-500 group-hover:text-teal-400 transition-colors" />
          </div>
          <p className="text-sm font-medium text-slate-400 group-hover:text-white transition-colors">Ajouter un milieu</p>
        </button>
      </div>
    </div>
  );
}

function WaterBodyDetail({ waterBody, onBack }: { waterBody: WaterBody; onBack: () => void }) {
  const { data: measurements, loading: measLoading } = useMeasurements(waterBody.id);
  const { data: organisms } = useOrganisms(waterBody.id);
  const latest = useMemo(() => getLatestByMetric(measurements), [measurements]);

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Back button */}
      <button onClick={onBack} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors">
        <ArrowLeft className="w-4 h-4" /> Retour aux milieux
      </button>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <StatusDot status={waterBody.status} />
            <h1 className="font-display font-bold text-white text-2xl">{waterBody.name}</h1>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span>{WATER_BODY_TYPE_LABELS[waterBody.type]}</span>
            <span>·</span>
            <span>{waterBody.volume_liters} litres</span>
            <span>·</span>
            <StatusBadge status={waterBody.status} />
          </div>
        </div>
      </div>

      {/* Water viz */}
      <WaterTankViz waterBody={waterBody} fillPercent={72} />

      {/* Metrics */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="section-title">Paramètres physico-chimiques</h2>
          <span className="text-xs text-slate-500 flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" /> 7 derniers jours
          </span>
        </div>
        {measLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
            {[...Array(6)].map((_, i) => <div key={i} className="skeleton h-28" />)}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
            {METRIC_LIST.map((info) => {
              const val = latest[info.key];
              const series = getMetricSeries(measurements, info.key as Metric);
              if (val === null || val === undefined || series.length === 0) {
                return (
                  <div key={info.key} className="kpi-card opacity-50">
                    <p className="text-xs text-slate-400 uppercase tracking-wider">{info.label}</p>
                    <p className="text-slate-500 text-sm mt-2">Aucune donnée</p>
                  </div>
                );
              }
              return <MetricCard key={info.key} metric={info.key as Metric} currentValue={val} data={series} />;
            })}
          </div>
        )}
      </div>

      {/* Organisms */}
      <div>
        <h2 className="section-title mb-3 flex items-center gap-2">
          <Leaf className="w-4.5 h-4.5 text-teal-400" />
          Organismes vivants
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {organisms.length === 0 && <p className="text-sm text-slate-500">Aucun organisme enregistré.</p>}
          {organisms.map((org) => {
            const Icon = ORGANISM_ICONS[org.kind] ?? Leaf;
            const healthColor = org.health >= 80 ? 'text-teal-400' : org.health >= 50 ? 'text-amber-400' : 'text-coral-400';
            return (
              <div key={org.id} className="surface surface-hover p-4">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-night-800 flex items-center justify-center shrink-0">
                    <Icon className="w-5 h-5 text-slate-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{org.name}</p>
                    <p className="text-xs text-slate-500">{ORGANISM_KIND_LABELS[org.kind]} · {org.population} individus</p>
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 h-1.5 rounded-full bg-night-700 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${org.health >= 80 ? 'bg-teal-500' : org.health >= 50 ? 'bg-amber-500' : 'bg-coral-500'}`}
                          style={{ width: `${org.health}%` }}
                        />
                      </div>
                      <span className={`text-xs font-mono ${healthColor}`}>{org.health}%</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Measurement history */}
      <div>
        <h2 className="section-title mb-3 flex items-center gap-2">
          <Calendar className="w-4.5 h-4.5 text-teal-400" />
          Historique des mesures
        </h2>
        <div className="surface overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-night-700/40 text-xs text-slate-400 uppercase tracking-wider">
                  <th className="text-left p-3 font-medium">Paramètre</th>
                  <th className="text-right p-3 font-medium">Valeur</th>
                  <th className="text-right p-3 font-medium">Idéal</th>
                  <th className="text-left p-3 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {measurements.length === 0 && (
                  <tr><td colSpan={4} className="p-4 text-slate-500 text-center">Aucune mesure enregistrée.</td></tr>
                )}
                {[...measurements].reverse().slice(0, 20).map((m) => {
                  const info = METRICS[m.metric as Metric];
                  return (
                    <tr key={m.id} className="border-b border-night-800/40 hover:bg-night-800/30 transition-colors">
                      <td className="p-3 text-slate-300">{info?.label ?? m.metric}</td>
                      <td className="p-3 text-right font-mono text-white">{m.value} {m.unit}</td>
                      <td className="p-3 text-right text-xs text-slate-500">{info?.ideal[0]}–{info?.ideal[1]}{info?.unit}</td>
                      <td className="p-3 text-xs text-slate-500">{new Date(m.recorded_at).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
