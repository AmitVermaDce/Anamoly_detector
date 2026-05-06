export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

export interface AlgorithmInfo {
  name: string;
  display_name: string;
  description: string;
}

export interface DetectionLevelInfo {
  name: string;
  group_cols: string[];
  description: string;
}

export interface AnomalyDetectionRequest {
  query_name: string;
  algorithm: string;
  detection_level: string | null;
  columns: string[];
  parameters: Record<string, unknown>;
  start_date: string | null;
  end_date: string | null;
}

export interface AnomalyDetectionResponse {
  query_name: string;
  algorithm: string;
  detection_level?: string;
  total_records: number;
  anomaly_count: number;
  anomaly_rate: number;
  records: Record<string, unknown>[];
  summary: AnomalySummary;
}

export interface AnomalySummary {
  total_records: number;
  anomaly_count: number;
  normal_count: number;
  mean_anomaly_score?: number;
  max_anomaly_score?: number;
  severity_distribution: Record<string, number>;
}

export interface AnomalyRecord {
  [key: string]: unknown;
  is_anomaly: boolean;
  anomaly_score: number;
  algorithm: string;
}
