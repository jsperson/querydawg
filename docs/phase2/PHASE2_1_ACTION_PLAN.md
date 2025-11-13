# Phase 2.1 Action Plan - Fix Column Disambiguation

**Date:** 2025-11-13
**Goal:** Fix Phase 2 regression by making column disambiguation conditional
**Target:** 84.2-84.7% accuracy (Run 21)

---

## Problem Statement

**Run 20 Result:** 83.72% (-0.08% vs Run 19: 83.80%)
**Root Cause:** LLM over-applied disambiguation to ALL columns (100%) instead of only multi-table columns (~20-35%)
**Impact:** ~50% verbosity increase, ~70% noise-to-signal ratio in regressed databases

---

## Solution: Phase 2.1 - Conditional Column Disambiguation

### Change 1: Make Disambiguation Conditional

**Current prompt** (`backend/app/services/semantic_layer_generator.py`, lines 276-325):
```
**PHASE 2 STRUCTURED COLUMN DISAMBIGUATION:**
For columns that appear in 2+ tables, you MUST provide:
...
```

**Problem:** LLM interpreted this as "provide for ALL columns"

**Fix:** Add explicit exclusion for single-table columns:

```
**PHASE 2 STRUCTURED COLUMN DISAMBIGUATION:**

IMPORTANT: First count how many tables each column appears in.

For columns that appear in 2+ tables ONLY, you MUST provide:
1. primary_location
2. foreign_key_locations
3. directional_guidance
4. subject_vs_relationship

For columns that ONLY appear in ONE table:
- DO NOT provide any "disambiguation" field
- Omit the entire disambiguation block
- The column's business_meaning and typical_filters are sufficient

EXAMPLES:

✅ CORRECT (column appears in 2+ tables):
{
  "name": "CountryCode",
  "disambiguation": {
    "primary_location": "country",
    "appears_in_tables": ["city", "countrylanguage"],
    "directional_guidance": "Use city.CountryCode when identifying the country a city belongs to.",
    "foreign_key_locations": ["city", "countrylanguage"],
    "subject_vs_relationship": "country.Code = the country entity itself, city.CountryCode = relationship to the country"
  }
}

✅ CORRECT (column appears in 1 table only):
{
  "name": "Population",
  // NO disambiguation field - column only appears in city table
  "business_meaning": "The number of people living in the city."
}

❌ INCORRECT (disambiguation for single-table column):
{
  "name": "Population",
  "disambiguation": {
    "primary_location": "city",
    "appears_in_tables": ["city"],  // ❌ Only 1 table!
    "directional_guidance": "Use city.Population when..."  // ❌ Unnecessary!
  }
}
```

### Change 2: Update JSON Output Schema

**Current schema** (lines 369-400):
```
disambiguation:
  primary_location: The table that "owns" this column
  foreign_key_locations: List of tables where this column appears as a FK
  ...
```

**Fix:** Make it clear disambiguation is **optional**:

```
disambiguation (OPTIONAL - only for columns appearing in 2+ tables):
  primary_location: The table that "owns" this column (source of truth)
  foreign_key_locations: List of tables where this column appears as a FK
  directional_guidance: When to use primary vs FK versions (SUBJECT vs RELATIONSHIP)
  subject_vs_relationship: Explicit subject vs relationship pattern

NOTE: Omit this field entirely for columns that only appear in 1 table.
```

---

## Implementation Steps

### Step 1: Update Prompt (10 minutes)

**File:** `backend/app/services/semantic_layer_generator.py`
**Lines:** 276-325

**Changes:**
1. Add "IMPORTANT: First count how many tables each column appears in."
2. Change "For columns that appear in 2+ tables" to "For columns that appear in 2+ tables ONLY"
3. Add explicit exclusion: "For columns that ONLY appear in ONE table: DO NOT provide disambiguation"
4. Add ✅ CORRECT and ❌ INCORRECT examples

### Step 2: Update JSON Schema (5 minutes)

**File:** `backend/app/services/semantic_layer_generator.py`
**Lines:** 369-400

**Changes:**
1. Change `disambiguation:` to `disambiguation (OPTIONAL - only for columns appearing in 2+ tables):`
2. Add note: "Omit this field entirely for columns that only appear in 1 table."

### Step 3: Test on Regressed Databases (30 minutes)

**Command:**
```bash
python scripts/test_phase21_generation.py
```

**Test databases:** car_1, world_1 (the regressed ones)

**Expected results:**
- car_1: 23 → ~8 columns with disambiguation (65% reduction)
- world_1: 12 → ~2 columns with disambiguation (83% reduction)
- Verbosity: ~30-40% reduction
- Single-table columns have NO disambiguation field

### Step 4: Full Regeneration (1 hour)

**If tests pass:**
1. Push Phase 2.1 code to GitHub
2. User regenerates all 20 semantic layers on Railway
3. Embed to Pinecone (auto-delete will clean up old versions)
4. User triggers Benchmark Run 21

