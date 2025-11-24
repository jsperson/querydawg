# Temperature Optimization Test Plan

**Date:** 2025-11-14
**Goal:** Reduce whack-a-mole effect and improve result stability
**Hypothesis:** Current temperature=0.0 is already deterministic; variance is from RAG retrieval randomness

---

## Background

### Phase 2 Lessons Learned

Three different semantic layer approaches yielded nearly identical accuracy:

- **Run 19 (Phase 1):** 83.80% (866/1034) - minimal structure
- **Run 20 (Phase 2):** 83.72% (866/1034) - maximum structure (same 866 correct!)
- **Run 21 (Phase 2.1):** 83.51% (863/1034) - conditional structure

**Whack-a-Mole Effect:** 19-24 database swings between runs

**Conclusion:** Semantic layer content has minimal impact. Variance likely from:
1. RAG retrieval randomness (different embeddings retrieved each time)
2. LLM generation randomness (temperature > 0)
3. Embedding model variance

---

## Current Temperature Configuration

**File:** `backend/app/services/llm/config.py`

```python
TASKS = {
    "baseline_sql": {
        "temperature": 0.0,  # Fully deterministic
    },
    "enhanced_sql": {
        "temperature": 0.0,  # Fully deterministic
    },
    "semantic_layer": {
        "temperature": 0.0,  # Fully deterministic
    }
}
```

**CRITICAL FINDING:** Temperature is ALREADY at 0.0 (deterministic)!

This means whack-a-mole effect is NOT caused by LLM temperature randomness.

---

## Revised Hypothesis

Since temperature=0.0 and we still see 19-24 swings:

1. **RAG retrieval variance** (MOST LIKELY)
   - Different semantic layer chunks retrieved each time
   - Embedding similarity scores vary slightly
   - Top-k retrieval may change order

2. **Model non-determinism** (POSSIBLE)
   - Even at temperature=0.0, some models have slight randomness
   - Token selection may vary due to floating-point precision

3. **Prompt length variance** (POSSIBLE)
   - Retrieved context varies → different prompt lengths
   - May affect model behavior even at temp=0.0

---

## Test Plan

### Option A: Confirm Temperature=0.0 is Actually Deterministic (HIGH PRIORITY)

**Goal:** Verify that same question + same RAG context = same SQL output

**Test Design:**
1. Pick 5 questions from different databases
2. Run each question 10 times with IDENTICAL RAG context (manually inject)
3. Check if SQL output is 100% identical across all 10 runs

**Implementation:**
```python
# scripts/test_temperature_determinism.py
# Fix RAG context, run same question 10x, check for variance
```

**Expected Result:**
- If 100% identical: Temperature=0.0 is deterministic, variance is from RAG
- If variance exists: Model has inherent randomness even at temp=0.0

**Timeline:** 30 minutes to implement + 15 minutes to run

---

### Option B: Test RAG Retrieval Stability (HIGH PRIORITY)

**Goal:** Measure how much RAG context varies between runs

**Test Design:**
1. Pick same 5 questions from Option A
2. Run RAG retrieval 10 times per question
3. Measure:
   - Top-k chunks retrieved (do they change?)
   - Similarity scores (do they vary?)
   - Chunk order (does ranking change?)

**Implementation:**
```python
# scripts/test_rag_stability.py
# Run retrieval 10x, log retrieved chunks + scores
```

**Expected Result:**
- If retrieval varies: RAG is source of whack-a-mole
- If retrieval is stable: Variance is elsewhere

**Timeline:** 1 hour to implement + 15 minutes to run

---

### Option C: Test Temperature Impact (LOWER PRIORITY)

**Goal:** Verify temperature=0.0 vs 0.1 vs 0.3 impact

**Test Design:**
1. Run 3 databases (50-100 questions total)
2. Test each temperature: 0.0, 0.1, 0.3
3. Run 3 iterations per temperature
4. Measure:
   - Average accuracy
   - Variance between iterations
   - Whack-a-mole swings

**Databases to Test:**
- flight_2 (80 questions, showed -3 regression in Run 21)
- dog_kennels (81 questions, showed +5 improvement in Run 21)
- pets_1 (42 questions, lost perfect score in Run 21)

**Expected Result:**
- Temperature=0.0: Low variance (deterministic)
- Temperature=0.1: Slight variance
- Temperature=0.3: Higher variance

**Timeline:** 2 hours to implement + 2 hours to run (9 benchmark runs)

---

## Recommended Execution Order

### Phase 1: Diagnosis (2 hours total)

1. **Test A: Temperature Determinism** (45 min)
   - Confirms if temp=0.0 is truly deterministic
   - Reveals if model has inherent randomness

2. **Test B: RAG Stability** (1.25 hours)
   - Measures RAG retrieval variance
   - Identifies if RAG is root cause of whack-a-mole

**Outcome:** Identify root cause of variance before optimization

---

### Phase 2: Optimization (Based on Phase 1 Results)

**If RAG is unstable:**
- Add retrieval logging to production
- Test different embedding strategies
- Test re-ranking approaches
- Consider semantic caching

