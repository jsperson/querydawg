# Run 20 Results Analysis - Phase 2 Impact Assessment

**Date:** 2025-11-13
**Status:** Phase 2 Did Not Improve Accuracy
**Run:** Full Spider 1.0 Turso 20

---

## Executive Summary

**Phase 2 structured templates did NOT achieve expected improvement:**

- **Run 19 (Phase 1):** 83.80% accuracy (867/1034 questions)
- **Run 20 (Phase 2):** 83.72% accuracy (866/1034 questions)
- **Change:** -0.08% (-1 question)

**Phase 2 Target:** 84.5-85.0% (+0.7-1.2%)
**Actual Result:** Essentially no change

**Key Findings:**
- ✅ Some improvements: pets_1 reached 100% (+2), tvshow +3, network_1 +1 (FK direction fix worked)
- ❌ Notable regressions: car_1 -4, world_1 -4
- ❌ Whack-a-mole persists: 19 total swings (6 improved, 4 regressed)
- ❌ Net result: -1 question vs Run 19

---

## Run Details

### Run 20 (Phase 2)
- **Benchmark:** Full Spider 1.0 Turso 20
- **Date:** 2025-11-13
- **Total Questions:** 1034
- **Correct (enhanced_exec_match):** 866
- **Accuracy:** 83.72%
- **Semantic Layer Version:** Phase 2 (structured templates)
- **Semantic Layer Updated:** 2025-11-13T04:32:05
- **Pinecone Embedded:** 2025-11-13T04:56:47

### Run 19 (Phase 1 Baseline)
- **Benchmark:** Full Spider 1.0 Turso 19
- **Date:** 2025-11-10
- **Total Questions:** 1034
- **Correct (enhanced_exec_match):** 867
- **Accuracy:** 83.80%
- **Semantic Layer Version:** Phase 1 (guideline chunks removed)

### Overall Comparison

| Metric | Run 19 | Run 20 | Change |
|--------|--------|--------|--------|
| Total Questions | 1034 | 1034 | 0 |
| Correct | 867 | 866 | -1 |
| Accuracy | 83.80% | 83.72% | -0.08% |
| Phase 2 Target | - | 84.5-85.0% | ❌ Not met |

---

## Database-Level Results

### Full Breakdown (All 20 Databases)

| Database | Total Q | R19 Correct | R20 Correct | Δ | R19% | R20% | Δ% | Status |
|----------|---------|-------------|-------------|---|------|------|----|----|
| tvshow | 62 | 49 | 52 | +3 | 79.0% | 83.9% | +4.8% | ✅ Improved |
| pets_1 | 42 | 40 | 42 | +2 | 95.2% | 100.0% | +4.8% | ✅ Improved |
| battle_death | 16 | 12 | 13 | +1 | 75.0% | 81.2% | +6.2% | ✅ Improved |
| concert_singer | 45 | 38 | 39 | +1 | 84.4% | 86.7% | +2.2% | ✅ Improved |
| flight_2 | 80 | 73 | 74 | +1 | 91.2% | 92.5% | +1.2% | ✅ Improved |
| network_1 | 56 | 47 | 48 | +1 | 83.9% | 85.7% | +1.8% | ✅ Improved |
| student_transcripts_tracking | 95 | 76 | 76 | 0 | 80.0% | 80.0% | 0.0% | ➖ No change |
| cre_Doc_Template_Mgt | 81 | 60 | 60 | 0 | 74.1% | 74.1% | 0.0% | ➖ No change |
| course_teach | 23 | 19 | 19 | 0 | 82.6% | 82.6% | 0.0% | ➖ No change |
| employee_hire_evaluation | 46 | 35 | 35 | 0 | 76.1% | 76.1% | 0.0% | ➖ No change |
| museum_visit | 23 | 20 | 20 | 0 | 87.0% | 87.0% | 0.0% | ➖ No change |
| orchestra | 42 | 36 | 36 | 0 | 85.7% | 85.7% | 0.0% | ➖ No change |
| poker_player | 23 | 21 | 21 | 0 | 91.3% | 91.3% | 0.0% | ➖ No change |
| real_estate_properties | 59 | 46 | 46 | 0 | 78.0% | 78.0% | 0.0% | ➖ No change |
| voter_1 | 26 | 21 | 21 | 0 | 80.8% | 80.8% | 0.0% | ➖ No change |
| wta_1 | 36 | 27 | 27 | 0 | 75.0% | 75.0% | 0.0% | ➖ No change |
| dog_kennels | 82 | 65 | 64 | -1 | 79.3% | 78.0% | -1.2% | ❌ Regressed |
| singer | 30 | 29 | 28 | -1 | 96.7% | 93.3% | -3.3% | ❌ Regressed |
| car_1 | 92 | 67 | 63 | -4 | 72.8% | 68.5% | -4.3% | ❌ Regressed |
| world_1 | 120 | 92 | 88 | -4 | 76.7% | 73.3% | -3.3% | ❌ Regressed |

