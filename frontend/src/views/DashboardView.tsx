import { ExternalLink, Leaf, ShieldCheck, Sparkles } from 'lucide-react';
import { KpiCard } from '../components/KpiCard';
import { ParameterCard } from '../components/ParameterCard';
import { WaterTankViz } from '../components/WaterTankViz';
import { diagnostics, kpis, metrics, waterBodies } from '../lib/data';

export function DashboardView() {
  return (
    <div className="space-y-8">
      <section className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <div className="rounded-3xl border border-white/5 bg-white/5 p-6 shadow-panel">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.24em] text-ecobiome-accent/70">État global</p>
              <h3 className="mt-3 text-3xl font-semibold text-ecobiome-text">Surveillance des milieux en un coup d’œil</h3>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-300">
                Aperçu des écosystèmes, des paramètres critiques et des diagnostics récents pour garder vos aquariums et bassins sains.
              </p>
            </div>
            <div className="inline-flex items-center gap-3 rounded-3xl bg-ecobiome-surfaceAlt px-5 py-4 text-sm text-slate-200">
              <Sparkles className="h-5 w-5 text-ecobiome-accent" />
              <span>Thème EcoBiome Night</span>
            </div>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {kpis.map((kpi) => (
              <KpiCard key={kpi.title} {...kpi} />
            ))}
          </div>
        </div>

        <div className="grid gap-6">
          <div className="rounded-3xl border border-white/5 bg-white/5 p-6 shadow-panel">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-[0.24em] text-ecobiome-accent/75">Milieu principal</p>
                <h3 className="mt-2 text-2xl font-semibold text-ecobiome-text">Récif Corallien Principal</h3>
              </div>
              <span className="rounded-3xl bg-amber-500/10 px-4 py-2 text-sm font-semibold text-amber-300">Vigilance</span>
            </div>
            <div className="mt-6">
              <WaterTankViz fill={72} />
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <div className="rounded-3xl border border-white/5 bg-ecobiome-surfaceAlt p-5">
                <p className="text-sm text-slate-400">Volume</p>
                <p className="mt-2 text-xl font-semibold text-ecobiome-text">450 L</p>
              </div>
              <div className="rounded-3xl border border-white/5 bg-ecobiome-surfaceAlt p-5">
                <p className="text-sm text-slate-400">Dernière mise à jour</p>
                <p className="mt-2 text-xl font-semibold text-ecobiome-text">03/08/2026</p>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-white/5 bg-white/5 p-6 shadow-panel">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-[0.24em] text-ecobiome-accent/75">Qualité de l’eau</p>
                <h3 className="mt-2 text-2xl font-semibold text-ecobiome-text">Paramètres en temps réel</h3>
              </div>
              <div className="inline-flex items-center gap-2 rounded-3xl bg-ecobiome-surfaceAlt px-4 py-3 text-sm text-slate-300">
                <Leaf className="h-4 w-4 text-ecobiome-accent" />
                7 derniers jours
              </div>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {metrics.map((metric) => (
                <ParameterCard key={metric.label} {...metric} />
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-3xl border border-white/5 bg-white/5 p-6 shadow-panel">
          <div className="flex items-center justify-between gap-4">
            <h3 className="text-xl font-semibold text-ecobiome-text">Diagnostics récents</h3>
            <button className="inline-flex items-center gap-2 rounded-2xl bg-ecobiome-accent/10 px-4 py-2 text-sm text-ecobiome-accent transition hover:bg-ecobiome-accent/15">
              Tout voir
              <ExternalLink className="h-4 w-4" />
            </button>
          </div>

          <div className="mt-6 space-y-4">
            {diagnostics.map((diagnostic) => (
              <article key={diagnostic.name} className="rounded-3xl border border-white/5 bg-ecobiome-surfaceAlt p-5">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm text-slate-400">{diagnostic.name}</p>
                    <p className="mt-2 text-lg font-semibold text-ecobiome-text">{diagnostic.summary}</p>
                  </div>
                  <span className="rounded-3xl bg-ecobiome-accent/10 px-3 py-2 text-sm font-semibold text-ecobiome-accent">{diagnostic.confidence}</span>
                </div>
                <p className="mt-4 text-sm leading-6 text-slate-400">{diagnostic.date}</p>
              </article>
            ))}
          </div>
        </div>

        <div className="rounded-3xl border border-white/5 bg-white/5 p-6 shadow-panel">
          <div className="flex items-center justify-between gap-4">
            <h3 className="text-xl font-semibold text-ecobiome-text">État des milieux</h3>
            <span className="text-sm uppercase tracking-[0.3em] text-slate-400">Synthèse</span>
          </div>

          <div className="mt-6 space-y-4">
            {waterBodies.map((item) => (
              <article key={item.id} className="flex items-center justify-between gap-4 rounded-3xl border border-white/5 bg-ecobiome-surfaceAlt p-4 transition hover:border-ecobiome-accent/20">
                <div>
                  <p className="text-sm text-slate-400">{item.name}</p>
                  <p className="mt-2 text-lg font-semibold text-ecobiome-text">{item.category} · {item.volume}</p>
                </div>
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
                  item.status === 'Stable' ? 'bg-emerald-500/10 text-emerald-300' : item.status === 'Vigilance' ? 'bg-amber-500/10 text-amber-300' : 'bg-coral/10 text-coral'
                }`}>
                  {item.status}
                </span>
              </article>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
