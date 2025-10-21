/**
 * API client for DataPrism backend
 * Uses Next.js API routes as proxy to keep API keys secure
 */

import {
  DatabaseListResponse,
  SchemaResponse,
  TextToSQLRequest,
  TextToSQLResponse,
  ExecuteRequest,
  ExecuteResponse,
} from './api-types';

const API_BASE = '/api';

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

export const api = {
  /**
   * Get list of available databases
   */
  getDatabases: () =>
    fetchAPI<DatabaseListResponse>('/databases'),

  /**
   * Get schema for a specific database
   */
  getSchema: (database: string) =>
    fetchAPI<SchemaResponse>(`/schema/${database}`),

  /**
   * Generate SQL from natural language question
   */
  generateSQL: (request: TextToSQLRequest) =>
    fetchAPI<TextToSQLResponse>('/text-to-sql/baseline', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  /**
   * Execute SQL query and get results
   */
  executeSQL: (request: ExecuteRequest) =>
    fetchAPI<ExecuteResponse>('/execute', {
      method: 'POST',
      body: JSON.stringify(request),
    }),
};
