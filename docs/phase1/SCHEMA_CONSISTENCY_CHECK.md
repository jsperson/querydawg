# Schema Consistency Check

**Generated:** 2025-11-01

## Summary

Checked column consistency across:
- **Supabase** (PostgreSQL database)
- **Railway/Backend** (FastAPI with Pydantic models)
- **Vercel/Frontend** (Next.js with TypeScript interfaces)

---

## benchmark_runs Table

### Supabase Schema (27 columns)
✅ All columns present in database

### Backend Model: `BenchmarkSummary`
Located: `backend/app/models/benchmark.py:50-83`

**Fields:**
- run_id ✅
- name ✅
- run_type ✅
- status ✅
- status_reason ✅
- total_questions ✅
- completed ✅
- failed ✅
- baseline_exact_match_rate ✅
- baseline_exec_match_rate ✅
- baseline_avg_cost ⚠️ (calculated, not in DB)
- baseline_total_cost ✅
- enhanced_exact_match_rate ✅
- enhanced_exec_match_rate ✅
- enhanced_avg_cost ⚠️ (calculated, not in DB)
- enhanced_total_cost ✅
- total_time_ms ✅
- avg_time_per_question_ms ⚠️ (calculated, not in DB)
- created_at ✅
- started_at ✅
- completed_at ✅

**Missing from model but in DB:**
- last_processed_question_id (internal tracking)
- retry_count (internal tracking)
- last_error (internal tracking)
- cancelled_at (timestamp)
- created_by (audit field)
- notes (audit field)
- current_question (real-time tracking)
- databases (array of database names)

### Frontend Interface: `BenchmarkSummary`
Located: `frontend/src/app/admin/benchmark/[id]/page.tsx:10-29`

**Fields:**
- run_id ✅
- name ✅
- run_type ✅
- status ✅
- status_reason ✅
- total_questions ✅
- completed ✅
- failed ✅
- baseline_exact_match_rate ✅
- baseline_exec_match_rate ✅
- baseline_total_cost ✅
- enhanced_exact_match_rate ✅
- enhanced_exec_match_rate ✅
- enhanced_total_cost ✅
- total_time_ms ✅
- created_at ✅
- started_at ✅
- completed_at ✅

**Missing (but may not be needed):**
- baseline_avg_cost
- enhanced_avg_cost
- avg_time_per_question_ms

**Assessment:** ✅ Frontend has all essential display fields

---

## benchmark_results Table

### Supabase Schema (26 columns)
✅ All columns present including new `enhanced_semantic_retrieval_method`

### Backend Model: `BenchmarkResult`
Located: `backend/app/models/benchmark.py:85-117`

**Core Fields:**
- run_id ✅
- question_id ✅
- database ✅
- question ✅
- gold_sql ✅
- difficulty ✅

**Baseline Fields:**
- baseline_sql ✅
- baseline_exact_match ✅
- baseline_exec_match ✅
- baseline_error ✅
- baseline_execution_time_ms ✅
- baseline_cost_usd ✅
- baseline_tokens_used ✅
- baseline_retry_count ✅

**Enhanced Fields:**
- enhanced_sql ✅
- enhanced_exact_match ✅
- enhanced_exec_match ✅
- enhanced_error ✅
- enhanced_execution_time_ms ✅
- enhanced_cost_usd ✅
- enhanced_tokens_used ✅
- enhanced_semantic_chunks_used ✅
- enhanced_semantic_retrieval_method ✅
- enhanced_retry_count ✅

**Metadata:**
- processed_at ✅ (as Optional[str] ISO format)

**Missing from model but in DB:**
- id (auto-generated UUID, not needed in model)

**Assessment:** ✅ Backend model matches database schema

### Frontend Interface: `BenchmarkResult`
Located: `frontend/src/app/admin/benchmark/[id]/page.tsx:31-46`

**Core Fields:**
- run_id ✅
- question_id ✅
- database ✅
- question ✅
- gold_sql ✅
- difficulty ✅

**Baseline Fields:**
- baseline_sql ✅
- baseline_exact_match ✅
- baseline_exec_match ✅
- baseline_error ✅

**Enhanced Fields:**
- enhanced_sql ✅
- enhanced_exact_match ✅
- enhanced_exec_match ✅
- enhanced_error ✅

**❌ MISSING FIELDS (Available in Backend/DB):**
- baseline_execution_time_ms
- baseline_cost_usd
- baseline_tokens_used
- baseline_retry_count
- enhanced_execution_time_ms
- enhanced_cost_usd
- enhanced_tokens_used
- enhanced_semantic_chunks_used ⚠️ **NEW - Not in Frontend**
- enhanced_semantic_retrieval_method ⚠️ **NEW - Not in Frontend**
- enhanced_retry_count
- processed_at

**Assessment:** ⚠️ Frontend is missing many analysis-useful fields

---

## Findings

### ✅ No Breaking Inconsistencies
All backend models correctly map to database schema. Backend APIs will function correctly.

### ⚠️ Frontend Missing Fields

The frontend TypeScript interface for `BenchmarkResult` is missing **11 fields** that exist in both the database and backend:

**Performance Metrics:**
- `baseline_execution_time_ms`
- `enhanced_execution_time_ms`

**Cost Tracking:**
- `baseline_cost_usd`
- `enhanced_cost_usd`

**Token Usage:**
- `baseline_tokens_used`
- `enhanced_tokens_used`

**NEW Semantic Layer Tracking:**
- `enhanced_semantic_chunks_used` ⚠️
- `enhanced_semantic_retrieval_method` ⚠️

**Retry Information:**
- `baseline_retry_count`
- `enhanced_retry_count`

**Timestamps:**
- `processed_at`

### Impact Assessment

**Current State:**
- ✅ Backend → Database: Fully consistent
- ✅ Backend API responses will include all fields
- ⚠️ Frontend will receive but ignore the extra fields (TypeScript allows extra properties in responses)

**If Frontend Needs These Fields:**
1. Update `BenchmarkResult` interface in `frontend/src/app/admin/benchmark/[id]/page.tsx`
2. Add UI components to display:
   - Semantic retrieval method (vector_search_success, fallback, etc.)
   - Chunk count used
   - Cost comparison
   - Token usage
   - Execution times
   - Retry counts

**Recommendation:**
- No immediate action required if current display is sufficient
- Consider adding semantic layer tracking display to diagnose issues like Run 16
- Cost and performance metrics would be valuable for analysis

---

## Next Steps

1. **Optional:** Update frontend types to match backend (no breaking change, just additional fields)
2. **Optional:** Add UI to display semantic retrieval method and chunk counts
3. **Monitor:** Ensure migration for `enhanced_semantic_retrieval_method` has been applied to production
