import type { Metric } from '@/lib/types';
import { METRICS } from '@/lib/types';
import {
  Activity,
  AlertTriangle,
  Atom,
  Cloud,
  Droplet,
  FlaskConical,
  Gem,
  Hexagon,
  Mountain,
  Ruler,
  Skull,
  Sun,
  Leaf,
  Thermometer,
  Waves,
  Wind,
  Zap,
  type LucideIcon,
} from 'lucide-react';

const ICONS: Record<string, LucideIcon> = {
  Activity,
  AlertTriangle,
  Atom,
  Cloud,
  Droplet,
  FlaskConical,
  Gem,
  Hexagon,
  Mountain,
  Ruler,
  Skull,
  Sun,
  Leaf,
  Thermometer,
  Waves,
  Wind,
  Zap,
};

interface SparklineProps {
  metric: Metric;
  data: number[];
  width?: number;
  height?: number;
}

export function Sparkline({ metric, data, width = 120, height = 36 }: SparklineProps) {
  const info = METRICS[metric];
  const Icon = ICONS[info.icon] ?? Droplet;

  if (data.length === 0) {
    return <div className="h-9" />;
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const padding = 3;
  const points = data.map((value, index) => {
    const denominator = Math.max(data.length - 1, 1);
    const x = padding + (index / denominator) * (width - padding * 2);
    const y = padding + (1 - (value - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  });

  const lastValue = data[data.length - 1];
  const contextual = info.contextual === true;
  const inIdeal = !contextual && lastValue >= info.ideal[0] && lastValue <= info.ideal[1];
  const inWarning = !contextual && !inIdeal && lastValue >= info.warning[0] && lastValue <= info.warning[1];
  const strokeColor = contextual ? '#94a3b8' : inIdeal ? '#34d3a4' : inWarning ? '#fbbf24' : '#fb7185';
  const fillColor = contextual ? 'rgba(148,163,184,0.10)' : inIdeal ? 'rgba(52,211,164,0.12)' : inWarning ? 'rgba(251,191,36,0.12)' : 'rgba(251,113,133,0.12)';
  const pathD = `M ${points.join(' L ')}`;
  const areaD = `${pathD} L ${width - padding},${height - padding} L ${padding},${height - padding} Z`;
  const lastX = padding + (width - padding * 2);
  const lastY = padding + (1 - (lastValue - min) / range) * (height - padding * 2);

  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={`spark-${metric}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={fillColor} />
          <stop offset="100%" stopColor="transparent" />
        </linearGradient>
      </defs>
      <path d={areaD} fill={`url(#spark-${metric})`} />
      <path d={pathD} fill="none" stroke={strokeColor} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={lastX} cy={lastY} r="2.5" fill={strokeColor} className="animate-pulse-slow" />
      <Icon x={width - 14} y={0} width={12} height={12} className="text-slate-500 opacity-50" />
    </svg>
  );
}
