import { useState, useMemo } from 'react';
import { useJournal } from '@/lib/hooks';
import { JOURNAL_SOURCE_LABELS, type JournalEntry } from '@/lib/types';
import { BookOpen, Youtube, FileText, PenLine, ChevronRight, Tag, ArrowLeft, Calendar } from 'lucide-react';

const SOURCE_ICONS = {
  youtube_transcript: Youtube,
  manual: PenLine,
  literature: FileText,
};

export function JournalView() {
  const { data: entries, loading } = useJournal();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filterTag, setFilterTag] = useState<string | null>(null);

  const allTags = useMemo(() => {
    const tags = new Set<string>();
    entries.forEach((e) => e.tags.forEach((t) => tags.add(t)));
    return Array.from(tags).sort();
  }, [entries]);

  const filtered = useMemo(() => {
    if (!filterTag) return entries;
    return entries.filter((e) => e.tags.includes(filterTag));
  }, [entries, filterTag]);

  const selected = useMemo(() => entries.find((e) => e.id === selectedId) ?? null, [entries, selectedId]);

  if (loading) {
    return <div className="p-6 space-y-4"><div className="skeleton h-96" /></div>;
  }

  if (selected) {
    return <JournalDetail entry={selected} onBack={() => setSelectedId(null)} />;
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <p className="text-sm text-slate-400">{entries.length} entrées de connaissance scientifique tracées</p>

      {/* Tag filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <button
          onClick={() => setFilterTag(null)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${!filterTag ? 'bg-teal-500/15 text-teal-300 border border-teal-500/20' : 'bg-night-850/40 text-slate-400 border border-transparent hover:text-white'}`}
        >
          Tous
        </button>
        {allTags.map((tag) => (
          <button
            key={tag}
            onClick={() => setFilterTag(tag)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${filterTag === tag ? 'bg-teal-500/15 text-teal-300 border border-teal-500/20' : 'bg-night-850/40 text-slate-400 border border-transparent hover:text-white'}`}
          >
            {tag}
          </button>
        ))}
      </div>

      {/* Entries grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((entry) => {
          const SourceIcon = SOURCE_ICONS[entry.source] ?? BookOpen;
          return (
            <button
              key={entry.id}
              onClick={() => setSelectedId(entry.id)}
              className="surface surface-hover p-5 text-left group"
            >
              <div className="flex items-start gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-night-800 flex items-center justify-center shrink-0">
                  <SourceIcon className="w-5 h-5 text-teal-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-display font-semibold text-white text-base leading-tight group-hover:text-teal-300 transition-colors">{entry.title}</h3>
                  <p className="text-xs text-slate-500 mt-1">{JOURNAL_SOURCE_LABELS[entry.source]}</p>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-teal-400 transition-colors" />
              </div>
              <p className="text-sm text-slate-400 line-clamp-2 leading-relaxed">{entry.summary}</p>
              <div className="flex items-center gap-2 mt-3 flex-wrap">
                {entry.tags.slice(0, 4).map((tag) => (
                  <span key={tag} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-night-800 text-xs text-slate-400">
                    <Tag className="w-2.5 h-2.5" /> {tag}
                  </span>
                ))}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function JournalDetail({ entry, onBack }: { entry: JournalEntry; onBack: () => void }) {
  const SourceIcon = SOURCE_ICONS[entry.source] ?? BookOpen;
  return (
    <div className="p-6 space-y-6 animate-fade-in max-w-4xl">
      <button onClick={onBack} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors">
        <ArrowLeft className="w-4 h-4" /> Retour au journal
      </button>

      <div className="surface p-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-xl bg-teal-500/15 flex items-center justify-center">
            <SourceIcon className="w-6 h-6 text-teal-400" />
          </div>
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider">{JOURNAL_SOURCE_LABELS[entry.source]}</p>
            <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
              <Calendar className="w-3 h-3" /> {new Date(entry.created_at).toLocaleDateString('fr-FR')}
            </p>
          </div>
        </div>

        <h1 className="font-display font-bold text-white text-2xl mb-4 text-balance">{entry.title}</h1>

        <div className="p-4 rounded-xl bg-teal-500/10 border border-teal-500/20 mb-6">
          <p className="text-sm text-teal-100 leading-relaxed">{entry.summary}</p>
        </div>

        <div className="prose prose-invert max-w-none">
          <p className="text-slate-300 leading-relaxed whitespace-pre-line">{entry.content}</p>
        </div>

        {entry.source_ref && (
          <div className="mt-6 pt-4 border-t border-night-700/40">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Source</p>
            <p className="text-sm text-teal-400 break-all">{entry.source_ref}</p>
          </div>
        )}

        <div className="mt-4 flex items-center gap-2 flex-wrap">
          {entry.tags.map((tag) => (
            <span key={tag} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-night-800 text-xs text-slate-400">
              <Tag className="w-3 h-3" /> {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
