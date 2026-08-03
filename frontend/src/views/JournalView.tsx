import { BookOpen, Tag } from 'lucide-react';
import { journalEntries } from '../lib/data';

export function JournalView() {
  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/5 bg-white/5 p-6 shadow-panel">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-ecobiome-accent/75">Journal scientifique</p>
            <h3 className="mt-2 text-3xl font-semibold text-ecobiome-text">Notes, sources et références</h3>
          </div>
          <button className="inline-flex items-center gap-2 rounded-2xl bg-ecobiome-accent/10 px-4 py-2 text-sm font-semibold text-ecobiome-accent transition hover:bg-ecobiome-accent/20">
            Ajouter une entrée
          </button>
        </div>

        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          {journalEntries.map((entry) => (
            <article key={entry.title} className="rounded-3xl border border-white/5 bg-ecobiome-surfaceAlt p-6 shadow-panel transition hover:border-ecobiome-accent/20">
              <div className="flex items-center gap-3 text-ecobiome-accent">
                <BookOpen className="h-5 w-5" />
                <p className="text-sm uppercase tracking-[0.24em]">{entry.source}</p>
              </div>
              <h4 className="mt-4 text-xl font-semibold text-ecobiome-text">{entry.title}</h4>
              <p className="mt-3 text-sm leading-6 text-slate-300">{entry.summary}</p>
              <div className="mt-5 flex flex-wrap gap-2 text-xs text-slate-400">
                {entry.tags.map((tag) => (
                  <span key={tag} className="rounded-full bg-ecobiome-background/80 px-3 py-1">{tag}</span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
