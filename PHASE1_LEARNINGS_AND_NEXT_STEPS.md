# Phase 1 Learnings and Next Steps

## Performance History Summary

| Run | Date | Accuracy | Change | Description |
|-----|------|----------|--------|-------------|
| Run 13 | Nov 5 | 84.03% | Baseline | Before Phase 1 changes |
| Run 14 | Nov 6 | 83.82% | -0.21% | Prescriptive guidelines in semantic layers |
| Run 15 | Nov 6 | 83.51% | -0.52% | Error-prevention guidelines in semantic layers |
| Run 16 | Nov 7 | 83.40% | -0.63% | Guidelines moved to system prompt |

## Phase 1 Key Learnings

### ❌ What Didn't Work

1. **Guidelines in Semantic Layers are Non-Deterministic**
   - Each LLM generation creates slightly different content
   - Guidelines vary between regenerations causing instability
   - Fixing one database breaks others unpredictably
   - Example: Run 14 fixed network_1 but broke pets_1

2. **System Prompt Guidelines Create Conflicts**
   - New guidelines conflict with existing ones
   - LLM doesn't know which to prioritize
   - "Whack-a-mole" effect: fixing voter_1 broke network_1
   - Example: "SELECT only requested columns" conflicts with "GROUP BY IDs not names"

3. **Syntactic Rules Don't Fix Semantic Problems**
   - "students who have likes" is ambiguous (give vs receive)
   - Rules can't resolve meaning, only syntax
   - Need better semantic descriptions, not more rules

### ✅ What Did Work

1. **Turso Schema Extraction**
   - Successfully preserves case sensitivity
   - File: `backend/app/database/turso_schema_extractor.py`
   - Result: network_1 correctly has "Friend", "Highschooler", "Likes"

2. **Some Targeted Improvements**
   - voter_1: Fixed in Run 16 (+13.3% recovery from Run 15)
   - pets_1: Reached 100% in Run 16
   - battle_death: +6.3% in Run 16

3. **Case Sensitivity Guidance in System Prompt**
   - Guideline 12 in `backend/app/services/llm/prompts.py`
   - Consistently works across all runs

## Detailed Failure Analysis

### Run 16 New Regressions

**network_1 regressions (-5.4%):**

1. **dev_0904**: "Show the names of high schoolers who have likes, and numbers of likes for each."
   - Run 15 ✅: `GROUP BY Highschooler.ID`
   - Run 16 ❌: `GROUP BY Highschooler.name` (names can duplicate!)
   - **Cause**: New "SELECT only requested columns" overrode "GROUP BY IDs not names"

2. **dev_0906**: "What is the name of the high schooler who has the greatest number of likes?"
   - Run 15 ✅: Joined on `student_id` (students WHO GIVE likes)
   - Run 16 ❌: Joined on `liked_id` (students WHO RECEIVE likes)
   - **Cause**: Ambiguous question - semantically unclear

3. **dev_0914**: "Find the average grade of all students who have some friends."
   - Run 15 ✅: `WHERE ID IN (SELECT student_id FROM Friend)`
   - Run 16 ❌: `INNER JOIN Friend` without GROUP BY (creates duplicates)
   - **Cause**: New INNER JOIN guidance over-applied. For filtering, WHERE IN is better

**car_1 regressions (-5.4%):**
- Similar patterns observed
- Need detailed analysis

## Next Steps Plan

### Step 1: Stabilize Current State (Priority 1)

**Goal**: Stop the bleeding, establish stable baseline at ~84%

**Actions**:

1. **Revert Guideline Changes**
   ```bash
   # Revert commit 7d2f45b (semantic layer generator guidelines)
   # Revert commit 10b95f2 (system prompt guidelines 3-4)
   # Keep Turso extraction changes
   ```

2. **Files to Modify**:
   - `backend/app/services/semantic_layer_generator.py`
     - Remove SQL Query Generation Guidelines section (lines 270-303)
     - Keep Turso extraction logic

   - `backend/app/services/llm/prompts.py`
     - Remove new Guidelines 3-4 (JOIN types, SELECT columns)
     - Keep existing Guidelines 1-2, 5-12
     - Keep case sensitivity guidance (proven stable)
     - Keep aggregation vs sorting guidance (proven stable)

3. **Regenerate Semantic Layers**
   - Via Vercel UI: Regenerate all 20 databases
   - Focus on accurate descriptions, not prescriptive rules
   - Let LLM generate content naturally without guideline constraints

4. **Run Benchmark Run 17**
   - Target: ≥84.0% (match Run 13 baseline)
   - Success criteria: No database regression >5%

### Step 2: Phase 2 - Semantic Understanding (Priority 2)

**Goal**: Fix semantic ambiguities through better descriptions, not syntax rules

**Approach 1: Enhanced Column Disambiguation**

Add directional meaning to ambiguous columns:

```json
{
  "name": "student_id",
  "business_meaning": "The student who GIVES the like (not receives)",
  "directional_context": {
    "in_likes_table": "This is the liker, not the liked",
    "common_mistake": "Don't confuse with liked_id (the recipient)"
  }
}
```

**Approach 2: Query Pattern Examples**

Add successful query patterns to semantic layers:

