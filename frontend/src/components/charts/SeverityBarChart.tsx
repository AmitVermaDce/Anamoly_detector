interface Props {
  distribution: Record<string, number>;
}

const COLORS: Record<string, string> = {
  low: '#10b981',
  medium: '#f59e0b',
  high: '#ef4444',
};

export function SeverityChart({ distribution }: Props) {
  const entries = Object.entries(distribution);
  const max = Math.max(...entries.map(([, v]) => v), 1);

  return (
    <div className="space-y-3">
      {entries.map(([severity, count]) => (
        <div key={severity} className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="capitalize">{severity}</span>
            <span>{count}</span>
          </div>
          <div className="h-2 w-full rounded-full bg-muted">
            <div
              className="h-2 rounded-full transition-all"
              style={{
                width: `${(count / max) * 100}%`,
                backgroundColor: COLORS[severity] || '#888',
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
