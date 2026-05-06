import { createContext, useContext, useState } from 'react';
import { AnomalyDetectionResponse } from '@/types';

interface AnomalyState {
  lastResult: AnomalyDetectionResponse | null;
  selectedRecord: Record<string, unknown> | null;
  isLoading: boolean;
  error: string | null;
  setLastResult: (result: AnomalyDetectionResponse | null) => void;
  setSelectedRecord: (record: Record<string, unknown> | null) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

const AnomalyContext = createContext<AnomalyState | null>(null);

export function AnomalyProvider({ children }: { children: React.ReactNode }) {
  const [lastResult, setLastResult] = useState<AnomalyDetectionResponse | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<Record<string, unknown> | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const value: AnomalyState = {
    lastResult,
    selectedRecord,
    isLoading,
    error,
    setLastResult,
    setSelectedRecord,
    setIsLoading,
    setError,
    clearError: () => setError(null),
  };

  return <AnomalyContext.Provider value={value}>{children}</AnomalyContext.Provider>;
}

export function useAnomalyStore() {
  const ctx = useContext(AnomalyContext);
  if (!ctx) throw new Error('useAnomalyStore must be used within AnomalyProvider');
  return ctx;
}
