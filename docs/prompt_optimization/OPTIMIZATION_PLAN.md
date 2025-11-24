# Prompt & RAG Optimization Plan - Option A

**Date:** 2025-11-14
**Strategy:** Freeze Phase 2 semantic layers, optimize prompts + RAG hyperparameters
**Target:** 84.2-85.2% accuracy (+0.5-1.5% from current 83.72%)

---

## Current Configuration

### LLM Settings
- **Model:** gpt-4o-mini
- **Temperature:** 0.0 (deterministic, confirmed by Test A)
- **Task:** enhanced_sql

### RAG Settings
- **top_k_chunks:** 10 (default)
- **Embedding model:** text-embedding-3-small (1536 dimensions)
- **Chunk type weights:**
  - table: 1.2 (boost table-specific docs)
  - cross_table_patterns: 1.1 (boost multi-table patterns)
  - overview: 0.7 (penalize generic overviews)
  - ambiguities: 0.6 (penalize ambiguities)

### System Prompt
- **Length:** ~4828 characters
- **Guidelines:** 10 main rules + 5 error-prevention rules (13-17)
- **Examples:** 6 examples covering aggregation, case sensitivity, disambiguation
- **Structure:** Comprehensive, covers most common error patterns

---

## Analysis: Current System Prompt

### Strengths

1. **Comprehensive Guidelines** (Lines 342-373)
   - Syntax instructions ✅
   - Table qualification ✅
   - Column disambiguation ✅
   - Aggregation vs sorting (CRITICAL) ✅
   - Case sensitivity (SQLite) ✅

2. **Error Prevention Rules** (Lines 124-149 in baseline prompt, copied to enhanced)
   - Only SELECT requested columns ✅
   - Only JOIN when necessary ✅
   - Include bridge tables for many-to-many ✅
   - Match FK direction to question intent ✅
   - GROUP BY ID columns, not names ✅

3. **Examples** (Lines 376-409)
   - Aggregation patterns ✅
   - Case sensitivity ✅
   - Column disambiguation ✅

### Weaknesses

1. **Missing Semantic Layer Utilization Guidance**
   - Current prompt mentions semantic layer in preamble but doesn't explain HOW to use Phase 2 structured fields
   - No guidance on prioritizing relationship `join_pattern` fields
   - No guidance on using column `disambiguation` fields
   - No examples showing semantic layer usage

2. **Missing Spider-Specific Patterns**
   - No guidance on common Spider dataset patterns
   - No examples for bridge table identification (e.g., pets_1)
   - No examples for FK direction disambiguation (e.g., network_1)

3. **Too Much Text, Not Enough Structure**
   - 4828 characters is long for gpt-4o-mini context
   - Could reorganize to put most critical rules first
   - Could use more concise language

4. **No Few-Shot Examples with Semantic Layer**
   - Examples don't show how to USE semantic layer fields
   - No before/after examples showing semantic layer benefit

---

## Optimization Opportunities

### Opportunity 1: Add Semantic Layer Utilization Guidance (HIGH IMPACT)

**Problem:** Prompt doesn't explain how to use Phase 2 structured fields.

**Solution:** Add explicit section on semantic layer usage.

**Proposed Addition:**
```
USING SEMANTIC LAYER EFFECTIVELY:

When semantic layer context is provided, use it to:

1. **Relationship Guidance** - Check `join_pattern` and `when_to_use` fields:
   - These fields provide explicit JOIN syntax and usage scenarios
   - Follow the recommended join patterns to avoid incorrect relationships
   - Example: If semantic layer says "JOIN students ON pets.student_id = students.id"
     → Use this EXACT join pattern, don't invent your own

2. **Column Disambiguation** - Check `disambiguation` fields for columns in 2+ tables:
   - `primary_location`: Which table "owns" this column (source of truth)
   - `directional_guidance`: How to use this column correctly
   - `subject_vs_relationship`: Whether column represents subject or relationship
   - Example: If `Name` appears in both Student and Pet tables:
     → Check disambiguation to know which table's Name to use

3. **Bridge Table Identification** - Check `is_bridge_table` field:
   - Many-to-many relationships REQUIRE the bridge table
   - If a table has `is_bridge_table: true`, include it in joins
   - Example: Student ↔ Has_Pet ↔ Pet requires Has_Pet in the JOIN

4. **Business Terms** - Map question terms to technical names:
   - Check `business_name` and `synonyms` fields
   - Example: Question says "average pet weight" → column is `weight`, synonym is "mass"
```

**Expected Impact:** 0.3-0.5% accuracy gain

---

### Opportunity 2: Optimize RAG top_k (MEDIUM IMPACT)

**Problem:** Current top_k=10 may retrieve too much noise OR miss important chunks.

**Analysis:**
- Test B showed RAG is deterministic (same chunks every time)
- But we don't know if top_k=10 is optimal
- Too many chunks = noise, too few = missing context

