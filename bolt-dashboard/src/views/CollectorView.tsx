import { useCallback, useEffect, useState, type FormEvent } from 'react';
import {
  acquireCollectorSource,
  getCollectorPending,
  getCollectorStatus,
  proposeCollectorClaims,
  reviewCollectorItem,
  type CollectorAcquireResult,
  type CollectorPendingItem,
  type CollectorStatus,
} from '@/lib/api';
import {
  Check,
  DatabaseZap,
  FileSearch,
  Loader2,
  RefreshCw,
  X,
} from 'lucide-react';

function statusValue(
  status: CollectorStatus | null,
  key: string,
): string {
  if (!status || !(key in status)) {
    return '—';
  }
  return String(status[key]);
}

export function CollectorView() {
  const [status, setStatus] = useState<CollectorStatus | null>(null);
  const [pending, setPending] = useState<CollectorPendingItem[]>([]);
  const [source, setSource] = useState('');
  const [languages, setLanguages] = useState('fr,en');
  const [acquiring, setAcquiring] = useState(false);
  const [loadingPending, setLoadingPending] = useState(false);
  const [lastRun, setLastRun] =
    useState<CollectorAcquireResult | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    setLoadingPending(true);
    try {
      const [nextStatus, nextPending] = await Promise.all([
        getCollectorStatus(),
        getCollectorPending(),
      ]);
      setStatus(nextStatus);
      setPending(nextPending);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoadingPending(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleAcquire = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    if (!source.trim()) {
      return;
    }

    setAcquiring(true);
    setError(null);
    setMessage(null);
    try {
      const preferredLanguages = languages
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);
      const result = await acquireCollectorSource({
        source: source.trim(),
        languages: preferredLanguages,
      });
      setLastRun(result);
      setMessage(
        `Acquisition terminée : ${result.source.title || result.source.canonical_locator}`,
      );
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setAcquiring(false);
    }
  };

  const handleProposeClaims = async (representationId: string) => {
    setError(null);
    setMessage(null);
    try {
      const result = await proposeCollectorClaims(representationId);
      setMessage(
        `${result.claim_count} claim(s) proposé(s) pour review humaine.`,
      );
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleReview = async (
    item: CollectorPendingItem,
    decision: 'accept' | 'reject',
  ) => {
    setError(null);
    setMessage(null);
    try {
      await reviewCollectorItem({
        target_type: item.target_type,
        target_id: item.target_id,
        decision,
      });
      setMessage(
        `${item.target_type} ${decision === 'accept' ? 'accepté' : 'rejeté'}.`,
      );
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <DatabaseZap className="w-5 h-5 text-teal-400" />
            <h1 className="font-display font-bold text-white text-2xl">
              Collector
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-2 max-w-3xl">
            Acquisition locale et traçable de sources scientifiques. Une
            source acquise n'est jamais automatiquement promue en vérité
            scientifique : les passages et claims restent soumis à review.
          </p>
        </div>
        <button
          onClick={() => void refresh()}
          className="surface surface-hover px-3 py-2 text-sm text-slate-300 flex items-center gap-2"
          disabled={loadingPending}
        >
          <RefreshCw
            className={`w-4 h-4 ${loadingPending ? 'animate-spin' : ''}`}
          />
          Actualiser
        </button>
      </div>

      {error && (
        <div className="surface border border-coral-500/40 p-4 text-sm text-coral-300">
          {error}
        </div>
      )}
      {message && (
        <div className="surface border border-teal-500/40 p-4 text-sm text-teal-300">
          {message}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        <div className="xl:col-span-2 surface p-5">
          <h2 className="section-title mb-4 flex items-center gap-2">
            <FileSearch className="w-4 h-4 text-teal-400" />
            Ajouter une source
          </h2>
          <form onSubmit={handleAcquire} className="space-y-4">
            <div>
              <label className="text-xs text-slate-400 block mb-1.5">
                URL, vidéo YouTube ou chemin de fichier local
              </label>
              <input
                value={source}
                onChange={(event) => setSource(event.target.value)}
                placeholder="https://... ou C:\...\document.pdf"
                className="w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white outline-none focus:border-teal-500/60"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1.5">
                Langues préférées des transcriptions
              </label>
              <input
                value={languages}
                onChange={(event) => setLanguages(event.target.value)}
                placeholder="fr,en"
                className="w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white outline-none focus:border-teal-500/60"
              />
            </div>
            <button
              type="submit"
              disabled={acquiring || !source.trim()}
              className="rounded-xl bg-teal-500 text-night-950 px-4 py-2.5 text-sm font-semibold disabled:opacity-50 flex items-center gap-2"
            >
              {acquiring ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <DatabaseZap className="w-4 h-4" />
              )}
              {acquiring ? 'Acquisition en cours…' : 'Analyser la source'}
            </button>
          </form>
        </div>

        <div className="surface p-5">
          <h2 className="section-title mb-4">État du Collector</h2>
          <dl className="space-y-3 text-sm">
            {[
              ['schema_version', 'Schéma'],
              ['sources', 'Sources'],
              ['representations', 'Représentations'],
              ['claims', 'Claims'],
              ['review_decisions', 'Décisions'],
              ['pending_segments', 'Segments à revoir'],
              ['pending_claims', 'Claims à revoir'],
            ].map(([key, label]) => (
              <div key={key} className="flex justify-between gap-3">
                <dt className="text-slate-500">{label}</dt>
                <dd className="font-mono text-slate-200">
                  {statusValue(status, key)}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>

      {lastRun && (
        <div className="surface p-5 space-y-4">
          <div>
            <h2 className="section-title">Dernière acquisition</h2>
            <p className="text-sm text-white mt-2">
              {lastRun.source.title || lastRun.source.canonical_locator}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {lastRun.source.source_type} · adapter {lastRun.adapter.name}{' '}
              {lastRun.adapter.version} · job {lastRun.job.status}
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {lastRun.representations.map((representation) => (
              <div
                key={representation.id}
                className="rounded-xl border border-night-700/50 bg-night-900/30 p-4"
              >
                <p className="text-sm text-white">
                  {representation.representation_kind}
                </p>
                <p className="text-xs text-slate-500 mt-1 break-all">
                  {representation.id}
                </p>
                <p className="text-xs text-slate-400 mt-2">
                  {representation.segment_count} segment(s) ·{' '}
                  {representation.language || 'langue inconnue'}
                  {representation.duplicate ? ' · doublon' : ''}
                </p>
                <button
                  onClick={() =>
                    void handleProposeClaims(representation.id)
                  }
                  className="mt-3 text-xs rounded-lg border border-teal-500/40 px-3 py-2 text-teal-300 hover:bg-teal-500/10"
                >
                  Proposer les claims
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="surface overflow-hidden">
        <div className="p-5 border-b border-night-700/40 flex items-center justify-between">
          <div>
            <h2 className="section-title">Review humaine en attente</h2>
            <p className="text-xs text-slate-500 mt-1">
              {pending.length} élément(s)
            </p>
          </div>
          {loadingPending && (
            <Loader2 className="w-4 h-4 text-slate-500 animate-spin" />
          )}
        </div>

        {pending.length === 0 ? (
          <div className="p-8 text-sm text-slate-500 text-center">
            Aucun élément en attente.
          </div>
        ) : (
          <div className="divide-y divide-night-700/40">
            {pending.map((item) => (
              <div key={`${item.target_type}:${item.target_id}`} className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-xs uppercase tracking-wider text-teal-400">
                      {item.target_type}
                      {item.passage_index
                        ? ` · passage ${item.passage_index}`
                        : ''}
                    </p>
                    <p className="text-sm text-slate-200 mt-2 whitespace-pre-wrap">
                      {item.text}
                    </p>
                    <p className="text-[11px] font-mono text-slate-600 mt-2 break-all">
                      {item.target_id}
                    </p>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <button
                      onClick={() => void handleReview(item, 'accept')}
                      className="rounded-lg border border-teal-500/40 p-2 text-teal-300 hover:bg-teal-500/10"
                      title="Accepter"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => void handleReview(item, 'reject')}
                      className="rounded-lg border border-coral-500/40 p-2 text-coral-300 hover:bg-coral-500/10"
                      title="Rejeter"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
