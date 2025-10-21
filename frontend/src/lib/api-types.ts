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
  results: Record<string, any>[];
  columns: string[];
  row_count: number;
  execution_time_ms: number;
  truncated: boolean;
  database: string;
}

export interface ErrorResponse {
  detail: string;
}
