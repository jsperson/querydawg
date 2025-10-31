"""
Pydantic models for API responses
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime


class DatabaseListResponse(BaseModel):
    """Database list response"""
    databases: List[str]
    count: int


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None


class ColumnInfo(BaseModel):
    """Column information"""
    name: str
    type: str
    nullable: bool
    primary_key: bool
    default: Optional[str] = None


class ForeignKeyInfo(BaseModel):
    """Foreign key information"""
    column: str
    referenced_table: str
    referenced_column: str


class TableInfo(BaseModel):
    """Table information"""
    name: str
    columns: List[ColumnInfo]
    foreign_keys: List[ForeignKeyInfo]
    row_count: int


class SchemaResponse(BaseModel):
    """Database schema response"""
    database: str
    tables: List[TableInfo]


class TextToSQLRequest(BaseModel):
    """Request for text-to-SQL generation"""
    question: str
    database: str


class SQLMetadata(BaseModel):
    """Metadata about SQL generation"""
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    generation_time_ms: int
    model: str
    provider: str
    database: str
    has_semantic_layer: bool = False  # Whether semantic layer was used (enhanced mode only)


class TextToSQLResponse(BaseModel):
    """Response from text-to-SQL generation"""
    sql: str
    explanation: str
    metadata: SQLMetadata


class ExecuteRequest(BaseModel):
    """Request for SQL execution"""
    sql: str
    database: str


class ExecuteResponse(BaseModel):
    """Response from SQL execution"""
    results: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: int
    truncated: bool
    database: str


class CompareExecuteRequest(BaseModel):
    """Request for executing multiple SQL queries for comparison"""
    gold_sql: str
    baseline_sql: str
    enhanced_sql: str
    database: str


class QueryExecutionResult(BaseModel):
    """Result from executing a single query"""
    success: bool
    results: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    row_count: Optional[int] = None
    execution_time_ms: Optional[int] = None
    error: Optional[str] = None


class CompareExecuteResponse(BaseModel):
    """Response from executing multiple SQL queries for comparison"""
    gold: QueryExecutionResult
    baseline: QueryExecutionResult
    enhanced: QueryExecutionResult
    database: str
