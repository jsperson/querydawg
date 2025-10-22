/**
 * TypeScript types for backend API
 */

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

export interface DatabaseListResponse {
  databases: string[];
  count: number;
}

export interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  default?: string;
}

export interface ForeignKeyInfo {
  column: string;
  referenced_table: string;
  referenced_column: string;
}

export interface TableInfo {
  name: string;
  columns: ColumnInfo[];
  foreign_keys: ForeignKeyInfo[];
  row_count: number;
}

export interface SchemaResponse {
  database: string;
  tables: TableInfo[];
}

export interface TextToSQLRequest {
  question: string;
  database: string;
}

export interface SQLMetadata {
  tokens_used: number;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  generation_time_ms: number;
  model: string;
  provider: string;
  database: string;
}

export interface TextToSQLResponse {
  sql: string;
  explanation: string;
  metadata: SQLMetadata;
}

export interface ExecuteRequest {
  sql: string;
  database: string;
}

export interface ExecuteResponse {
  results: Record<string, unknown>[];
  columns: string[];
  row_count: number;
  execution_time_ms: number;
  truncated: boolean;
  database: string;
}

export interface ErrorResponse {
  detail: string;
}

// Semantic Layer Types
export interface SemanticLayerMetadata {
  generated_at: string;
  generator_version: string;
  llm_provider: string;
  llm_model: string;
  anonymized: boolean;
  sample_rows_per_table: number;
  custom_instructions_used: boolean;
}

export interface SemanticLayerResponse {
  database: string;
  semantic_layer: Record<string, unknown>;
  metadata: SemanticLayerMetadata;
  prompt_used?: string;
}

export interface GenerateSemanticLayerRequest {
  database: string;
  custom_instructions?: string;
  anonymize?: boolean;
  sample_rows?: number;
}

export interface ViewPromptRequest {
  database: string;
  custom_instructions?: string;
  anonymize?: boolean;
  sample_rows?: number;
}

export interface ViewPromptResponse {
  database: string;
  prompt: string;
  prompt_length: string;
  anonymized: string;
}

export interface SemanticLayerListItem {
  id: string;
  database_name: string;
  version: string;
  created_at: string;
  llm_model: string;
}

export interface CustomInstructionsRequest {
  instructions: string;
}

export interface CustomInstructionsResponse {
  instructions: string;
}
