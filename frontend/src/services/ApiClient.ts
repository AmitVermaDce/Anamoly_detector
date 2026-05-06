import {
  AlgorithmInfo,
  AnomalyDetectionRequest,
  AnomalyDetectionResponse,
  DetectionLevelInfo,
  HealthResponse,
} from '@/types';

const API_BASE_URL = '/api/v1';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = body.detail || response.statusText || 'An unexpected error occurred';
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export class ApiClient {
  async getHealth(): Promise<HealthResponse> {
    return apiFetch<HealthResponse>('/health');
  }

  async getQueries(): Promise<string[]> {
    const data = await apiFetch<{ queries: string[] }>('/queries');
    return data.queries;
  }

  async getAlgorithms(): Promise<AlgorithmInfo[]> {
    const data = await apiFetch<{ algorithms: AlgorithmInfo[] }>('/algorithms');
    return data.algorithms;
  }

  async getLevels(): Promise<DetectionLevelInfo[]> {
    const data = await apiFetch<{ levels: DetectionLevelInfo[] }>('/levels');
    return data.levels;
  }

  async detectAnomalies(request: AnomalyDetectionRequest): Promise<AnomalyDetectionResponse> {
    return apiFetch<AnomalyDetectionResponse>('/detect', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }
}

export const apiClient = new ApiClient();