**Proposed Test:**
Test top_k values: 5, 7, 10, 15, 20

**Hypothesis:**
- top_k=5: May miss important context (especially for complex databases like dog_kennels with 8 tables)
- top_k=7: Sweet spot for most databases
- top_k=10: Current default (baseline)
- top_k=15: More context, but may add noise
- top_k=20: Likely too much noise

**Test Method:**
1. Pick 3 databases with varying complexity:
   - Simple: pets_1 (3 tables, 42 questions)
   - Medium: car_1 (6 tables, 92 questions)
   - Complex: dog_kennels (8 tables, 81 questions)
2. Run each database with top_k = 5, 7, 10, 15, 20
3. Measure accuracy for each top_k
4. Identify optimal top_k

**Expected Impact:** 0.1-0.3% accuracy gain (may vary by database)

---

### Opportunity 3: Adjust Chunk Type Weights (LOW IMPACT)

**Problem:** Current weights may not be optimal.

**Current Weights:**
- table: 1.2 (boost)
- cross_table_patterns: 1.1 (boost)
- overview: 0.7 (penalize)
- ambiguities: 0.6 (penalize)

**Proposed Changes:**

**Option A: Boost table chunks more aggressively**
- table: 1.5 (increase from 1.2)
- cross_table_patterns: 1.2 (increase from 1.1)
- overview: 0.5 (decrease from 0.7)
- ambiguities: 0.4 (decrease from 0.6)

**Rationale:** Table-specific docs are most valuable; overviews and ambiguities add noise.

**Option B: Differentiate single-table vs multi-table patterns**
- table: 1.3 (slight increase)
- cross_table_patterns: 1.5 (increase from 1.1) - multi-table questions need relationship context
- overview: 0.6 (slight decrease)
- ambiguities: 0.5 (slight decrease)

**Rationale:** Multi-table questions benefit most from relationship guidance.

**Expected Impact:** 0.0-0.2% accuracy gain (small effect)

---

### Opportunity 4: Add Phase 2-Specific Examples (MEDIUM IMPACT)

**Problem:** Examples don't show how Phase 2 structured fields help.

**Proposed Examples:**

```
USING SEMANTIC LAYER - BRIDGE TABLE EXAMPLE:
Question: "Find names of students who have pets"
Schema: Student(StuID, Name), Has_Pet(StuID, PetID), Pets(PetID, PetName)
Semantic Layer: Has_Pet has `is_bridge_table: true`, `join_pattern: "Student → Has_Pet → Pets"`

WRONG (missing bridge table):
SELECT DISTINCT Student.Name FROM Student
JOIN Pets ON Student.StuID = Pets.StuID

CORRECT (using bridge table per semantic layer):
SELECT DISTINCT Student.LName FROM Student
JOIN Has_Pet ON Student.StuID = Has_Pet.StuID
JOIN Pets ON Has_Pet.PetID = Pets.PetID

Why: Semantic layer's `is_bridge_table` field identifies Has_Pet as required for many-to-many relationship.

USING SEMANTIC LAYER - FK DIRECTION EXAMPLE:
Question: "Count friends Kyle has"
Schema: Friend(student_id, friend_id), Highschooler(ID, name)
Semantic Layer: Friend.student_id has `directional_guidance: "The subject who HAS friends"`

WRONG (reversed FK):
SELECT COUNT(*) FROM Friend
JOIN Highschooler ON Friend.friend_id = Highschooler.ID
WHERE Highschooler.name = 'Kyle'

CORRECT (following semantic layer guidance):
SELECT COUNT(*) FROM Friend
JOIN Highschooler ON Friend.student_id = Highschooler.ID
WHERE Highschooler.name = 'Kyle'

Why: Semantic layer's `directional_guidance` clarifies that student_id is the subject (who has friends), not friend_id.
```

**Expected Impact:** 0.2-0.4% accuracy gain

---

### Opportunity 5: Reorganize Prompt for Clarity (LOW IMPACT)

**Problem:** Most critical rules are buried in the middle of the prompt.

**Proposed Structure:**
1. **Preamble** (what you are, what you do)
2. **MOST CRITICAL RULES FIRST** (aggregation vs sorting, bridge tables, FK direction)
3. **Database-specific instructions** (syntax, qualification)
4. **Standard SQL best practices** (JOINs, WHERE, ORDER BY)
5. **Semantic layer usage** (how to use Phase 2 fields)
6. **Error prevention** (case sensitivity, column disambiguation)
7. **Examples** (6-8 examples covering all critical patterns)

**Expected Impact:** 0.1-0.2% accuracy gain (clearer structure)

---

## Recommended Implementation Plan

### Phase 1: High-Impact Prompt Improvements (1-2 hours)

**Changes:**
1. Add Semantic Layer Utilization Guidance section (Opportunity 1)
2. Add Phase 2-Specific Examples (Opportunity 4)
3. Reorganize prompt structure (Opportunity 5)

