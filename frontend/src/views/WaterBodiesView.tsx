import { ArrowRight, Droplet, Layers, Zap } from 'lucide-react';
import { waterBodies } from '../lib/data';

export function WaterBodiesView() {
  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/5 bg-white/5 p-6 shadow-panel">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-ecobiome-accent/75">Milieux aquatiques</p>
            <h3 className="mt-2 text-3xl font-semibold text-ecobiome-text">Liste des écosystèmes</h3>
          </div>
          <button className="inline-flex items-center gap-2 rounded-2xl bg-ecobiome-accent/10 px-4 py-2 text-sm font-semibold text-ecobiome-accent transition hover:bg-ecobiome-accent/20">
            Ajouter un milieu
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
        <div className="mt-8 grid gap-4 lg:grid-cols-2">
          {waterBodies.map((item) => (
            <article key={item.id} className="rounded-3xl border border-white/5 bg-ecobiome-surfaceAlt p-6 shadow-panel transition hover:border-ecobiome-accent/20">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-slate-400">{item.category}</p>
                  <h4 className="mt-2 text-xl font-semibold text-ecobiome-text">{item.name}</h4>
                </div>
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
                  item.status === 'Stable' ? 'bg-emerald-500/10 text-emerald-300' : item.status === 'Vigilance' ? 'bg-amber-500/10 text-amber-300' : 'bg-coral/10 text-coral'
                }`}>
                  {item.status}
                </span>
              </div>
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <div className="rounded-3xl bg-ecobiome-background/70 p-4">
                  <p className="text-sm text-slate-400">Volume</p>
                  <p className="mt-2 text-lg font-semibold text-ecobiome-text">{item.volume}</p>
                </div>
                <div className="rounded-3xl bg-ecobiome-background/70 p-4">
                  <p className="text-sm text-slate-400">Remplissage</p>
                  <p className="mt-2 text-lg font-semibold text-ecobiome-text">{item.fill}%</p>
                </div>
              </div>
              <div className="mt-6 flex items-center justify-between gap-4 text-sm text-slate-300">
                <p>{item.summary}</p>
                <span className="inline-flex items-center gap-2 rounded-2xl bg-ecobiome-surface px-3 py-2 text-xs">Mis à jour {item.updated}</span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="rounded-3xl border border-white/5 bg-white/5 p-6 shadow-panel">
          <div className="flex items-center gap-3 text-slate-300">
            <Droplet className="h-5 w-5 text-ecobiome-accent" />
            <p className="text-sm uppercase tracking-[0.24em]">Paramètres hydriques</p>
          </div>
          <div className="mt-6 space-y-4 text-sm leading-7 text-slate-300">
            <p>Suivez l’équilibre entre les cycles de l’azote, l’oxygène dissous et la stabilité du pH.</p>
            <p>Chaque milieu affiche un état de santé, des seuils critiques et des suggestions de stabilisation.</p>
          </div>
        </div>

        <div className="rounded-3xl border border-white/5 bg-white/5 p-6 shadow-panel">
          <div className="flex items-center gap-3 text-slate-300">
            <Layers className="h-5 w-5 text-ecobiome-accent" />
            <p className="text-sm uppercase tracking-[0.24em]">Organismes et biocharge</p>
          </div>
          <div className="mt-6 grid gap-4">
            <div className="rounded-3xl bg-ecobiome-background/80 p-4">
              <p className="text-sm text-slate-400">Coraux, poissons, bactéries nitrifiantes</p>
              <p className="mt-2 text-lg font-semibold text-ecobiome-text">Biocharge active</p>
            </div>
            <div className="rounded-3xl bg-ecobiome-background/80 p-4">
              <p className="text-sm text-slate-400">Algues, microfaune, plantes</p>
              <p className="mt-2 text-lg font-semibold text-ecobiome-text">Équilibre progressif</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
