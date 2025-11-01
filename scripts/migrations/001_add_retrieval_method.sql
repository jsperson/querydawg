-- Migration: Add enhanced_semantic_retrieval_method column
-- Date: 2025-11-01
-- Purpose: Track how semantic layer was retrieved (RAG vs fallback vs none)

-- Add column for tracking retrieval method
ALTER TABLE benchmark_results
ADD COLUMN IF NOT EXISTS enhanced_semantic_retrieval_method TEXT;

-- Add comment for documentation
COMMENT ON COLUMN benchmark_results.enhanced_semantic_retrieval_method IS
'Tracks how semantic layer was retrieved: vector_search_success, vector_search_empty_fallback, vector_search_error_fallback, full_layer_direct, or none';

-- Create index for efficient queries on retrieval method
CREATE INDEX IF NOT EXISTS idx_benchmark_results_retrieval_method
ON benchmark_results(enhanced_semantic_retrieval_method);
