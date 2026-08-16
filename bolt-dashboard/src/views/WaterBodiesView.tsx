import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import {
  addEquipment,
  addMeasurement,
  createWaterBody,
  deleteEquipment,
  recordWaterExchange,
  setFillLevel,
} from '@/lib/api';
import {
  getLatestByMetric,
  getMetricSeries,
  useEquipment,
  useEcology,
  useMeasurements,
  useWaterBodies,
} from '@/lib/hooks';
import {
  EQUIPMENT_TYPE_LABELS,
  EXPERIENCE_LEVEL_DESCRIPTIONS,
  EXPERIENCE_LEVEL_LABELS,
  METRIC_LIST,
  METRICS,
  METRICS_BY_EXPERIENCE_LEVEL,
  WATER_BODY_TYPE_LABELS,
  type EquipmentType,
  type ExperienceLevel,
  type Metric,
  type WaterBody,
} from '@/lib/types';
import { MetricCard } from '@/components/MetricCard';
import { EcosystemInputsPanel } from '@/views/EcosystemInputsPanel';
import { MeasurementExplorerView } from '@/views/MeasurementExplorerView';
import { StatusBadge, StatusDot } from '@/components/StatusBadge';
import { WaterTankViz } from '@/components/WaterTankViz';
import {
  ArrowLeft,
  Calendar,
  Gauge,
  Loader2,
  Plus,
  RefreshCw,
  Trash2,
  TrendingUp,
  Wrench,
  X,
} from 'lucide-react';

interface WaterBodiesViewProps {
  initialWaterBody: WaterBody | null;
  onClearInitial: () => void;
  onOpenGlossaryForMetric: (metric: Metric) => void;
}


