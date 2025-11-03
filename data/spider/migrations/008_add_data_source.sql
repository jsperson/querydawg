-- ============================================================================
-- Migration 008: Add data_source column to benchmark_runs
-- Created: 2025-01-03
-- Purpose: Track which database platform (Turso/Supabase) each benchmark used
-- ============================================================================

-- Add data_source column to benchmark_runs
ALTER TABLE public.benchmark_runs
ADD COLUMN IF NOT EXISTS data_source TEXT
CHECK (data_source IN ('supabase', 'turso'))
DEFAULT 'supabase';

-- Update existing rows to have supabase as default (they were all run on Supabase)
UPDATE public.benchmark_runs
SET data_source = 'supabase'
WHERE data_source IS NULL;

-- Make it NOT NULL after backfilling
ALTER TABLE public.benchmark_runs
ALTER COLUMN data_source SET NOT NULL;

-- Add comment
COMMENT ON COLUMN public.benchmark_runs.data_source IS
'Database platform used for benchmark execution: supabase (PostgreSQL) or turso (SQLite)';

-- Add index for filtering by data_source
CREATE INDEX IF NOT EXISTS idx_runs_data_source ON public.benchmark_runs(data_source);
