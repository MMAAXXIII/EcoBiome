import { useEffect, useMemo, useState } from 'react';
import {
  GLOSSARY_CATEGORY_LABELS,
  SCIENTIFIC_GLOSSARY,
  type GlossaryCategory,
} from '@/lib/scientificGlossary';
import { BookOpen, ChevronDown, ChevronRight, ExternalLink, Search } from 'lucide-react';

const CATEGORY_ORDER: GlossaryCategory[] = [
  'physique',
  'acidite',
  'azote',
  'mineraux',
  'gaz',
  'lumiere',
  'biologie',
];

export function ScientificGlossaryView({
  initialEntryId = null,
  onInitialEntryHandled,
}: {
  initialEntryId?: string | null;
  onInitialEntryHandled?: () => void;
}) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<GlossaryCategory | 'all'>('all');
  const [openId, setOpenId] = useState<string | null>('oxygen');

  useEffect(() => {
    if (!initialEntryId) {
      return;
    }
    setQuery('');
    setCategory('all');
    setOpenId(initialEntryId);
    const frame = window.requestAnimationFrame(() => {
      document.getElementById(`glossary-${initialEntryId}`)?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
      onInitialEntryHandled?.();
    });
    return () => window.cancelAnimationFrame(frame);
  }, [initialEntryId, onInitialEntryHandled]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase('fr-FR');
    return SCIENTIFIC_GLOSSARY.filter((entry) => {
      if (category !== 'all' && entry.category !== category) {
        return false;
      }
      if (!needle) {
        return true;
      }
      const haystack = [
        entry.term,
        entry.symbol,
        entry.unit,
        entry.definition,
        entry.utility,
        entry.chemistry,
        ...entry.influencedBy,
        ...entry.related,
      ].join(' ').toLocaleLowerCase('fr-FR');
      return haystack.includes(needle);
    });
  }, [category, query]);

  return (
    <div className="p-6 space-y-6 animate-fade-in max-w-6xl">
      <div>
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-teal-500/15 flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-teal-400" />
          </div>
          <div>
            <h1 className="font-display font-bold text-white text-2xl">
              Lexique scientifique EcoBiome
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Définitions, symboles, unités, utilité biologique, relations et formules employées dans l’application.
            </p>
          </div>
        </div>
      </div>

      <div className="surface p-4 border border-teal-500/20">
        <p className="text-sm text-slate-300 leading-relaxed">
          Les fiches distinguent le vocabulaire pédagogique de la définition scientifique exacte.
          Les équations affichent leurs hypothèses de validité ; elles ne créent pas de plage universelle
          « idéale » lorsque l’interprétation dépend des espèces ou du contexte.
        </p>
      </div>

      <div className="surface p-4 space-y-3">
        <label className="relative block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Rechercher : oxygène, NH₃, KH, nitrification, PAR…"
            className="w-full rounded-xl bg-night-900/70 border border-night-700 pl-9 pr-3 py-2.5 text-sm text-white outline-none focus:border-teal-500/60"
          />
        </label>

        <div className="flex gap-2 flex-wrap">
          <button
            type="button"
            onClick={() => setCategory('all')}
            className={`rounded-xl px-3 py-1.5 text-xs border ${
              category === 'all'
                ? 'bg-teal-500/15 border-teal-500/30 text-teal-300'
                : 'border-night-700 text-slate-400 hover:text-white'
            }`}
          >
            Tous
          </button>
          {CATEGORY_ORDER.map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setCategory(key)}
              className={`rounded-xl px-3 py-1.5 text-xs border ${
                category === key
                  ? 'bg-teal-500/15 border-teal-500/30 text-teal-300'
                  : 'border-night-700 text-slate-400 hover:text-white'
              }`}
            >
              {GLOSSARY_CATEGORY_LABELS[key]}
            </button>
          ))}
        </div>
      </div>

      <p className="text-xs text-slate-500">
        {filtered.length} terme(s) affiché(s)
      </p>

      <div className="space-y-3">
        {filtered.map((entry) => {
          const open = openId === entry.id;
          return (
            <article id={`glossary-${entry.id}`} key={entry.id} className="surface overflow-hidden scroll-mt-6">
              <button
                type="button"
                onClick={() => setOpenId(open ? null : entry.id)}
                className="w-full p-4 text-left flex items-start gap-3 hover:bg-night-800/30 transition-colors"
              >
                <div className="mt-0.5 text-slate-500">
                  {open ? (
                    <ChevronDown className="w-4 h-4" />
                  ) : (
                    <ChevronRight className="w-4 h-4" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                    <h2 className="font-display font-semibold text-white">
                      {entry.term}
                    </h2>
                    {entry.symbol !== '—' && (
                      <span className="font-mono text-teal-300 text-sm">
                        {entry.symbol}
                      </span>
                    )}
                    {entry.unit !== '—' && (
                      <span className="text-xs text-slate-500">
                        {entry.unit}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    {GLOSSARY_CATEGORY_LABELS[entry.category]}
                  </p>
                </div>
              </button>

              {open && (
                <div className="px-5 pb-5 space-y-5 border-t border-night-700/40">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-4">
                    <GlossaryText title="Définition" text={entry.definition} />
                    <GlossaryText title="À quoi ça sert ?" text={entry.utility} />
                    <GlossaryText title="Chimie / symbole" text={entry.chemistry} />
                    <div>
                      <p className="text-xs uppercase tracking-wider text-slate-500 mb-2">
                        Facteurs influents
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {entry.influencedBy.map((item) => (
                          <span
                            key={item}
                            className="rounded-lg bg-night-900/60 border border-night-700 px-2 py-1 text-xs text-slate-300"
                          >
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {entry.equations.length > 0 && (
                    <div className="space-y-3">
                      <p className="text-xs uppercase tracking-wider text-slate-500">
                        Relations et calculs
                      </p>
                      {entry.equations.map((equation) => (
                        <div
                          key={`${entry.id}-${equation.label}`}
                          className="rounded-xl bg-night-900/60 border border-night-700 p-4"
                        >
                          <p className="text-sm font-medium text-white">
                            {equation.label}
                          </p>
                          <p className="font-mono text-sm text-teal-300 mt-2 break-words">
                            {equation.formula}
                          </p>
                          <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                            {equation.applicability}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                  {entry.cautions.length > 0 && (
                    <div className="rounded-xl bg-amber-500/5 border border-amber-500/15 p-4">
                      <p className="text-xs uppercase tracking-wider text-amber-300 mb-2">
                        Points d’attention
                      </p>
                      <ul className="space-y-1.5">
                        {entry.cautions.map((item) => (
                          <li key={item} className="text-sm text-slate-300">
                            • {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {entry.related.length > 0 && (
                    <div>
                      <p className="text-xs uppercase tracking-wider text-slate-500 mb-2">
                        Relié à
                      </p>
                      <p className="text-sm text-slate-300">
                        {entry.related.join(' · ')}
                      </p>
                    </div>
                  )}

                  {entry.sources.length > 0 && (
                    <div className="pt-3 border-t border-night-700/40">
                      <p className="text-xs uppercase tracking-wider text-slate-500 mb-2">
                        Sources
                      </p>
                      <div className="flex flex-col gap-2">
                        {entry.sources.map((source) => (
                          <a
                            key={source.url}
                            href={source.url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1.5 text-sm text-teal-400 hover:text-teal-300 w-fit"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                            {source.label}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </article>
          );
        })}
      </div>
    </div>
  );
}

function GlossaryText({ title, text }: { title: string; text: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wider text-slate-500 mb-2">
        {title}
      </p>
      <p className="text-sm text-slate-300 leading-relaxed">
        {text}
      </p>
    </div>
  );
}