### Summary Statistics

**Improvements:** 6 databases, +9 questions total
- tvshow: +3 (+4.8%)
- pets_1: +2 (+4.8%)
- battle_death: +1 (+6.2%)
- concert_singer: +1 (+2.2%)
- flight_2: +1 (+1.2%)
- network_1: +1 (+1.8%)

**No Change:** 10 databases

**Regressions:** 4 databases, -10 questions total
- car_1: -4 (-4.3%)
- world_1: -4 (-3.3%)
- dog_kennels: -1 (-1.2%)
- singer: -1 (-3.3%)

**Whack-a-Mole Effect:**
- Total swings: 19 (9 improved + 10 regressed)
- Net change: -1 question
- Effect persists from Phase 1

---

## Analysis: Why Phase 2 Didn't Improve Accuracy

### Phase 2 Changes Recap

**What was changed:**
1. **Structured Relationship Documentation** (6 required fields):
   - `join_pattern`: Explicit SQL join syntax
   - `when_to_use`: Specific question patterns requiring this join
   - `vs_confusion`: What NOT to confuse this relationship with
   - `relationship_type`: one-to-many, many-to-one, many-to-many
   - `is_bridge_table`: boolean for many-to-many bridges
   - `complete_join_path`: Multi-hop join paths

2. **Column Disambiguation** (4 required fields):
   - `primary_location`: Which table "owns" this column
   - `foreign_key_locations`: Tables where column appears as FK
   - `directional_guidance`: SUBJECT vs RELATIONSHIP usage pattern
   - `subject_vs_relationship`: Explicit distinction

**Target:** +0.5-1.0% from relationship structure + +0.5-1.0% from column disambiguation = +1.0-2.0% total (84.8-85.8%)

**Actual Result:** -0.08% (no improvement)

### Hypothesis: Why Phase 2 Failed

#### 1. Structured Templates May Have Made Descriptions Too Rigid

**Observation:** Phase 2 added 10 new required fields to semantic layers, increasing verbosity and structure.

**Possible Issue:**
- More structured content might reduce LLM flexibility during query generation
- Explicit "DO NOT confuse" statements might have introduced confusion where none existed before
- Rigid templates might not adapt well to different database complexities

**Evidence Needed:**
- Compare actual semantic layer content for regressed databases (car_1, world_1)
- Check if Phase 2 descriptions are significantly longer/more rigid
- Review if `vs_confusion` fields created new ambiguities

#### 2. Some Improvements, But Equal or Greater Regressions

**Wins:**
- pets_1: +2 (now 100%!) - bridge table identification worked
- tvshow: +3 (+4.8%) - relationship clarity helped
- network_1: +1 - FK direction fix worked as intended

**Losses:**
- car_1: -4 (-4.3%) - significant regression
- world_1: -4 (-3.3%) - significant regression

**Pattern:** Phase 2 helped simpler databases with clear relationship patterns (pets_1, network_1) but may have hurt complex databases with many tables and ambiguous relationships (car_1, world_1).

#### 3. LLM May Not Be Following Phase 2 Format Correctly

