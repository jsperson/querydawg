/**
 * API client for QueryDawg backend
 * Uses Next.js API routes as proxy to keep API keys secure
 */

import {
  DatabaseListResponse,
  SchemaResponse,
  TextToSQLRequest,
  TextToSQLResponse,
  ExecuteRequest,
  ExecuteResponse,
  GenerateSemanticLayerRequest,
  SemanticLayerResponse,
  ViewPromptRequest,
  ViewPromptResponse,
  SemanticLayerListItem,
  CustomInstructionsRequest,
  CustomInstructionsResponse,
  DatabaseOverviewResponse,
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
    fetchAPI<DatabaseListResponse>(`/databases?_t=${Date.now()}`),

  /**
   * Get schema for a specific database
   */
  getSchema: (database: string) =>
    fetchAPI<SchemaResponse>(`/schema/${database}`),

  /**
   * Generate SQL from natural language question (baseline)
   */
  generateSQL: (request: TextToSQLRequest) =>
    fetchAPI<TextToSQLResponse>('/text-to-sql/baseline', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  /**
   * Generate SQL from natural language question (enhanced with semantic layer)
   */
  generateSQLEnhanced: (request: TextToSQLRequest) =>
    fetchAPI<TextToSQLResponse>('/text-to-sql/enhanced', {
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

  // Semantic Layer APIs
  /**
   * Generate semantic layer for a database
   */
  generateSemanticLayer: (request: GenerateSemanticLayerRequest) =>
    fetchAPI<SemanticLayerResponse>('/semantic/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  /**
   * View prompt without generating
   */
  viewPrompt: (request: ViewPromptRequest) =>
    fetchAPI<ViewPromptResponse>('/semantic/prompt', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  /**
   * Get semantic layer for a database
   */
  getSemanticLayer: (database: string, version?: string) => {
    const params = version ? `?version=${version}` : '';
    return fetchAPI<SemanticLayerResponse>(`/semantic/${database}${params}`);
  },

  /**
   * Get database overview/summary from semantic layer
   */
  getDatabaseOverview: (database: string) =>
    fetchAPI<DatabaseOverviewResponse>(`/semantic/overview/${database}`),

  /**
   * List all semantic layers
   */
  listSemanticLayers: () =>
    fetchAPI<SemanticLayerListItem[]>(`/semantic?_t=${Date.now()}`),

  /**
   * Delete semantic layer for a database
   */
  deleteSemanticLayer: (database: string, connectionName: string = 'Supabase') =>
    fetchAPI<{ message: string }>(`/semantic/${database}?connection_name=${connectionName}`, {
      method: 'DELETE',
    }),

  /**
   * Get custom instructions
   */
  getCustomInstructions: () =>
    fetchAPI<CustomInstructionsResponse>('/semantic/instructions'),

  /**
   * Set custom instructions
   */
  setCustomInstructions: (request: CustomInstructionsRequest) =>
    fetchAPI<{ message: string }>('/semantic/instructions', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  /**
   * Get databases that have semantic layers
   */
  getDatabasesWithSemanticLayers: (connectionName: string = 'Supabase') =>
    fetchAPI<{ databases: string[] }>(`/semantic/status?connection_name=${connectionName}`),
};
