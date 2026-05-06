interface Props {
  normalCount: number;
  anomalyCount: number;
}

export function DistributionChart({ normalCount, anomalyCount }: Props) {
  const total = normalCount + anomalyCount || 1;
  const normalPct = Math.round((normalCount / total) * 100);
  const anomalyPct = Math.round((anomalyCount / total) * 100);

  return (
    <div className="space-y-4">
      <div className="flex h-8 w-full overflow-hidden rounded-md">
        <div className="bg-emerald-500" style={{ width: `${normalPct}%` }} />
        <div className="bg-red-500" style={{ width: `${anomalyPct}%` }} />
      </div>
      <div className="flex justify-between text-sm">
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full bg-emerald-500" />
          <span>Normal: {normalCount} ({normalPct}%)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full bg-red-500" />
          <span>Anomaly: {anomalyCount} ({anomalyPct}%)</span>
        </div>
      </div>
    </div>
  );
}
