export function MetricSparkline({ points }: { points: number[] }) {
  const maxValue = Math.max(...points);
  const minValue = Math.min(...points);
  const stepX = 100 / Math.max(points.length - 1, 1);

  const path = points
    .map((value, index) => {
      const x = index * stepX;
      const y = 100 - ((value - minValue) / Math.max(maxValue - minValue, 1)) * 100;
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ');

  return (
    <svg viewBox="0 0 100 100" className="h-10 w-full overflow-visible">
      <path d={path} fill="none" stroke="#6EE06A" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
