# Run 17 Results and Current State
**Date:** 2025-11-09
**Status:** Stabilization attempt completed, results analyzed

---

## Phase 1 Stabilization: Code Changes Deployed

### Changes Made (Commit 00b92ae)
1. ✅ Removed "SQL Query Generation Guidelines" section from semantic_layer_generator.py (lines 270-294)
2. ✅ Removed conflicting Guidelines 3-4 from prompts.py:
   - Guideline 3: "JOIN Types - Be Precise"
   - Guideline 4: "SELECT Only Requested Columns"
3. ✅ Renumbered remaining guidelines (5-12 → 3-10)
4. ✅ Preserved Turso extraction logic (case sensitivity working)

### Semantic Layers Regenerated
- **20/20 databases** regenerated (Nov 9, 2025 18:37-18:49 UTC)
- **Case sensitivity preserved**: network_1 has "Friend", "Highschooler", "Likes"
- **Guidelines are natural/descriptive** (not prescriptive)
- **Embeddings updated**: 152 new vectors uploaded to Pinecone ($0.0008 cost)

---

## Run 17 Results: NO IMPROVEMENT

### Overall Accuracy
- **Run 13 (Baseline):** 84.03%
- **Run 16 (Before stabilization):** 83.40%
- **Run 17 (After stabilization):** **83.40%** ⚠️

**Result:** IDENTICAL to Run 16 - Stabilization did NOT work

---

## Per-Database Analysis (Run 17 vs Run 16)

### Improvements ✅
1. **student_transcripts_tracking**: 71.79% → 78.21% (+6.42%)
2. **car_1**: 64.13% → 67.39% (+3.26%)
3. **tvshow**: 83.87% → 87.10% (+3.23%)
4. **cre_Doc_Template_Mgt**: 83.33% → 84.52% (+1.19%)

### No Change (11 databases)
- world_1, course_teach, employee_hire_evaluation, wta_1, poker_player, real_estate_properties, singer, voter_1, museum_visit

### Regressions ❌
1. **battle_death**: 81.25% → 75.00% (-6.25%) 🔴
2. **orchestra**: 95.00% → 90.00% (-5.00%) 🔴
3. **flight_2**: 93.75% → 90.00% (-3.75%)
4. **network_1**: 80.36% → 76.79% (-3.57%)
5. **pets_1**: 100.00% → 97.62% (-2.38%)
6. **concert_singer**: 86.67% → 84.44% (-2.23%)
7. **dog_kennels**: 81.71% → 80.49% (-1.22%)

---

## Key Findings

### The Whack-a-Mole Effect Continues
- **4 databases improved** (student_transcripts_tracking, car_1, tvshow, cre_Doc_Template_Mgt)
- **7 databases regressed** (battle_death, orchestra, flight_2, network_1, pets_1, concert_singer, dog_kennels)
- **Net result:** Improvements canceled out by regressions

### New Major Regressions
1. **battle_death**: -6.25% (worst regression)
2. **orchestra**: -5.00% (second worst)
3. **network_1**: Now at 76.79% (down from 82.14% in Run 13)

### Compared to Baseline (Run 13)
- **Still -0.63%** from baseline (83.40% vs 84.03%)
- **student_transcripts_tracking** is only database with net gain vs Run 13 (+3.85%)
- **network_1** is down -5.35% from baseline
- **battle_death** is down -6.25% from baseline
- **orchestra** is down -5.00% from baseline

---

## Critical Insight

**The problem is NOT just the guidelines!**

Removing prescriptive guidelines and regenerating semantic layers did not stabilize performance. The whack-a-mole effect persists, suggesting:

1. **Semantic layer non-determinism** is more fundamental than we thought
2. **LLM generates different content each time** regardless of prompt structure
3. **Random variation between runs** may be inherent to the approach
4. **The baseline (Run 13)** may have been lucky, not reproducible

---

## Next Steps to Investigate

### Hypothesis 1: Railway Deployment Lag
- Changes were pushed to GitHub (commit 00b92ae)
- Railway auto-deploys from main branch
- **Need to verify:** Did Railway actually deploy the new code before Run 17?
- **Action:** Check Railway deployment logs for timing

### Hypothesis 2: Semantic Layer Non-Determinism
- Each semantic layer regeneration creates different content
- Even "natural" descriptions vary between generations
- **Need to verify:** Are Run 17 semantic layers actually different from Run 16?
- **Action:** Compare specific semantic layer content between regenerations

### Hypothesis 3: System Prompt Still Has Issues
- Remaining guidelines may still conflict
- Case sensitivity guideline (Guideline 10) may be causing issues
- **Need to verify:** Examine failing queries to see if remaining guidelines are problematic
- **Action:** Deep dive on battle_death and orchestra regressions

### Hypothesis 4: Fundamental Approach Problem
- Semantic layers + guidelines may be inherently unstable
- LLM may need explicit few-shot examples, not descriptions
- **Need to consider:** Skip Phase 2, go straight to few-shot learning
- **Action:** Review Phase 2 plan in PHASE1_LEARNINGS_AND_NEXT_STEPS.md

---

## Files and Locations

### Key Documents
- `PHASE1_LEARNINGS_AND_NEXT_STEPS.md` - Original 3-phase improvement plan
- `docs/progress_tracker.md` - Updated with Week 6.5 optimization section
- This file: `RUN17_RESULTS_AND_STATE.md`

### Database IDs
- Run 13 (baseline): `4f144555-bff7-4684-8b83-04f24fd5d08a`
- Run 16 (before stabilization): `e4a4645e-32fe-4324-a062-9b9201b36a17`
- Run 17 (after stabilization): `9f8dc4ae-f448-4180-92fe-cf1cce74bb7a`

### Code Changes
- Commit 00b92ae: Phase 1 stabilization reverts
- Commit 6e60946: Progress tracker update

### Deployments
- Semantic layers regenerated: Nov 9, 2025 18:37-18:49 UTC
- Embeddings regenerated: 152 vectors, $0.0008 cost
- Run 17 completed: Nov 9, 2025 21:36:15 UTC

---

## Immediate Actions Required

1. **Verify Railway deployment** - Check if commit 00b92ae was actually deployed before Run 17
2. **Compare semantic layers** - Check if Run 17 layers are actually different from Run 16
3. **Deep dive on regressions** - Analyze battle_death and orchestra failures
4. **Reconsider approach** - May need to abandon guidelines entirely, use few-shot instead

---

## Decision Point

**If stabilization truly failed:**
- Phase 1 approach (removing guidelines) did not work
- Phase 2 approach (better semantic descriptions) may also fail due to non-determinism
- **Consider skipping to Phase 3:** Few-shot learning with explicit SQL examples

**If deployment issue:**
- Re-run benchmark after verifying Railway deployment
- Semantic layers may still be correct for stabilization

---

**Status:** Awaiting investigation and decision on next steps
**Last Updated:** 2025-11-09 after Run 17 analysis
**Next Review:** After deployment verification and regression analysis