**Expected Gain:** 0.6-1.1%

**Testing:**
- Run 3 databases (pets_1, car_1, dog_kennels) with new prompt
- Compare to Run 20 baseline
- Verify improvements on regressed databases (car_1: 63→66+, world_1: 88→91+)

---

### Phase 2: RAG Hyperparameter Tuning (2-3 hours)

**Changes:**
1. Test top_k values: 5, 7, 10, 15, 20 (Opportunity 2)
2. Test chunk weight adjustments (Opportunity 3)

**Expected Gain:** 0.1-0.5%

**Testing:**
- Run same 3 databases with different top_k values
- Measure accuracy vs top_k
- Identify optimal top_k
- Test new chunk weights

---

### Phase 3: Full Validation (4-6 hours)

**Changes:**
1. Apply best prompt from Phase 1
2. Apply best RAG settings from Phase 2
3. Run FULL benchmark (all 20 databases, 1034 questions)

**Expected Result:** 84.2-85.2% accuracy (Run 22)

**Success Criteria:**
- Overall accuracy >= 84.2%
- Whack-a-mole effect reduced (fewer than 15 swings vs Run 20)
- Regressed databases recover (car_1: 63→66+, world_1: 88→91+)

---

## Risk Assessment

### Low Risk
- Phase 1 prompt improvements (deterministic system, can revert easily)
- RAG top_k tuning (only affects retrieval, not generation)

### Medium Risk
- Chunk weight changes (may help some databases, hurt others)
- Adding more examples (may make prompt too long, reduce effectiveness)

### High Risk
- NONE (we're keeping Phase 2 semantic layers frozen, only optimizing prompts/RAG)

---

## Rollback Plan

If any optimization makes results worse:

1. **Immediate Rollback:** Revert prompt changes in prompts.py, redeploy
2. **Partial Rollback:** Keep successful changes, remove unsuccessful ones
3. **Full Rollback:** Go back to Run 20 configuration (current baseline)

All changes are code-only (no semantic layer regeneration), so rollback is instant.

---

## Success Metrics

### Primary Metric: Overall Accuracy
- **Current (Run 20):** 83.72% (866/1034)
- **Target (Run 22):** 84.2-85.2% (871-881/1034)
- **Minimum Acceptable:** 84.0% (869/1034) - **+0.28% gain**

### Secondary Metric: Database Stability
- **Current Whack-a-Mole:** 19 swings between Run 19→20
- **Target:** <15 swings between Run 20→22
- **Stretch Goal:** <10 swings (high stability)

### Tertiary Metric: Regressed Database Recovery
- **car_1:** 63/92 (68.5%) → **Target: 66+/92 (71.7%+)**
- **world_1:** 88/120 (73.3%) → **Target: 91+/120 (75.8%+)**

---

## Timeline

### Week 1 (Nov 14-15)
- ✅ Test A: Temperature determinism complete
- ✅ Test B: RAG stability complete
- ✅ Analysis: Optimization opportunities identified
- 📋 Phase 1: Implement prompt improvements (1-2 hours)
- 📋 Phase 1: Test on 3 databases (1 hour)

### Week 2 (Nov 18-20)
- 📋 Phase 2: Test RAG hyperparameters (2-3 hours)
- 📋 Phase 2: Identify optimal settings (1 hour)
- 📋 Phase 3: Full benchmark run (4-6 hours)
- 📋 Phase 3: Analysis and documentation (1-2 hours)

**Total Estimated Time:** 10-15 hours
**Total Estimated Cost:** $5-10 in API calls

---

## Files to Modify

1. **`backend/app/services/llm/prompts.py`**
   - `enhanced_sql_system()` - add semantic layer guidance
   - Add new examples for Phase 2 fields
   - Reorganize structure

2. **`backend/app/services/embedding_service.py`**
   - `CHUNK_TYPE_WEIGHTS` - adjust weights if Phase 2 testing shows benefit

3. **`backend/app/services/text_to_sql/enhanced.py`**
   - `top_k_chunks` default value - adjust if Phase 2 testing shows benefit

4. **`backend/app/services/llm/config.py`**
   - (No changes - temperature=0.0 is already optimal)

---

## Next Steps

1. ✅ Document optimization plan (this file)
2. ⏭️ Implement Phase 1 prompt improvements
3. ⏭️ Test Phase 1 on 3 databases
4. ⏭️ Analyze Phase 1 results
5. ⏭️ Implement Phase 2 RAG tuning
6. ⏭️ Test Phase 2 on 3 databases
7. ⏭️ Run Phase 3 full benchmark (Run 22)
8. ⏭️ Document final results

---

**Status:** Plan Complete - Ready to Implement Phase 1
**Date:** 2025-11-14
**Expected Completion:** Nov 20, 2025
