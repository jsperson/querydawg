-- Migration: Add prompt logging columns to benchmark_results
-- Date: 2025-11-02
-- Purpose: Enable debugging of semantic layer effectiveness by storing prompts used

-- Add prompt logging columns to benchmark_results table
ALTER TABLE benchmark_results
ADD COLUMN IF NOT EXISTS baseline_system_prompt TEXT,
ADD COLUMN IF NOT EXISTS baseline_user_prompt TEXT,
ADD COLUMN IF NOT EXISTS enhanced_system_prompt TEXT,
ADD COLUMN IF NOT EXISTS enhanced_user_prompt TEXT,
ADD COLUMN IF NOT EXISTS enhanced_semantic_chunks TEXT;

-- Add comments for documentation
COMMENT ON COLUMN benchmark_results.baseline_system_prompt IS 'System prompt used for baseline SQL generation';
COMMENT ON COLUMN benchmark_results.baseline_user_prompt IS 'User prompt used for baseline SQL generation (includes schema)';
COMMENT ON COLUMN benchmark_results.enhanced_system_prompt IS 'System prompt used for enhanced SQL generation';
COMMENT ON COLUMN benchmark_results.enhanced_user_prompt IS 'User prompt used for enhanced SQL generation (includes schema + semantic layer)';
COMMENT ON COLUMN benchmark_results.enhanced_semantic_chunks IS 'JSON string of semantic layer chunks retrieved for this query';

-- Create index on run_id for efficient prompt retrieval during analysis
CREATE INDEX IF NOT EXISTS idx_benchmark_results_run_id_prompts
ON benchmark_results(run_id)
WHERE enhanced_user_prompt IS NOT NULL;

-- Verify migration
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'benchmark_results'
        AND column_name = 'baseline_system_prompt'
    ) THEN
        RAISE NOTICE '✅ Migration successful: Prompt logging columns added';
    ELSE
        RAISE EXCEPTION '❌ Migration failed: Columns not added';
    END IF;
END $$;
