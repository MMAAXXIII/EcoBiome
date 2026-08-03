import { ImagePlus, Layers } from 'lucide-react';
import { mediaItems } from '../lib/data';

export function MediaView() {
  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/5 bg-white/5 p-6 shadow-panel">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-ecobiome-accent/75">Galerie média</p>
            <h3 className="mt-2 text-3xl font-semibold text-ecobiome-text">Bibliothèque visuelle</h3>
          </div>
          <button className="inline-flex items-center gap-2 rounded-2xl bg-ecobiome-accent/10 px-4 py-2 text-sm font-semibold text-ecobiome-accent transition hover:bg-ecobiome-accent/20">
            Ajouter un support
            <ImagePlus className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-8 grid gap-4 lg:grid-cols-2">
          {mediaItems.map((item) => (
            <article key={item.title} className="rounded-3xl border border-white/5 bg-ecobiome-surfaceAlt p-6 shadow-panel transition hover:border-ecobiome-accent/20">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-slate-400">{item.category}</p>
                  <h4 className="mt-2 text-xl font-semibold text-ecobiome-text">{item.title}</h4>
                </div>
                <span className="rounded-full bg-ecobiome-background/80 px-3 py-1 text-xs uppercase tracking-[0.24em] text-slate-400">{item.status}</span>
              </div>
              <div className="mt-5 rounded-3xl bg-[radial-gradient(circle_at_top,_rgba(110,224,106,0.1),_transparent_55%)] p-5 text-sm leading-6 text-slate-300">
                Aperçu de la ressource visuelle et notes de contexte sur le milieu associé.
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