```json
{
  "common_query_patterns": [
    {
      "question_pattern": "students who have likes",
      "means": "students who GIVE likes",
      "correct_join": "JOIN Likes ON Highschooler.ID = Likes.student_id",
      "wrong_join": "JOIN Likes ON Highschooler.ID = Likes.liked_id"
    },
    {
      "question_pattern": "average grade of students who have friends",
      "approach": "Filter first, then aggregate",
      "correct": "WHERE ID IN (SELECT student_id FROM Friend)",
      "wrong": "INNER JOIN Friend (creates duplicates)"
    }
  ]
}
```

**Approach 3: Few-Shot Learning**

Add successful examples to system prompt at query time:

```python
# In enhanced_sql_system() prompt
For databases with directional relationships, be aware:

Example (network_1):
Q: "Find students who have likes"
Correct: JOIN Likes ON Highschooler.ID = Likes.student_id (student GIVES likes)
Wrong: JOIN Likes ON Highschooler.ID = Likes.liked_id (student RECEIVES likes)

Example (network_1):
Q: "Average grade of students who have friends"
Correct: WHERE ID IN (SELECT student_id FROM Friend) (filter, no duplicates)
Wrong: INNER JOIN Friend (creates duplicate rows, inflates average)
```

### Step 3: Targeted Database Fixes (Priority 3)

Focus on consistently poor performers:

1. **wta_1** (32.3%) - worst performer, needs investigation
2. **car_1** (64-70%) - unstable across runs
3. **student_transcripts_tracking** (71-74%) - complex schema

## Implementation Timeline

### Week 1: Stabilization
- Day 1: Revert problematic changes, keep Turso extraction
- Day 2: Simplify system prompt, remove conflicting guidelines
- Day 3: Regenerate all 20 semantic layers
- Day 4: Run benchmark Run 17
- Day 5: Analyze Run 17, confirm stability

### Week 2: Phase 2 Design
- Day 1-2: Design enhanced column disambiguation format
- Day 3: Design query pattern examples format
- Day 4: Design few-shot learning approach
- Day 5: Prototype on network_1 (test case)

### Week 3: Phase 2 Implementation
- Day 1-2: Implement semantic layer generator enhancements
- Day 3: Regenerate semantic layers with Phase 2 features
- Day 4: Run benchmark Run 18
- Day 5: Analyze results, iterate if needed

## Success Criteria

### Stabilization Phase (Run 17)
- ✅ Performance ≥ 84.0% (match Run 13 baseline)
- ✅ No database regression > 5%
- ✅ Consistent results across runs (no whack-a-mole)

### Phase 2 (Run 18)
- ✅ Performance ≥ 85.0% (+1% from baseline)
- ✅ network_1 ≥ 87% (fix ambiguous JOIN cases)
- ✅ voter_1 maintains 93%+ (don't break what works)
- ✅ car_1 stabilizes around 70%+

## Decision Points

**After Run 17**:
- If ≥84%: Proceed to Phase 2
- If <84%: Analyze what's still broken, adjust stabilization

**After Run 18**:
- If ≥85%: Phase 2 successful, iterate on remaining issues
- If 84-85%: Marginal improvement, reassess approach
- If <84%: Phase 2 made things worse, revert to Run 17 baseline

## Files Changed (Current State)

### Commits to Keep
- ✅ Turso schema extraction: `backend/app/database/turso_schema_extractor.py`
- ✅ Generator using Turso: `backend/app/services/semantic_layer_generator.py` (Turso parts only)

### Commits to Revert
- ❌ Commit 7d2f45b: Semantic layer generator guidelines (lines 270-303)
- ❌ Commit 10b95f2: System prompt guidelines 3-4 (conflicting rules)

### Files to Update for Stabilization
1. `backend/app/services/semantic_layer_generator.py`
   - Remove: Lines 270-303 (SQL Query Generation Guidelines)
   - Keep: Turso extraction logic (lines 19-70)

2. `backend/app/services/llm/prompts.py`
   - Remove: New Guidelines 3-4 (JOIN types, SELECT columns)
   - Keep: Guidelines 1-2, 5-12 (non-conflicting)

## Risk Mitigation

1. **Test each change incrementally** - Don't batch multiple changes
2. **Keep Run 13 semantic layers backed up** - Can revert if needed
3. **Focus on top 3 failing databases** - Don't try to fix everything at once
4. **Measure twice, regenerate once** - Regeneration is expensive (time + cost)

## Technical Debt Created

1. **Semantic Layer Non-Determinism**
   - Current approach relies on LLM generation consistency
   - Need to investigate making key parts deterministic
   - Consider template-based generation for critical sections

2. **Guideline Conflict Resolution**
   - No mechanism to prioritize conflicting guidelines
   - LLM can't reason about which rule to apply when
   - Phase 2 should avoid adding more guidelines

3. **Semantic Ambiguity**
   - Many questions are genuinely ambiguous
   - "students who have likes" = give OR receive?
   - Need better disambiguation in semantic layer content

## References

- **Benchmark results**: Supabase `benchmark_runs` and `benchmark_results` tables
- **Schema files**: `data/spider/database/*/schema.sql` (local reference only)
- **Turso databases**: Actual source of truth for schema with correct case
- **Semantic layers**: Supabase `semantic_layers` table (generated)
- **Vector embeddings**: Pinecone `querydawg-semantic` index

---

**Document Status**: Living document, update after each benchmark run
**Last Updated**: 2025-11-07 after Run 16 analysis
**Next Review**: After Run 17 completion
