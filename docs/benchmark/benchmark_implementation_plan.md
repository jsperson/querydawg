# Spider 1.0 Benchmark Implementation Plan

**Status:** In Progress
**Started:** 2025-10-28
**Goal:** Run full Spider 1.0 dev set (1,034 questions) with baseline vs enhanced comparison

---

## Approved Decisions

### Technical Choices
- ✅ **Spider Evaluation:** Use official `evaluation.py` from Spider repo
- ✅ **SQL Normalization:** Use `sqlglot` for robust SQL parsing
- ✅ **Background Tasks:** Use FastAPI BackgroundTasks (MVP), design for Celery swap later
- ✅ **Budget Limit:** $5.00 per benchmark run
- ✅ **Connection Pooling:** psycopg2.pool.SimpleConnectionPool (2-10 connections)
- ✅ **Retry Strategy:** 3 attempts with exponential backoff (2s, 4s, 8s)

### Codex Feedback Incorporated
- ✅ Added `cancelled_at`, `status_reason`, `retry_count` columns
- ✅ Added indexes on `status`, composite index for failure filters
- ✅ Centralized cost tracking with budget limits
- ✅ Pre-aggregated stats in backend API
- ✅ Frontend polling with exponential backoff after completion
- ✅ Read-only transaction wrapper for safe SQL execution
- ✅ Store generated SQL for re-evaluation capability

---

## Database Schema

### Table: `benchmark_runs`
```sql
CREATE TABLE benchmark_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  run_type TEXT NOT NULL CHECK (run_type IN ('baseline', 'enhanced', 'both')),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),

  -- Configuration
  question_count INTEGER NOT NULL,
  databases TEXT[],

  -- Progress tracking
  completed_count INTEGER DEFAULT 0,
  failed_count INTEGER DEFAULT 0,
  current_question TEXT,
  last_processed_question_id TEXT,  -- For future pause/resume

  -- Results summary (calculated on completion)
  baseline_exact_match DECIMAL,
  baseline_exec_match DECIMAL,
  enhanced_exact_match DECIMAL,
  enhanced_exec_match DECIMAL,

  -- Costs and timing
  total_cost_usd DECIMAL DEFAULT 0,
  baseline_cost_usd DECIMAL DEFAULT 0,
  enhanced_cost_usd DECIMAL DEFAULT 0,
  total_time_ms BIGINT,

  -- Error tracking
  retry_count INTEGER DEFAULT 0,
  last_error TEXT,
  status_reason TEXT,  -- "completed", "cancelled_by_user", "budget_exceeded", "fatal_error"

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  cancelled_at TIMESTAMPTZ,

  -- Metadata
  created_by TEXT,
  notes TEXT
);

-- Indexes
CREATE INDEX idx_runs_status ON benchmark_runs(status);
CREATE INDEX idx_runs_created_at ON benchmark_runs(created_at DESC);
```

### Table: `benchmark_results`
```sql
CREATE TABLE benchmark_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_id UUID NOT NULL REFERENCES benchmark_runs(id) ON DELETE CASCADE,

  -- Question details (from Spider dev.json)
  question_id TEXT NOT NULL,
  database TEXT NOT NULL,
  question TEXT NOT NULL,
  gold_sql TEXT NOT NULL,
  difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard', 'extra')),

  -- Baseline results
  baseline_sql TEXT,                    -- Generated SQL (for review/re-eval)
  baseline_exact_match BOOLEAN,
  baseline_exec_match BOOLEAN,
  baseline_error TEXT,
  baseline_execution_time_ms INTEGER,
  baseline_cost_usd DECIMAL,
  baseline_tokens_used INTEGER,
  baseline_retry_count INTEGER DEFAULT 0,

  -- Enhanced results
  enhanced_sql TEXT,                    -- Generated SQL (for review/re-eval)
  enhanced_exact_match BOOLEAN,
  enhanced_exec_match BOOLEAN,
  enhanced_error TEXT,
  enhanced_execution_time_ms INTEGER,
  enhanced_cost_usd DECIMAL,
  enhanced_tokens_used INTEGER,
  enhanced_semantic_chunks_used INTEGER,
  enhanced_retry_count INTEGER DEFAULT 0,

  -- Timestamps
  processed_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT unique_run_question UNIQUE(run_id, question_id)
);

-- Indexes
CREATE INDEX idx_results_run_id ON benchmark_results(run_id);
CREATE INDEX idx_results_database ON benchmark_results(database);
CREATE INDEX idx_results_difficulty ON benchmark_results(difficulty);

-- Composite index for "failures only" filter
CREATE INDEX idx_results_failure_analysis ON benchmark_results(
  run_id,
  baseline_exact_match,
  enhanced_exact_match
) WHERE baseline_exact_match = FALSE OR enhanced_exact_match = FALSE;
```

---

## Backend Architecture