**Test Results:** Phase 2 test generation (3 databases) showed LLM followed format perfectly.

**Production Question:** Did LLM follow format for all 20 databases during full regeneration?

**Evidence Needed:**
- Inspect actual Supabase semantic layers for car_1 and world_1
- Verify all Phase 2 fields present
- Check quality of `join_pattern`, `when_to_use`, `vs_confusion` content

#### 4. Whack-a-Mole Effect Still Present

**Observation:** 19 total swings between Run 19 and Run 20 (similar to previous runs).

**Interpretation:** Phase 2 structured templates did NOT reduce variance as intended. Changes that should have made semantic layers more deterministic and consistent did not eliminate whack-a-mole effect.

**Implication:** Variance may be coming from:
- RAG retrieval inconsistency (not semantic layer content)
- Query generation prompt variance (not semantic layer quality)
- Database-specific sensitivity to description changes

---

## Notable Results

### Success Cases

#### pets_1: Now 100% (Previously 95.2%)
- **Change:** +2 questions
- **Why:** Bridge table (Has_Pet) correctly identified with `is_bridge_table: true`
- **Phase 2 Field Impact:** `complete_join_path` made multi-hop joins explicit
- **Conclusion:** Phase 2 relationship structure worked as intended for this database

#### network_1: FK Direction Fix Worked
- **Change:** +1 question (83.9% → 85.7%)
- **Why:** `vs_confusion` field prevented friend_id vs student_id confusion
- **Phase 2 Field Impact:** `join_pattern` made FK direction explicit
- **Example:** "DO NOT confuse with student_id - this is the ID of the friend, not the student."
- **Conclusion:** Addresses Run 18 → 19 regression for network_1

#### tvshow: Largest Absolute Improvement
- **Change:** +3 questions (79.0% → 83.9%)
- **Why:** Relationship clarity likely improved join understanding
- **Conclusion:** Phase 2 relationship structure helpful for medium-complexity databases

### Regression Cases

#### car_1: Largest Absolute Regression
- **Change:** -4 questions (72.8% → 68.5%)
- **Complexity:** 8 tables, 92 questions (high complexity)
- **Why:** Unknown - requires investigation
- **Hypothesis:** Structured templates may have added confusion for complex multi-table joins

#### world_1: Second Largest Regression
- **Change:** -4 questions (76.7% → 73.3%)
- **Complexity:** 3 tables, 120 questions (high question count)
- **Why:** Unknown - requires investigation
- **Hypothesis:** Column disambiguation may have created ambiguity for simple schema with many questions

---

## Phase 2 Target vs Actual

### Original Phase 2 Plan Estimates

| Priority | Enhancement | Expected Impact |
|----------|-------------|-----------------|
| 1 | Structured Relationship Documentation | +0.5-1.0% |
| 2 | Column Disambiguation | +0.5-1.0% |
| **Total** | **Phase 2** | **+1.0-2.0%** |

### Actual Impact

| Enhancement | Expected | Actual | Met Target? |
|-------------|----------|--------|-------------|
| Relationship Documentation | +0.5-1.0% | -0.08% | ❌ No |
| Column Disambiguation | +0.5-1.0% | -0.08% | ❌ No |
| **Total** | **+1.0-2.0%** | **-0.08%** | ❌ No |

**Target:** 84.5-85.0%
**Actual:** 83.72%
**Gap:** -0.78% to -1.28%

---

## Comparison to Previous Runs

### Accuracy Progression

| Run | Date | Accuracy | Change | Notes |
|-----|------|----------|--------|-------|
| Run 17 | Nov 10 | 83.40% | - | Baseline |
| Run 18 | Nov 10 | 83.60% | +0.20% | Attempt to reduce variance |
| Run 19 | Nov 10 | 83.80% | +0.20% | Phase 1 (guideline chunks removed) |
| Run 20 | Nov 13 | 83.72% | -0.08% | Phase 2 (structured templates) |

**Trend:** Accuracy has plateaued at ~83.7-83.8% for the past 3 runs.

---

## Recommendations

