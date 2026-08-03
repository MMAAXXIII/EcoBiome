function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

export function WaterTankViz({ fill }: { fill: number }) {
  const safeFill = clamp(fill, 10, 92);

  return (
    <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-b from-ecobiome-surfaceAlt to-ecobiome-background p-6 shadow-panel">
      <div className="absolute inset-x-0 top-6 h-8 bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.08),_transparent_60%)]" />
      <div className="relative flex h-[320px] items-end justify-center">
        <div className="h-full w-full rounded-[1.8rem] border border-white/5 bg-[#06121d]">
          <div
            className="absolute inset-x-6 bottom-6 rounded-[1.5rem] bg-gradient-to-b from-[#6EE06A]/70 to-[#062427] shadow-[inset_0_0_40px_rgba(0,0,0,0.25)]"
            style={{ height: `${safeFill}%` }}
          />
          <div className="absolute inset-x-0 bottom-0 h-6 bg-[radial-gradient(circle_at_bottom,_rgba(255,255,255,0.15),_transparent_55%)]" />
          <div className="absolute left-8 bottom-[calc(6%+2px)] w-2 rounded-full bg-slate-200/30 blur-sm" style={{ height: '72px' }} />
          <div className="absolute right-12 bottom-[calc(22%+2px)] w-2 rounded-full bg-slate-200/30 blur-sm" style={{ height: '56px' }} />
          <div className="absolute bottom-[calc(18%+12px)] left-[calc(50%-28px)] h-6 w-10 rounded-full bg-white/10 blur-sm" />
        </div>
      </div>
      <div className="mt-6 flex items-center justify-between text-sm text-slate-400">
        <span>Remplissage</span>
        <span>{fill}%</span>
      </div>
    </div>
  );
}
