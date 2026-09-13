import { HealthResponse } from '../types/health';
import {
  ResearchAnalyzeRequest,
  ResearchAnalyzeResponse,
  ResearchClarifyRequest,
  DefinedExperimentSpec,
  ResearchDefineRequest,
  BacktestResult,
  TestExecutionRequest,
  LearnReport,
  ResearchLearnRequest,
} from '../types/research';

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

/**
 * Send structured field clarifications for an existing experiment to the backend.
 */
export async function clarifyExperiment(
  request: ResearchClarifyRequest
): Promise<{ data: ResearchAnalyzeResponse; latencyMs: number }> {
  const endpoint = `${API_BASE_URL}/api/research/clarify`;
  const startTime = performance.now();

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(request),
    });

    const latencyMs = Math.round(performance.now() - startTime);

    if (!response.ok) {
      let errorMsg = `Clarification request failed with status ${response.status}`;
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
    throw new ApiError(`Unable to reach clarification service at ${API_BASE_URL}: ${message}`);
  }
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

/**
 * Validates that an experiment is READY and locks it into a DefinedExperimentSpec execution contract.
 */
export async function defineExperiment(
  request: ResearchDefineRequest
): Promise<{ data: DefinedExperimentSpec; latencyMs: number }> {
  const endpoint = `${API_BASE_URL}/api/research/define`;
  const startTime = performance.now();

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(request),
    });

    const latencyMs = Math.round(performance.now() - startTime);

    if (!response.ok) {
      let errorMsg = `Define request failed with status ${response.status}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          errorMsg = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch {
        // fallback to errorMsg
      }
      throw new ApiError(errorMsg, response.status);
    }

    const data: DefinedExperimentSpec = await response.json();
    return { data, latencyMs };
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    const message = error instanceof Error ? error.message : 'Unknown network connection failure';
    throw new ApiError(`Unable to reach define service at ${API_BASE_URL}: ${message}`);
  }
}

/**
 * Executes a deterministic simulated backtest on a DefinedExperimentSpec.
 * Calls POST /api/research/test without live execution, external data, or LLM calls.
 */
export async function runBacktestSimulation(
  request: TestExecutionRequest
): Promise<{ data: BacktestResult; latencyMs: number }> {
  const endpoint = `${API_BASE_URL}/api/research/test`;
  const startTime = performance.now();

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(request),
    });

    const latencyMs = Math.round(performance.now() - startTime);

    if (!response.ok) {
      let errorMsg = `Test simulation failed with status ${response.status}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          errorMsg = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch {
        // fallback to errorMsg
      }
      throw new ApiError(errorMsg, response.status);
    }

    const data: BacktestResult = await response.json();
    return { data, latencyMs };
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    const message = error instanceof Error ? error.message : 'Unknown network connection failure';
    throw new ApiError(`Unable to reach backtest service at ${API_BASE_URL}: ${message}`);
  }
}

/**
 * Generates a deterministic research interpretation report (LearnReport) from backtest results.
 * Calls POST /api/research/learn without external network, database, or LLM calls.
 */
export async function generateLearnReport(
  request: ResearchLearnRequest
): Promise<{ data: LearnReport; latencyMs: number }> {
  const endpoint = `${API_BASE_URL}/api/research/learn`;
  const startTime = performance.now();

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(request),
    });

    const latencyMs = Math.round(performance.now() - startTime);

    if (!response.ok) {
      let errorMsg = `Learn request failed with status ${response.status}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          errorMsg = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch {
        // fallback to errorMsg
      }
      throw new ApiError(errorMsg, response.status);
    }

    const data: LearnReport = await response.json();
    return { data, latencyMs };
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    const message = error instanceof Error ? error.message : 'Unknown network connection failure';
    throw new ApiError(`Unable to reach research learn service at ${API_BASE_URL}: ${message}`);
  }
}
