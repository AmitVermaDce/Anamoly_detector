import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '@/services/ApiClient';
import { useAnomalyStore } from '@/store/anomalyStore';
import { AnomalyDetectionRequest } from '@/types';

export function useQueries() {
  const [data, setData] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiClient.getQueries()
      .then((queries) => { if (!cancelled) { setData(queries); setError(null); } })
      .catch((err) => { if (!cancelled) setError(err); })
      .finally(() => { if (!cancelled) setIsLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return { data, isLoading, error };
}

export function useAlgorithms() {
  const [data, setData] = useState<{ name: string; display_name: string; description: string }[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiClient.getAlgorithms()
      .then((algorithms) => { if (!cancelled) { setData(algorithms); setError(null); } })
      .catch((err) => { if (!cancelled) setError(err); })
      .finally(() => { if (!cancelled) setIsLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return { data, isLoading, error };
}

export function useLevels() {
  const [data, setData] = useState<{ name: string; group_cols: string[]; description: string }[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    apiClient.getLevels()
      .then((levels) => { if (!cancelled) setData(levels); })
      .finally(() => { if (!cancelled) setIsLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return { data, isLoading };
}

export function useDetectAnomalies() {
  const { setLastResult, setIsLoading, setError } = useAnomalyStore();

  const mutate = useCallback(async (request: AnomalyDetectionRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await apiClient.detectAnomalies(request);
      setLastResult(result);
    } catch (err: any) {
      setError(err.message || 'Detection failed');
    } finally {
      setIsLoading(false);
    }
  }, [setLastResult, setIsLoading, setError]);

  return { mutate };
}