### File Structure
```
backend/app/
├── models/
│   └── benchmark.py              # Pydantic models
├── database/
│   └── benchmark_store.py        # Supabase operations
├── services/
│   ├── benchmark_runner.py       # Core evaluation logic
│   └── cost_tracker.py           # Centralized cost tracking
├── routers/
│   └── benchmark.py              # FastAPI endpoints
└── data/
    └── spider_dev.json           # Downloaded Spider dev set
```

### Key Components

**1. Cost Tracker** (`services/cost_tracker.py`)
```python
class CostTracker:
    def __init__(self, budget_limit: float = 5.0):
        self.budget_limit = budget_limit
        self.total_cost = 0.0

    def record_cost(self, cost: float, run_id: str):
        self.total_cost += cost
        if self.total_cost > self.budget_limit:
            raise BudgetExceededError(f"Budget ${self.budget_limit} exceeded")
```

**2. Benchmark Runner** (`services/benchmark_runner.py`)
- Connection pooling (2-10 connections)
- Retry logic with exponential backoff (tenacity)
- Spider evaluation.py integration
- Read-only transaction wrapping
- Incremental result storage

**3. SQL Normalization**
```python
import sqlglot

def normalize_sql(sql: str) -> str:
    try:
        parsed = sqlglot.parse_one(sql, dialect="postgres")
        return parsed.sql(dialect="postgres", normalize=True)
    except Exception:
        return sql.lower().strip()  # Fallback
```

**4. Safe Execution**
```python
def _execute_safely(self, sql: str, database: str):
    conn = self._get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute("SET statement_timeout = '5s'")
            cur.execute(f"SET search_path TO {database}")
            cur.execute(sql)
            results = sorted(cur.fetchall(), key=lambda x: str(x))
            return results, None
    except Exception as e:
        return [], str(e)
    finally:
        conn.rollback()
        self.db_pool.putconn(conn)
```

---

## API Endpoints

```python
POST   /api/benchmark/run           # Start new benchmark
GET    /api/benchmark/runs          # List all runs
GET    /api/benchmark/run/{id}/status    # Real-time progress
GET    /api/benchmark/run/{id}/summary   # Pre-aggregated metrics
GET    /api/benchmark/run/{id}/results   # Detailed results (paginated)
DELETE /api/benchmark/run/{id}      # Delete run
```

### Summary Endpoint Returns
```json
{
  "by_database": [
    {"database": "car_1", "total": 52, "baseline_correct": 22, "enhanced_correct": 31},
    ...
  ],
  "by_difficulty": [
    {"difficulty": "easy", "total": 248, "baseline_correct": 180, "enhanced_correct": 210},
    ...
  ],
  "overall": {
    "total_questions": 1034,
    "baseline_exact_match_rate": 0.423,
    "enhanced_exact_match_rate": 0.587,
    ...
  }
}
```

---

## Frontend Structure

```
frontend/src/app/admin/benchmark/
├── page.tsx                      # Control panel
├── [id]/
│   └── page.tsx                  # Results dashboard
└── components/
    ├── BenchmarkForm.tsx         # Configuration form
    ├── ProgressMonitor.tsx       # Live progress
    ├── SummaryCards.tsx          # Metric cards
    ├── ResultsTable.tsx          # Detailed table
    ├── ComparisonView.tsx        # SQL comparison modal
    └── Charts.tsx                # Recharts visualizations
```

### Polling Strategy
```typescript
let delay = 2000;  // Start at 2s

while (status !== 'completed') {
  await fetchStatus();
  await sleep(delay);

  if (status === 'completed') {
    delay = Math.min(delay * 2, 30000);  // Slow down
  }
}
```

---

## Implementation Phases

### Phase 1: Database Setup ✅ NEXT
1. Create Supabase migration SQL
2. Run migration
3. Test with sample data

### Phase 2: Backend Core (Headless)
1. Download Spider dev.json
2. Implement BenchmarkStore
3. Implement BenchmarkRunner with:
   - Connection pooling
   - Retry logic
   - Cost tracking
   - Spider evaluation
4. Create CLI test script (5-10 questions)

### Phase 3: API Layer
1. Implement 5 endpoints
2. Background task abstraction
3. Pre-aggregated stats

### Phase 4: Frontend
1. Control panel
2. Progress monitor
3. Results dashboard
4. Comparison modal

---

## Dependencies to Add

```txt
# backend/requirements.txt
sqlglot>=20.0.0          # SQL parsing/normalization
tenacity>=8.2.0          # Retry logic with backoff
```

---

## Success Criteria

✅ Click "Start Benchmark" → Process all 1,034 questions
✅ Live progress updates every 2 seconds
✅ Complete run in ~20-30 minutes
✅ View accuracy by database, difficulty level
✅ Filter to failed questions and compare SQL
✅ Track per-question and total costs
✅ Stay under $5 budget

---

## Future Enhancements (Post-MVP)

- [ ] Pause/Resume capability
- [ ] Celery/Arq for persistent background jobs
- [ ] Custom gold SQL overrides
- [ ] A/B testing mode
- [ ] Export to CSV/PDF
- [ ] Historical trend charts

---

**Last Updated:** 2025-10-28
**Implementation Started:** Phase 1 in progress
