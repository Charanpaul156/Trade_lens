import { HealthResponse } from '../types/health';
import { ResearchAnalyzeRequest, ResearchAnalyzeResponse } from '../types/research';

/**
 * Base API URL derived dynamically from environment variables.
 * Configured in .env or .env.local via VITE_API_BASE_URL.
 */
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public responseBody?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Perform a typed GET request to the backend health endpoint.
 */
export async function getHealth(): Promise<{ data: HealthResponse; latencyMs: number }> {
  const endpoint = `${API_BASE_URL}/api/health`;
  const startTime = performance.now();

  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    const latencyMs = Math.round(performance.now() - startTime);

    if (!response.ok) {
      throw new ApiError(
        `Backend responded with status HTTP ${response.status} (${response.statusText})`,
        response.status
      );
    }

    const data: HealthResponse = await response.json();
    return { data, latencyMs };
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    const message = error instanceof Error ? error.message : 'Unknown network connection failure';
    throw new ApiError(`Unable to reach backend at ${API_BASE_URL}: ${message}`);
  }
}

/**
 * Send natural language trading question to backend AI research analyzer endpoint.
 */
export async function analyzeResearchQuestion(
  question: string
): Promise<{ data: ResearchAnalyzeResponse; latencyMs: number }> {
  const endpoint = `${API_BASE_URL}/api/research/analyze`;
  const startTime = performance.now();

  try {
    const payload: ResearchAnalyzeRequest = { question };
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const latencyMs = Math.round(performance.now() - startTime);

    if (!response.ok) {
      let errorMsg = `Analysis request failed with status ${response.status}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          errorMsg = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch {
        // use fallback errorMsg
      }
      throw new ApiError(errorMsg, response.status);
    }

    const data: ResearchAnalyzeResponse = await response.json();
    return { data, latencyMs };
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    const message = error instanceof Error ? error.message : 'Unknown network connection failure';
    throw new ApiError(`Unable to reach AI analyzer at ${API_BASE_URL}: ${message}`);
  }
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

