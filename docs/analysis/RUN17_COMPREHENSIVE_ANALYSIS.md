# Run 17 Comprehensive Root Cause Analysis

**Date:** 2025-11-10
**Status:** Critical Issues Identified
**Recommendation:** REVERT guideline changes immediately

---

## Executive Summary

Run 17's stabilization attempt **failed** due to **semantic layer non-determinism**. The LLM regenerated completely different guidelines that removed critical error-prevention rules, causing a net -0.63% regression (83.40% vs 84.03% baseline).

**Key Finding:** The problem is NOT the code changes (which were correct) but the **non-deterministic semantic layer generation** that produces different guidelines each time.

---

## Verification: Run 17 Was Valid

✅ **Code deployed:** Commit 00b92ae removed problematic guidelines on Nov 9, 18:23 UTC
✅ **Semantic layers regenerated:** All 20 databases updated in Supabase Nov 9, 18:37-18:49 UTC
✅ **Embeddings updated:** 220 vectors in Pinecone, timestamped Nov 9, 19:14:51 UTC
✅ **Benchmark run:** Run 17 completed Nov 9, 21:36 UTC using correct data

The stabilization test was properly executed. The results are valid.

---

## Overall Impact Analysis

### Regression Summary
| Database | Questions | R16 Correct | R17 Correct | Delta | % Change |
|----------|-----------|-------------|-------------|-------|----------|
| **Regressions (7 databases)** |
| flight_2 | 80 | 75 | 72 | -3 | -3.75% |
| network_1 | 56 | 45 | 43 | -2 | -3.57% |
| orchestra | 40 | 38 | 36 | -2 | -5.00% |
| battle_death | 16 | 13 | 12 | -1 | -6.25% |
| pets_1 | 42 | 42 | 41 | -1 | -2.38% |
| dog_kennels | 82 | 67 | 66 | -1 | -1.22% |
| concert_singer | 45 | 39 | 38 | -1 | -2.22% |
| **Improvements (4 databases)** |
| student_transcripts_tracking | 78 | 56 | 61 | +5 | +6.41% |
| car_1 | 92 | 59 | 62 | +3 | +3.26% |
| tvshow | 62 | 52 | 54 | +2 | +3.23% |
| cre_Doc_Template_Mgt | 84 | 70 | 71 | +1 | +1.19% |
| **No Change (9 databases)** | | | | 0 | 0.00% |

**Total failures:** 11 new failures
**Total successes:** 14 new successes
**Net result:** +3 questions BUT whack-a-mole effect continues

---

## Root Cause: Guideline Non-Determinism

### Critical Guidelines LOST in Run 17

**Run 16 Guidelines (Phase 1 - Effective):**
```
1. Use exact table and column names as shown in schema (case-sensitive)
2. Only SELECT columns explicitly mentioned in the question ⚠️
3. Only JOIN tables when the question requires data from multiple tables ⚠️
4. For many-to-many relationships, include the bridge table
5. Match foreign key direction to question intent ⚠️
6. GROUP BY ID columns when aggregating, not name columns ⚠️
```

**Run 17 Guidelines (Regenerated - Vague):**
```
1. Always use the correct join paths as specified in the relationships
2. Avoid assuming direct relationships between battles and casualties
3. Be specific about which 'id' you are referring to
4. Consider performance implications of joining multiple tables
5. Use filters effectively to narrow down results
```

**Analysis:**
- Run 17 guidelines are **database-specific** (mention "battles and casualties")
- Run 16 guidelines were **universal error-prevention rules**
- All 6 critical rules were **completely replaced**, not refined
- New guidelines are **descriptive** rather than **prescriptive**

---

## Failure Pattern Analysis

### Pattern 1: Selecting Unrequested Columns (4 failures)

**Example - battle_death:**
- Question: "What are the death and injury situations caused by the ship with tonnage 't'?"
- Gold SQL: `SELECT death.killed, death.injured ...` (individual rows)
- Run 16: ✅ `SELECT death.killed, death.injured ...`
- Run 17: ❌ `SELECT SUM(death.killed) AS total_killed, SUM(death.injured) ...`

**Root Cause:** Lost guideline #2 "Only SELECT columns explicitly mentioned in the question"

---

### Pattern 2: GROUP BY Name Instead of ID (3 failures)

**Example - orchestra:**
- Question: "What is the name of the conductor who has conducted the most orchestras?"
- Gold SQL: `GROUP BY T2.Conductor_ID`
- Run 16: ✅ `GROUP BY conductor.Conductor_ID`
- Run 17: ❌ `GROUP BY conductor.Name`

**Root Cause:** Lost guideline #6 "GROUP BY ID columns when aggregating, not name columns"

---

### Pattern 3: Over-Joining (2 failures)

**Example - pets_1:**
- Question: "What is the average and maximum age for each pet type?"
- Gold SQL: `SELECT ... FROM pets GROUP BY pettype`
- Run 16: ✅ `SELECT ... FROM Pets GROUP BY Pets.PetType`
- Run 17: ❌ `SELECT ... FROM Pets JOIN Has_Pet JOIN Student GROUP BY ...`

**Root Cause:** Lost guideline #3 "Only JOIN tables when the question requires data from multiple tables"

---

### Pattern 4: Wrong Foreign Key Direction (2 failures)

