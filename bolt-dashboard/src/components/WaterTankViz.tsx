import { useEffect, useMemo, useState } from 'react';
import type {
  EcologyOperation,
  LivestockItem,
  Metric,
  WaterBody,
} from '@/lib/types';
import {
  evaluateBiologicalAlerts,
  getRecentFeedingVisual,
  livingTankKnownSpeciesCount,
} from '@/lib/livingTank';
import { StatusDot } from './StatusBadge';
import { Calendar, Volume2, Waves } from 'lucide-react';

interface WaterTankVizProps {
  waterBody: WaterBody;
  fillPercent?: number;
  latestMeasurements?: Partial<Record<Metric, number | null>>;
  livestock?: LivestockItem[];
  recentOperations?: EcologyOperation[];
}

function FishSilhouette({
  left,
  top,
  flip,
  scale,
}: {
  left: number;
  top: number;
  flip: boolean;
  scale: number;
}) {
  return (
    <svg
      className="absolute text-slate-100/35"
      viewBox="0 0 54 24"
      aria-hidden="true"
      style={{
        left: `${left}%`,
        top: `${top}%`,
        width: `${34 * scale}px`,
        transform: `scaleX(${flip ? -1 : 1})`,
      }}
    >
      <path
        fill="currentColor"
        d="M4 12 0 4l12 5c5-6 14-8 23-5 8 3 13 8 17 8-4 0-9 5-17 8-9 3-18 1-23-5L0 20l4-8Z"
      />
      <circle cx="39" cy="9" r="1.4" fill="rgba(2,6,23,.75)" />
    </svg>
  );
}

function FoodParticles({
  form,
  count,
  opacity,
}: {
  form: string;
  count: number;
  opacity: number;
}) {
  const isFlake = form === 'flakes' || form === 'flake';
  return (
    <div
      className="absolute inset-x-0 top-1 h-16 pointer-events-none transition-opacity duration-1000"
      style={{ opacity }}
      aria-label="Nourriture récemment distribuée"
    >
      {Array.from({ length: count }).map((_, index) => {
        const left = 8 + ((index * 37) % 84);
        const top = 2 + ((index * 17) % 38);
        const delay = (index % 7) * 0.18;
        const size = 3 + (index % 3);
        return (
          <span
            key={index}
            className={
              isFlake
                ? 'absolute bg-amber-300/80 border border-amber-100/30 animate-pulse'
                : 'absolute rounded-full bg-amber-300/80 border border-amber-100/30 animate-pulse'
            }
            style={{
              left: `${left}%`,
              top: `${top}%`,
              width: `${isFlake ? size + 2 : size}px`,
              height: `${isFlake ? Math.max(2, size - 1) : size}px`,
              transform: `rotate(${(index * 43) % 170}deg)`,
              animationDelay: `${delay}s`,
            }}
          />
        );
      })}
    </div>
  );
}

