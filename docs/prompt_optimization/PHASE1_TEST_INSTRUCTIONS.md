# Phase 1 Prompt Optimization - Test Instructions

**Date:** 2025-11-14
**Changes:** Semantic layer utilization guidance + Phase 2-specific examples
**Commit:** 2c8ff96
**Status:** Ready for Testing

---

## Changes Made

### File Modified
`backend/app/services/llm/prompts.py` - `enhanced_sql_system()` function

### Key Improvements

1. **Reorganized Prompt Structure:**
   - CRITICAL RULES first (most important patterns at top)
   - USING SEMANTIC LAYER EFFECTIVELY section
   - STANDARD SQL GUIDELINES section
   - EXAMPLES section with 7 examples (2 new Phase 2 examples)

2. **Added Semantic Layer Utilization Guidance:**
   - Section A: Relationship Guidance (`join_pattern`, `when_to_use`)
   - Section B: Bridge Table Identification (`is_bridge_table`)
   - Section C: Column Disambiguation (`primary_location`, `directional_guidance`)
   - Section D: Business Terms (`business_name`, `synonyms`)

3. **Added Phase 2-Specific Examples:**
   - Example 4: Bridge table pattern (Has_Pet many-to-many with `is_bridge_table`)
   - Example 5: FK direction pattern (Friend table with `directional_guidance`)

### Expected Impact
- **Target:** +0.6-1.1% accuracy gain
- **Overall accuracy goal:** 84.2-84.8% (from current 83.72%)
- **Database recovery:** car_1: 63→66+, world_1: 88→91+

---

## Testing Plan

### Phase 1 Quick Validation (3 Databases)

**Goal:** Verify prompt improvements help before running full benchmark.

**Test Databases:**
1. **pets_1** (42 questions, 3 tables)
   - Run 20: 42/42 (100%) - perfect score
   - Run 21: 41/42 (97.6%) - lost perfect score
   - **Test Goal:** Recover to 100% (42/42)
   - **Why:** Tests bridge table identification (`Has_Pet.is_bridge_table`)

2. **car_1** (92 questions, 6 tables)
   - Run 19: 67/92 (72.8%)
   - Run 20: 63/92 (68.5%) - **regressed -4**
   - Run 21: 63/92 (68.5%) - no change
   - **Test Goal:** Recover to 66+/92 (71.7%+)
   - **Why:** Tests column disambiguation (multiple tables with same column names)

3. **dog_kennels** (81 questions, 8 tables)
   - Run 20: 60/81 (74.1%)
   - Run 21: 65/81 (80.2%) - **improved +5**
   - **Test Goal:** Maintain or improve 65+/81 (80.2%+)
   - **Why:** Tests complex multi-table relationships

**Total Questions:** 215 (pets_1: 42 + car_1: 92 + dog_kennels: 81)

---

## How to Run the Test

### Option A: Manual Test (Railway Deployment)

Since the prompt changes are already committed and pushed, you can trigger a test run on Railway:

1. **Deploy Changes to Railway** (if auto-deploy is not enabled)
   - Changes are already in `main` branch (commit 2c8ff96)
   - Railway will auto-deploy the updated prompts

2. **Run Partial Benchmark** (3 databases only)
   - Use Railway API or admin interface
   - Run benchmark on: `pets_1`, `car_1`, `dog_kennels`
   - OR: Run full benchmark if you prefer (will take longer but gives complete picture)

3. **Compare Results**
   - Compare to Run 20 baseline (Phase 2):
     - pets_1: 42/42 (target)
     - car_1: 63/92 (baseline) → 66+/92 (target)
     - dog_kennels: 60/81 (Run 20 baseline) → 65+/81 (target)

### Option B: Full Benchmark Run (Run 22)

If you want to test all 20 databases immediately:

1. **Trigger Full Benchmark**
   - Name: "Full Spider 1.0 Turso 22 - Phase 1 Prompt Optimization"
   - Description: "Testing semantic layer utilization guidance + Phase 2 examples"

2. **Success Criteria**
   - **Primary:** Overall accuracy >= 84.2% (871+/1034)
   - **Secondary:** <15 whack-a-mole swings (vs 19 in Run 19→20)
   - **Tertiary:** Recover regressed databases (car_1, world_1)

---

## Expected Results

### Best Case (Optimistic)
- **pets_1:** 42/42 (100%) - recovered perfect score ✅
- **car_1:** 68/92 (73.9%) - recovered +5 from Run 20 ✅
- **dog_kennels:** 67/81 (82.7%) - improved +2 from Run 21 ✅
- **Combined:** 177/215 (82.3%) for 3 databases
- **Full benchmark:** 84.8% (877/1034) if pattern holds

### Realistic Case (Expected)
- **pets_1:** 42/42 (100%) - recovered ✅
- **car_1:** 66/92 (71.7%) - recovered +3 ✅
- **dog_kennels:** 65/81 (80.2%) - maintained Run 21 level ✅
- **Combined:** 173/215 (80.5%) for 3 databases
- **Full benchmark:** 84.2-84.5% (871-874/1034)

