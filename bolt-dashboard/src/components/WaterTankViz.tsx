import type { WaterBody } from '@/lib/types';
import { StatusDot } from './StatusBadge';
import { Waves, Volume2, Calendar } from 'lucide-react';

interface WaterTankVizProps {
  waterBody: WaterBody;
  fillPercent?: number;
}

export function WaterTankViz({ waterBody, fillPercent = 72 }: WaterTankVizProps) {
  const statusColor =
    waterBody.status === 'stable' ? 'from-teal-500/30 to-teal-600/20 border-teal-500/30'
    : waterBody.status === 'warning' ? 'from-amber-500/30 to-amber-600/20 border-amber-500/30'
    : 'from-coral-500/30 to-coral-600/20 border-coral-500/30';

  const waterColor =
    waterBody.status === 'stable' ? 'from-teal-400/40 to-teal-600/30'
    : waterBody.status === 'warning' ? 'from-amber-400/40 to-amber-600/30'
    : 'from-coral-400/40 to-coral-600/30';

  return (
    <div className={`relative rounded-2xl border bg-gradient-to-b ${statusColor} p-5 overflow-hidden`}>
      <div className="absolute inset-0 bg-grid opacity-30" />
      <div className="relative z-10 flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <StatusDot status={waterBody.status} />
            <h3 className="font-display font-bold text-white text-lg">{waterBody.name}</h3>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="flex items-center gap-1"><Waves className="w-3 h-3" /> {waterBody.type}</span>
            <span className="flex items-center gap-1"><Volume2 className="w-3 h-3" /> {waterBody.volume_liters} L</span>
          </div>
        </div>
      </div>

      {/* Tank visualization */}
      <div className="relative h-40 rounded-xl border border-night-600/50 bg-night-950/60 overflow-hidden">
        {/* Water fill */}
        <div
          className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t ${waterColor} transition-all duration-1000`}
          style={{ height: `${fillPercent}%` }}
        >
          {/* Water surface waves */}
          <svg className="absolute top-0 left-0 w-full -translate-y-1/2" viewBox="0 0 400 20" preserveAspectRatio="none" style={{ height: '20px' }}>
            <path
              d="M0,10 Q50,0 100,10 T200,10 T300,10 T400,10 V20 H0 Z"
              fill="currentColor"
              className={waterBody.status === 'stable' ? 'text-teal-400/30' : waterBody.status === 'warning' ? 'text-amber-400/30' : 'text-coral-400/30'}
            />
          </svg>
          {/* Bubbles */}
          <div className="absolute inset-0 overflow-hidden">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="absolute rounded-full bg-white/10 animate-pulse-slow"
                style={{
                  width: `${4 + Math.random() * 6}px`,
                  height: `${4 + Math.random() * 6}px`,
                  left: `${10 + i * 15}%`,
                  bottom: `${Math.random() * 60}%`,
                  animationDelay: `${i * 0.5}s`,
                }}
              />
            ))}
          </div>
        </div>

        {/* Tank glass reflection */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-0 w-1/4 h-full bg-gradient-to-r from-white/5 to-transparent" />
        </div>
      </div>

      <div className="relative z-10 mt-3 flex items-center justify-between text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          Mis à jour {new Date(waterBody.updated_at).toLocaleDateString('fr-FR')}
        </span>
        <span className="font-mono">Remplissage {fillPercent}%</span>
      </div>
    </div>
  );
}
