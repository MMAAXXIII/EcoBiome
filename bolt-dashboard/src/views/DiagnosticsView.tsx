import { useState, useMemo } from 'react';
import { useDiagnostics, useDiagnosticFindings, useWaterBodies } from '@/lib/hooks';
import { StatusDot, StatusBadge } from '@/components/StatusBadge';
import { Microscope, ChevronRight, GitBranch, AlertTriangle, Info, AlertCircle, Clock, Target } from 'lucide-react';

export function DiagnosticsView() {
  const { data: diagnostics, loading } = useDiagnostics();
  const { data: waterBodies } = useWaterBodies();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selected = useMemo(() => diagnostics.find((d) => d.id === selectedId) ?? null, [diagnostics, selectedId]);
  const { data: findings } = useDiagnosticFindings(selected?.id ?? null);

  if (loading) {
    return <div className="p-6 space-y-4"><div className="skeleton h-96" /></div>;
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <p className="text-sm text-slate-400">{diagnostics.length} sessions de diagnostic analysées</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Diagnostic list */}
        <div className="lg:col-span-1 space-y-3">
          {diagnostics.map((diag) => {
            const wb = waterBodies.find((w) => w.id === diag.water_body_id);
            const isActive = selected?.id === diag.id;
            const diagStatus = diag.status === 'healthy' ? 'stable' : diag.status === 'warning' ? 'warning' : 'critical';
            return (
              <button
                key={diag.id}
                onClick={() => setSelectedId(diag.id)}
                className={`w-full surface p-4 text-left transition-all ${isActive ? 'border-teal-500/40 bg-night-800/60' : 'surface-hover'}`}
              >
                <div className="flex items-start gap-3">
                  <StatusDot status={diagStatus as 'stable' | 'warning' | 'critical'} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{wb?.name ?? 'Milieu inconnu'}</p>
                    <p className="text-xs text-slate-400 line-clamp-2 mt-1">{diag.summary}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(diag.created_at).toLocaleDateString('fr-FR')}</span>
                      <span className="flex items-center gap-1"><Target className="w-3 h-3" /> {diag.confidence}%</span>
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Detail panel */}
        <div className="lg:col-span-2">
          {selected ? (
            <div className="space-y-4 animate-fade-in">
              {/* Header */}
              <div className="surface p-5">
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Microscope className="w-5 h-5 text-teal-400" />
                      <h2 className="font-display font-bold text-white text-xl">
                        {waterBodies.find((w) => w.id === selected.water_body_id)?.name}
                      </h2>
                    </div>
                    <StatusBadge status={selected.status === 'healthy' ? 'stable' : selected.status === 'warning' ? 'warning' : 'critical'} />
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500 uppercase tracking-wider">Confiance</p>
                    <p className="font-display font-bold text-2xl text-teal-400">{selected.confidence}%</p>
                  </div>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed">{selected.summary}</p>
                {selected.root_cause && (
                  <div className="mt-3 p-3 rounded-xl bg-coral-500/10 border border-coral-500/20">
                    <p className="text-xs text-coral-400 font-medium uppercase tracking-wider mb-1">Cause racine</p>
                    <p className="text-sm text-slate-300">{selected.root_cause}</p>
                  </div>
                )}
              </div>

              {/* Findings */}
              <div>
                <h3 className="section-title mb-3 flex items-center gap-2">
                  <GitBranch className="w-4.5 h-4.5 text-teal-400" />
                  Conclusions et chaînes causales
                </h3>
                <div className="space-y-3">
                  {findings.length === 0 && <p className="text-sm text-slate-500">Aucune conclusion détaillée.</p>}
                  {findings.map((f, idx) => {
                    const sevIcon = f.severity === 'critical' ? AlertCircle : f.severity === 'warning' ? AlertTriangle : Info;
                    const sevColor = f.severity === 'critical' ? 'text-coral-400' : f.severity === 'warning' ? 'text-amber-400' : 'text-teal-400';
                    const sevBg = f.severity === 'critical' ? 'bg-coral-500/10 border-coral-500/20' : f.severity === 'warning' ? 'bg-amber-500/10 border-amber-500/20' : 'bg-teal-500/10 border-teal-500/20';
                    const SevIcon = sevIcon;
                    return (
                      <div key={f.id ?? idx} className={`surface p-4 border-l-4 ${f.severity === 'critical' ? 'border-l-coral-500' : f.severity === 'warning' ? 'border-l-amber-500' : 'border-l-teal-500'}`}>
                        <div className="flex items-start gap-3 mb-2">
                          <div className={`w-8 h-8 rounded-lg ${sevBg} flex items-center justify-center shrink-0`}>
                            <SevIcon className={`w-4 h-4 ${sevColor}`} />
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-white">{f.metric}</p>
                            <p className="text-xs text-slate-400 mt-0.5">{f.observation}</p>
                          </div>
                        </div>
                        <p className="text-sm text-slate-300 leading-relaxed mb-3">{f.explanation}</p>

                        {/* Causal chain */}
                        {f.causal_chain && f.causal_chain.length > 0 && (
                          <div className="flex flex-wrap items-center gap-1.5 mt-2">
                            <span className="text-xs text-slate-500 mr-1">Chaîne causale:</span>
                            {f.causal_chain.map((step, i) => (
                              <div key={i} className="flex items-center gap-1.5">
                                <span className={`px-2 py-1 rounded-lg text-xs font-medium ${sevBg} ${sevColor}`}>{step}</span>
                                {i < f.causal_chain.length - 1 && <ChevronRight className="w-3 h-3 text-slate-600" />}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="surface p-12 flex flex-col items-center justify-center text-center min-h-[400px]">
              <Microscope className="w-12 h-12 text-slate-600 mb-4" />
              <p className="text-slate-400">Sélectionnez un diagnostic pour voir le détail</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
