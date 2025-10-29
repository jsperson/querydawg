-- ============================================================================
-- Migration 004: Spider Benchmark Schema
-- Created: 2025-10-28
-- Purpose: Tables for storing benchmark runs and results
-- ============================================================================

-- ============================================================================
-- TABLE: benchmark_runs
-- Stores metadata about each benchmark execution
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.benchmark_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  run_type TEXT NOT NULL CHECK (run_type IN ('baseline', 'enhanced', 'both')),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),

  -- Configuration
  question_count INTEGER NOT NULL,
  databases TEXT[],  -- Array of database names to test (NULL = all)

  -- Progress tracking
  completed_count INTEGER DEFAULT 0,
  failed_count INTEGER DEFAULT 0,
  current_question TEXT,  -- Currently processing question text
  last_processed_question_id TEXT,  -- For future pause/resume capability

  -- Results summary (calculated after completion)
  baseline_exact_match DECIMAL(5,4),  -- e.g., 0.4230 = 42.30%
  baseline_exec_match DECIMAL(5,4),
  enhanced_exact_match DECIMAL(5,4),
  enhanced_exec_match DECIMAL(5,4),

  -- Costs and timing
  total_cost_usd DECIMAL(10,4) DEFAULT 0,
  baseline_cost_usd DECIMAL(10,4) DEFAULT 0,
  enhanced_cost_usd DECIMAL(10,4) DEFAULT 0,
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
  created_by TEXT,  -- User/session identifier
  notes TEXT
);

-- Indexes for benchmark_runs
CREATE INDEX IF NOT EXISTS idx_runs_status ON public.benchmark_runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON public.benchmark_runs(created_at DESC);

-- ============================================================================
-- TABLE: benchmark_results
-- Stores detailed results for each question in a benchmark run
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.benchmark_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_id UUID NOT NULL REFERENCES public.benchmark_runs(id) ON DELETE CASCADE,

  -- Question details (from Spider dev.json)
  question_id TEXT NOT NULL,  -- e.g., "dev_0001"
  database TEXT NOT NULL,     -- e.g., "car_1"
  question TEXT NOT NULL,     -- Natural language question
  gold_sql TEXT NOT NULL,     -- Ground truth SQL from Spider
  difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard', 'extra')),

  -- Baseline results
  baseline_sql TEXT,                    -- Generated SQL (stored for review)
  baseline_exact_match BOOLEAN,         -- Normalized string match with gold
  baseline_exec_match BOOLEAN,          -- Query results match gold results
  baseline_error TEXT,                  -- Error message if generation/execution failed
  baseline_execution_time_ms INTEGER,   -- Time to execute query
  baseline_cost_usd DECIMAL(10,6),      -- API cost for this question
  baseline_tokens_used INTEGER,         -- Total tokens (prompt + completion)
  baseline_retry_count INTEGER DEFAULT 0,

  -- Enhanced results (with semantic layer)
  enhanced_sql TEXT,                    -- Generated SQL (stored for review)
  enhanced_exact_match BOOLEAN,         -- Normalized string match with gold
  enhanced_exec_match BOOLEAN,          -- Query results match gold results
  enhanced_error TEXT,                  -- Error message if generation/execution failed
  enhanced_execution_time_ms INTEGER,   -- Time to execute query
  enhanced_cost_usd DECIMAL(10,6),      -- API cost for this question
  enhanced_tokens_used INTEGER,         -- Total tokens (prompt + completion)
  enhanced_semantic_chunks_used INTEGER, -- Number of vector search results used
  enhanced_retry_count INTEGER DEFAULT 0,

  -- Timestamps
  processed_at TIMESTAMPTZ DEFAULT NOW(),

  -- Ensure each question only appears once per run
  CONSTRAINT unique_run_question UNIQUE(run_id, question_id)
);

-- Indexes for benchmark_results
CREATE INDEX IF NOT EXISTS idx_results_run_id ON public.benchmark_results(run_id);
CREATE INDEX IF NOT EXISTS idx_results_database ON public.benchmark_results(database);
CREATE INDEX IF NOT EXISTS idx_results_difficulty ON public.benchmark_results(difficulty);

-- Composite index for "failures only" filter
-- Only indexes rows where at least one approach failed
CREATE INDEX IF NOT EXISTS idx_results_failure_analysis ON public.benchmark_results(
  run_id,
  baseline_exact_match,
  enhanced_exact_match
) WHERE baseline_exact_match = FALSE OR enhanced_exact_match = FALSE;

-- ============================================================================
-- COMMENTS (for documentation)
-- ============================================================================

COMMENT ON TABLE public.benchmark_runs IS 'Stores metadata about Spider benchmark executions';
COMMENT ON TABLE public.benchmark_results IS 'Stores detailed results for each question in a benchmark run';

COMMENT ON COLUMN public.benchmark_runs.run_type IS 'Type of benchmark: baseline (schema only), enhanced (with semantic layer), or both';
COMMENT ON COLUMN public.benchmark_runs.status IS 'Current status: pending, running, completed, failed, or cancelled';
COMMENT ON COLUMN public.benchmark_runs.question_count IS 'Total number of questions to process (may be subset of full 1034)';
COMMENT ON COLUMN public.benchmark_runs.databases IS 'Array of database names to test (NULL = all 20 databases)';
COMMENT ON COLUMN public.benchmark_runs.status_reason IS 'Human-readable reason for final status (e.g., budget_exceeded, cancelled_by_user)';

COMMENT ON COLUMN public.benchmark_results.baseline_sql IS 'Generated SQL from baseline approach (stored for review and re-evaluation)';
COMMENT ON COLUMN public.benchmark_results.enhanced_sql IS 'Generated SQL from enhanced approach (stored for review and re-evaluation)';
COMMENT ON COLUMN public.benchmark_results.baseline_exact_match IS 'True if normalized baseline SQL matches normalized gold SQL';
COMMENT ON COLUMN public.benchmark_results.baseline_exec_match IS 'True if baseline query results match gold query results';
COMMENT ON COLUMN public.benchmark_results.enhanced_exact_match IS 'True if normalized enhanced SQL matches normalized gold SQL';
COMMENT ON COLUMN public.benchmark_results.enhanced_exec_match IS 'True if enhanced query results match gold query results';

-- ============================================================================
-- GRANT PERMISSIONS (if using Supabase RLS)
-- ============================================================================

-- Grant service role full access
GRANT ALL ON public.benchmark_runs TO service_role;
GRANT ALL ON public.benchmark_results TO service_role;

-- Grant anon/authenticated read access (optional - adjust based on security needs)
-- GRANT SELECT ON public.benchmark_runs TO authenticated;
-- GRANT SELECT ON public.benchmark_results TO authenticated;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