export function WaterTankViz({
  waterBody,
  fillPercent,
  latestMeasurements = {},
  livestock = [],
  recentOperations = [],
}: WaterTankVizProps) {
  const [showAlerts, setShowAlerts] = useState(false);
  const [nowMs, setNowMs] = useState(() => Date.now());

  const renderedFill = Math.max(
    0,
    Math.min(100, fillPercent ?? waterBody.fill_percent),
  );

  const alerts = useMemo(
    () => evaluateBiologicalAlerts(livestock, latestMeasurements),
    [latestMeasurements, livestock],
  );
  const feedingVisual = useMemo(
    () => getRecentFeedingVisual(recentOperations, nowMs),
    [nowMs, recentOperations],
  );
  const totalLivestock = livestock.reduce(
    (total, item) => total + Math.max(0, item.count),
    0,
  );
  const representedFish = Math.min(8, totalLivestock);
  const knownSpeciesCount = livingTankKnownSpeciesCount(livestock);

  useEffect(() => {
    if (!feedingVisual) return undefined;
    const timer = window.setInterval(() => setNowMs(Date.now()), 5000);
    return () => window.clearInterval(timer);
  }, [feedingVisual]);

  const statusColor =
    alerts.length > 0
      ? 'from-amber-500/30 to-amber-600/20 border-amber-500/40'
      : waterBody.status === 'stable'
        ? 'from-teal-500/30 to-teal-600/20 border-teal-500/30'
        : waterBody.status === 'warning'
          ? 'from-amber-500/30 to-amber-600/20 border-amber-500/30'
          : waterBody.status === 'critical'
            ? 'from-coral-500/30 to-coral-600/20 border-coral-500/30'
            : 'from-slate-500/20 to-slate-700/10 border-slate-500/20';

  const waterColor =
    waterBody.status === 'stable'
      ? 'from-teal-400/40 to-teal-600/30'
      : waterBody.status === 'warning' || alerts.length > 0
        ? 'from-amber-400/30 to-cyan-700/25'
        : waterBody.status === 'critical'
          ? 'from-coral-400/40 to-coral-600/30'
          : 'from-cyan-400/35 to-cyan-700/25';

  const waveColor =
    waterBody.status === 'stable'
      ? 'text-teal-400/30'
      : waterBody.status === 'warning' || alerts.length > 0
        ? 'text-amber-300/30'
        : waterBody.status === 'critical'
          ? 'text-coral-400/30'
          : 'text-cyan-400/25';

  return (
    <div
      className={`relative rounded-2xl border bg-gradient-to-b ${statusColor} p-5 overflow-hidden`}
    >
      <div className="absolute inset-0 bg-grid opacity-30" />
      <div className="relative z-10 flex items-start justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <StatusDot status={waterBody.status} />
            <h3 className="font-display font-bold text-white text-lg">
              {waterBody.name}
            </h3>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="flex items-center gap-1">
              <Waves className="w-3 h-3" /> {waterBody.type}
            </span>
            <span className="flex items-center gap-1">
              <Volume2 className="w-3 h-3" />{' '}
              {waterBody.current_volume_liters.toFixed(1)} /{' '}
              {waterBody.capacity_liters.toFixed(1)} L
            </span>
          </div>
        </div>

        {alerts.length > 0 && (
          <button
            type="button"
            onClick={() => setShowAlerts((value) => !value)}
            className="relative z-20 min-w-9 h-9 rounded-full bg-amber-400 text-night-950 border-2 border-amber-100/60 font-display font-black text-lg shadow-lg shadow-amber-950/30"
            title={`${alerts.length} alerte(s) biologique(s)`}
            aria-label={`${alerts.length} alerte(s) biologique(s)`}
          >
            !
            {alerts.length > 1 && (
              <span className="absolute -top-2 -right-2 min-w-5 h-5 px-1 rounded-full bg-coral-500 text-white text-[10px] leading-5 border border-night-950">
                {alerts.length}
              </span>
            )}
          </button>
        )}
      </div>

      <div className="relative h-40 rounded-xl border border-night-600/50 bg-night-950/60 overflow-hidden">
        <div
          className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t ${waterColor} transition-all duration-700`}
          style={{ height: `${renderedFill}%` }}
        >
          <svg
            className="absolute top-0 left-0 w-full -translate-y-1/2"
            viewBox="0 0 400 20"
            preserveAspectRatio="none"
            style={{ height: '20px' }}
          >
            <path
              d="M0,10 Q50,0 100,10 T200,10 T300,10 T400,10 V20 H0 Z"
              fill="currentColor"
              className={waveColor}
            />
          </svg>

          <div className="absolute inset-0 overflow-hidden">
            {Array.from({ length: 6 }).map((_, index) => (
              <div
                key={index}
                className="absolute rounded-full bg-white/10 animate-pulse-slow"
                style={{
                  width: `${4 + (index % 3) * 2}px`,
                  height: `${4 + (index % 3) * 2}px`,
                  left: `${10 + index * 15}%`,
                  bottom: `${12 + (index * 17) % 60}%`,
                  animationDelay: `${index * 0.5}s`,
                }}
              />
            ))}

            {Array.from({ length: representedFish }).map((_, index) => (
              <FishSilhouette
                key={index}
                left={8 + ((index * 23) % 76)}
                top={20 + ((index * 29) % 58)}
                flip={index % 2 === 1}
                scale={0.75 + (index % 3) * 0.12}
              />
            ))}

            {feedingVisual && (
              <FoodParticles
                form={feedingVisual.form}
                count={feedingVisual.particleCount}
                opacity={feedingVisual.opacity}
              />
            )}
          </div>

          {feedingVisual && (
            <div
              className="absolute top-2 left-2 rounded-lg bg-night-950/70 border border-amber-300/30 px-2 py-1 text-[10px] text-amber-100 backdrop-blur-sm transition-opacity duration-1000"
              style={{ opacity: feedingVisual.opacity }}
            >
              Nourrissage récent · {feedingVisual.foodName}
              {feedingVisual.amountG !== null
                ? ` · ${feedingVisual.amountG.toFixed(2)} g`
                : ''}
            </div>
          )}
        </div>

        {alerts.length > 0 && (
          <button
            type="button"
            onClick={() => setShowAlerts((value) => !value)}
            className="absolute right-3 top-3 z-20 w-10 h-10 rounded-full bg-amber-400/95 text-night-950 border-2 border-amber-100/70 font-display font-black text-xl shadow-lg animate-pulse"
            title="Afficher les alertes biologiques"
            aria-label="Afficher les alertes biologiques"
          >
            !
          </button>
        )}

        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-0 w-1/4 h-full bg-gradient-to-r from-white/5 to-transparent" />
        </div>
      </div>

      {(totalLivestock > 0 || feedingVisual || knownSpeciesCount > 0) && (
        <div className="relative z-10 mt-2 flex flex-wrap gap-2 text-[10px] text-slate-400">
          {totalLivestock > 0 && (
            <span className="rounded-full bg-night-900/50 border border-night-700 px-2 py-1">
              Population déclarée : {totalLivestock}
            </span>
          )}
          {knownSpeciesCount > 0 && (
            <span className="rounded-full bg-night-900/50 border border-night-700 px-2 py-1">
              {knownSpeciesCount} espèce(s) avec référence biologique
            </span>
          )}
          {feedingVisual && (
            <span className="rounded-full bg-amber-500/10 border border-amber-500/20 px-2 py-1 text-amber-200">
              Nourriture visible temporairement
            </span>
          )}
        </div>
      )}

      {showAlerts && alerts.length > 0 && (
        <div className="relative z-20 mt-3 space-y-2">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3"
            >
              <div className="flex items-start gap-2">
                <span className="mt-0.5 w-6 h-6 shrink-0 rounded-full bg-amber-400 text-night-950 font-black inline-flex items-center justify-center">
                  !
                </span>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-amber-100">
                    {alert.title}
                  </p>
                  <p className="text-xs text-slate-300 mt-1">
                    {alert.message}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-1">
                    {alert.evidenceNote}
                  </p>
                  <a
                    href={alert.sourceUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-block text-[10px] text-teal-300 hover:text-teal-200 mt-1"
                  >
                    Source : {alert.sourceLabel}
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="relative z-10 mt-3 flex items-center justify-between text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          Mis à jour {new Date(waterBody.updated_at).toLocaleDateString('fr-FR')}
        </span>
        <span className="font-mono">
          Remplissage {renderedFill.toFixed(1)}%
        </span>
      </div>
    </div>
  );
}
