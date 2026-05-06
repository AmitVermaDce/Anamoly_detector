import { useNavigate } from 'react-router-dom';
import { useAnomalyStore } from '@/store/anomalyStore';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

export function AnomalyDetails() {
  const navigate = useNavigate();
  const { selectedRecord } = useAnomalyStore();

  if (!selectedRecord) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20">
        <p className="text-muted-foreground">No record selected.</p>
        <Button onClick={() => navigate('/')}>Back to Dashboard</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Button variant="outline" onClick={() => navigate('/')}>
        <span className="mr-2">&larr;</span> Back
      </Button>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Anomaly Record Details</CardTitle>
            {selectedRecord.is_anomaly ? (
              <Badge variant="destructive">Anomaly</Badge>
            ) : (
              <Badge variant="secondary">Normal</Badge>
            )}
          </div>
          <CardDescription>Detailed view of the selected record.</CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 sm:grid-cols-2">
            {Object.entries(selectedRecord).map(([key, value]) => (
              <div key={key} className="flex flex-col gap-1">
                <dt className="text-sm font-medium text-muted-foreground">{key}</dt>
                <dd className="text-sm">
                  {typeof value === 'boolean' ? (
                    value ? <Badge variant="destructive">Yes</Badge> : <Badge variant="secondary">No</Badge>
                  ) : (
                    String(value)
                  )}
                </dd>
              </div>
            ))}
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}