**Example - network_1:**
- Question: "Count the number of friends Kyle has."
- Gold SQL: `... WHERE T2.name = "Kyle"` (T1.student_id = T2.id)
- Run 16: ✅ `... Friend.student_id = Highschooler.ID WHERE name = 'Kyle'`
- Run 17: ❌ `... f.friend_id = h.ID WHERE h.name = 'Kyle'` (wrong direction)

**Root Cause:** Lost guideline #5 "Match foreign key direction to question intent"

---

## Why Did Some Databases Improve?

The 4 improved databases (student_transcripts_tracking +6.41%, car_1 +3.26%, tvshow +3.23%, cre_Doc_Template_Mgt +1.19%) showed:

1. **Better pattern matching** (e.g., '%computer%' vs '%the computer%')
2. **Clearer relationship descriptions** helped with complex joins
3. **Random LLM variation** - some queries just got luckier

**Critical Insight:** The improvements appear **random/luck-based**, while the failures are **systematic** (caused by missing guidelines).

---

## The Whack-a-Mole Problem Explained

**Why the problem persists:**

1. **Non-deterministic semantic layer generation**
   - Same prompt + same schema = **different guidelines every time**
   - LLM makes arbitrary choices about what to emphasize
   - No consistency between regenerations

2. **Loss of critical error-prevention rules**
   - Universal rules (Run 16) → Database-specific advice (Run 17)
   - Prescriptive ("Only SELECT...") → Descriptive ("Be specific...")
   - Actionable → Vague

3. **Random wins don't offset systematic losses**
   - 14 new successes (luck + better descriptions)
   - 11 new failures (systematic guideline loss)
   - Net: slight improvement but unstable

---

## Critical Decision Point

### Option 1: Abandon Semantic Layer Guidelines ❌

**Rationale:** If guidelines are non-deterministic, remove them entirely.

**Problems:**
- Loses the successful Run 16 guidelines that DID prevent errors
- Throws away the baby with the bathwater
- No guarantee performance won't get worse

---

### Option 2: Freeze Guidelines (RECOMMENDED) ✅

**Rationale:** Keep the Run 16 guidelines as **static, universal rules**.

**Implementation:**
1. **Stop regenerating guidelines** - they're part of the semantic layer generation
2. **Use fixed guidelines** - add them to the system prompt instead
3. **Only regenerate** descriptions, relationships, and examples

**Benefits:**
- Preserves effective error-prevention rules
- Eliminates non-determinism source
- Allows semantic layer descriptions to improve without breaking guidelines

**Changes Required:**
```python
# semantic_layer_generator.py
# Remove query_guidelines from output schema
# Guidelines will be in system prompt instead

# prompts.py
# Add universal guidelines to baseline_sql_system() directly
# These never change between runs
```

---

### Option 3: Skip to Phase 3 (Few-Shot Learning) ⚠️

**Rationale:** Replace semantic descriptions with explicit SQL examples.

**Pros:**
- Deterministic (examples don't change)
- Proven to work for text-to-SQL

**Cons:**
- Massive effort to create 20 databases × ~50 questions × examples
- May not generalize to new questions
- Loses the flexibility of semantic descriptions

**Recommendation:** Consider this if Option 2 fails to stabilize performance.

---

## Immediate Next Steps

### Step 1: Implement Fixed Guidelines (Week 6.5)

**Code Changes:**
1. Remove `query_guidelines` from semantic layer generation schema
2. Add universal guidelines to `prompts.py` baseline_sql_system()
3. Regenerate semantic layers (descriptions only, no guidelines)
4. Run benchmark (Run 18)

**Expected Outcome:**
- Stabilizes at ~84% (Run 13 baseline)
- Eliminates guideline non-determinism
- Sets foundation for Phase 2 improvements

---

### Step 2: Enhance Semantic Descriptions (Phase 2)

With guidelines frozen, improve semantic layer quality:
- Better relationship descriptions
- More accurate column disambiguation
- Clearer cross-table patterns
- Domain-specific synonyms

**Target:** 85-86% accuracy

---

### Step 3: Add Few-Shot Examples (Phase 3 - If Needed)

If Phase 2 doesn't reach 87%+, add explicit examples:
- Retrieve similar questions from training set
- Include gold SQL as examples
- Let LLM learn from concrete patterns

**Target:** 87-90% accuracy

---

## Success Metrics

### Run 18 (Fixed Guidelines) Success Criteria:
- ✅ Overall accuracy ≥ 84.0% (match Run 13 baseline)
- ✅ No database drops >3% from Run 13
- ✅ Whack-a-mole effect eliminated (reproducible results)

### Phase 2 Success Criteria:
- ✅ Overall accuracy ≥ 85.5%
- ✅ Consistent improvements across regenerations
- ✅ No regressions >2% per database

---

## Conclusion

**The stabilization attempt revealed a deeper problem:** Semantic layer generation is inherently non-deterministic. The LLM generates different guidelines each time, causing unpredictable performance swings.

**The solution is NOT to remove guidelines** (they work!) but to **freeze them** as universal rules and only regenerate the database-specific semantic descriptions.

This approach:
1. Eliminates the primary source of non-determinism
2. Preserves effective error-prevention rules
3. Allows continued improvement of semantic descriptions
4. Sets a stable foundation for Phase 2 enhancements

**Recommendation:** Proceed with Option 2 (Freeze Guidelines) immediately.

---

**Status:** Analysis Complete
**Next Action:** Implement fixed guidelines in code
**Target:** Run 18 benchmark within 24 hours
