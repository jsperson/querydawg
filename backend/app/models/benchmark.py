"""
Pydantic models for Spider benchmark system
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from decimal import Decimal


class BenchmarkConfig(BaseModel):
    """Configuration for creating a new benchmark run"""
    name: str = Field(..., description="User-friendly name for this benchmark run")
    run_type: Literal['baseline', 'enhanced', 'both'] = Field(..., description="Which approaches to test")
    databases: Optional[List[str]] = Field(None, description="Specific databases to test (None = all 20)")
    question_limit: Optional[int] = Field(None, description="Limit number of questions (None = all 1034)")


class BenchmarkRunCreate(BaseModel):
    """Data needed to create a benchmark_runs record"""
    name: str
    run_type: str
    question_count: int
    databases: Optional[List[str]]
    created_by: Optional[str] = None
    notes: Optional[str] = None


class BenchmarkRunResponse(BaseModel):
    """Real-time status of a running benchmark"""
    id: str
    name: str
    run_type: str
    status: str
    progress: float = Field(..., description="Completion percentage (0.0 to 1.0)")
    completed_count: int
    failed_count: int
    question_count: int
    current_question: Optional[str] = None
    total_cost_usd: Decimal
    created_at: datetime
    started_at: Optional[datetime] = None

    # Running metrics (calculated from completed results so far)
    baseline_exec_match_rate: Optional[float] = None
    baseline_correct_count: Optional[int] = None
    enhanced_exec_match_rate: Optional[float] = None
    enhanced_correct_count: Optional[int] = None


class BenchmarkSummary(BaseModel):
    """Complete summary of a benchmark run with calculated metrics"""
    run_id: str
    name: str
    run_type: str
    status: str
    status_reason: Optional[str] = None

    # Overall metrics
    total_questions: int
    completed: int
    failed: int

    # Baseline metrics
    baseline_exact_match_rate: Optional[float] = None
    baseline_exec_match_rate: Optional[float] = None
    baseline_avg_cost: Optional[float] = None
    baseline_total_cost: Optional[float] = None

    # Enhanced metrics
    enhanced_exact_match_rate: Optional[float] = None
    enhanced_exec_match_rate: Optional[float] = None
    enhanced_avg_cost: Optional[float] = None
    enhanced_total_cost: Optional[float] = None

    # Timing
    total_time_ms: Optional[int] = None
    avg_time_per_question_ms: Optional[int] = None

    # Timestamps
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BenchmarkResult(BaseModel):
    """Detailed result for a single question"""
    run_id: str
    question_id: str
    database: str
    question: str
    gold_sql: str
    difficulty: Optional[str] = None

    # Baseline
    baseline_sql: Optional[str] = None
    baseline_exact_match: Optional[bool] = None
    baseline_exec_match: Optional[bool] = None
    baseline_error: Optional[str] = None
    baseline_execution_time_ms: Optional[int] = None
    baseline_cost_usd: Optional[Decimal] = None
    baseline_tokens_used: Optional[int] = None
    baseline_retry_count: int = 0

    # Enhanced
    enhanced_sql: Optional[str] = None
    enhanced_exact_match: Optional[bool] = None
    enhanced_exec_match: Optional[bool] = None
    enhanced_error: Optional[str] = None
    enhanced_execution_time_ms: Optional[int] = None
    enhanced_cost_usd: Optional[Decimal] = None
    enhanced_tokens_used: Optional[int] = None
    enhanced_semantic_chunks_used: Optional[int] = None
    enhanced_retry_count: int = 0

    processed_at: Optional[str] = None  # ISO format datetime string


class BenchmarkResultsResponse(BaseModel):
    """Paginated response for benchmark results"""
    results: List[BenchmarkResult]
    total: int
    filtered: int
    page: int
    page_size: int


class SpiderQuestion(BaseModel):
    """Spider dataset question format"""
    question_id: str
    database: str
    question: str
    query: str  # Gold SQL
    difficulty: Optional[str] = None


class AggregatedStats(BaseModel):
    """Pre-aggregated statistics"""
    database: Optional[str] = None
    difficulty: Optional[str] = None
    total: int
    baseline_correct: int = 0
    enhanced_correct: int = 0
    baseline_accuracy: float = 0.0
    enhanced_accuracy: float = 0.0


class BenchmarkSummaryStats(BaseModel):
    """Pre-aggregated statistics for charts"""
    by_database: List[AggregatedStats]
    by_difficulty: List[AggregatedStats]
    overall: AggregatedStats
