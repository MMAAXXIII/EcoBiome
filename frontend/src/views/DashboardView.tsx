import { useState, useMemo, useEffect } from 'react';
import { useWaterBodies, useAllMeasurements, useDiagnostics, getLatestByMetric, getMetricSeries } from '@/lib/hooks';
import { METRIC_LIST, type Metric, type WaterBody } from '@/lib/types';
import { MetricCard } from '@/components/MetricCard';
import { WaterTankViz } from '@/components/WaterTankViz';
import { StatusBadge, StatusDot } from '@/components/StatusBadge';
import { Droplets, AlertTriangle, CheckCircle2, Activity, TrendingUp, ChevronRight, Microscope } from 'lucide-react';

interface ProjectDashboardSummary {
  description: string;
  project_type: string;
  tags: string[];
  journal_event_count: number;
  media_file_count: number;
  diagnostic_count: number;
  hypothesis_count: number;
  experiment_count: number;
  conclusion_count: number;
}
interface DashboardViewProps {
  onNavigateToWaterBody: (wb: WaterBody) => void;
  onNavigateToView: (view: 'waterbodies' | 'diagnostics' | 'journal') => void;
}

export function DashboardView({ onNavigateToWaterBody, onNavigateToView }: DashboardViewProps) {

  // 👉 MODULE BACKEND
  const [projectInfo, setProjectInfo] = useState<ProjectDashboardSummary | null>(null);

  useEffect(() => {
    fetch("http://localhost:8000/dashboard")
      .then((res) => res.json())
      .then((json) => setProjectInfo(json))
      .catch((err) => console.error("Erreur backend :", err));
  }, []);

  // 👉 Supabase hooks
  const { data: waterBodies, loading: wbLoading } = useWaterBodies();
  const { data: allMeasurements, loading: measLoading } = useAllMeasurements();
  const { data: diagnostics } = useDiagnostics();
  const [selectedWbId, setSelectedWbId] = useState<string | null>(null);

  const selectedWb = useMemo(() => {
    if (waterBodies.length === 0) return null;
    return waterBodies.find((w) => w.id === selectedWbId) ?? waterBodies[0];
  }, [waterBodies, selectedWbId]);

  const selectedMeasurements = useMemo(() => {
    if (!selectedWb) return [];
    return allMeasurements.filter((m) => m.water_body_id === selectedWb.id);
  }, [allMeasurements, selectedWb]);

  const latest = useMemo(() => getLatestByMetric(selectedMeasurements), [selectedMeasurements]);

  const stats = useMemo(() => {
    const stable = waterBodies.filter((w) => w.status === 'stable').length;
    const warning = waterBodies.filter((w) => w.status === 'warning').length;
    const critical = waterBodies.filter((w) => w.status === 'critical').length;
    return { total: waterBodies.length, stable, warning, critical };
  }, [waterBodies]);

  const recentDiagnostics = diagnostics.slice(0, 4);


  if (wbLoading || measLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-32" />)}
        </div>
        <div className="skeleton h-96" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">

      {projectInfo && (
  <div className="surface p-5 mb-6">
    <h2 className="section-title mb-2">Résumé du projet EcoBiome</h2>
    <p className="text-slate-300">{projectInfo.description}</p>

    <ul className="mt-3 text-sm text-slate-400 space-y-1">
      <li>Type : {projectInfo.project_type}</li>
      <li>Tags : {projectInfo.tags.join(", ")}</li>
      <li>Événements : {projectInfo.journal_event_count}</li>
      <li>Médias : {projectInfo.media_file_count}</li>
      <li>Diagnostics : {projectInfo.diagnostic_count}</li>
      <li>Hypothèses : {projectInfo.hypothesis_count}</li>
      <li>Expériences : {projectInfo.experiment_count}</li>
      <li>Conclusions : {projectInfo.conclusion_count}</li>
    </ul>
  </div>
)}
      {/* Top KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="kpi-card border-l-4 border-l-teal-500">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500/15 flex items-center justify-center">
              <Droplets className="w-5 h-5 text-teal-400" />
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider">Milieux aquatiques</p>
              <p className="font-display font-bold text-white text-2xl">{stats.total}</p>
            </div>
          </div>
        </div>

        <div className="kpi-card border-l-4 border-l-teal-500">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500/15 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-teal-400" />
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider">Stables</p>
              <p className="font-display font-bold text-white text-2xl">{stats.stable}</p>
            </div>
          </div>
        </div>

        <div className="kpi-card border-l-4 border-l-amber-500">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/15 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider">En vigilance</p>
              <p className="font-display font-bold text-white text-2xl">{stats.warning}</p>
            </div>
          </div>
        </div>

        <div className="kpi-card border-l-4 border-l-coral-500">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-coral-500/15 flex items-center justify-center">
              <Activity className="w-5 h-5 text-coral-400" />
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider">Critiques</p>
              <p className="font-display font-bold text-white text-2xl">{stats.critical}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Water body selector */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {waterBodies.map((wb) => (
          <button
            key={wb.id}
            onClick={() => setSelectedWbId(wb.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
              selectedWb?.id === wb.id
                ? 'bg-night-700/60 text-white border border-night-600'
                : 'bg-night-850/40 text-slate-400 border border-transparent hover:text-white hover:bg-night-800/40'
            }`}
          >
            <StatusDot status={wb.status} />
            {wb.name}
          </button>
        ))}
      </div>

      {/* Main grid: water viz + metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Water tank viz */}
        <div className="lg:col-span-1">
          {selectedWb && (
            <div onClick={() => onNavigateToWaterBody(selectedWb)} className="cursor-pointer group">
              <WaterTankViz waterBody={selectedWb} fillPercent={72} />
              <p className="mt-2 text-xs text-slate-500 group-hover:text-teal-400 transition-colors flex items-center gap-1">
                Voir le détail <ChevronRight className="w-3 h-3" />
              </p>
            </div>
          )}
        </div>

        {/* Metrics grid */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="section-title">Paramètres en temps réel</h2>
            <span className="text-xs text-slate-500 flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5" /> 7 derniers jours
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
            {METRIC_LIST.map((metricInfo) => {
              const val = latest[metricInfo.key];
              const series = getMetricSeries(selectedMeasurements, metricInfo.key);
              if (val === null || val === undefined || series.length === 0) {
                return (
                  <div key={metricInfo.key} className="kpi-card opacity-50">
                    <p className="text-xs text-slate-400 uppercase tracking-wider">{metricInfo.label}</p>
                    <p className="text-slate-500 text-sm mt-2">Aucune donnée</p>
                  </div>
                );
              }
              return (
                <MetricCard
                  key={metricInfo.key}
                  metric={metricInfo.key as Metric}
                  currentValue={val}
                  data={series}
                />
              );
            })}
          </div>
        </div>
      </div>

      {/* Bottom row: recent diagnostics + water body list */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent diagnostics */}
        <div className="surface p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title flex items-center gap-2">
              <Microscope className="w-4.5 h-4.5 text-teal-400" />
              Diagnostics récents
            </h2>
            <button onClick={() => onNavigateToView('diagnostics')} className="text-xs text-teal-400 hover:text-teal-300 flex items-center gap-1">
              Tout voir <ChevronRight className="w-3 h-3" />
            </button>
          </div>
          <div className="space-y-3">
            {recentDiagnostics.length === 0 && <p className="text-sm text-slate-500">Aucun diagnostic.</p>}
            {recentDiagnostics.map((diag) => {
              const wb = waterBodies.find((w) => w.id === diag.water_body_id);
              return (
                <div key={diag.id} className="flex items-start gap-3 p-3 rounded-xl bg-night-900/40 hover:bg-night-800/40 transition-colors">
                  <StatusDot status={diag.status === 'healthy' ? 'stable' : diag.status === 'warning' ? 'warning' : 'critical'} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{wb?.name ?? 'Milieu inconnu'}</p>
                    <p className="text-xs text-slate-400 line-clamp-1">{diag.summary}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xs font-mono text-slate-500">{diag.confidence}%</p>
                    <p className="text-[10px] text-slate-600">{new Date(diag.created_at).toLocaleDateString('fr-FR')}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Water body overview */}
        <div className="surface p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title flex items-center gap-2">
              <Droplets className="w-4.5 h-4.5 text-teal-400" />
              État des milieux
            </h2>
            <button onClick={() => onNavigateToView('waterbodies')} className="text-xs text-teal-400 hover:text-teal-300 flex items-center gap-1">
              Tout voir <ChevronRight className="w-3 h-3" />
            </button>
          </div>
          <div className="space-y-3">
            {waterBodies.map((wb) => (
              <div
                key={wb.id}
                onClick={() => onNavigateToWaterBody(wb)}
                className="flex items-center gap-3 p-3 rounded-xl bg-night-900/40 hover:bg-night-800/40 transition-colors cursor-pointer group"
              >
                <StatusDot status={wb.status} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate group-hover:text-teal-300 transition-colors">{wb.name}</p>
                  <p className="text-xs text-slate-500">{wb.type} · {wb.volume_liters} L</p>
                </div>
                <StatusBadge status={wb.status} />
                <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-teal-400 transition-colors" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
