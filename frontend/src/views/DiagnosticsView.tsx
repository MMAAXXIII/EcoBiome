import { ArrowRight, Activity, CircleDot } from 'lucide-react';
import { diagnostics } from '../lib/data';

export function DiagnosticsView() {
  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/5 bg-white/5 p-6 shadow-panel">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-ecobiome-accent/75">Diagnostics</p>
            <h3 className="mt-2 text-3xl font-semibold text-ecobiome-text">Sessions de diagnostic</h3>
          </div>
          <button className="inline-flex items-center gap-2 rounded-2xl bg-ecobiome-accent/10 px-4 py-2 text-sm font-semibold text-ecobiome-accent transition hover:bg-ecobiome-accent/20">
            Nouveau diagnostic
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-8 grid gap-4">
          {diagnostics.map((item) => (
            <article key={item.name} className="rounded-3xl border border-white/5 bg-ecobiome-surfaceAlt p-6 shadow-panel transition hover:border-ecobiome-accent/20">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-slate-400">{item.name}</p>
                  <h4 className="mt-2 text-xl font-semibold text-ecobiome-text">{item.summary}</h4>
                </div>
                <div className="text-right">
                  <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Confiance</p>
                  <p className="mt-2 text-2xl font-semibold text-ecobiome-accent">{item.confidence}</p>
                </div>
              </div>
              <div className="mt-6 flex items-center justify-between gap-4 text-sm text-slate-400">
                <div className="inline-flex items-center gap-2 rounded-3xl bg-ecobiome-background/70 px-4 py-2">
                  <Activity className="h-4 w-4 text-ecobiome-accent" />
                  Analyse causale
                </div>
                <span className="inline-flex items-center gap-2 rounded-3xl bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.24em] text-slate-400">
                  <CircleDot className="h-3.5 w-3.5" />
                  {item.date}
                </span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl border border-white/5 bg-white/5 p-6 shadow-panel">
          <h4 className="text-xl font-semibold text-ecobiome-text">Chaînes causales</h4>
          <p className="mt-4 text-sm leading-6 text-slate-300">
            Visualisez les causes racines et les séquences de décisions pour comprendre l’évolution de chaque milieu.
          </p>
          <div className="mt-6 space-y-4">
            <div className="rounded-3xl bg-ecobiome-background/80 p-4 text-sm text-slate-300">
              <p className="font-semibold text-ecobiome-text">Pic de nitrites → Bactéries insuffisantes → Charge organique</p>
              <p className="mt-2">Suggérer une stabilisation de filtration et un apport progressif de bactéries nitrifiantes.</p>
            </div>
            <div className="rounded-3xl bg-ecobiome-background/80 p-4 text-sm text-slate-300">
              <p className="font-semibold text-ecobiome-text">pH bas → Oxygène dissous réduit → Stress des poissons</p>
              <p className="mt-2">Vérifiez la circulation, ajustez l’aération et évitez les chocs chimiques.</p>
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-white/5 bg-white/5 p-6 shadow-panel">
          <div className="flex items-center gap-3 text-slate-300">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-3xl bg-ecobiome-accent/10 text-ecobiome-accent">
              <Zap className="h-5 w-5" />
            </span>
            <div>
              <p className="text-sm uppercase tracking-[0.24em] text-ecobiome-accent/75">Action rapide</p>
              <h4 className="mt-2 text-xl font-semibold text-ecobiome-text">Prochaines interventions</h4>
            </div>
          </div>
          <ul className="mt-6 space-y-3 text-sm text-slate-300">
            <li className="rounded-3xl bg-ecobiome-background/80 p-4">Aérer le Système Aquaponique Nord dans les 2 heures.</li>
            <li className="rounded-3xl bg-ecobiome-background/80 p-4">Préparer un ajout de bactéries nitrifiantes pour le récif.</li>
            <li className="rounded-3xl bg-ecobiome-background/80 p-4">Surveiller le pH du bassin japonais pendant 24h.</li>
          </ul>
        </div>
      </section>
    </div>
  );
}