### Step 5: Validate Run 21 Results (30 minutes)

**Expected results:**
- Overall: 84.2-84.7% (+0.5-1.0% vs Run 20: 83.72%)
- car_1: 63 → 66-67 correct (+3-4 questions, recover regression)
- world_1: 88 → 91-92 correct (+3-4 questions, recover regression)
- pets_1, network_1, tvshow: maintain improvements (+2, +1, +3)

**Success criteria:**
- Run 21 >= 84.2% (meets lower bound of Phase 2 target)
- car_1 and world_1 recover to Run 19 levels
- No new regressions in other databases

---

## Risk Assessment

### Risk 1: LLM Still Over-Applies Disambiguation

**Likelihood:** Low (new prompt is very explicit with examples)

**Mitigation:**
- Test on car_1 and world_1 first
- Manually inspect generated semantic layers
- If LLM still provides disambiguation for all columns, consider:
  - Adding post-processing to remove disambiguation from single-table columns
  - Using a different LLM with better instruction following

### Risk 2: Removing Disambiguation Hurts Accuracy

**Likelihood:** Very Low (single-table columns don't need disambiguation)

**Reasoning:**
- Disambiguation was ONLY meant for multi-table columns
- Single-table columns already have business_meaning and typical_filters
- Reducing noise should improve, not hurt, accuracy

### Risk 3: Phase 2.1 Still Doesn't Reach 84.5%+

**Likelihood:** Medium

**Contingency:**
- If Run 21 = 84.0-84.2% (improvement but below target):
  - Declare Phase 2.1 successful, move to Phase 3 (cross-table patterns)
  - Expected +0.3-0.5% from cross-table patterns could push to 84.5%+

- If Run 21 < 84.0% (no improvement):
  - Revert to Option 2: Remove disambiguation entirely, keep relationship fields
  - Or Option 3: Selective application to databases with genuine ambiguities

---

## Timeline

**Total:** 2-3 hours active work, 1 hour waiting for regeneration

| Step | Time | Owner |
|------|------|-------|
| 1. Update prompt | 10 min | Claude |
| 2. Update JSON schema | 5 min | Claude |
| 3. Test on car_1, world_1 | 30 min | Claude |
| 4. Push to GitHub | 5 min | Claude |
| 5. Regenerate on Railway | 45 min | User (automated) |
| 6. Embed to Pinecone | 15 min | User (automated) |
| 7. Run Benchmark 21 | ~2 hours | User (on Vercel) |
| 8. Analyze Run 21 | 30 min | Claude |
| **Total** | **~4 hours** | |

---

## Success Metrics

### Primary Metric
**Run 21 accuracy >= 84.2%** (+0.5% vs Run 20: 83.72%)

### Secondary Metrics
1. **Verbosity reduction:** 30-40% fewer lines in semantic layers
2. **Disambiguation coverage:** 20-35% of columns (vs 100% in Run 20)
3. **car_1 recovery:** 63 → 66-67 correct (+3-4 questions)
4. **world_1 recovery:** 88 → 91-92 correct (+3-4 questions)
5. **Whack-a-mole reduction:** <15 total swings (vs 19 in Run 20)

---

## Fallback Plan

**If Phase 2.1 fails (Run 21 < 84.0%):**

### Option A: Remove Column Disambiguation Entirely

Keep Phase 2 relationship fields (join_pattern, when_to_use, vs_confusion) which helped pets_1, network_1, tvshow.

Remove all column disambiguation fields.

**Expected accuracy:** 84.0-84.3%

### Option B: Revert to Run 19

Completely revert Phase 2, go back to Run 19 baseline (83.80%).

Focus on different optimization approach:
- RAG retrieval optimization
- Query generation prompt engineering
- Temperature tuning

### Option C: Selective Phase 2 Application

Apply Phase 2.1 only to databases that benefited:
- pets_1, network_1, tvshow: Keep Phase 2.1
- car_1, world_1, others: Revert to Phase 1

Hybrid approach for maximum accuracy.

**Expected accuracy:** 84.3-84.5%

---

## Deliverables

1. ✅ `ROOT_CAUSE_ANALYSIS.md` - Detailed analysis of why Phase 2 failed
2. ✅ `PHASE2_1_ACTION_PLAN.md` - This document
3. ⏳ Updated `semantic_layer_generator.py` with conditional disambiguation
4. ⏳ Test results for car_1 and world_1 with Phase 2.1
5. ⏳ Run 21 benchmark results
6. ⏳ Run 21 analysis document

---

## Decision Point

**Proceed with Phase 2.1 implementation?**

**Recommended:** YES - Root cause is clear, fix is straightforward, risk is low.

**Alternative:** If user prefers safer approach, implement Option A (remove column disambiguation entirely) or Option C (selective application).

---

**Status:** Ready for Implementation
**Date:** 2025-11-13
**Next:** Update semantic_layer_generator.py with conditional disambiguation prompt
