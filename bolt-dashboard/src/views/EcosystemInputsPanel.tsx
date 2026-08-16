import { useEffect, useState, type FormEvent, type ReactNode } from 'react';
import {
  addFeedProduct,
  addLivestock,
  addPlant,
  addSubstrateLayer,
  addWaterSource,
  adjustLivestock,
  deleteLivestock,
  deletePlant,
  deleteSubstrateLayer,
  deleteWaterSource,
  importFeedProduct,
  recordEcosystemOperation,
  recordFeeding,
  recordTopUp,
  setLivestockSexDistribution,
} from '@/lib/api';
import { useEcology, useGuidance } from '@/lib/hooks';
import type { EcologyOperation, ExperienceLevel, FeedProduct, GuidanceSnapshot, LivestockItem, WaterBody, WaterSourceType } from '@/lib/types';
import {
  AlertTriangle,
  Beef,
  CheckCircle2,
  Droplets,
  Fish,
  Leaf,
  Plus,
  RefreshCw,
  Shovel,
  Trash2,
  Wrench,
} from 'lucide-react';

interface Props {
  waterBody: WaterBody;
  experienceLevel: ExperienceLevel;
  onWaterBodyChanged: () => Promise<void>;
}

type Section = 'life' | 'water' | 'operations';
type OperationType =
  | 'filter_maintenance'
  | 'power_outage'
  | 'additive'
  | 'fertilization'
  | 'bacteria_addition'
  | 'co2_change'
  | 'water_treatment'
  | 'siphoning'
  | 'plant_pruning'
  | 'substrate_maintenance'
  | 'medication'
  | 'other';

const inputClass = 'mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white outline-none focus:border-teal-500/60';
const labelClass = 'text-xs text-slate-400';

function numberOrNull(value: string): number | null {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function EcosystemInputsPanel({ waterBody, experienceLevel, onWaterBodyChanged }: Props) {
  const { data, loading, error, refetch } = useEcology(waterBody.id);
  const {
    data: guidance,
    loading: guidanceLoading,
    error: guidanceError,
    refetch: refetchGuidance,
  } = useGuidance(waterBody.id, experienceLevel);
  const [section, setSection] = useState<Section>('life');
  const [actionError, setActionError] = useState<string | null>(null);
  const ammoniaIndicator = data.derived_indicators.un_ionized_ammonia;
  const estimatedNh3 = (
    typeof ammoniaIndicator === 'object'
    && ammoniaIndicator !== null
    && 'nh3_n_mg_l' in ammoniaIndicator
    && typeof ammoniaIndicator.nh3_n_mg_l === 'number'
  ) ? ammoniaIndicator.nh3_n_mg_l : null;

  const run = async (action: () => Promise<unknown>, waterChanged = false) => {
    setActionError(null);
    try {
      await action();
      await refetch();
      await refetchGuidance();
      if (waterChanged) await onWaterBodyChanged();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
      throw err;
    }
  };

  if (loading) return <div className="skeleton h-96" />;

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
        <Kpi label="Biomasse animale connue" value={`${data.known_livestock_biomass_g.toFixed(1)} g`} />
        <Kpi label="Populations suivies" value={`${data.livestock.length + data.plants.length}`} />
        <Kpi label="Événements de nourrissage" value={`${data.feeding_event_count}`} />
        <Kpi
          label="NH₃-N non ionisé estimé"
          value={estimatedNh3 === null ? 'Données insuffisantes' : `${estimatedNh3.toFixed(4)} mg N/L`}
        />
      </div>
      {estimatedNh3 !== null && (
        <p className="text-xs text-slate-500">
          Estimation calculée depuis TAN + pH + température avec l’approximation d’équilibre d’Emerson (eau douce / salinité nulle).
        </p>
      )}

      <GuidancePanel data={guidance} loading={guidanceLoading} error={guidanceError} />

      <div className="flex gap-2 flex-wrap">
        <Tab active={section === 'life'} onClick={() => setSection('life')}>Vie & nourrissage</Tab>
        <Tab active={section === 'water'} onClick={() => setSection('water')}>Eau & substrat</Tab>
        <Tab active={section === 'operations'} onClick={() => setSection('operations')}>Interventions</Tab>
      </div>

      {(error || actionError) && (
        <div className="surface border border-coral-500/40 p-4 text-sm text-coral-300">
          {actionError ?? error}
        </div>
      )}

      {section === 'life' && (
        <LifeSection
          waterBodyId={waterBody.id}
          livestock={data.livestock}
          plants={data.plants}
          feedProducts={data.feed_products}
          operations={data.recent_operations}
          experienceLevel={experienceLevel}
          run={run}
        />
      )}
      {section === 'water' && (
        <WaterSection
          waterBody={waterBody}
          waterSources={data.water_sources}
          substrateLayers={data.substrate_layers}
          experienceLevel={experienceLevel}
          run={run}
        />
      )}
      {section === 'operations' && (
        <OperationsSection
          waterBodyId={waterBody.id}
          operations={data.recent_operations}
          experienceLevel={experienceLevel}
          run={run}
        />
      )}
    </div>
  );
}

