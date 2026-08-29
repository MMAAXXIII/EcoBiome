import { useEffect, useState } from 'react';
import {
  ArrowRight,
  Atom,
  BookOpenCheck,
  Database,
  FlaskConical,
  Info,
  ShieldCheck,
} from 'lucide-react';

interface HumanProcess {
  key: string;
  title: string;
  model_view: {
    source: { label: string; before: string; after: string; unit: string };
    target: { label: string; before: string; after: string; unit: string };
  };
  explicit_extent: {
    value: string;
    unit: string;
    is_scenario_input: boolean;
  };
  explanation: {
    what_happens: string;
    scientific_basis: string;
    scenario_boundary: string;
  };
  technical_provenance: {
    evaluation_id: string;
    assertion_id: string;
    assertion_sha256: string;
    bridge_id: string;
    bridge_sha256: string;
    selection_id: string;
    selection_sha256: string;
    receipt_id: string;
    support_sha256: string;
  };
}

interface HumanExplanation {
  canonical_sha256: string;
  schema_version: string;
  title: string;
  introduction: string;
  abstraction_note: string;
  model_limit: string;
  processes: HumanProcess[];
}

interface NitrogenDemoResponse {
  status: string;
  artifact_sha256: string;
  scientific_foundation_sha256: string;
  non_predictive: boolean;
  human_explanation: HumanExplanation;
  technical_explanation: string;
}