### Option 1: Investigate and Refine Phase 2 (Recommended)

**Action Plan:**
1. **Inspect Regressed Databases:**
   - Compare Phase 1 vs Phase 2 semantic layers for car_1 and world_1
   - Identify what changed in relationship descriptions
   - Check if `vs_confusion` or `directional_guidance` introduced ambiguity

2. **Analyze Phase 2 Content Quality:**
   - Verify LLM followed Phase 2 format for all 20 databases
   - Check if `join_pattern` and `when_to_use` are high quality
   - Review if descriptions became too verbose/rigid

3. **Selective Refinement:**
   - Keep successful Phase 2 fields (e.g., `is_bridge_table` helped pets_1)
   - Remove or refine problematic fields (e.g., `vs_confusion` might create new confusion)
   - Test refined version on car_1 and world_1

**Timeline:** 1-2 days for investigation, 1 day for refinement and testing

**Expected Outcome:** Phase 2.1 with improved prompts, targeting 84.5-85.0%

### Option 2: Revert Phase 2, Try Different Approach

**Reasoning:** Phase 2 structured templates did not improve accuracy and may have hurt complex databases.

**Alternative Approaches:**
1. **Cross-Table Patterns (Priority 3 from Phase 2 plan):** Add common join patterns and query templates
2. **Domain Synonyms (Priority 4):** Expand synonym lists
3. **RAG Optimization:** Focus on retrieval quality rather than semantic layer content
4. **Query Generation Prompt:** Improve prompt rather than semantic layers

**Timeline:** 1-2 days per approach

**Expected Outcome:** Find alternative path to 84.5-85.0%

### Option 3: Accept Phase 2 as Neutral, Move to Phase 3

**Reasoning:** Phase 2 improvements (pets_1, network_1, tvshow) balanced by regressions (car_1, world_1).

**Next Phase Focus:**
- Priority 3: Cross-Table Patterns
- Priority 4: Domain Synonyms
- New: RAG retrieval optimization
- New: Query generation prompt engineering

**Timeline:** Immediate (no Phase 2 investigation needed)

**Risk:** May repeat same mistake if we don't understand why Phase 2 failed

### Option 4: Revert to Run 19, Focus on Variance Reduction

**Reasoning:** Whack-a-mole effect (19 swings) suggests variance is the real problem, not semantic layer quality.

**Focus Areas:**
1. **RAG Retrieval Consistency:** Ensure same semantic layer chunks retrieved for same question
2. **Query Generation Temperature:** Lower temperature to reduce randomness
3. **Prompt Determinism:** Make prompts more explicit and less open-ended

**Timeline:** 1-2 days for investigation

**Expected Outcome:** Reduce whack-a-mole swings from 19 to <10

---

## Next Steps

**Immediate Action (Day 2):**
1. Inspect car_1 and world_1 Phase 2 semantic layers from Supabase
2. Compare to Phase 1 versions (if available) or identify what might have caused regression
3. Review Phase 2 content quality across all 20 databases
4. Decide on Option 1, 2, 3, or 4 based on findings

**Decision Point:**
- If Phase 2 content quality is poor → Option 1 (refine Phase 2)
- If Phase 2 content quality is good → Option 2 or 4 (different approach)
- If no clear pattern → Option 3 (move to Phase 3)

---

## Conclusion

Phase 2 structured templates did not achieve the expected +1.0-2.0% accuracy improvement. While some databases improved (pets_1, tvshow, network_1), others regressed (car_1, world_1), resulting in a net -0.08% change.

**Key Questions:**
1. Did Phase 2 structured templates make descriptions too rigid?
2. Did `vs_confusion` or `directional_guidance` introduce new ambiguities?
3. Is the whack-a-mole effect caused by semantic layer variance or something else?

**Recommendation:** Investigate car_1 and world_1 regressions before proceeding with Phase 2.1 or alternative approaches.

---

**Status:** Phase 2 Complete - Investigation Required
**Date:** 2025-11-13
**Next:** Analyze regressed databases (car_1, world_1) to understand root cause
