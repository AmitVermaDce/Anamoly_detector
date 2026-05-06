import { useMemo, useState } from 'react';
import { useAlgorithms, useDetectAnomalies, useLevels, useQueries } from '@/hooks/useAnomalyDetection';
import { useAnomalyStore } from '@/store/anomalyStore';
import { AnomalyDetectionRequest } from '@/types';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { DistributionChart, SeverityChart, TimeSeriesChart } from '@/components/charts';

export function Dashboard() {
  const [queryName, setQueryName] = useState('');
  const [algorithm, setAlgorithm] = useState('isolation_forest');
  const [detectionLevel, setDetectionLevel] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [filterText, setFilterText] = useState('');

  const { data: queries = [], isLoading: queriesLoading, error: queriesError } = useQueries();
  const { data: algorithms = [], isLoading: algorithmsLoading, error: algorithmsError } = useAlgorithms();
  const { data: levels = [] } = useLevels();
  const detectMutation = useDetectAnomalies();
  const { lastResult, isLoading, error } = useAnomalyStore();

  const algorithmOptions = useMemo(() => algorithms.map((a) => ({ value: a.name, label: a.display_name })), [algorithms]);
  const queryOptions = useMemo(() => queries.map((q) => ({
    value: q,
    label: q.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
  })), [queries]);
  const levelOptions = useMemo(() => levels.map((l) => ({
    value: l.name,
    label: l.name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
  })), [levels]);

  const handleDetect = () => {
    const request: AnomalyDetectionRequest = {
      query_name: queryName,
      algorithm,
      detection_level: detectionLevel || null,
      columns: [],
      parameters: {},
      start_date: startDate || null,
      end_date: endDate || null,
    };
    detectMutation.mutate(request);
  };

  const filteredRecords = useMemo(() => {
    if (!lastResult) return [];
    if (!filterText) return lastResult.records;
    const lower = filterText.toLowerCase();
    return lastResult.records.filter((r) => Object.values(r).some((v) => String(v).toLowerCase().includes(lower)));
  }, [lastResult, filterText]);

  const timeColumn = useMemo(() => {
    if (!lastResult || lastResult.records.length === 0) return null;
    const keys = Object.keys(lastResult.records[0]);
    return keys.find((k) => /date|timestamp|time/i.test(k)) || keys[0];
  }, [lastResult]);

  const numericColumn = useMemo(() => {
    if (!lastResult || lastResult.records.length === 0) return null;
    const keys = Object.keys(lastResult.records[0]);
    return keys.find((k) => /amount|value|score|revenue|count/i.test(k))
      || keys.find((k) => typeof lastResult!.records[0][k] === 'number')
      || keys[0];
  }, [lastResult]);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <ellipse cx="12" cy="5" rx="9" ry="3" />
              <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
              <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{queriesLoading ? '...' : queries.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Algorithms</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="20" x2="18" y2="10" />
              <line x1="12" y1="20" x2="12" y2="4" />
              <line x1="6" y1="20" x2="6" y2="14" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{algorithmsLoading ? '...' : algorithms.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Records</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
              <line x1="8" y1="2" x2="8" y2="6" />
              <line x1="3" y1="10" x2="21" y2="10" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{lastResult ? lastResult.total_records.toLocaleString() : '-'}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Anomalies</CardTitle>
            <svg className="h-4 w-4 text-destructive" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">{lastResult ? lastResult.anomaly_count.toLocaleString() : '-'}</div>
            {lastResult && (
              <p className="text-xs text-muted-foreground">{lastResult.anomaly_rate}% of total</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Anomaly Detection</CardTitle>
          <CardDescription>Select a query, algorithm, and date range to detect anomalies.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Select label="Query" value={queryName} onChange={(e) => setQueryName(e.target.value)} options={[{ value: '', label: 'Select query...' }, ...queryOptions]} />
            <Select label="Algorithm" value={algorithm} onChange={(e) => setAlgorithm(e.target.value)} options={algorithmOptions} />
            <Select label="Detection Level" value={detectionLevel} onChange={(e) => setDetectionLevel(e.target.value)} options={[{ value: '', label: 'Default (no grouping)' }, ...levelOptions]} />
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium">Start Date</label>
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2" />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium">End Date</label>
              <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2" />
            </div>
          </div>

          <Button onClick={handleDetect} isLoading={isLoading} disabled={!queryName}>Run Detection</Button>

          {(queriesError || algorithmsError || error) && (
            <div className="rounded-md bg-destructive/15 p-4 text-sm text-destructive">
              {queriesError && <p><strong>Queries:</strong> {queriesError.message}</p>}
              {algorithmsError && <p><strong>Algorithms:</strong> {algorithmsError.message}</p>}
              {error && <p>{error}</p>}
            </div>
          )}
        </CardContent>
      </Card>

      {lastResult && (
        <>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Distribution</CardTitle><CardDescription>Normal vs anomaly breakdown</CardDescription></CardHeader>
              <CardContent>
                <DistributionChart normalCount={lastResult.summary.normal_count} anomalyCount={lastResult.summary.anomaly_count} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Severity</CardTitle><CardDescription>Anomaly severity distribution</CardDescription></CardHeader>
              <CardContent>
                {Object.keys(lastResult.summary.severity_distribution).length > 0 ? (
                  <SeverityChart distribution={lastResult.summary.severity_distribution} />
                ) : (
                  <p className="text-sm text-muted-foreground">No severity data available.</p>
                )}
              </CardContent>
            </Card>
          </div>

          {timeColumn && numericColumn && (
            <Card>
              <CardHeader><CardTitle>Time Series</CardTitle><CardDescription>{timeColumn} vs {numericColumn}</CardDescription></CardHeader>
              <CardContent>
                <TimeSeriesChart data={lastResult.records} xKey={timeColumn} yKey={numericColumn} />
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle>Results</CardTitle>
                <CardDescription>{filteredRecords.length} of {lastResult.total_records} records</CardDescription>
              </div>
              <div className="relative">
                <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
                <input
                  type="text"
                  placeholder="Filter records..."
                  value={filterText}
                  onChange={(e) => setFilterText(e.target.value)}
                  className="h-10 w-full rounded-md border border-border bg-background py-2 pl-9 pr-4 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 sm:w-64"
                />
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b">
                    <tr>
                      {lastResult.records.length > 0 && Object.keys(lastResult.records[0]).map((key) => (
                        <th key={key} className="px-4 py-3 text-left font-medium text-muted-foreground">{key}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {filteredRecords.slice(0, 100).map((record, idx) => (
                      <tr key={idx} className={record.is_anomaly ? 'bg-destructive/5' : 'hover:bg-muted/50'}>
                        {Object.values(record).map((value, vidx) => (
                          <td key={vidx} className="px-4 py-3">
                            {typeof value === 'boolean' ? (
                              value ? <Badge variant="destructive">Yes</Badge> : <Badge variant="secondary">No</Badge>
                            ) : (
                              String(value)
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredRecords.length > 100 && (
                  <p className="mt-4 text-center text-sm text-muted-foreground">Showing first 100 of {filteredRecords.length} records.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