function GuidancePanel({ data, loading, error }: {
  data: GuidanceSnapshot | null;
  loading: boolean;
  error: string | null;
}) {
  if (loading) {
    return <div className="skeleton h-40" />;
  }
  if (error) {
    return <div className="surface border border-coral-500/30 p-4 text-sm text-coral-300">Impossible de calculer les priorités de saisie : {error}</div>;
  }
  if (!data) return null;
  const remaining = Math.max(0, data.required_count - data.known_required_count);
  return (
    <section className="surface p-5 border border-teal-500/20">
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wider text-teal-400">Couverture des données</p>
          <h2 className="font-display font-semibold text-white text-lg mt-1">
            {data.known_required_count}/{data.required_count} informations attendues renseignées
          </h2>
          <p className="text-xs text-slate-500 mt-1">{data.message}</p>
        </div>
        <div className="rounded-xl bg-night-900/60 px-4 py-3 min-w-36">
          <p className="text-xs text-slate-500">À compléter</p>
          <p className="font-display font-bold text-2xl text-white">{remaining}</p>
        </div>
      </div>
      {data.next_actions.length === 0 ? (
        <div className="mt-4 flex items-center gap-2 text-sm text-teal-300">
          <CheckCircle2 className="w-4 h-4" />
          Les informations attendues pour ce niveau sont renseignées.
        </div>
      ) : (
        <div className="mt-4 space-y-2">
          <p className="text-xs text-slate-500 uppercase tracking-wider">Prochaines informations les plus utiles</p>
          {data.next_actions.map((item) => (
            <div key={item.key} className="rounded-xl bg-night-900/50 p-3 flex items-start gap-3">
              <AlertTriangle className="w-4 h-4 text-amber-300 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm text-white">{item.label}</p>
                <p className="text-xs text-slate-500 mt-0.5">{item.rationale}</p>
              </div>
            </div>
          ))}
        </div>
      )}
      {data.items.some((item) => item.status === 'check') && (
        <details className="mt-4">
          <summary className="text-xs text-slate-400 cursor-pointer flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" /> Éléments à vérifier seulement s’ils s’appliquent au milieu
          </summary>
          <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2">
            {data.items.filter((item) => item.status === 'check').map((item) => (
              <div key={item.key} className="rounded-lg bg-night-900/40 p-3">
                <p className="text-xs text-slate-300">{item.label}</p>
                <p className="text-xs text-slate-600 mt-1">{item.applicability_note || item.rationale}</p>
              </div>
            ))}
          </div>
        </details>
      )}
    </section>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return <div className="kpi-card"><p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p><p className="font-display font-bold text-xl text-white mt-1">{value}</p></div>;
}

function Tab({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return <button onClick={onClick} className={`px-3 py-2 rounded-xl text-sm border ${active ? 'bg-teal-500/15 border-teal-500/30 text-teal-300' : 'bg-night-850/40 border-night-700 text-slate-400'}`}>{children}</button>;
}

function LifeSection({ waterBodyId, livestock, plants, feedProducts, operations, experienceLevel, run }: {
  waterBodyId: string;
  livestock: LivestockItem[];
  plants: Array<{ id: string; common_name: string; scientific_name: string; count: number | null; coverage_percent: number | null; notes: string }>;
  feedProducts: FeedProduct[];
  operations: EcologyOperation[];
  experienceLevel: ExperienceLevel;
  run: (action: () => Promise<unknown>, waterChanged?: boolean) => Promise<void>;
}) {
  const [animalName, setAnimalName] = useState('');
  const [animalScientific, setAnimalScientific] = useState('');
  const [count, setCount] = useState('1');
  const [maleCount, setMaleCount] = useState('0');
  const [femaleCount, setFemaleCount] = useState('0');
  const [mass, setMass] = useState('');
  const [lifeStage, setLifeStage] = useState('');
  const [adjustSex, setAdjustSex] = useState<Record<string, 'male' | 'female' | 'unknown'>>({});
  const [sexDrafts, setSexDrafts] = useState<Record<string, { male: string; female: string }>>({});

  const [plantName, setPlantName] = useState('');
  const [plantScientific, setPlantScientific] = useState('');
  const [plantCount, setPlantCount] = useState('');
  const [coverage, setCoverage] = useState('');

  const [importUrl, setImportUrl] = useState('');
  const [showManualFood, setShowManualFood] = useState(false);
  const [manualBrand, setManualBrand] = useState('');
  const [manualName, setManualName] = useState('');
  const [manualVariant, setManualVariant] = useState('');
  const [manualForm, setManualForm] = useState('flakes');
  const [manualDietaryRole, setManualDietaryRole] = useState('complete');
  const [manualTargetSpecies, setManualTargetSpecies] = useState('');
  const [manualFeedingZone, setManualFeedingZone] = useState('unknown');
  const [manualProtein, setManualProtein] = useState('');
  const [manualFat, setManualFat] = useState('');
  const [manualFibre, setManualFibre] = useState('');
  const [manualMoisture, setManualMoisture] = useState('');
  const [manualAsh, setManualAsh] = useState('');
  const [manualPhosphorus, setManualPhosphorus] = useState('');
  const [manualIngredients, setManualIngredients] = useState('');
  const [manualAdditives, setManualAdditives] = useState('');
  const [manualFeedingGuide, setManualFeedingGuide] = useState('');
  const [manualSourceUrl, setManualSourceUrl] = useState('');

  const [feedProductId, setFeedProductId] = useState('');
  const [food, setFood] = useState('');
  const [amount, setAmount] = useState('');
  const [protein, setProtein] = useState('');
  const [consumedPercent, setConsumedPercent] = useState('100');
  const [targetPopulationId, setTargetPopulationId] = useState('all');

  const showIntermediate = experienceLevel !== 'beginner';
  const showAdvanced = experienceLevel === 'advanced';

  useEffect(() => {
    if (!feedProductId && feedProducts.length > 0) {
      setFeedProductId(feedProducts[0].id);
    }
  }, [feedProductId, feedProducts]);

  const submitAnimal = async (event: FormEvent) => {
    event.preventDefault();
    const parsedCount = Number(count);
    const parsedMale = Number(maleCount);
    const parsedFemale = Number(femaleCount);
    if (
      !animalName.trim()
      || !Number.isInteger(parsedCount)
      || !Number.isInteger(parsedMale)
      || !Number.isInteger(parsedFemale)
      || parsedCount < 0
      || parsedMale < 0
      || parsedFemale < 0
      || parsedMale + parsedFemale > parsedCount
    ) return;
    await run(() => addLivestock(waterBodyId, {
      common_name: animalName.trim(),
      scientific_name: animalScientific.trim(),
      count: parsedCount,
      male_count: parsedMale,
      female_count: parsedFemale,
      average_mass_g: numberOrNull(mass),
      life_stage: lifeStage.trim(),
    }));
    setAnimalName('');
    setAnimalScientific('');
    setCount('1');
    setMaleCount('0');
    setFemaleCount('0');
    setMass('');
    setLifeStage('');
  };

  const submitSexDistribution = async (item: LivestockItem) => {
    const draft = sexDrafts[item.id];
    const male = Number(draft?.male ?? item.male_count);
    const female = Number(draft?.female ?? item.female_count);
    if (
      !Number.isInteger(male)
      || !Number.isInteger(female)
      || male < 0
      || female < 0
      || male + female > item.count
    ) return;
    await run(() => setLivestockSexDistribution(waterBodyId, item.id, {
      male_count: male,
      female_count: female,
    }));
  };

  const submitPlant = async (event: FormEvent) => {
    event.preventDefault();
    if (!plantName.trim()) return;
    await run(() => addPlant(waterBodyId, {
      common_name: plantName.trim(),
      scientific_name: plantScientific.trim(),
      count: numberOrNull(plantCount),
      coverage_percent: numberOrNull(coverage),
    }));
    setPlantName('');
    setPlantScientific('');
    setPlantCount('');
    setCoverage('');
  };

  const submitImportFood = async (event: FormEvent) => {
    event.preventDefault();
    if (!importUrl.trim()) return;
    await run(() => importFeedProduct(importUrl.trim()));
    setImportUrl('');
  };

  const submitManualFood = async (event: FormEvent) => {
    event.preventDefault();
    if (!manualName.trim()) return;
    await run(() => addFeedProduct({
      brand: manualBrand.trim(),
      name: manualName.trim(),
      variant: manualVariant.trim(),
      form: manualForm,
      feed_category: manualForm === 'frozen' ? 'frozen' : manualForm === 'live' ? 'live' : 'prepared_dry',
      dietary_role: manualDietaryRole,
      target_species_text: manualTargetSpecies.trim(),
      feeding_zone: manualFeedingZone,
      ingredients_text: manualIngredients.trim(),
      crude_protein_percent: numberOrNull(manualProtein),
      crude_fat_percent: numberOrNull(manualFat),
      crude_fibre_percent: numberOrNull(manualFibre),
      moisture_percent: numberOrNull(manualMoisture),
      crude_ash_percent: numberOrNull(manualAsh),
      phosphorus_percent: numberOrNull(manualPhosphorus),
      additives_text: manualAdditives.trim(),
      feeding_guide_text: manualFeedingGuide.trim(),
      source_url: manualSourceUrl.trim(),
    }));
    setManualBrand('');
    setManualName('');
    setManualVariant('');
    setManualDietaryRole('complete');
    setManualTargetSpecies('');
    setManualFeedingZone('unknown');
    setManualProtein('');
    setManualFat('');
    setManualFibre('');
    setManualMoisture('');
    setManualAsh('');
    setManualPhosphorus('');
    setManualIngredients('');
    setManualAdditives('');
    setManualFeedingGuide('');
    setManualSourceUrl('');
    setShowManualFood(false);
  };

  const submitFeeding = async (event: FormEvent) => {
    event.preventDefault();
    const parsed = Number(amount);
    if (!Number.isFinite(parsed) || parsed <= 0) return;
    if (!feedProductId && !food.trim()) return;
    await run(() => recordFeeding(waterBodyId, {
      feed_product_id: feedProductId || null,
      food_name: feedProductId ? '' : food.trim(),
      amount_g: parsed,
      protein_percent: feedProductId ? null : numberOrNull(protein),
      target_population_ids: targetPopulationId === 'all' ? [] : [targetPopulationId],
      consumed_percent: numberOrNull(consumedPercent),
    }));
    setAmount('');
  };

  const latestFeeding = operations.find((item) => item.operation_type === 'feeding');
  const latestImpact = (
    latestFeeding
    && typeof latestFeeding.details.feed_load_estimate === 'object'
    && latestFeeding.details.feed_load_estimate !== null
  ) ? latestFeeding.details.feed_load_estimate as Record<string, unknown> : null;

  return <div className="space-y-6">
    <section className="space-y-3">
      <div>
        <h2 className="section-title flex items-center gap-2"><Fish className="w-4 h-4 text-teal-400" /> Charge animale</h2>
        <p className="text-xs text-slate-500 mt-1">
          Effectif, sexe et masse moyenne permettent de relier plus proprement reproduction, nourrissage et charge biologique.
        </p>
      </div>
      <form onSubmit={(e) => void submitAnimal(e)} className="surface p-4 grid grid-cols-2 md:grid-cols-7 gap-3">
        <label className={`${labelClass} col-span-2`}>Nom courant<input className={inputClass} value={animalName} onChange={(e) => setAnimalName(e.target.value)} placeholder="Medaka" /></label>
        {showAdvanced && <label className={`${labelClass} col-span-2`}>Nom scientifique<input className={inputClass} value={animalScientific} onChange={(e) => setAnimalScientific(e.target.value)} placeholder="Oryzias latipes" /></label>}
        <label className={labelClass}>Total<input className={inputClass} inputMode="numeric" value={count} onChange={(e) => setCount(e.target.value)} /></label>
        <label className={labelClass}>Mâles ♂<input className={inputClass} inputMode="numeric" value={maleCount} onChange={(e) => setMaleCount(e.target.value)} /></label>
        <label className={labelClass}>Femelles ♀<input className={inputClass} inputMode="numeric" value={femaleCount} onChange={(e) => setFemaleCount(e.target.value)} /></label>
        {showIntermediate && <label className={labelClass}>Masse moy. (g)<input className={inputClass} inputMode="decimal" value={mass} onChange={(e) => setMass(e.target.value)} /></label>}
        {showIntermediate && <label className={`${labelClass} col-span-2`}>Stade / taille<input className={inputClass} value={lifeStage} onChange={(e) => setLifeStage(e.target.value)} placeholder="juvénile, adulte…" /></label>}
        <div className="col-span-2 md:col-span-7 flex justify-between items-center gap-3">
          <p className="text-xs text-slate-500">Les individus non sexés restent explicitement « indéterminés ».</p>
          <button className="rounded-xl bg-teal-500 text-night-950 px-4 py-2 text-sm font-semibold"><Plus className="inline w-4 h-4 mr-1" />Ajouter la population</button>
        </div>
      </form>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {livestock.length === 0 && <div className="surface p-5 text-sm text-slate-500">Aucune population animale renseignée.</div>}
        {livestock.map((item) => {
          const selectedSex = adjustSex[item.id] ?? 'unknown';
          const draft = sexDrafts[item.id] ?? {
            male: String(item.male_count),
            female: String(item.female_count),
          };
          return <div key={item.id} className="surface p-4">
            <div className="flex justify-between gap-3">
              <div><h3 className="font-semibold text-white">{item.common_name}</h3><p className="text-xs italic text-slate-500">{item.scientific_name || 'Nom scientifique non renseigné'}</p></div>
              <button onClick={() => void run(() => deleteLivestock(waterBodyId, item.id))} className="text-slate-600 hover:text-coral-400"><Trash2 className="w-4 h-4" /></button>
            </div>
            <div className="grid grid-cols-3 gap-2 mt-3 text-xs">
              <Mini label="Effectif" value={`${item.count}`} />
              <Mini label="Masse moy." value={item.average_mass_g === null ? '—' : `${item.average_mass_g} g`} />
              <Mini label="Biomasse" value={item.biomass_g === null ? 'inconnue' : `${item.biomass_g.toFixed(1)} g`} />
            </div>
            <div className="grid grid-cols-3 gap-2 mt-2 text-xs">
              <Mini label="Mâles ♂" value={`${item.male_count}`} />
              <Mini label="Femelles ♀" value={`${item.female_count}`} />
              <Mini label="Indéterminés ?" value={`${item.unknown_sex_count}`} />
            </div>

            <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2">
              <label className={labelClass}>Mâles connus<input className={inputClass} inputMode="numeric" value={draft.male} onChange={(e) => setSexDrafts((current) => ({ ...current, [item.id]: { male: e.target.value, female: draft.female } }))} /></label>
              <label className={labelClass}>Femelles connues<input className={inputClass} inputMode="numeric" value={draft.female} onChange={(e) => setSexDrafts((current) => ({ ...current, [item.id]: { male: draft.male, female: e.target.value } }))} /></label>
              <div className="flex items-end"><button type="button" onClick={() => void submitSexDistribution(item)} className="w-full px-3 py-2.5 rounded-xl bg-night-800 text-xs text-slate-200">Mettre à jour les sexes</button></div>
            </div>

            <div className="flex gap-2 mt-3 flex-wrap items-center">
              <select className="rounded-lg bg-night-800 px-2 py-1 text-xs text-slate-300" value={selectedSex} onChange={(e) => setAdjustSex((current) => ({ ...current, [item.id]: e.target.value as 'male' | 'female' | 'unknown' }))}>
                <option value="unknown">Sexe indéterminé</option>
                <option value="male">Mâle ♂</option>
                <option value="female">Femelle ♀</option>
              </select>
              <button type="button" onClick={() => void run(() => adjustLivestock(waterBodyId, item.id, { delta_count: 1, reason: 'addition', sex: selectedSex }))} className="px-2 py-1 rounded-lg bg-night-800 text-xs text-slate-300">+1</button>
              <button type="button" disabled={item.count === 0} onClick={() => void run(() => adjustLivestock(waterBodyId, item.id, { delta_count: -1, reason: 'removal', sex: selectedSex }))} className="px-2 py-1 rounded-lg bg-night-800 text-xs text-slate-300 disabled:opacity-40">−1 retrait</button>
              <button type="button" disabled={item.count === 0} onClick={() => void run(() => adjustLivestock(waterBodyId, item.id, { delta_count: -1, reason: 'death', sex: selectedSex }))} className="px-2 py-1 rounded-lg bg-night-800 text-xs text-slate-300 disabled:opacity-40">−1 décès</button>
            </div>
          </div>;
        })}
      </div>
    </section>

    <section className="space-y-3">
      <div>
        <h2 className="section-title flex items-center gap-2"><Beef className="w-4 h-4 text-teal-400" /> Bibliothèque d’aliments</h2>
        <p className="text-xs text-slate-500 mt-1">
          Les aliments sont décrits comme des produits scientifiques réutilisables : forme, ingrédients, constituants analytiques, source et version de la fiche.
        </p>
      </div>

      <form onSubmit={(e) => void submitImportFood(e)} className="surface p-4 grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3">
        <label className={labelClass}>Importer une fiche produit par URL
          <input className={inputClass} value={importUrl} onChange={(e) => setImportUrl(e.target.value)} placeholder="https://www.zooplus.fr/..." />
        </label>
        <div className="flex items-end"><button className="rounded-xl bg-teal-500 text-night-950 px-4 py-2.5 text-sm font-semibold">Importer la fiche</button></div>
        <p className="md:col-span-2 text-xs text-slate-500">
          N9 V1 accepte les pages HTTPS Zooplus et Tetra. Les données factuelles sont structurées ; le texte marketing n’est pas copié dans l’identité scientifique.
        </p>
      </form>

      <button type="button" onClick={() => setShowManualFood((value) => !value)} className="text-xs text-teal-300 hover:text-teal-200">
        {showManualFood ? 'Masquer la saisie manuelle' : 'Ajouter un aliment manuellement'}
      </button>
      {showManualFood && (
        <form onSubmit={(e) => void submitManualFood(e)} className="surface p-4 grid grid-cols-2 md:grid-cols-6 gap-3">
          <label className={labelClass}>Marque<input className={inputClass} value={manualBrand} onChange={(e) => setManualBrand(e.target.value)} placeholder="Tetra" /></label>
          <label className={`${labelClass} col-span-2`}>Produit<input className={inputClass} value={manualName} onChange={(e) => setManualName(e.target.value)} placeholder="TetraMin Flakes" /></label>
          <label className={labelClass}>Variante / format<input className={inputClass} value={manualVariant} onChange={(e) => setManualVariant(e.target.value)} placeholder="1 000 mL" /></label>
          <label className={labelClass}>Forme<select className={inputClass} value={manualForm} onChange={(e) => setManualForm(e.target.value)}>
            <option value="flakes">Flocons</option><option value="micro_granules">Micro-granulés</option><option value="granules">Granulés</option><option value="pellets">Pellets</option><option value="sticks">Sticks</option><option value="tablets">Comprimés</option><option value="wafers">Wafers</option><option value="chips">Chips</option><option value="powder">Poudre</option><option value="gel">Gel</option><option value="freeze_dried">Lyophilisé</option><option value="frozen">Congelé</option><option value="live">Vivant</option><option value="other">Autre</option>
          </select></label>
          <label className={labelClass}>Rôle<select className={inputClass} value={manualDietaryRole} onChange={(e) => setManualDietaryRole(e.target.value)}><option value="complete">Aliment complet</option><option value="complementary">Complémentaire</option><option value="treat">Friandise</option><option value="unknown">Non précisé</option></select></label>
          <SmallInput label="Protéines brutes %" value={manualProtein} set={setManualProtein} />
          <SmallInput label="Matières grasses %" value={manualFat} set={setManualFat} />
          {showIntermediate && <><SmallInput label="Cellulose brute %" value={manualFibre} set={setManualFibre} /><SmallInput label="Humidité %" value={manualMoisture} set={setManualMoisture} /></>}
          {showAdvanced && <><SmallInput label="Cendres brutes %" value={manualAsh} set={setManualAsh} /><SmallInput label="Phosphore (P) %" value={manualPhosphorus} set={setManualPhosphorus} /><label className={`${labelClass} col-span-2`}>Espèces / groupes ciblés<input className={inputClass} value={manualTargetSpecies} onChange={(e) => setManualTargetSpecies(e.target.value)} /></label><label className={labelClass}>Zone de prise<select className={inputClass} value={manualFeedingZone} onChange={(e) => setManualFeedingZone(e.target.value)}><option value="unknown">Non précisée</option><option value="surface">Surface</option><option value="surface_to_midwater">Surface → pleine eau</option><option value="midwater">Pleine eau</option><option value="bottom">Fond</option><option value="surface_to_bottom">Toute la colonne</option></select></label></>}
          <label className={`${labelClass} col-span-2 md:col-span-4`}>Composition / ingrédients<textarea className={`${inputClass} min-h-20`} value={manualIngredients} onChange={(e) => setManualIngredients(e.target.value)} /></label>
          {showIntermediate && <label className={`${labelClass} col-span-2`}>Additifs<textarea className={`${inputClass} min-h-20`} value={manualAdditives} onChange={(e) => setManualAdditives(e.target.value)} /></label>}
          {showIntermediate && <label className={`${labelClass} col-span-2 md:col-span-4`}>Conseils de distribution<textarea className={`${inputClass} min-h-20`} value={manualFeedingGuide} onChange={(e) => setManualFeedingGuide(e.target.value)} /></label>}
          <label className={`${labelClass} col-span-2`}>URL source<input className={inputClass} value={manualSourceUrl} onChange={(e) => setManualSourceUrl(e.target.value)} /></label>
          <div className="col-span-2 md:col-span-6 flex justify-end"><button className="rounded-xl bg-teal-500 text-night-950 px-4 py-2 text-sm font-semibold">Ajouter à la bibliothèque</button></div>
        </form>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
        {feedProducts.map((product) => <div key={product.id} className="surface p-4">
          <div className="flex justify-between gap-3">
            <div>
              <p className="font-semibold text-white">{product.brand ? `${product.brand} — ` : ''}{product.name}</p>
              <p className="text-xs text-slate-500">{product.variant || product.form} · {product.dietary_role}</p>
            </div>
            <span className="text-[10px] uppercase tracking-wider text-teal-300">{product.form}</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mt-3 text-xs">
            <Mini label="Protéines" value={product.crude_protein_percent === null ? '—' : `${product.crude_protein_percent}%`} />
            <Mini label="Lipides" value={product.crude_fat_percent === null ? '—' : `${product.crude_fat_percent}%`} />
            <Mini label="Fibres" value={product.crude_fibre_percent === null ? '—' : `${product.crude_fibre_percent}%`} />
            <Mini label="Humidité" value={product.moisture_percent === null ? '—' : `${product.moisture_percent}%`} />
            <Mini label="Cendres" value={product.crude_ash_percent === null ? '—' : `${product.crude_ash_percent}%`} />
            <Mini label="Phosphore P" value={product.phosphorus_percent === null ? '—' : `${product.phosphorus_percent}%`} />
          </div>
          <p className="text-xs text-slate-500 mt-3">Rôle : {product.dietary_role} · zone : {product.feeding_zone}{product.target_species_text ? ` · cible : ${product.target_species_text}` : ''}</p>
          {product.ingredients_text && <p className="text-xs text-slate-400 mt-3 leading-relaxed"><span className="text-slate-500">Ingrédients :</span> {product.ingredients_text}</p>}
          {product.additives_text && <p className="text-xs text-slate-500 mt-2"><span className="text-slate-400">Additifs :</span> {product.additives_text}</p>}
          {product.feeding_guide_text && <p className="text-xs text-slate-500 mt-2"><span className="text-slate-400">Distribution :</span> {product.feeding_guide_text}</p>}
          <div className="flex gap-3 mt-3 text-xs">
            {product.source_url && <a className="text-teal-400 hover:underline" href={product.source_url} target="_blank" rel="noreferrer">Fiche source</a>}
            {product.manufacturer_url && <a className="text-teal-400 hover:underline" href={product.manufacturer_url} target="_blank" rel="noreferrer">Fabricant</a>}
          </div>
        </div>)}
      </div>
    </section>

    <section className="space-y-3">
      <div>
        <h2 className="section-title flex items-center gap-2"><Beef className="w-4 h-4 text-teal-400" /> Nourrissage</h2>
        <p className="text-xs text-slate-500 mt-1">
          EcoBiome calcule d’abord ce qui entre réellement dans le système. Les effets TAN / NO₃⁻ / O₂ affichés ici sont des bornes stœchiométriques, pas une prédiction biologique sans coefficient espèce-aliment.
        </p>
      </div>
      <form onSubmit={(e) => void submitFeeding(e)} className="surface p-4 grid grid-cols-1 md:grid-cols-5 gap-3">
        <label className={`${labelClass} md:col-span-2`}>Aliment
          <select className={inputClass} value={feedProductId} onChange={(e) => setFeedProductId(e.target.value)}>
            <option value="">Aliment non catalogué</option>
            {feedProducts.map((product) => <option key={product.id} value={product.id}>{product.brand ? `${product.brand} — ` : ''}{product.name}{product.variant ? ` (${product.variant})` : ''}</option>)}
          </select>
        </label>
        {!feedProductId && <label className={labelClass}>Nom libre<input className={inputClass} value={food} onChange={(e) => setFood(e.target.value)} /></label>}
        <label className={labelClass}>Quantité (g)<input className={inputClass} inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} /></label>
        <label className={labelClass}>Population cible<select className={inputClass} value={targetPopulationId} onChange={(e) => setTargetPopulationId(e.target.value)}><option value="all">Toutes les populations animales</option>{livestock.map((item) => <option key={item.id} value={item.id}>{item.common_name} — {item.count} ind.</option>)}</select></label>
        <label className={labelClass}>Part consommée estimée (%)<input className={inputClass} inputMode="decimal" value={consumedPercent} onChange={(e) => setConsumedPercent(e.target.value)} /></label>
        {!feedProductId && showIntermediate && <label className={labelClass}>Protéines brutes (%)<input className={inputClass} inputMode="decimal" value={protein} onChange={(e) => setProtein(e.target.value)} /></label>}
        <div className="flex items-end"><button className="w-full rounded-xl bg-teal-500 text-night-950 px-4 py-2.5 text-sm font-semibold">Enregistrer le nourrissage</button></div>
      </form>

      {latestImpact && (
        <div className="surface p-4 border border-teal-500/20">
          <p className="text-sm font-semibold text-white">Dernier bilan de charge alimentaire</p>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-2 mt-3 text-xs">
            <Mini label="Taux de ration" value={formatImpact(latestImpact.feed_rate_percent_biomass_decimal, '% biomasse')} />
            <Mini label="Protéines" value={formatImpact(latestImpact.protein_g_decimal, 'g')} />
            <Mini label="N protéique estimé" value={formatImpact(latestImpact.estimated_protein_nitrogen_mg_decimal, 'mg N')} />
            <Mini label="Δ TAN-N borne haute" value={formatImpact(latestImpact.tan_n_upper_bound_delta_mg_l_decimal, 'mg N/L')} />
            <Mini label="O₂ nitrification borne haute" value={formatImpact(latestImpact.nitrification_o2_upper_bound_delta_mg_l_decimal, 'mg/L')} />
          </div>
          <p className="text-xs text-amber-300/80 mt-3">
            Ces valeurs décrivent l’entrée et des bornes théoriques. La prédiction attendue nécessite encore digestibilité, rétention/croissance et excrétion propres à l’espèce et au régime.
          </p>
        </div>
      )}
    </section>

    <section className="space-y-3">
      <div><h2 className="section-title flex items-center gap-2"><Leaf className="w-4 h-4 text-teal-400" /> Végétation</h2><p className="text-xs text-slate-500 mt-1">Le nombre seul est souvent insuffisant : la couverture donne une meilleure idée de la biomasse végétale fonctionnelle.</p></div>
      <form onSubmit={(e) => void submitPlant(e)} className="surface p-4 grid grid-cols-1 md:grid-cols-5 gap-3">
        <label className={labelClass}>Nom courant<input className={inputClass} value={plantName} onChange={(e) => setPlantName(e.target.value)} /></label>
        {showAdvanced && <label className={labelClass}>Nom scientifique<input className={inputClass} value={plantScientific} onChange={(e) => setPlantScientific(e.target.value)} /></label>}
        {showIntermediate && <label className={labelClass}>Nombre / tiges<input className={inputClass} inputMode="numeric" value={plantCount} onChange={(e) => setPlantCount(e.target.value)} /></label>}
        {showIntermediate && <label className={labelClass}>Couverture (%)<input className={inputClass} inputMode="decimal" value={coverage} onChange={(e) => setCoverage(e.target.value)} /></label>}
        <div className="flex items-end"><button className="w-full rounded-xl bg-teal-500 text-night-950 px-3 py-2.5 text-sm font-semibold">Ajouter</button></div>
      </form>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">{plants.map((item) => <div className="surface p-4" key={item.id}><div className="flex justify-between"><div><p className="font-medium text-white">{item.common_name}</p><p className="text-xs italic text-slate-500">{item.scientific_name || '—'}</p></div><button onClick={() => void run(() => deletePlant(waterBodyId, item.id))}><Trash2 className="w-4 h-4 text-slate-600" /></button></div><div className="mt-3 text-xs text-slate-400">{item.count !== null ? `${item.count} unité(s)` : 'quantité non renseignée'} · {item.coverage_percent !== null ? `${item.coverage_percent}% de couverture` : 'couverture inconnue'}</div></div>)}</div>
    </section>
  </div>;
}

function formatImpact(value: unknown, unit: string): string {
  if (typeof value !== 'string' || !value) return '—';
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return `${value} ${unit}`.trim();
  const digits = Math.abs(parsed) >= 10 ? 2 : 4;
  return `${parsed.toFixed(digits).replace(/0+$/, '').replace(/\.$/, '')} ${unit}`.trim();
}

function WaterSection({ waterBody, waterSources, substrateLayers, experienceLevel, run }: {
  waterBody: WaterBody;
  waterSources: Array<{ id: string; name: string; source_type: WaterSourceType; temperature_c: number | null; ph: number | null; kh_dkh: number | null; gh_dgh: number | null; conductivity_us_cm: number | null; nitrate_mg_l: number | null; nitrite_mg_l: number | null; ammonia_mg_l: number | null; phosphate_mg_l: number | null; chloride_mg_l: number | null; calcium_mg_l: number | null; magnesium_mg_l: number | null; salinity_g_l: number | null }>;
  substrateLayers: Array<{ id: string; material: string; thickness_cm: number | null; grain_min_mm: number | null; grain_max_mm: number | null; organic: boolean }>;
  experienceLevel: ExperienceLevel;
  run: (action: () => Promise<unknown>, waterChanged?: boolean) => Promise<void>;
}) {
  const [sourceName, setSourceName] = useState('Eau du robinet');
  const [sourceType, setSourceType] = useState<WaterSourceType>('tap');
  const [temp, setTemp] = useState(''); const [ph, setPh] = useState(''); const [kh, setKh] = useState(''); const [gh, setGh] = useState(''); const [cond, setCond] = useState(''); const [nitrate, setNitrate] = useState(''); const [nitrite, setNitrite] = useState(''); const [ammonia, setAmmonia] = useState(''); const [phosphate, setPhosphate] = useState(''); const [chloride, setChloride] = useState(''); const [calcium, setCalcium] = useState(''); const [magnesium, setMagnesium] = useState(''); const [salinity, setSalinity] = useState('');
  const [topUp, setTopUp] = useState(''); const [topUpSource, setTopUpSource] = useState('');
  const [material, setMaterial] = useState(''); const [thickness, setThickness] = useState(''); const [grainMin, setGrainMin] = useState(''); const [grainMax, setGrainMax] = useState(''); const [organic, setOrganic] = useState(false);
  const showIntermediate = experienceLevel !== 'beginner';
  const showAdvanced = experienceLevel === 'advanced';

  const submitSource = async (event: FormEvent) => { event.preventDefault(); if (!sourceName.trim()) return; await run(() => addWaterSource(waterBody.id, { name: sourceName.trim(), source_type: sourceType, temperature_c: numberOrNull(temp), ph: numberOrNull(ph), kh_dkh: numberOrNull(kh), gh_dgh: numberOrNull(gh), conductivity_us_cm: numberOrNull(cond), nitrate_mg_l: numberOrNull(nitrate), nitrite_mg_l: numberOrNull(nitrite), ammonia_mg_l: numberOrNull(ammonia), phosphate_mg_l: numberOrNull(phosphate), chloride_mg_l: numberOrNull(chloride), calcium_mg_l: numberOrNull(calcium), magnesium_mg_l: numberOrNull(magnesium), salinity_g_l: numberOrNull(salinity) })); };
  const submitTopUp = async (event: FormEvent) => { event.preventDefault(); const volume = Number(topUp); if (!Number.isFinite(volume) || volume <= 0) return; await run(() => recordTopUp(waterBody.id, { volume_liters: volume, water_source_id: topUpSource || null }), true); setTopUp(''); };
  const submitLayer = async (event: FormEvent) => { event.preventDefault(); const thick = Number(thickness); if (!material.trim() || !Number.isFinite(thick) || thick <= 0) return; await run(() => addSubstrateLayer(waterBody.id, { material: material.trim(), thickness_cm: thick, grain_min_mm: numberOrNull(grainMin), grain_max_mm: numberOrNull(grainMax), organic })); setMaterial(''); setThickness(''); };

  return <div className="space-y-6">
    <section className="space-y-3"><div><h2 className="section-title flex items-center gap-2"><Droplets className="w-4 h-4 text-teal-400" /> Profils d’eau</h2><p className="text-xs text-slate-500 mt-1">Réutilisables pour les changements d’eau et compléments après évaporation.</p></div>
      <form onSubmit={(e) => void submitSource(e)} className="surface p-4 grid grid-cols-2 md:grid-cols-5 gap-3">
        <label className={`${labelClass} col-span-2`}>Nom<input className={inputClass} value={sourceName} onChange={(e) => setSourceName(e.target.value)} /></label><label className={labelClass}>Origine<select className={inputClass} value={sourceType} onChange={(e) => setSourceType(e.target.value as WaterSourceType)}><option value="tap">Robinet</option><option value="rain">Pluie</option><option value="ro">Osmosée</option><option value="well">Puits</option><option value="mixed">Mélange</option><option value="other">Autre</option></select></label>
        <SmallInput label="Température (T) °C" value={temp} set={setTemp} /><SmallInput label="pH — potentiel hydrogène" value={ph} set={setPh} /><SmallInput label="KH (HCO₃⁻ / CO₃²⁻) °dKH" value={kh} set={setKh} />
        {showIntermediate && <><SmallInput label="GH (Ca²⁺ / Mg²⁺) °dGH" value={gh} set={setGh} /><SmallInput label="Conductivité (κ) µS/cm" value={cond} set={setCond} /><SmallInput label="Nitrates (NO₃⁻) mg/L" value={nitrate} set={setNitrate} /><SmallInput label="Nitrites (NO₂⁻) mg/L" value={nitrite} set={setNitrite} /></>}
        {showAdvanced && <><SmallInput label="Ammoniac / ammonium (NH₃ / NH₄⁺) mg/L" value={ammonia} set={setAmmonia} /><SmallInput label="Phosphates (PO₄³⁻) mg/L" value={phosphate} set={setPhosphate} /><SmallInput label="Chlorures (Cl⁻) mg/L" value={chloride} set={setChloride} /><SmallInput label="Calcium (Ca²⁺) mg/L" value={calcium} set={setCalcium} /><SmallInput label="Magnésium (Mg²⁺) mg/L" value={magnesium} set={setMagnesium} /><SmallInput label="Salinité (S) g/L" value={salinity} set={setSalinity} /></>}
        <div className="col-span-2 md:col-span-5 flex justify-end"><button className="rounded-xl bg-teal-500 text-night-950 px-4 py-2 text-sm font-semibold">Créer le profil</button></div>
      </form>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">{waterSources.map((source) => <div key={source.id} className="surface p-4"><div className="flex justify-between"><div><p className="font-medium text-white">{source.name}</p><p className="text-xs text-slate-500">{source.source_type}</p></div><button onClick={() => void run(() => deleteWaterSource(waterBody.id, source.id))}><Trash2 className="w-4 h-4 text-slate-600" /></button></div><p className="text-xs text-slate-400 mt-3">pH (potentiel hydrogène) {source.ph ?? '—'} · KH {source.kh_dkh ?? '—'} °dKH · GH {source.gh_dgh ?? '—'} °dGH · κ {source.conductivity_us_cm ?? '—'} µS/cm · NO₃⁻ {source.nitrate_mg_l ?? '—'} mg/L</p></div>)}</div>
    </section>

    <section className="space-y-3"><h2 className="section-title flex items-center gap-2"><RefreshCw className="w-4 h-4 text-teal-400" /> Complément après évaporation</h2><form onSubmit={(e) => void submitTopUp(e)} className="surface p-4 grid grid-cols-1 md:grid-cols-3 gap-3"><SmallInput label="Volume ajouté (L)" value={topUp} set={setTopUp} /><label className={labelClass}>Profil d’eau<select className={inputClass} value={topUpSource} onChange={(e) => setTopUpSource(e.target.value)}><option value="">Non précisé</option>{waterSources.map((source) => <option key={source.id} value={source.id}>{source.name}</option>)}</select></label><div className="flex items-end"><button className="w-full rounded-xl bg-teal-500 text-night-950 px-4 py-2.5 text-sm font-semibold">Ajouter l’eau</button></div></form></section>

    <section className="space-y-3"><div><h2 className="section-title flex items-center gap-2"><Shovel className="w-4 h-4 text-teal-400" /> Substrat</h2><p className="text-xs text-slate-500 mt-1">Décrire les couches, leur épaisseur, granulométrie et caractère organique.</p></div><form onSubmit={(e) => void submitLayer(e)} className="surface p-4 grid grid-cols-2 md:grid-cols-5 gap-3"><label className={`${labelClass} col-span-2`}>Matériau<input className={inputClass} value={material} onChange={(e) => setMaterial(e.target.value)} placeholder="Pouzzolane, sable, terre…" /></label><SmallInput label="Épaisseur cm" value={thickness} set={setThickness} />{showIntermediate && <><SmallInput label="Grain min mm" value={grainMin} set={setGrainMin} /><SmallInput label="Grain max mm" value={grainMax} set={setGrainMax} /><label className={`${labelClass} col-span-2 md:col-span-4 flex items-center gap-2 mt-5`}><input type="checkbox" checked={organic} onChange={(e) => setOrganic(e.target.checked)} /> Couche contenant une fraction organique</label></>}<button className="rounded-xl bg-teal-500 text-night-950 px-3 py-2 text-sm font-semibold">Ajouter la couche</button></form><div className="space-y-2">{substrateLayers.map((layer, index) => <div key={layer.id} className="surface p-3 flex items-center justify-between gap-3"><div><p className="text-sm text-white">Couche {index + 1} — {layer.material}</p><p className="text-xs text-slate-500">{layer.thickness_cm ?? '—'} cm · granulométrie {layer.grain_min_mm ?? '—'}–{layer.grain_max_mm ?? '—'} mm {layer.organic ? '· organique' : ''}</p></div><button onClick={() => void run(() => deleteSubstrateLayer(waterBody.id, layer.id))}><Trash2 className="w-4 h-4 text-slate-600" /></button></div>)}</div></section>
  </div>;
}

function OperationsSection({ waterBodyId, operations, experienceLevel, run }: {
  waterBodyId: string;
  operations: Array<{ event_id: string; occurred_at: string; operation_type: string; note: string; details: Record<string, unknown> }>;
  experienceLevel: ExperienceLevel;
  run: (action: () => Promise<unknown>, waterChanged?: boolean) => Promise<void>;
}) {
  const [type, setType] = useState<OperationType>('filter_maintenance');
  const operationOptions: Array<{ value: OperationType; label: string; minimum: ExperienceLevel }> = [
    { value: 'filter_maintenance', label: 'Entretien filtration', minimum: 'beginner' },
    { value: 'power_outage', label: 'Coupure / arrêt', minimum: 'beginner' },
    { value: 'siphoning', label: 'Siphonnage / retrait de déchets', minimum: 'beginner' },
    { value: 'plant_pruning', label: 'Taille plantes', minimum: 'beginner' },
    { value: 'additive', label: 'Ajout de produit', minimum: 'intermediate' },
    { value: 'fertilization', label: 'Fertilisation', minimum: 'intermediate' },
    { value: 'bacteria_addition', label: 'Ajout de bactéries', minimum: 'intermediate' },
    { value: 'water_treatment', label: 'Conditionnement / traitement de l’eau', minimum: 'intermediate' },
    { value: 'co2_change', label: 'Modification CO₂', minimum: 'advanced' },
    { value: 'substrate_maintenance', label: 'Entretien substrat', minimum: 'advanced' },
    { value: 'medication', label: 'Traitement / médicament', minimum: 'advanced' },
    { value: 'other', label: 'Autre', minimum: 'beginner' },
  ];
  const rank: Record<ExperienceLevel, number> = { beginner: 0, intermediate: 1, advanced: 2 };
  const visibleOptions = operationOptions.filter((item) => rank[item.minimum] <= rank[experienceLevel]);

  useEffect(() => {
    if (!visibleOptions.some((item) => item.value === type)) {
      setType('filter_maintenance');
    }
  }, [experienceLevel, type]);
  const [label, setLabel] = useState(''); const [quantity, setQuantity] = useState(''); const [unit, setUnit] = useState(''); const [note, setNote] = useState('');
  const submit = async (event: FormEvent) => { event.preventDefault(); if (!label.trim()) return; await run(() => recordEcosystemOperation(waterBodyId, { operation_type: type, label: label.trim(), quantity: numberOrNull(quantity), unit: unit.trim(), note: note.trim() })); setLabel(''); setQuantity(''); setUnit(''); setNote(''); };
  return <div className="space-y-5"><div><h2 className="section-title flex items-center gap-2"><Wrench className="w-4 h-4 text-teal-400" /> Intervention / perturbation</h2><p className="text-xs text-slate-500 mt-1">Entretien du filtre, coupure électrique, traitement, fertilisation, taille, remuage du substrat… Ces événements expliquent souvent une variation ultérieure de l’eau.</p></div><form onSubmit={(e) => void submit(e)} className="surface p-4 grid grid-cols-1 md:grid-cols-5 gap-3"><label className={labelClass}>Type<select className={inputClass} value={type} onChange={(e) => setType(e.target.value as typeof type)}>{visibleOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label><label className={`${labelClass} md:col-span-2`}>Description<input className={inputClass} value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Nettoyage de la mousse 30 PPI" /></label><SmallInput label="Quantité" value={quantity} set={setQuantity} /><label className={labelClass}>Unité<input className={inputClass} value={unit} onChange={(e) => setUnit(e.target.value)} /></label><label className={`${labelClass} md:col-span-4`}>Note<input className={inputClass} value={note} onChange={(e) => setNote(e.target.value)} /></label><button className="rounded-xl bg-teal-500 text-night-950 px-3 py-2 text-sm font-semibold self-end">Enregistrer</button></form><div className="space-y-2">{operations.length === 0 && <div className="surface p-5 text-sm text-slate-500">Aucune intervention N7 enregistrée.</div>}{operations.map((op) => <div key={op.event_id} className="surface p-3"><div className="flex justify-between gap-3"><p className="text-sm text-white">{operationLabel(op.operation_type)}</p><span className="text-xs text-slate-600">{new Date(op.occurred_at).toLocaleString('fr-FR')}</span></div><p className="text-xs text-slate-400 mt-1">{String(op.details.label ?? op.details.food_name ?? op.details.common_name ?? op.details.material ?? '')}</p>{op.note && <p className="text-xs text-slate-500 mt-1">{op.note}</p>}</div>)}</div></div>;
}

function operationLabel(type: string): string {
  const labels: Record<string, string> = { feeding: 'Nourrissage', livestock_added: 'Ajout d’animaux', livestock_removed: 'Retrait d’animaux', livestock_death: 'Mortalité', livestock_corrected: 'Correction d’effectif', plant_added: 'Ajout de plantes', plant_removed: 'Retrait de plantes', top_up: 'Complément d’eau', equipment_added: 'Matériel ajouté', equipment_removed: 'Matériel retiré', water_source_added: 'Profil d’eau créé', water_source_removed: 'Profil d’eau retiré', substrate_layer_added: 'Couche de substrat ajoutée', substrate_layer_removed: 'Couche de substrat retirée', filter_maintenance: 'Entretien filtration', power_outage: 'Coupure / arrêt électrique', additive: 'Ajout de produit', fertilization: 'Fertilisation', bacteria_addition: 'Ajout de bactéries', co2_change: 'Modification CO₂', water_treatment: 'Traitement de l’eau', siphoning: 'Siphonnage', plant_pruning: 'Taille de plantes', substrate_maintenance: 'Entretien du substrat', medication: 'Traitement / médicament' };
  return labels[type] ?? type;
}

function SmallInput({ label, value, set }: { label: string; value: string; set: (value: string) => void }) {
  return <label className={labelClass}>{label}<input className={inputClass} inputMode="decimal" value={value} onChange={(e) => set(e.target.value)} /></label>;
}

function Mini({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg bg-night-900/50 p-2"><span className="text-slate-500">{label}</span><p className="font-mono text-white">{value}</p></div>;
}
