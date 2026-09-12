export interface HealthResponse {
  status: string;
  service: string;
}

export type ConnectionStatus = 'checking' | 'connected' | 'disconnected' | 'error';

export interface HealthState {
  status: ConnectionStatus;
  data: HealthResponse | null;
  error: string | null;
  latencyMs: number | null;
  lastChecked: Date | null;
}