export function NitrogenView() {
  const [data, setData] = useState<NitrogenDemoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    void fetch('/api/nitrogen-demo', {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    })
      .then(async (response) => {
        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new Error(payload.error ?? `EcoBiome API ${response.status}`);
        }
        return response.json() as Promise<NitrogenDemoResponse>;
      })
      .then((payload) => {
        if (active) setData(payload);
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : String(reason));
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        <div className="skeleton h-28" />
        <div className="skeleton h-72" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6">
        <div className="surface p-6 border border-coral-500/30">
          <p className="text-coral-400 font-medium">Démonstration indisponible</p>
          <p className="text-sm text-slate-400 mt-2">
            {error ?? 'Aucune donnée reçue.'}
          </p>
          <p className="text-xs text-slate-500 mt-3">
            Cette vue échoue volontairement si la Scientific Foundation V6 exacte
            n'est pas disponible.
          </p>
        </div>
      </div>
    );
  }

  const explanation = data.human_explanation;

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="surface p-6">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Atom className="w-5 h-5 text-teal-400" />
              <h2 className="font-display font-bold text-white text-2xl">
                {explanation.title}
              </h2>
            </div>
            <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">
              {explanation.introduction}
            </p>
          </div>
          <div className="shrink-0 rounded-xl border border-amber-500/25 bg-amber-500/10 px-4 py-3">
            <p className="text-xs uppercase tracking-wider text-amber-400 font-semibold">
              Démonstration, pas prévision
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Les extents sont des entrées de scénario, pas le résultat d'une cinétique.
            </p>
          </div>
        </div>
      </div>

      <section>
        <h3 className="section-title mb-3">Deux mécanismes, deux vues de modèle</h3>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {explanation.processes.map((process) => (
            <div key={process.key} className="surface p-5 space-y-4">
              <div className="flex items-center gap-2">
                <FlaskConical className="w-4 h-4 text-teal-400" />
                <h4 className="text-sm font-semibold text-white">{process.title}</h4>
                <span className="ml-auto text-sm font-display font-bold text-teal-400">
                  {process.explicit_extent.value} {process.explicit_extent.unit}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] items-center gap-3">
                <div className="rounded-xl bg-night-800/70 p-3">
                  <p className="text-xs uppercase tracking-wider text-slate-500">
                    {process.model_view.source.label}
                  </p>
                  <p className="mt-2 text-lg font-display font-bold text-slate-200">
                    {process.model_view.source.before}
                    <span className="mx-2 text-slate-600">→</span>
                    <span className="text-teal-400">{process.model_view.source.after}</span>
                    <span className="ml-1 text-xs font-normal text-slate-500">
                      {process.model_view.source.unit}
                    </span>
                  </p>
                </div>
                <ArrowRight className="hidden md:block w-4 h-4 text-slate-600" />
                <div className="rounded-xl bg-teal-500/10 p-3">
                  <p className="text-xs uppercase tracking-wider text-teal-500/80">
                    {process.model_view.target.label}
                  </p>
                  <p className="mt-2 text-lg font-display font-bold text-slate-200">
                    {process.model_view.target.before}
                    <span className="mx-2 text-slate-600">→</span>
                    <span className="text-teal-400">{process.model_view.target.after}</span>
                    <span className="ml-1 text-xs font-normal text-slate-500">
                      {process.model_view.target.unit}
                    </span>
                  </p>
                </div>
              </div>

              <p className="text-sm text-slate-300 leading-relaxed">
                {process.explanation.what_happens}
              </p>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <ShieldCheck className="w-4 h-4 text-teal-400 shrink-0" />
                Support scientifique revu · décision humaine tracée
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 rounded-xl border border-sky-500/20 bg-sky-500/10 p-4 flex gap-3">
          <Info className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-sky-300">
              Comment lire ces catégories
            </p>
            <p className="text-sm text-slate-400 mt-1 leading-relaxed">
              {explanation.abstraction_note}
            </p>
          </div>
        </div>
      </section>

      <section>
        <h3 className="section-title mb-3 flex items-center gap-2">
          <BookOpenCheck className="w-4 h-4 text-teal-400" />
          Pourquoi ?
        </h3>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {explanation.processes.map((process) => (
            <article key={process.key} className="surface p-5 space-y-4">
              <h4 className="font-display font-semibold text-white">
                {process.title}
              </h4>
              <div>
                <p className="text-xs uppercase tracking-wider text-teal-400 font-medium">
                  Base scientifique
                </p>
                <p className="text-sm text-slate-300 leading-relaxed mt-1.5">
                  {process.explanation.scientific_basis}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-amber-400 font-medium">
                  Limite du scénario
                </p>
                <p className="text-sm text-slate-400 leading-relaxed mt-1.5">
                  {process.explanation.scenario_boundary}
                </p>
              </div>
            </article>
          ))}
        </div>

        <div className="surface p-5 mt-4 border border-amber-500/15">
          <p className="text-sm font-medium text-white">Ce qu'EcoBiome ne calcule pas encore</p>
          <p className="text-sm text-slate-400 mt-2 leading-relaxed">
            {explanation.model_limit}
          </p>
        </div>
      </section>

      <details className="surface p-5">
        <summary className="cursor-pointer text-sm font-medium text-slate-300">
          Provenance et limites techniques
        </summary>
        <div className="mt-4 space-y-4 text-xs text-slate-400">
          <p className="flex items-start gap-2">
            <Database className="w-4 h-4 text-teal-400 shrink-0" />
            Scientific Foundation V6 : <code>{data.scientific_foundation_sha256}</code>
          </p>
          <p>
            Artefact vertical : <code>{data.artifact_sha256}</code>
          </p>
          <p>
            Projection humaine : <code>{explanation.canonical_sha256}</code>
          </p>
          {explanation.processes.map((process) => (
            <div key={process.key} className="rounded-lg bg-night-900/50 p-3 space-y-1">
              <p className="text-slate-300 font-medium">{process.title}</p>
              <p>assertion : <code>{process.technical_provenance.assertion_id}</code></p>
              <p>bridge : <code>{process.technical_provenance.bridge_id}</code></p>
              <p>selection : <code>{process.technical_provenance.selection_id}</code></p>
              <p>receipt : <code>{process.technical_provenance.receipt_id}</code></p>
            </div>
          ))}
          <details className="rounded-lg border border-slate-700/50 p-3">
            <summary className="cursor-pointer text-slate-400">
              Trace technique brute
            </summary>
            <pre className="mt-3 whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-slate-500">
              {data.technical_explanation}
            </pre>
          </details>
        </div>
      </details>
    </div>
  );
}
