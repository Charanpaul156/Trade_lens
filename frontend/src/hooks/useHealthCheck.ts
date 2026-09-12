import { useState, useEffect, useCallback } from 'react';
import { HealthState } from '../types/health';
import { getHealth, ApiError } from '../services/api';

export function useHealthCheck(pollIntervalMs: number = 10000) {
  const [state, setState] = useState<HealthState>({
    status: 'checking',
    data: null,
    error: null,
    latencyMs: null,
    lastChecked: null,
  });

  const checkConnection = useCallback(async () => {
    setState((prev) => ({ ...prev, status: 'checking' }));
    try {
      const { data, latencyMs } = await getHealth();
      setState({
        status: 'connected',
        data,
        error: null,
        latencyMs,
        lastChecked: new Date(),
      });
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : 'Backend connection failed';
      setState({
        status: 'disconnected',
        data: null,
        error: errorMessage,
        latencyMs: null,
        lastChecked: new Date(),
      });
    }
  }, []);

  useEffect(() => {
    checkConnection();
    if (pollIntervalMs > 0) {
      const interval = setInterval(checkConnection, pollIntervalMs);
      return () => clearInterval(interval);
    }
  }, [checkConnection, pollIntervalMs]);

  return {
    ...state,
    refetch: checkConnection,
  };
}
