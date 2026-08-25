import { useEffect, useMemo, useState } from 'react';
import { ArrowRight, Atom, CheckCircle2, Database, FlaskConical, ShieldCheck } from 'lucide-react';

interface QuantityPayload {
  material_component_id: string | null;
  value: { type: string; value: string };
  unit: string;
}

interface StateEnvelope {
  sha256: string;
  state: { quantities: QuantityPayload[] };
}

interface ProcessStep {
  ordinal: number;
  source_component_id: string;
  target_component_id: string;
  explicit_extent: {
    value: string;
    unit: string;
    basis_kind: string;
    is_explicit_input: boolean;
  };
}

interface NitrogenDemoResponse {
  status: string;
  artifact_sha256: string;
  scientific_foundation_sha256: string;
  non_predictive: boolean;
  explanation: string;
  artifact: {
    starting_state: StateEnvelope;
    ending_state: StateEnvelope;
    process_steps: ProcessStep[];
  };
}

const LABELS: Record<string, string> = {
  reduced_inorganic_nitrogen: 'Azote inorganique réduit',
  oxidized_inorganic_nitrogen: 'Azote inorganique oxydé',
  dissolved_inorganic_nitrogen: 'Azote inorganique dissous',
  biological_nitrogen: 'Azote biologique',
};

function byComponent(state: StateEnvelope): Record<string, QuantityPayload> {
  return Object.fromEntries(
    state.state.quantities
      .filter((item) => item.material_component_id)
      .map((item) => [item.material_component_id as string, item]),
  );
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
    return () => { active = false; };
  }, []);

  const initial = useMemo(() => (data ? byComponent(data.artifact.starting_state) : {}), [data]);
  const final = useMemo(() => (data ? byComponent(data.artifact.ending_state) : {}), [data]);

  if (loading) {
    return <div className="p-6 space-y-4"><div className="skeleton h-28" /><div className="skeleton h-72" /></div>;
  }

  if (error || !data) {
    return (
      <div className="p-6">
        <div className="surface p-6 border border-coral-500/30">
          <p className="text-coral-400 font-medium">Démonstration indisponible</p>
          <p className="text-sm text-slate-400 mt-2">{error ?? 'Aucune donnée reçue.'}</p>
          <p className="text-xs text-slate-500 mt-3">
            Cette vue échoue volontairement si la Scientific Foundation V6 exacte n'est pas disponible.
          </p>
        </div>
      </div>
    );
  }

  const componentOrder = [
    'reduced_inorganic_nitrogen',
    'oxidized_inorganic_nitrogen',
    'dissolved_inorganic_nitrogen',
    'biological_nitrogen',
  ];

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="surface p-6">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Atom className="w-5 h-5 text-teal-400" />
              <h2 className="font-display font-bold text-white text-2xl">
                Pourquoi l'azote se transforme-t-il ?
              </h2>
            </div>
            <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">
              Première verticale scientifique d'EcoBiome : deux transformations sont rejouées
              avec conservation de masse, support scientifique revu et provenance humaine.
            </p>
          </div>
          <div className="shrink-0 rounded-xl border border-amber-500/25 bg-amber-500/10 px-4 py-3">
            <p className="text-xs uppercase tracking-wider text-amber-400 font-semibold">
              Démonstration, pas prévision
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Les deux extents de 1 mg N sont des entrées explicites.
            </p>
          </div>
        </div>
      </div>

      <section>
        <h3 className="section-title mb-3">Avant → après</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          {componentOrder.map((component) => {
            const before = initial[component];
            const after = final[component];
            return (
              <div key={component} className="surface p-4">
                <p className="text-xs uppercase tracking-wider text-slate-500">
                  {LABELS[component] ?? component}
                </p>
                <div className="flex items-center gap-2 mt-3">
                  <span className="text-xl font-display font-bold text-slate-300">
                    {before?.value.value ?? '—'}
                  </span>
                  <ArrowRight className="w-4 h-4 text-slate-600" />
                  <span className="text-xl font-display font-bold text-teal-400">
                    {after?.value.value ?? '—'}
                  </span>
                  <span className="text-xs text-slate-500">{after?.unit ?? 'mg N'}</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section>
        <h3 className="section-title mb-3">Transformations démontrées</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {data.artifact.process_steps.map((step) => (
            <div key={step.ordinal} className="surface p-5">
              <div className="flex items-center gap-2 mb-4">
                <FlaskConical className="w-4 h-4 text-teal-400" />
                <span className="text-sm font-medium text-white">Étape {step.ordinal}</span>
                <span className="ml-auto text-sm font-display font-bold text-teal-400">
                  {step.explicit_extent.value} {step.explicit_extent.unit}
                </span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span className="rounded-lg bg-night-800 px-2.5 py-1.5 text-slate-300">
                  {LABELS[step.source_component_id] ?? step.source_component_id}
                </span>
                <ArrowRight className="w-4 h-4 text-slate-600 shrink-0" />
                <span className="rounded-lg bg-teal-500/10 px-2.5 py-1.5 text-teal-300">
                  {LABELS[step.target_component_id] ?? step.target_component_id}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-4 text-xs text-slate-400">
                <ShieldCheck className="w-4 h-4 text-teal-400" />
                Support scientifique revu · décision humaine tracée
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="surface p-5">
        <div className="flex items-center gap-2 mb-3">
          <CheckCircle2 className="w-5 h-5 text-teal-400" />
          <h3 className="font-display font-semibold text-white">Pourquoi ?</h3>
        </div>
        <pre className="whitespace-pre-wrap font-sans text-sm text-slate-300 leading-relaxed">
          {data.explanation}
        </pre>
      </section>

      <details className="surface p-5">
        <summary className="cursor-pointer text-sm font-medium text-slate-300">
          Provenance et limites techniques
        </summary>
        <div className="mt-4 space-y-3 text-xs text-slate-400">
          <p className="flex items-start gap-2">
            <Database className="w-4 h-4 text-teal-400 shrink-0" />
            Scientific Foundation V6 : <code>{data.scientific_foundation_sha256}</code>
          </p>
          <p>Artefact reproductible : <code>{data.artifact_sha256}</code></p>
          <p>RateModel : absent · dt : absent · forecast : false · extent : explicit input.</p>
        </div>
      </details>
    </div>
  );
}
