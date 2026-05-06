interface Props {
  data: Record<string, unknown>[];
  xKey: string;
  yKey: string;
}

export function TimeSeriesChart({ data, xKey, yKey }: Props) {
  const points = data.map((d) => ({
    x: typeof d[xKey] === 'string' ? new Date(d[xKey] as string).getTime() : (d[xKey] as number),
    y: typeof d[yKey] === 'string' ? parseFloat(d[yKey] as string) : (d[yKey] as number),
    isAnomaly: !!d.is_anomaly,
  }));

  const yValues = points.map((p) => p.y).filter((v) => !isNaN(v));
  const yMin = Math.min(...yValues);
  const yMax = Math.max(...yValues);
  const yRange = yMax - yMin || 1;

  const xValues = points.map((p) => p.x).filter((v) => !isNaN(v));
  const xMin = Math.min(...xValues);
  const xMax = Math.max(...xValues);
  const xRange = xMax - xMin || 1;

  const width = 800;
  const height = 320;
  const padding = 40;
  const plotW = width - padding * 2;
  const plotH = height - padding * 2;

  const toSvgX = (x: number) => padding + ((x - xMin) / xRange) * plotW;
  const toSvgY = (y: number) => height - padding - ((y - yMin) / yRange) * plotH;

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full">
        {/* Axes */}
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="currentColor" strokeOpacity={0.2} />
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="currentColor" strokeOpacity={0.2} />

        {/* Points */}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={toSvgX(p.x)}
            cy={toSvgY(p.y)}
            r={p.isAnomaly ? 4 : 2}
            fill={p.isAnomaly ? '#ef4444' : '#94a3b8'}
            opacity={p.isAnomaly ? 1 : 0.6}
          />
        ))}

        {/* X labels */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => {
          const x = xMin + t * xRange;
          const date = new Date(x).toLocaleDateString();
          return (
            <text key={t} x={toSvgX(x)} y={height - padding + 18} textAnchor="middle" fontSize="10" fill="currentColor" fillOpacity={0.6}>
              {date}
            </text>
          );
        })}

        {/* Y labels */}
        {[0, 0.5, 1].map((t) => {
          const y = yMin + t * yRange;
          return (
            <text key={t} x={padding - 8} y={toSvgY(y) + 4} textAnchor="end" fontSize="10" fill="currentColor" fillOpacity={0.6}>
              {Math.round(y).toLocaleString()}
            </text>
          );
        })}
      </svg>
    </div>
  );
}