export function WaterBodiesView({
  initialWaterBody,
  onClearInitial,
  onOpenGlossaryForMetric,
}: WaterBodiesViewProps) {
  const {
    data: waterBodies,
    loading,
    error,
    refetch,
  } = useWaterBodies();
  const [selectedId, setSelectedId] = useState<string | null>(
    initialWaterBody?.id ?? null,
  );
  const [showCreate, setShowCreate] = useState(false);

  const selected = useMemo(() => {
    if (waterBodies.length === 0) {
      return null;
    }
    return (
      waterBodies.find((waterBody) => waterBody.id === selectedId) ??
      null
    );
  }, [waterBodies, selectedId]);

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        <div className="skeleton h-96" />
      </div>
    );
  }

  if (selected) {
    return (
      <WaterBodyDetail
        waterBody={selected}
        onBack={() => {
          setSelectedId(null);
          onClearInitial();
        }}
        onWaterBodyChanged={refetch}
        onOpenGlossaryForMetric={onOpenGlossaryForMetric}
      />
    );
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="font-display font-bold text-white text-2xl">
            Milieux aquatiques
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            {waterBodies.length} milieu(x) local(aux) suivi(s)
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="rounded-xl bg-teal-500 text-night-950 px-4 py-2.5 text-sm font-semibold flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Nouveau milieu
        </button>
      </div>

      {error && (
        <div className="surface border border-coral-500/40 p-4 text-sm text-coral-300">
          API locale indisponible : {error}
        </div>
      )}

      {showCreate && (
        <CreateWaterBodyPanel
          onCancel={() => setShowCreate(false)}
          onCreated={async (waterBody) => {
            await refetch();
            setShowCreate(false);
            setSelectedId(waterBody.id);
          }}
        />
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {waterBodies.map((waterBody) => (
          <div
            key={waterBody.id}
            onClick={() => setSelectedId(waterBody.id)}
            className="cursor-pointer group"
          >
            <WaterTankViz
              waterBody={waterBody}
              fillPercent={waterBody.fill_percent}
            />
          </div>
        ))}

        <button
          onClick={() => setShowCreate(true)}
          className="surface surface-hover p-5 flex flex-col items-center justify-center min-h-[280px] border-dashed border-2 border-night-700 hover:border-teal-500/40 group"
        >
          <div className="w-12 h-12 rounded-xl bg-night-800 group-hover:bg-teal-500/15 flex items-center justify-center transition-colors mb-3">
            <Plus className="w-6 h-6 text-slate-500 group-hover:text-teal-400 transition-colors" />
          </div>
          <p className="text-sm font-medium text-slate-400 group-hover:text-white transition-colors">
            Ajouter un milieu
          </p>
        </button>
      </div>
    </div>
  );
}

function CreateWaterBodyPanel({
  onCancel,
  onCreated,
}: {
  onCancel: () => void;
  onCreated: (waterBody: WaterBody) => Promise<void>;
}) {
  const [name, setName] = useState('Mon bassin');
  const [type, setType] = useState<'aquarium' | 'pond'>('pond');
  const [volume, setVolume] = useState('250');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const parsedVolume = Number(volume);
    if (!name.trim() || !Number.isFinite(parsedVolume) || parsedVolume <= 0) {
      setError('Nom et volume positif requis.');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const created = await createWaterBody({
        name: name.trim(),
        type,
        volume_liters: parsedVolume,
      });
      await onCreated(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="surface p-5 border border-teal-500/30">
      <div className="flex items-center justify-between gap-4 mb-4">
        <div>
          <h2 className="section-title">Créer un milieu local</h2>
          <p className="text-xs text-slate-500 mt-1">
            Le profil est stocké localement. Le volume initial devient une
            observation canonique N5.
          </p>
        </div>
        <button
          onClick={onCancel}
          className="p-2 text-slate-500 hover:text-white"
          title="Fermer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <form
        onSubmit={handleSubmit}
        className="grid grid-cols-1 md:grid-cols-4 gap-3"
      >
        <div className="md:col-span-2">
          <label className="text-xs text-slate-400 block mb-1.5">
            Nom
          </label>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white outline-none focus:border-teal-500/60"
          />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1.5">
            Type
          </label>
          <select
            value={type}
            onChange={(event) =>
              setType(event.target.value as 'aquarium' | 'pond')
            }
            className="w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white outline-none focus:border-teal-500/60"
          >
            <option value="pond">Bassin</option>
            <option value="aquarium">Aquarium</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1.5">
            Volume initial (L)
          </label>
          <input
            value={volume}
            onChange={(event) => setVolume(event.target.value)}
            inputMode="decimal"
            className="w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white outline-none focus:border-teal-500/60"
          />
        </div>

        {error && (
          <p className="md:col-span-4 text-sm text-coral-300">{error}</p>
        )}

        <div className="md:col-span-4 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="rounded-xl bg-teal-500 text-night-950 px-4 py-2.5 text-sm font-semibold disabled:opacity-50 flex items-center gap-2"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            Créer le milieu
          </button>
        </div>
      </form>
    </div>
  );
}

function WaterBodyDetail({
  waterBody,
  onBack,
  onWaterBodyChanged,
  onOpenGlossaryForMetric,
}: {
  waterBody: WaterBody;
  onBack: () => void;
  onWaterBodyChanged: () => Promise<void>;
  onOpenGlossaryForMetric: (metric: Metric) => void;
}) {
  const {
    data: measurements,
    loading: measLoading,
    error: measurementError,
    refetch: refetchMeasurements,
  } = useMeasurements(waterBody.id);
  const {
    data: ecology,
    refetch: refetchEcology,
  } = useEcology(waterBody.id);
  const [showMeasurementForm, setShowMeasurementForm] = useState(false);
  const [measurementMetric, setMeasurementMetric] = useState<Metric | null>(null);
  const [showFillForm, setShowFillForm] = useState(false);
  const [showWaterExchangeForm, setShowWaterExchangeForm] = useState(false);
  const [selectedMetricDetail, setSelectedMetricDetail] = useState<Metric | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'equipment' | 'ecosystem'>(
    'overview',
  );
  const [experienceLevel, setExperienceLevelState] = useState<ExperienceLevel>(() => {
    if (typeof window === 'undefined') return 'beginner';
    const stored = window.localStorage.getItem('ecobiome-experience-level');
    return stored === 'intermediate' || stored === 'advanced' ? stored : 'beginner';
  });
  const setExperienceLevel = (level: ExperienceLevel) => {
    setExperienceLevelState(level);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('ecobiome-experience-level', level);
    }
  };
  useEffect(() => {
    if (activeTab === 'overview') {
      void refetchEcology();
    }
  }, [activeTab, refetchEcology]);
  const openMeasurementFormForMetric = (metric: Metric) => {
    setMeasurementMetric(metric);
    setSelectedMetricDetail(null);
    setShowMeasurementForm(true);
    if (typeof window !== 'undefined') {
      window.requestAnimationFrame(() => {
        document.getElementById('measurement-entry-panel')?.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        });
      });
    }
  };

  const latest = useMemo(
    () => getLatestByMetric(measurements),
    [measurements],
  );
  const visibleMetricList = useMemo(
    () => METRIC_LIST.filter((info) =>
      METRICS_BY_EXPERIENCE_LEVEL[experienceLevel].includes(info.key),
    ),
    [experienceLevel],
  );

  if (selectedMetricDetail) {
    return (
      <MeasurementExplorerView
        waterBody={waterBody}
        measurements={measurements}
        primaryMetric={selectedMetricDetail}
        onBack={() => setSelectedMetricDetail(null)}
        onAddMeasurement={openMeasurementFormForMetric}
        onOpenGlossary={onOpenGlossaryForMetric}
      />
    );
  }

  if (activeTab === 'ecosystem') {
    return (
      <div className="p-6 space-y-6 animate-fade-in">
        <button onClick={onBack} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Retour aux milieux
        </button>
        <div>
          <h1 className="font-display font-bold text-white text-2xl">{waterBody.name}</h1>
          <p className="text-sm text-slate-400 mt-1">Charge biologique, flux, eau de remplacement, substrat et interventions</p>
        </div>
        <ExperienceLevelBar level={experienceLevel} onChange={setExperienceLevel} />
        <DetailTabs active={activeTab} onChange={setActiveTab} />
        <EcosystemInputsPanel
          waterBody={waterBody}
          experienceLevel={experienceLevel}
          onWaterBodyChanged={onWaterBodyChanged}
        />
      </div>
    );
  }

  if (activeTab === 'equipment') {
    return (
      <div className="p-6 space-y-6 animate-fade-in">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Retour aux milieux
        </button>
        <div>
          <h1 className="font-display font-bold text-white text-2xl">
            {waterBody.name}
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Inventaire du matériel et paramètres de fonctionnement
          </p>
        </div>
        <ExperienceLevelBar level={experienceLevel} onChange={setExperienceLevel} />
        <DetailTabs active={activeTab} onChange={setActiveTab} />
        <EquipmentPanel waterBodyId={waterBody.id} experienceLevel={experienceLevel} />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Retour aux milieux
      </button>

      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <StatusDot status={waterBody.status} />
            <h1 className="font-display font-bold text-white text-2xl">
              {waterBody.name}
            </h1>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span>{WATER_BODY_TYPE_LABELS[waterBody.type]}</span>
            <span>·</span>
            <span>Capacité {waterBody.capacity_liters.toFixed(1)} L</span>
            <span>·</span>
            <span>Eau {waterBody.current_volume_liters.toFixed(1)} L</span>
            <span>·</span>
            <StatusBadge status={waterBody.status} />
          </div>
          {waterBody.status === 'unknown' && (
            <p className="text-xs text-slate-500 mt-2">
              Aucun diagnostic scientifique n'est encore calculé : EcoBiome
              ne déclare pas artificiellement ce milieu stable.
            </p>
          )}
        </div>

        <div className="flex flex-wrap justify-end gap-2">
          <button
            onClick={() => setShowFillForm((value) => !value)}
            className="rounded-xl bg-night-800 text-slate-200 border border-night-600 px-3 py-2.5 text-sm font-semibold flex items-center gap-2"
          >
            <Gauge className="w-4 h-4" />
            Remplissage
          </button>
          <button
            onClick={() => setShowWaterExchangeForm((value) => !value)}
            className="rounded-xl bg-night-800 text-slate-200 border border-night-600 px-3 py-2.5 text-sm font-semibold flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Changement d'eau
          </button>
          <button
            onClick={() => {
              setMeasurementMetric(null);
              setShowMeasurementForm((value) => !value);
            }}
            className="rounded-xl bg-teal-500 text-night-950 px-4 py-2.5 text-sm font-semibold flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Ajouter une mesure
          </button>
        </div>
      </div>

      <ExperienceLevelBar level={experienceLevel} onChange={setExperienceLevel} />
      <DetailTabs active={activeTab} onChange={setActiveTab} />

      {showFillForm && (
        <FillLevelPanel
          waterBody={waterBody}
          onSaved={async () => {
            await onWaterBodyChanged();
            setShowFillForm(false);
          }}
          onCancel={() => setShowFillForm(false)}
        />
      )}

      {showWaterExchangeForm && (
        <WaterExchangePanel
          waterBody={waterBody}
          onSaved={async () => {
            await onWaterBodyChanged();
            setShowWaterExchangeForm(false);
          }}
          onCancel={() => setShowWaterExchangeForm(false)}
        />
      )}

      {showMeasurementForm && (
        <MeasurementPanel
          waterBodyId={waterBody.id}
          experienceLevel={experienceLevel}
          initialMetric={measurementMetric}
          onSaved={async () => {
            await refetchMeasurements();
            setMeasurementMetric(null);
            setShowMeasurementForm(false);
          }}
          onCancel={() => {
            setMeasurementMetric(null);
            setShowMeasurementForm(false);
          }}
        />
      )}

      {measurementError && (
        <div className="surface border border-coral-500/40 p-4 text-sm text-coral-300">
          {measurementError}
        </div>
      )}

      <WaterTankViz
        waterBody={waterBody}
        latestMeasurements={latest}
        livestock={ecology.livestock}
        recentOperations={ecology.recent_operations}
      />

      <div>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="section-title">Paramètres physico-chimiques</h2>
            <p className="text-xs text-slate-500 mt-1">Les symboles, unités et formules sont détaillés dans le Lexique scientifique.</p>
          </div>
          <span className="text-xs text-slate-500 flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" />
            Mesures N5 locales
          </span>
        </div>
        {measLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
            {[...Array(6)].map((_, index) => (
              <div key={index} className="skeleton h-28" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
            {visibleMetricList.map((info) => {
              const value = latest[info.key];
              const series = getMetricSeries(
                measurements,
                info.key as Metric,
              );
              if (
                value === null ||
                value === undefined ||
                series.length === 0
              ) {
                return (
                  <div key={info.key} className="kpi-card opacity-70">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs text-slate-400 uppercase tracking-wider">
                        {info.label}
                      </p>
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => openMeasurementFormForMetric(info.key)}
                          title={`Ajouter une mesure de ${info.label}`}
                          aria-label={`Ajouter une mesure de ${info.label}`}
                          className="w-7 h-7 rounded-full border border-night-600 text-teal-300 inline-flex items-center justify-center font-bold text-base leading-none"
                        >
                          +
                        </button>
                        <button
                          type="button"
                          onClick={() => onOpenGlossaryForMetric(info.key)}
                          title={`Ouvrir ${info.label} dans le lexique`}
                          className="w-7 h-7 rounded-full border border-night-600 text-teal-300 inline-flex items-center justify-center font-bold text-xs"
                        >
                          ?
                        </button>
                        <button
                          type="button"
                          onClick={() => setSelectedMetricDetail(info.key)}
                          title={`Voir l’évolution détaillée de ${info.label}`}
                          className="w-7 h-7 rounded-full border border-night-600 text-slate-400 inline-flex items-center justify-center"
                        >
                          <TrendingUp className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <p className="text-slate-500 text-sm mt-2">
                      Aucune donnée
                    </p>
                  </div>
                );
              }
              return (
                <MetricCard
                  key={info.key}
                  metric={info.key as Metric}
                  currentValue={value}
                  data={series}
                  onAddMeasurement={openMeasurementFormForMetric}
                  onOpenGlossary={onOpenGlossaryForMetric}
                  onOpenDetails={(metric) => setSelectedMetricDetail(metric)}
                />
              );
            })}
          </div>
        )}
      </div>

      <div>
        <h2 className="section-title mb-3 flex items-center gap-2">
          <Calendar className="w-4.5 h-4.5 text-teal-400" />
          Historique des mesures
        </h2>
        <div className="surface overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-night-700/40 text-xs text-slate-400 uppercase tracking-wider">
                  <th className="text-left p-3 font-medium">
                    Paramètre
                  </th>
                  <th className="text-right p-3 font-medium">
                    Valeur
                  </th>
                  <th className="text-right p-3 font-medium">
                    Référence
                  </th>
                  <th className="text-left p-3 font-medium">Date</th>
                  <th className="text-right p-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {measurements.length === 0 && (
                  <tr>
                    <td
                      colSpan={5}
                      className="p-4 text-slate-500 text-center"
                    >
                      Aucune mesure enregistrée.
                    </td>
                  </tr>
                )}
                {[...measurements]
                  .reverse()
                  .slice(0, 20)
                  .map((measurement) => {
                    const info =
                      METRICS[measurement.metric as Metric];
                    return (
                      <tr
                        key={measurement.id}
                        className="border-b border-night-800/40 hover:bg-night-800/30 transition-colors"
                      >
                        <td className="p-3 text-slate-300">
                          {info?.label ?? measurement.metric}
                        </td>
                        <td className="p-3 text-right font-mono text-white">
                          {measurement.value} {measurement.unit}
                        </td>
                        <td className="p-3 text-right text-xs text-slate-500">
                          {info?.contextual
                            ? 'Selon espèces / contexte'
                            : `${info?.ideal[0]}–${info?.ideal[1]}${info?.unit ?? ''}`}
                        </td>
                        <td className="p-3 text-xs text-slate-500">
                          {new Date(
                            measurement.recorded_at,
                          ).toLocaleString('fr-FR', {
                            day: '2-digit',
                            month: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </td>
                        <td className="p-3">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              type="button"
                              onClick={() => openMeasurementFormForMetric(measurement.metric as Metric)}
                              title="Ajouter une nouvelle mesure"
                              aria-label={`Ajouter une mesure de ${info?.label ?? measurement.metric}`}
                              className="w-7 h-7 rounded-full border border-night-600 text-teal-300 inline-flex items-center justify-center font-bold text-base leading-none"
                            >
                              +
                            </button>
                            <button
                              type="button"
                              onClick={() => onOpenGlossaryForMetric(measurement.metric as Metric)}
                              title="Ouvrir dans le lexique"
                              aria-label={`Ouvrir ${info?.label ?? measurement.metric} dans le lexique`}
                              className="w-7 h-7 rounded-full border border-night-600 text-teal-300 inline-flex items-center justify-center font-bold text-xs"
                            >
                              ?
                            </button>
                            <button
                              type="button"
                              onClick={() => setSelectedMetricDetail(measurement.metric as Metric)}
                              title="Voir l’évolution détaillée"
                              aria-label={`Voir l’évolution détaillée de ${info?.label ?? measurement.metric}`}
                              className="w-7 h-7 rounded-full border border-night-600 text-slate-400 hover:text-white inline-flex items-center justify-center"
                            >
                              <TrendingUp className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

function ExperienceLevelBar({
  level,
  onChange,
}: {
  level: ExperienceLevel;
  onChange: (level: ExperienceLevel) => void;
}) {
  const levels: ExperienceLevel[] = ['beginner', 'intermediate', 'advanced'];
  return (
    <div className="surface p-4">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-500">Niveau d’affichage</p>
          <p className="text-sm text-slate-300 mt-1">{EXPERIENCE_LEVEL_DESCRIPTIONS[level]}</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {levels.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => onChange(item)}
              className={`rounded-xl px-3 py-2 text-sm border transition-colors ${
                level === item
                  ? 'bg-teal-500/15 border-teal-500/30 text-teal-300'
                  : 'bg-night-900/40 border-night-700 text-slate-400 hover:text-white'
              }`}
            >
              {EXPERIENCE_LEVEL_LABELS[item]}
            </button>
          ))}
        </div>
      </div>
      <p className="text-xs text-slate-600 mt-2">
        Ce réglage adapte uniquement la quantité d’information affichée. Il ne modifie ni les données enregistrées ni les contrats scientifiques.
      </p>
    </div>
  );
}

function DetailTabs({
  active,
  onChange,
}: {
  active: 'overview' | 'equipment' | 'ecosystem';
  onChange: (value: 'overview' | 'equipment' | 'ecosystem') => void;
}) {
  return (
    <div className="flex gap-2 border-b border-night-700/40 pb-3">
      <button
        onClick={() => onChange('overview')}
        className={`rounded-xl px-4 py-2 text-sm font-medium transition-colors ${
          active === 'overview'
            ? 'bg-teal-500/15 text-teal-300 border border-teal-500/30'
            : 'text-slate-400 hover:text-white bg-night-900/40'
        }`}
      >
        Vue d'ensemble
      </button>
      <button
        onClick={() => onChange('ecosystem')}
        className={`rounded-xl px-4 py-2 text-sm font-medium transition-colors ${
          active === 'ecosystem'
            ? 'bg-teal-500/15 text-teal-300 border border-teal-500/30'
            : 'text-slate-400 hover:text-white bg-night-900/40'
        }`}
      >
        Écosystème & flux
      </button>
      <button
        onClick={() => onChange('equipment')}
        className={`rounded-xl px-4 py-2 text-sm font-medium transition-colors flex items-center gap-2 ${
          active === 'equipment'
            ? 'bg-teal-500/15 text-teal-300 border border-teal-500/30'
            : 'text-slate-400 hover:text-white bg-night-900/40'
        }`}
      >
        <Wrench className="w-4 h-4" />
        Matériel
      </button>
    </div>
  );
}

function FillLevelPanel({
  waterBody,
  onSaved,
  onCancel,
}: {
  waterBody: WaterBody;
  onSaved: () => Promise<void>;
  onCancel: () => void;
}) {
  const [fillPercent, setFillPercent] = useState(
    Math.max(0, Math.min(100, waterBody.fill_percent)),
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const targetLiters = waterBody.capacity_liters * fillPercent / 100;

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await setFillLevel(waterBody.id, { fill_percent: fillPercent });
      await onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="surface p-5 border border-teal-500/30 space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="section-title flex items-center gap-2">
            <Gauge className="w-4 h-4 text-teal-400" /> Niveau de remplissage
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Capacité nominale {waterBody.capacity_liters.toFixed(1)} L. Le niveau enregistré devient une observation N5.
          </p>
        </div>
        <button onClick={onCancel} className="p-2 text-slate-500 hover:text-white"><X className="w-4 h-4" /></button>
      </div>
      <input
        type="range"
        min="0"
        max="100"
        step="0.5"
        value={fillPercent}
        onChange={(event) => setFillPercent(Number(event.target.value))}
        className="w-full accent-teal-500"
      />
      <div className="grid grid-cols-2 gap-3">
        <label className="text-xs text-slate-400">
          Remplissage (%)
          <input
            type="number"
            min="0"
            max="100"
            step="0.5"
            value={fillPercent}
            onChange={(event) => setFillPercent(Math.max(0, Math.min(100, Number(event.target.value))))}
            className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white"
          />
        </label>
        <div className="rounded-xl bg-night-900/50 border border-night-700 p-3">
          <p className="text-xs text-slate-500">Volume d'eau correspondant</p>
          <p className="text-xl font-mono text-white mt-1">{targetLiters.toFixed(1)} L</p>
        </div>
      </div>
      {error && <p className="text-sm text-coral-300">{error}</p>}
      <div className="flex justify-end">
        <button onClick={() => void save()} disabled={saving} className="rounded-xl bg-teal-500 text-night-950 px-4 py-2.5 text-sm font-semibold disabled:opacity-50">
          {saving ? 'Enregistrement…' : 'Enregistrer le niveau'}
        </button>
      </div>
    </div>
  );
}

function WaterExchangePanel({
  waterBody,
  onSaved,
  onCancel,
}: {
  waterBody: WaterBody;
  onSaved: () => Promise<void>;
  onCancel: () => void;
}) {
  const { data: ecology } = useEcology(waterBody.id);
  const [removed, setRemoved] = useState('');
  const [replacement, setReplacement] = useState('');
  const [waterSourceId, setWaterSourceId] = useState('');
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const removedValue = Number(removed || 0);
  const replacementValue = Number(replacement || 0);
  const resulting = waterBody.current_volume_liters - removedValue + replacementValue;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!Number.isFinite(removedValue) || !Number.isFinite(replacementValue) || removedValue < 0 || replacementValue < 0) {
      setError('Les volumes doivent être des nombres positifs ou nuls.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await recordWaterExchange(waterBody.id, {
        removed_volume_liters: removedValue,
        replacement_volume_liters: replacementValue,
        water_source_id: waterSourceId || null,
        note: note.trim(),
      });
      await onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="surface p-5 border border-cyan-500/30">
      <div className="flex items-center justify-between gap-4 mb-4">
        <div>
          <h2 className="section-title flex items-center gap-2"><RefreshCw className="w-4 h-4 text-cyan-400" /> Changement d'eau</h2>
          <p className="text-xs text-slate-500 mt-1">L'intervention est enregistrée comme WaterExchangeInterventionV1 puis enveloppée par N5.</p>
        </div>
        <button onClick={onCancel} className="p-2 text-slate-500 hover:text-white"><X className="w-4 h-4" /></button>
      </div>
      <form onSubmit={submit} className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <label className="text-xs text-slate-400">Volume retiré (L)<input value={removed} onChange={(e) => setRemoved(e.target.value)} inputMode="decimal" className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label>
        <label className="text-xs text-slate-400">Volume ajouté (L)<input value={replacement} onChange={(e) => setReplacement(e.target.value)} inputMode="decimal" className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label>
        <label className="text-xs text-slate-400">Eau de remplacement<select value={waterSourceId} onChange={(e) => setWaterSourceId(e.target.value)} className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white"><option value="">Non renseignée</option>{ecology.water_sources.map((source) => <option key={source.id} value={source.id}>{source.name}</option>)}</select></label>
        <div className="rounded-xl bg-night-900/50 border border-night-700 p-3">
          <p className="text-xs text-slate-500">Volume après opération</p>
          <p className="text-xl font-mono text-white mt-1">{Number.isFinite(resulting) ? resulting.toFixed(1) : '—'} L</p>
        </div>
        <label className="md:col-span-4 text-xs text-slate-400">Note facultative<input value={note} onChange={(e) => setNote(e.target.value)} className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" placeholder="Ex. changement hebdomadaire, eau reposée…" /></label>
        <p className="md:col-span-4 text-xs text-amber-300/80">{waterSourceId ? "Le profil d’eau est référencé et conservé avec l’intervention. La propagation chimique automatique reste différée tant que le moteur de mélange n’est pas validé." : "Aucun profil d’eau n’est sélectionné : l’effet chimique du changement d’eau restera indéterminé."}</p>
        {error && <p className="md:col-span-4 text-sm text-coral-300">{error}</p>}
        <div className="md:col-span-4 flex justify-end"><button disabled={saving} type="submit" className="rounded-xl bg-cyan-400 text-night-950 px-4 py-2.5 text-sm font-semibold disabled:opacity-50">{saving ? 'Enregistrement…' : "Enregistrer le changement d'eau"}</button></div>
      </form>
    </div>
  );
}

function EquipmentPanel({ waterBodyId, experienceLevel }: { waterBodyId: string; experienceLevel: ExperienceLevel }) {
  const { data, loading, error, refetch } = useEquipment(waterBodyId);
  const [showForm, setShowForm] = useState(false);
  const [equipmentType, setEquipmentType] = useState<EquipmentType>('water_pump');
  const [name, setName] = useState('');
  const [manufacturer, setManufacturer] = useState('');
  const [model, setModel] = useState('');
  const [power, setPower] = useState('');
  const [runtime, setRuntime] = useState('24');
  const [flow, setFlow] = useState('');
  const [measuredFlow, setMeasuredFlow] = useState('');
  const [spectrum, setSpectrum] = useState('');
  const [colorTemperature, setColorTemperature] = useState('');
  const [parSurface, setParSurface] = useState('');
  const [parBottom, setParBottom] = useState('');
  const [filterMedia, setFilterMedia] = useState('');
  const [mediaVolume, setMediaVolume] = useState('');
  const [specificSurface, setSpecificSurface] = useState('');
  const [biofilterMaturity, setBiofilterMaturity] = useState<'unknown' | 'new' | 'cycling' | 'mature' | 'disturbed'>('unknown');
  const [tanCapacity, setTanCapacity] = useState('');
  const [inoculated, setInoculated] = useState(false);
  const [lastMaintenance, setLastMaintenance] = useState('');
  const [inServiceSince, setInServiceSince] = useState('');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const showIntermediate = experienceLevel !== 'beginner';
  const showAdvanced = experienceLevel === 'advanced';

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) {
      setFormError('Un nom de matériel est requis.');
      return;
    }
    const numberOrNull = (raw: string) => raw.trim() ? Number(raw) : null;
    setSaving(true);
    setFormError(null);
    try {
      await addEquipment(waterBodyId, {
        equipment_type: equipmentType,
        name: name.trim(),
        manufacturer: manufacturer.trim(),
        model: model.trim(),
        power_watts: numberOrNull(power),
        daily_runtime_hours: numberOrNull(runtime),
        in_service_since: inServiceSince || null,
        flow_lph: numberOrNull(flow),
        measured_flow_lph: numberOrNull(measuredFlow),
        spectrum: spectrum.trim(),
        color_temperature_k: numberOrNull(colorTemperature),
        par_surface_umol_m2_s: numberOrNull(parSurface),
        par_bottom_umol_m2_s: numberOrNull(parBottom),
        filter_media: filterMedia.trim(),
        media_volume_liters: numberOrNull(mediaVolume),
        specific_surface_m2_per_l: numberOrNull(specificSurface),
        biofilter_maturity: equipmentType === 'filter' ? biofilterMaturity : 'unknown',
        tan_capacity_mg_n_day: numberOrNull(tanCapacity),
        inoculated: equipmentType === 'filter' ? inoculated : null,
        last_maintenance_at: lastMaintenance || null,
        notes: notes.trim(),
      });
      setName(''); setManufacturer(''); setModel(''); setPower(''); setFlow(''); setMeasuredFlow(''); setSpectrum(''); setColorTemperature(''); setParSurface(''); setParBottom(''); setFilterMedia(''); setMediaVolume(''); setSpecificSurface(''); setBiofilterMaturity('unknown'); setTanCapacity(''); setInoculated(false); setLastMaintenance(''); setInServiceSince(''); setNotes('');
      await refetch();
      setShowForm(false);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  const remove = async (equipmentId: string) => {
    setFormError(null);
    try {
      await deleteEquipment(waterBodyId, equipmentId);
      await refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-4">
        <div><h2 className="section-title">Matériel du milieu</h2><p className="text-xs text-slate-500 mt-1">Pompes, éclairage, filtration, chauffage, capteurs et autres équipements.</p></div>
        <button onClick={() => setShowForm((v) => !v)} className="rounded-xl bg-teal-500 text-night-950 px-4 py-2.5 text-sm font-semibold flex items-center gap-2"><Plus className="w-4 h-4" /> Ajouter du matériel</button>
      </div>
      {showForm && (
        <form onSubmit={submit} className="surface p-5 border border-teal-500/30 grid grid-cols-1 md:grid-cols-3 gap-3">
          <label className="text-xs text-slate-400">Type<select value={equipmentType} onChange={(e) => setEquipmentType(e.target.value as EquipmentType)} className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white">{Object.entries(EQUIPMENT_TYPE_LABELS).map(([key,label]) => <option key={key} value={key}>{label}</option>)}</select></label>
          <label className="text-xs text-slate-400">Nom<input value={name} onChange={(e) => setName(e.target.value)} className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" placeholder="Ex. Pompe principale" /></label>
          {showIntermediate && <label className="text-xs text-slate-400">Fabricant<input value={manufacturer} onChange={(e) => setManufacturer(e.target.value)} className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label>}
          <label className="text-xs text-slate-400">Modèle<input value={model} onChange={(e) => setModel(e.target.value)} className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" placeholder="Ex. Sera 110" /></label>
          <label className="text-xs text-slate-400">Consommation (W)<input value={power} onChange={(e) => setPower(e.target.value)} inputMode="decimal" className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label>
          <label className="text-xs text-slate-400">Fonctionnement (h/jour)<input value={runtime} onChange={(e) => setRuntime(e.target.value)} inputMode="decimal" className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label>
          {(equipmentType === 'water_pump' || equipmentType === 'air_pump' || equipmentType === 'filter') && <><label className="text-xs text-slate-400">Débit nominal (L/h)<input value={flow} onChange={(e) => setFlow(e.target.value)} inputMode="decimal" className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label>{showIntermediate && <label className="text-xs text-slate-400">Débit mesuré (L/h)<input value={measuredFlow} onChange={(e) => setMeasuredFlow(e.target.value)} inputMode="decimal" className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label>}</>}
          {equipmentType === 'lighting' && showIntermediate && <><label className="text-xs text-slate-400 md:col-span-2">Spectre / caractéristiques lumineuses<input value={spectrum} onChange={(e) => setSpectrum(e.target.value)} className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" placeholder="Ex. 6500 K, rouge 660 nm, bleu 450 nm…" /></label><label className="text-xs text-slate-400">Température de couleur (K)<input value={colorTemperature} onChange={(e) => setColorTemperature(e.target.value)} inputMode="decimal" className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label>{showAdvanced && <><label className="text-xs text-slate-400">PAR / PPFD surface (µmol photons/m²/s)<input value={parSurface} onChange={(e) => setParSurface(e.target.value)} inputMode="decimal" className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label><label className="text-xs text-slate-400">PAR / PPFD fond (µmol photons/m²/s)<input value={parBottom} onChange={(e) => setParBottom(e.target.value)} inputMode="decimal" className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label></>}</>}
          {equipmentType === 'filter' && showIntermediate && <><label className="text-xs text-slate-400">Média filtrant<input value={filterMedia} onChange={(e) => setFilterMedia(e.target.value)} className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" placeholder="Mousse 30 PPI, pouzzolane…" /></label><label className="text-xs text-slate-400">Volume média (L)<input value={mediaVolume} onChange={(e) => setMediaVolume(e.target.value)} inputMode="decimal" className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label><label className="text-xs text-slate-400">Maturité biologique<select value={biofilterMaturity} onChange={(e) => setBiofilterMaturity(e.target.value as typeof biofilterMaturity)} className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white"><option value="unknown">Inconnue</option><option value="new">Neuf</option><option value="cycling">En cyclage</option><option value="mature">Mature</option><option value="disturbed">Perturbé / après entretien</option></select></label><label className="text-xs text-slate-400 flex items-center gap-2 mt-6"><input type="checkbox" checked={inoculated} onChange={(e) => setInoculated(e.target.checked)} /> Média inoculé</label><label className="text-xs text-slate-400">Dernier entretien<input type="date" value={lastMaintenance} onChange={(e) => setLastMaintenance(e.target.value)} className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label>{showAdvanced && <><label className="text-xs text-slate-400">Surface spécifique (m²/L)<input value={specificSurface} onChange={(e) => setSpecificSurface(e.target.value)} inputMode="decimal" className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label><label className="text-xs text-slate-400">Capacité TAN mesurée (mg N/j)<input value={tanCapacity} onChange={(e) => setTanCapacity(e.target.value)} inputMode="decimal" className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label></>}</>}
          {showIntermediate && <label className="text-xs text-slate-400">En fonction depuis<input type="date" value={inServiceSince} onChange={(e) => setInServiceSince(e.target.value)} className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label>}
          <label className="md:col-span-3 text-xs text-slate-400">Notes<input value={notes} onChange={(e) => setNotes(e.target.value)} className="mt-1.5 w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white" /></label>
          {formError && <p className="md:col-span-3 text-sm text-coral-300">{formError}</p>}
          <div className="md:col-span-3 flex justify-end"><button disabled={saving} className="rounded-xl bg-teal-500 text-night-950 px-4 py-2.5 text-sm font-semibold disabled:opacity-50" type="submit">{saving ? 'Ajout…' : 'Ajouter'}</button></div>
        </form>
      )}
      {error && <div className="surface p-4 text-sm text-coral-300">{error}</div>}
      {loading ? <div className="skeleton h-32" /> : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {data.length === 0 && <div className="surface p-6 text-sm text-slate-500">Aucun matériel référencé pour ce milieu.</div>}
          {data.map((item) => (
            <div key={item.id} className="surface p-5">
              <div className="flex items-start justify-between gap-3">
                <div><p className="text-xs text-teal-400 uppercase tracking-wider">{EQUIPMENT_TYPE_LABELS[item.equipment_type]}</p><h3 className="font-semibold text-white mt-1">{item.name}</h3><p className="text-xs text-slate-500 mt-1">{[item.manufacturer, item.model].filter(Boolean).join(' · ') || 'Modèle non renseigné'}</p></div>
                <button onClick={() => void remove(item.id)} title="Supprimer" className="p-2 text-slate-600 hover:text-coral-400"><Trash2 className="w-4 h-4" /></button>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                {item.flow_lph !== null && <div className="rounded-lg bg-night-900/50 p-2"><span className="text-slate-500">Débit nominal</span><p className="font-mono text-white">{item.flow_lph} L/h</p></div>}
                {item.measured_flow_lph !== null && <div className="rounded-lg bg-night-900/50 p-2"><span className="text-slate-500">Débit mesuré</span><p className="font-mono text-white">{item.measured_flow_lph} L/h</p></div>}
                {item.par_surface_umol_m2_s !== null && <div className="rounded-lg bg-night-900/50 p-2"><span className="text-slate-500">PAR surface</span><p className="font-mono text-white">{item.par_surface_umol_m2_s} µmol/m²/s</p></div>}
                {item.par_bottom_umol_m2_s !== null && <div className="rounded-lg bg-night-900/50 p-2"><span className="text-slate-500">PAR fond</span><p className="font-mono text-white">{item.par_bottom_umol_m2_s} µmol/m²/s</p></div>}
                {item.media_volume_liters !== null && <div className="rounded-lg bg-night-900/50 p-2"><span className="text-slate-500">Média filtrant</span><p className="font-mono text-white">{item.media_volume_liters} L</p></div>}
                {item.specific_surface_m2_per_l !== null && <div className="rounded-lg bg-night-900/50 p-2"><span className="text-slate-500">Surface spécifique</span><p className="font-mono text-white">{item.specific_surface_m2_per_l} m²/L</p></div>}{item.equipment_type === 'filter' && <div className="rounded-lg bg-night-900/50 p-2"><span className="text-slate-500">Maturité biofiltre</span><p className="text-white">{item.biofilter_maturity}</p></div>}{item.tan_capacity_mg_n_day !== null && <div className="rounded-lg bg-night-900/50 p-2"><span className="text-slate-500">Capacité TAN</span><p className="font-mono text-white">{item.tan_capacity_mg_n_day} mg N/j</p></div>}
                {item.power_watts !== null && <div className="rounded-lg bg-night-900/50 p-2"><span className="text-slate-500">Puissance</span><p className="font-mono text-white">{item.power_watts} W</p></div>}
                {item.daily_runtime_hours !== null && <div className="rounded-lg bg-night-900/50 p-2"><span className="text-slate-500">Durée</span><p className="font-mono text-white">{item.daily_runtime_hours} h/j</p></div>}
                {item.daily_energy_wh !== null && <div className="rounded-lg bg-night-900/50 p-2"><span className="text-slate-500">Énergie/jour</span><p className="font-mono text-white">{item.daily_energy_wh.toFixed(1)} Wh</p></div>}
                {item.annual_energy_kwh !== null && <div className="rounded-lg bg-night-900/50 p-2"><span className="text-slate-500">Énergie/an</span><p className="font-mono text-white">{item.annual_energy_kwh.toFixed(1)} kWh</p></div>}
                {item.in_service_since && <div className="rounded-lg bg-night-900/50 p-2"><span className="text-slate-500">Depuis</span><p className="text-white">{new Date(`${item.in_service_since}T00:00:00`).toLocaleDateString('fr-FR')}</p></div>}
              </div>
              {item.spectrum && <p className="mt-3 text-xs text-slate-400"><span className="text-slate-500">Spectre :</span> {item.spectrum}</p>}
              {item.filter_media && <p className="mt-2 text-xs text-slate-400"><span className="text-slate-500">Média :</span> {item.filter_media}{item.inoculated ? ' · inoculé' : ''}</p>}
              {item.last_maintenance_at && <p className="mt-2 text-xs text-slate-500">Dernier entretien : {new Date(`${item.last_maintenance_at}T00:00:00`).toLocaleDateString('fr-FR')}</p>}
              {item.notes && <p className="mt-2 text-xs text-slate-500">{item.notes}</p>}
            </div>
          ))}
        </div>
      )}
      {formError && !showForm && <p className="text-sm text-coral-300">{formError}</p>}
    </div>
  );
}

function MeasurementPanel({
  waterBodyId,
  experienceLevel,
  initialMetric,
  onSaved,
  onCancel,
}: {
  waterBodyId: string;
  experienceLevel: ExperienceLevel;
  initialMetric?: Metric | null;
  onSaved: () => Promise<void>;
  onCancel: () => void;
}) {
  const [metric, setMetric] = useState<Metric>(initialMetric ?? 'temperature');
  const [value, setValue] = useState('');
  const [uncertainty, setUncertainty] = useState('0');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const valueInputRef = useRef<HTMLInputElement>(null);
  const visibleMetrics = useMemo(() => {
    const base = METRICS_BY_EXPERIENCE_LEVEL[experienceLevel];
    if (initialMetric && !base.includes(initialMetric)) {
      return [initialMetric, ...base];
    }
    return base;
  }, [experienceLevel, initialMetric]);

  useEffect(() => {
    if (initialMetric) {
      setMetric(initialMetric);
      return;
    }
    if (!visibleMetrics.includes(metric)) {
      setMetric(visibleMetrics[0] ?? 'temperature');
    }
  }, [initialMetric, metric, visibleMetrics]);

  useEffect(() => {
    valueInputRef.current?.focus();
  }, [initialMetric]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const parsedValue = Number(value);
    const parsedUncertainty = Number(uncertainty);
    if (
      !Number.isFinite(parsedValue) ||
      !Number.isFinite(parsedUncertainty) ||
      parsedUncertainty < 0
    ) {
      setError('Valeur numérique et incertitude positive requises.');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await addMeasurement(waterBodyId, {
        metric,
        value: parsedValue,
        uncertainty: parsedUncertainty,
      });
      await onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  const metricInfo = METRICS[metric];

  return (
    <div id="measurement-entry-panel" className="surface p-5 border border-teal-500/30">
      <div className="flex items-center justify-between gap-4 mb-4">
        <div>
          <h2 className="section-title">Nouvelle mesure</h2>
          <p className="text-xs text-slate-500 mt-1">
            La mesure sera persistée comme observation canonique N5. Les options métrologiques détaillées apparaissent en mode Avancé.
          </p>
        </div>
        <button
          onClick={onCancel}
          className="p-2 text-slate-500 hover:text-white"
          title="Fermer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <form
        onSubmit={handleSubmit}
        className="grid grid-cols-1 md:grid-cols-4 gap-3"
      >
        <div>
          <label className="text-xs text-slate-400 block mb-1.5">
            Paramètre
          </label>
          <select
            value={metric}
            onChange={(event) =>
              setMetric(event.target.value as Metric)
            }
            className="w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white outline-none focus:border-teal-500/60"
          >
            {visibleMetrics.map((key) => (
              <option key={key} value={key}>
                {METRICS[key].label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1.5">
            Valeur {metricInfo.unit ? `(${metricInfo.unit})` : ''}
          </label>
          <input
            ref={valueInputRef}
            value={value}
            onChange={(event) => setValue(event.target.value)}
            inputMode="decimal"
            placeholder="0"
            className="w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white outline-none focus:border-teal-500/60"
          />
        </div>
        {experienceLevel === 'advanced' && (
          <div>
            <label className="text-xs text-slate-400 block mb-1.5">
              Incertitude
            </label>
            <input
              value={uncertainty}
              onChange={(event) => setUncertainty(event.target.value)}
              inputMode="decimal"
              className="w-full rounded-xl bg-night-900/70 border border-night-700 px-3 py-2.5 text-sm text-white outline-none focus:border-teal-500/60"
            />
          </div>
        )}
        <div className="flex items-end">
          <button
            type="submit"
            disabled={saving}
            className="w-full rounded-xl bg-teal-500 text-night-950 px-4 py-2.5 text-sm font-semibold disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            Enregistrer
          </button>
        </div>

        {error && (
          <p className="md:col-span-4 text-sm text-coral-300">{error}</p>
        )}
      </form>
    </div>
  );
}
