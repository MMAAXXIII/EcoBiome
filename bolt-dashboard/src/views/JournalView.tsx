import { useMemo, useState } from 'react';
import { useJournal } from '@/lib/hooks';
import type { JournalEntry, JournalEventKind } from '@/lib/types';
import {
  ArrowLeft,
  Beaker,
  BookOpen,
  CalendarClock,
  ChevronRight,
  Droplets,
  FlaskConical,
  Wrench,
} from 'lucide-react';

type JournalFilter = 'all' | JournalEventKind;

function formatJournalDateTime(value: string) {
  return new Date(value).toLocaleString('fr-FR', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function EventIcon({ entry }: { entry: JournalEntry }) {
  if (entry.title === 'Changement d’eau') {
    return <Droplets className="w-5 h-5 text-sky-300" />;
  }
  if (entry.event_kind === 'intervention') {
    return <Wrench className="w-5 h-5 text-amber-300" />;
  }
  if (entry.title.startsWith('Mesure')) {
    return <FlaskConical className="w-5 h-5 text-teal-300" />;
  }
  return <Beaker className="w-5 h-5 text-teal-300" />;
}

export function JournalView() {
  const { data: entries, loading, error } = useJournal();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filter, setFilter] = useState<JournalFilter>('all');

  const filtered = useMemo(() => {
    if (filter === 'all') return entries;
    return entries.filter((entry) => entry.event_kind === filter);
  }, [entries, filter]);

  const selected = useMemo(
    () => entries.find((entry) => entry.id === selectedId) ?? null,
    [entries, selectedId],
  );

  if (loading) {
    return <div className="p-6 space-y-4"><div className="skeleton h-96" /></div>;
  }

  if (selected) {
    return <JournalDetail entry={selected} onBack={() => setSelectedId(null)} />;
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div>
        <h2 className="font-display font-semibold text-white text-lg">
          Chronologie du milieu
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          {entries.length} événements enregistrés dans le suivi scientifique.
        </p>
      </div>

      {error && (
        <div className="surface p-4 border border-coral-500/30 text-sm text-coral-200">
          Impossible de charger le journal : {error}
        </div>
      )}

      <div className="flex items-center gap-2 flex-wrap">
        {([
          ['all', 'Tous'],
          ['observation', 'Mesures et observations'],
          ['intervention', 'Interventions'],
        ] as const).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filter === key
                ? 'bg-teal-500/15 text-teal-300 border border-teal-500/20'
                : 'bg-night-850/40 text-slate-400 border border-transparent hover:text-white'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="surface p-8 text-center">
          <BookOpen className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <p className="text-sm text-slate-400">Aucune entrée dans cette catégorie.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((entry) => (
            <button
              key={entry.id}
              onClick={() => setSelectedId(entry.id)}
              className="surface surface-hover p-5 text-left group w-full"
            >
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-night-800 flex items-center justify-center shrink-0">
                  <EventIcon entry={entry} />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-display font-semibold text-white text-base leading-tight group-hover:text-teal-300 transition-colors">
                    {entry.title} — {formatJournalDateTime(entry.created_at)}
                  </h3>
                  <p className="text-xs text-slate-500 mt-1">
                    {entry.water_body_name}
                  </p>
                  <p className="text-sm text-slate-300 mt-2 leading-relaxed">
                    {entry.summary}
                  </p>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-teal-400 transition-colors mt-1" />
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function JournalDetail({
  entry,
  onBack,
}: {
  entry: JournalEntry;
  onBack: () => void;
}) {
  return (
    <div className="p-6 space-y-6 animate-fade-in max-w-4xl">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Retour au journal
      </button>

      <article className="surface p-8">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-12 h-12 rounded-xl bg-teal-500/15 flex items-center justify-center">
            <EventIcon entry={entry} />
          </div>
          <div>
            <p className="text-sm font-medium text-white">{entry.water_body_name}</p>
            <p className="text-xs text-slate-500 flex items-center gap-1 mt-1">
              <CalendarClock className="w-3.5 h-3.5" />
              {formatJournalDateTime(entry.created_at)}
            </p>
          </div>
        </div>

        <h1 className="font-display font-bold text-white text-2xl mb-5 text-balance">
          {entry.title} — {formatJournalDateTime(entry.created_at)}
        </h1>

        <div className="p-4 rounded-xl bg-teal-500/10 border border-teal-500/20 mb-7">
          <p className="text-sm text-teal-100 leading-relaxed">{entry.summary}</p>
        </div>

        <div className="prose prose-invert max-w-none">
          <p className="text-slate-300 leading-7 whitespace-pre-line text-[15px]">
            {entry.content}
          </p>
        </div>

        <details className="mt-8 border-t border-night-700/40 pt-5 group">
          <summary className="cursor-pointer select-none text-sm font-medium text-slate-400 hover:text-white transition-colors">
            Détails techniques et traçabilité
          </summary>
          <p className="text-xs text-slate-500 mt-3 leading-relaxed">
            Ces informations sont conservées pour l’audit et la reproductibilité.
            Elles ne sont pas nécessaires pour comprendre l’événement au quotidien.
          </p>
          <pre className="mt-3 p-4 rounded-xl bg-night-950/70 border border-night-700/40 overflow-x-auto text-xs text-slate-400 leading-relaxed whitespace-pre-wrap break-words">
            {entry.technical_content}
          </pre>
        </details>
      </article>
    </div>
  );
}