**If model is non-deterministic:**
- Test `seed` parameter (if supported by OpenAI)
- Test different models (gpt-4 vs gpt-4o-mini)
- Consider Claude (may have better determinism)

**If variance is minimal:**
- Conclude that 83.5-83.8% is natural ceiling
- Focus on model upgrade (gpt-4 vs gpt-4o-mini)
- Focus on prompt engineering

---

## Success Metrics

### Accuracy Target
- **Current:** 83.51-83.80%
- **Target:** 84.5-85.0% (if achievable)
- **Stretch:** 85.5%+

### Stability Target (NEW PRIORITY)
- **Current whack-a-mole:** 19-24 swings
- **Target:** <10 swings between runs
- **Stretch:** <5 swings (high stability)

**Key Insight:** Stability may be MORE valuable than 0.5% accuracy gain!
- Stable 83.5% is better than unstable 84.0% (trust in system)

---

## Implementation Files

### Test A: Temperature Determinism
**File:** `scripts/test_temperature_determinism.py`

```python
#!/usr/bin/env python3
"""
Test if temperature=0.0 produces deterministic results.
Run same question 10x with FIXED RAG context.
"""

# 1. Select 5 test questions
# 2. Manually inject fixed RAG context
# 3. Run SQL generation 10x per question
# 4. Check if SQL is 100% identical
# 5. Report variance metrics
```

### Test B: RAG Stability
**File:** `scripts/test_rag_stability.py`

```python
#!/usr/bin/env python3
"""
Test if RAG retrieval is stable across runs.
Run retrieval 10x per question, measure variance.
"""

# 1. Select 5 test questions
# 2. Run RAG retrieval 10x per question
# 3. Log retrieved chunks + similarity scores
# 4. Measure:
#    - Chunk ID variance (do same chunks get retrieved?)
#    - Score variance (do scores change?)
#    - Rank variance (does order change?)
# 5. Report stability metrics
```

### Test C: Temperature Impact (Optional)
**File:** `scripts/test_temperature_impact.py`

```python
#!/usr/bin/env python3
"""
Compare accuracy and variance across temperatures 0.0, 0.1, 0.3.
Run 3 databases × 3 temperatures × 3 iterations.
"""

# 1. Select 3 test databases
# 2. For each temperature (0.0, 0.1, 0.3):
#    - Run 3 iterations
#    - Measure accuracy + variance
# 3. Compare whack-a-mole effect
# 4. Report optimal temperature
```

---

## Risk Assessment

### Low Risk
- Test A (Temperature Determinism): Quick test, no production impact
- Test B (RAG Stability): Read-only test, measures existing behavior

### Medium Risk
- Test C (Temperature Impact): May waste time if RAG is root cause

### High Risk
- Skipping Phase 1 diagnosis: Could optimize wrong thing

---

## Cost-Benefit Analysis

### Test A (Temperature Determinism)
- **Time:** 45 minutes
- **Cost:** ~$0.10 in API calls (50 SQL generations)
- **Benefit:** Confirms if model is truly deterministic
- **ROI:** HIGH (answers fundamental question)

### Test B (RAG Stability)
- **Time:** 1.25 hours
- **Cost:** ~$0.20 in API calls (50 retrievals)
- **Benefit:** Identifies root cause of whack-a-mole
- **ROI:** VERY HIGH (may reveal 80% of variance comes from RAG)

### Test C (Temperature Impact)
- **Time:** 4 hours
- **Cost:** ~$15-20 in API calls (9 benchmark runs × ~200 questions)
- **Benefit:** Quantifies temperature impact
- **ROI:** LOW (if temp=0.0 already deterministic, minimal gain expected)

---

## Recommendation

**SKIP Test C (Temperature Impact) for now.**

**Reason:**
1. Temperature is ALREADY at 0.0 (deterministic)
2. Whack-a-mole still exists (19-24 swings)
3. Therefore, temperature is NOT the root cause
4. Testing 0.1 and 0.3 will likely INCREASE variance, not reduce it

**FOCUS on Test A + Test B:**
1. Confirm temp=0.0 is deterministic (Test A)
2. Measure RAG retrieval stability (Test B)
3. Based on findings, pursue RAG optimization (if RAG is unstable)

**Expected Outcome:**
- Test A: Confirms determinism
- Test B: Reveals RAG retrieval varies 20-30% between runs
- **Action:** Optimize RAG retrieval (caching, re-ranking, better embeddings)

---

## Next Steps

1. ✅ Document temperature test plan (this file)
2. ⏭️ Implement Test A: Temperature Determinism
3. ⏭️ Implement Test B: RAG Stability
4. ⏭️ Run Test A + B (1 hour total runtime)
5. ⏭️ Analyze results and determine root cause
6. ⏭️ Discuss RAG optimization with user (Step 4 from plan)

---

**Status:** Plan Complete - Ready to Implement Test A + B
**Date:** 2025-11-14
**Estimated Time to Results:** 3 hours (2 hours implementation + 1 hour testing)