### Worst Case (Pessimistic)
- **pets_1:** 41/42 (97.6%) - no change from Run 21
- **car_1:** 63/92 (68.5%) - no improvement
- **dog_kennels:** 63/81 (77.8%) - slight regression from Run 21
- **Combined:** 167/215 (77.7%) for 3 databases
- **Full benchmark:** 83.5-83.8% (864-867/1034) - no significant change

---

## Success Criteria

### Phase 1 Validation (3 Databases)

**Minimum Success:**
- At least 1 of the 3 databases improves vs Run 20
- No database regresses more than 1 question vs Run 20
- Combined accuracy >= 170/215 (79.1%)

**Strong Success:**
- At least 2 of the 3 databases improve vs Run 20
- pets_1 recovers to 100%
- Combined accuracy >= 173/215 (80.5%)

**Exceptional Success:**
- All 3 databases improve or maintain best score
- pets_1 = 100%, car_1 >= 66, dog_kennels >= 65
- Combined accuracy >= 175/215 (81.4%)

### Full Benchmark (Run 22)

**Minimum Success:**
- Overall accuracy >= 84.0% (869/1034) - **+0.28% vs Run 20**

**Strong Success:**
- Overall accuracy >= 84.2% (871/1034) - **+0.48% vs Run 20**
- Whack-a-mole < 15 swings (vs 19 in Run 19→20)

**Exceptional Success:**
- Overall accuracy >= 84.5% (874/1034) - **+0.78% vs Run 20**
- Whack-a-mole < 10 swings
- Both car_1 and world_1 recover to Run 19 levels

---

## Analysis After Testing

### Questions to Answer

1. **Did prompt improvements help?**
   - Compare Run 22 vs Run 20 (overall accuracy)
   - Identify which databases improved vs regressed
   - Calculate net change in questions correct

2. **Did semantic layer guidance work?**
   - Did pets_1 recover to 100%? (tests `is_bridge_table` guidance)
   - Did car_1 improve? (tests column `disambiguation` guidance)
   - Did databases with complex relationships improve?

3. **Was the whack-a-mole effect reduced?**
   - Count database swings between Run 20→22
   - Compare to Run 19→20 (19 swings) and Run 20→21 (24 swings)
   - Target: <15 swings

4. **What's next?**
   - If successful (+0.5%+): Proceed to Phase 2 (RAG hyperparameter tuning)
   - If modest (+0.2-0.5%): Analyze specific failures, refine prompt further
   - If unsuccessful (<0.2%): Investigate why, consider alternative approaches

---

## If Test Fails

### Rollback Plan

If Run 22 results are worse than Run 20:

1. **Immediate Rollback:**
   ```bash
   git revert 2c8ff96
   git push origin main
   ```

2. **Redeploy to Railway:** Railway will auto-deploy the reverted prompt

3. **Analysis:** Review which specific changes caused regressions

### Partial Rollback

If some changes helped but others hurt:

1. Keep successful changes (e.g., reorganization)
2. Remove unsuccessful changes (e.g., specific examples)
3. Test again with refined prompt

---

## Next Steps After Phase 1

### If Phase 1 Succeeds (+0.5%+)

**Proceed to Phase 2: RAG Hyperparameter Tuning**

1. Test different top_k values (5, 7, 10, 15, 20)
2. Test different chunk type weights
3. Identify optimal RAG settings
4. Run Phase 3 full validation (Run 23)

**Expected Timeline:** 2-3 hours implementation + 1-2 hours testing

### If Phase 1 is Modest (+0.2-0.5%)

**Option A: Refine Phase 1 Prompt**
- Analyze specific question failures
- Add more targeted examples
- Refine semantic layer guidance wording
- Test refined prompt (Run 22.1)

**Option B: Proceed to Phase 2 Anyway**
- Small gains compound
- RAG tuning may add another +0.2-0.5%
- Combined effect: +0.4-1.0%

### If Phase 1 Fails (<0.2%)

**Investigate Root Cause:**
1. Was the prompt too long? (check if gpt-4o-mini struggled with length)
2. Did new examples confuse the model?
3. Did reorganization hurt comprehension?
4. Are prompt improvements incompatible with Phase 2 semantic layers?

**Alternative Approaches:**
- Test simpler, more concise prompt
- Test different model (gpt-4 instead of gpt-4o-mini)
- Focus on RAG optimization instead of prompt changes

---

## Files

- **Prompt changes:** `backend/app/services/llm/prompts.py`
- **Commit:** 2c8ff96
- **This file:** `docs/prompt_optimization/PHASE1_TEST_INSTRUCTIONS.md`
- **Optimization plan:** `docs/prompt_optimization/OPTIMIZATION_PLAN.md`

---

**Status:** Ready for Testing on Railway
**Date:** 2025-11-14
**Next:** Trigger benchmark run and analyze results
