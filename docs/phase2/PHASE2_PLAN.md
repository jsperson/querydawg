# Phase 2 Plan: Semantic Layer Quality Improvements

**Start Date:** 2025-11-11
**Target Completion:** 2025-11-15
**Duration:** ~5 days

**Goal:** Improve semantic layer description quality to reach 85.5%+ accuracy while maintaining Phase 1 frozen guidelines

---

## Executive Summary

Phase 1 successfully stabilized accuracy at 83.80% by freezing universal guidelines in the system prompt. However, the whack-a-mole effect persists due to **semantic layer description variance** between regenerations.

Phase 2 will focus on improving the **quality** and **determinism** of semantic layer descriptions without changing the frozen guidelines. The target is 85.5%+ accuracy with reduced variance between runs.

---

## Current State Analysis

### What's Working (Phase 1)
- ✅ Frozen guidelines (rules 13-17) in system prompt
- ✅ Universal error-prevention rules (GROUP BY ID, FK direction, etc.)
- ✅ Clean Pinecone index (140 vectors, no guideline chunks)
- ✅ Auto-delete embedding pipeline

### What's Not Working
- ⚠️ Semantic descriptions vary between regenerations
- ⚠️ Relationship explanations are sometimes vague
- ⚠️ Column disambiguation is inconsistent
- ⚠️ Whack-a-mole effect (tvshow -4%, dog_kennels -2%, etc.)

### Root Cause
The LLM generating semantic layers produces different descriptions each time:
- Relationship wording changes
- Column disambiguation varies
- Cross-table pattern explanations differ
- This causes different chunks to be retrieved for similar questions
- Different retrieval → different SQL generation

---

## Phase 2 Priorities

### Priority 1: Relationship Descriptions (HIGH)

**Problem:**
Current relationship descriptions vary between runs:
- Run A: "Links students to courses"
- Run B: "Associates enrollments with course records"

Different wording → different vector embeddings → different retrieval results

**Solution:**
Add **deterministic structure** to relationship descriptions:

```python
# Current prompt (non-deterministic)
"Explain how this foreign key relationship works"

# Phase 2 prompt (deterministic structure)
"For each relationship, provide:
1. **Relationship type**: [one-to-many | many-to-one | many-to-many]
2. **Bridge table**: [Yes/No, table name if yes]
3. **Join path**: Explicit SQL join syntax
4. **When to use**: Specific question patterns that need this join
5. **Common mistakes**: What NOT to do

Format each field consistently using the exact template above."
```

**Example Improvement:**

*Current (variable):*
```
"Links students to their permanent addresses"
```

*Phase 2 (structured):*
```
Relationship: Students → Addresses (permanent_address_id)
Type: many-to-one
Bridge table: No
Join path: Students.permanent_address_id = Addresses.address_id
When to use: Questions about "permanent address", "home address", "where student lives"
Common mistakes: DO NOT confuse with current_address_id (temporary address)
```

**Implementation:**
- Modify `semantic_layer_generator.py` relationship prompt
- Add structured template requirement
- Require specific field names and order
- Test on 2-3 databases for consistency

**Expected Impact:** +0.5-1.0% accuracy, reduced variance

---

### Priority 2: Column Disambiguation (HIGH)

**Problem:**
When a column appears in multiple tables (e.g., `student_id` in both `Students` and `Enrollments`), the current descriptions don't clearly explain which one to use when.

**Solution:**
Add **directional context** to column descriptions:

```python
# Current prompt
"What does this column mean?"

# Phase 2 prompt
"For columns that appear in multiple tables, explain:
1. **Primary location**: Which table 'owns' this column
2. **Foreign key locations**: Which tables reference it
3. **Usage guidance**: When to query the primary vs foreign key version
4. **Directional intent**: Use primary for 'about the entity', use FK for 'related to the entity'"
```

**Example Improvement:**

*Current (ambiguous):*
```
student_id: A unique identifier for each student
```

*Phase 2 (directional):*
```
student_id in Students table:
  Primary location: Students (this is the source of truth)
  Also appears in: Enrollments, Transcript_Contents
  Use Students.student_id when: Question is ABOUT a student (their name, age, address)
  Use Enrollments.student_id when: Question is about what courses a student is TAKING
  Use Transcript_Contents.student_id when: Question is about a student's TRANSCRIPT
  Direction: Students.student_id = subject, FK.student_id = relationship
```

**Implementation:**
- Add column appearance analysis to semantic layer generator
- Detect which columns appear in multiple tables
- Generate directional guidance for each appearance
- Include "subject vs relationship" pattern

**Expected Impact:** +0.5-1.0% accuracy

---

### Priority 3: Cross-Table Query Patterns (MEDIUM)

**Problem:**
Current cross-table patterns are descriptive but lack concrete examples:
- "To find courses a student is taking, join Students with Enrollments"
- Missing: How to handle bridge tables, what to SELECT, how to filter

**Solution:**
Add **concrete SQL examples** to cross-table patterns:

```python
# Current prompt
"Describe common multi-table query patterns"

# Phase 2 prompt
"For each cross-table pattern, provide:
1. **Example question**: Natural language question
2. **Tables involved**: List in join order
3. **SQL template**: Concrete SQL with placeholders
4. **Key points**: What makes this pattern work
5. **Common errors**: What often goes wrong"
```

**Example Improvement:**

*Current (vague):*
```
Pattern: Student-Course Enrollment
Description: To find courses a student is taking, join Students with Enrollments and Courses
```

*Phase 2 (concrete):*
```
Pattern: Student-Course Enrollment
Example question: "What courses is John Smith taking?"
Tables: Students → Enrollments → Courses (in that order)
SQL template:
  SELECT Courses.name
  FROM Students
  JOIN Enrollments ON Students.student_id = Enrollments.student_id
  JOIN Courses ON Enrollments.course_id = Courses.course_id
  WHERE Students.name = 'John Smith'
Key points:
  - Enrollments is the bridge table (many-to-many)
  - Filter on Students, SELECT from Courses
  - JOIN in order: Students → bridge → Courses
Common errors:
  - Skipping Enrollments bridge table
  - Joining Courses directly to Students (no direct FK)
```

**Implementation:**
- Modify cross_table_patterns generation
- Add SQL template field
- Include concrete WHERE/SELECT examples
- Emphasize bridge table usage

**Expected Impact:** +0.3-0.5% accuracy

---

### Priority 4: Domain-Specific Synonyms (LOW)

**Problem:**
Natural language varies: "permanent address" vs "home address" vs "primary residence"
Current synonym lists are incomplete

**Solution:**
Generate **comprehensive synonym lists** using LLM:

```python
# Add to domain glossary generation
"For each business term, generate:
1. **Common synonyms**: 5-10 ways users might phrase this
2. **Question patterns**: Example questions using each synonym
3. **Disambiguation**: When synonyms mean different things"
```

**Example:**
```
Term: Permanent Address
Synonyms:
  - "home address"
  - "primary residence"
  - "where student lives"
  - "residential address"
  - "permanent location"
  - "home location"
Question patterns:
  - "What is the home address of..."
  - "Where does the student live..."
  - "Show me the permanent residence..."
Maps to: Students.permanent_address_id → Addresses
NOT the same as: Current Address (temporary, Students.current_address_id)
```

**Implementation:**
- Enhance domain glossary prompt
- Generate 5-10 synonyms per term using LLM
- Include example question patterns
- Add disambiguation notes

**Expected Impact:** +0.2-0.3% accuracy

---

## Implementation Plan

### Week 1: Relationship Descriptions + Column Disambiguation (Nov 11-12)

**Day 1 (Nov 11):**
- [ ] Modify `semantic_layer_generator.py` relationship prompt
- [ ] Add structured template for relationships
- [ ] Add column appearance analysis
- [ ] Add directional disambiguation logic
- [ ] Test on 2-3 databases (student_transcripts_tracking, network_1, pets_1)
- [ ] Manual review of generated relationships

**Day 2 (Nov 12):**
- [ ] Refine prompts based on Day 1 results
- [ ] Regenerate all 20 semantic layers
- [ ] Verify no guideline chunks created
- [ ] Embed to Pinecone (auto-delete should work)
- [ ] Run benchmark Run 20
- [ ] Analyze results

**Expected Run 20 Result:** 84.5-85.0% (+0.7-1.2% from Run 19)

---

### Week 2: Cross-Table Patterns (Nov 13-14)

**Day 3 (Nov 13):**
- [ ] Modify cross_table_patterns generation
- [ ] Add SQL template field
- [ ] Add concrete examples
- [ ] Test on complex databases (student_transcripts_tracking, dog_kennels)
- [ ] Manual review of patterns

**Day 4 (Nov 14):**
- [ ] Refine cross-table prompts
- [ ] Regenerate all 20 semantic layers
- [ ] Embed to Pinecone
- [ ] Run benchmark Run 21
- [ ] Analyze results

**Expected Run 21 Result:** 85.0-85.5% (+0.3-0.5% from Run 20)

**Decision Point:** If Run 21 ≥ 85.5%, skip Day 5. If < 85.5%, proceed with synonyms.

---

### Week 3: Domain Synonyms (Optional, Nov 15)

**Day 5 (Nov 15) - Only if needed:**
- [ ] Enhance domain glossary generation
- [ ] Add synonym expansion logic
- [ ] Regenerate all 20 semantic layers
- [ ] Embed to Pinecone
- [ ] Run benchmark Run 22
- [ ] Final analysis

**Expected Run 22 Result:** 85.5-86.0% (+0.2-0.5% from Run 21)

---

## Success Criteria

### Must Have (Phase 2 Complete)
- ✅ Overall accuracy ≥ 85.5%
- ✅ No database regression > 2% from Run 19
- ✅ Relationship descriptions use structured template
- ✅ Column disambiguation includes directional guidance
- ✅ All changes documented and committed

### Should Have
- ✅ At least 3 databases showing 90%+ accuracy
- ✅ Whack-a-mole effect reduced (fewer random swings between runs)
- ✅ Cross-table patterns include SQL examples
- ✅ Run 20-21 show consistent improvement (not random variance)

### Nice to Have
- ✅ Domain glossary includes comprehensive synonyms
- ✅ 86%+ accuracy achieved
- ✅ All 20 databases show stability (< 2% variance)

---

## Risk Mitigation

### Risk 1: Changes make things worse
**Mitigation:** Test on 2-3 databases first, manual review before full regeneration

### Risk 2: LLM generates different structures anyway
**Mitigation:** Use explicit templates and field names, add "YOU MUST follow this exact format" instructions

### Risk 3: Whack-a-mole continues despite improvements
**Mitigation:** If Run 20 shows regression, revert and try smaller incremental changes

### Risk 4: Time constraints
**Mitigation:** Prioritize High > Medium > Low, skip synonyms if running behind

---

## Rollback Plan

If any run shows regression from Run 19 (< 83.80%):

1. **Stop immediately** - Don't regenerate further
2. **Analyze the regression** - Check which databases regressed
3. **Review generated semantic layers** - Look for problematic descriptions
4. **Rollback semantic layers** - Restore from Supabase backup
5. **Rollback Pinecone** - Re-run clear_and_reembed.py with old semantic layers
6. **Try smaller change** - Isolate which improvement caused regression

**Supabase Backup Strategy:**
- Before each regeneration, export semantic layers to JSON
- Store in `data/semantic_layers_backups/run{N}_backup.json`
- Can restore via Supabase UI or API

---

## Measurement & Tracking

### Before Each Run
1. Export current semantic layers to backup
2. Document exact prompt changes made
3. Test on 2-3 databases first
4. Manual review of generated descriptions

### After Each Run
1. Overall accuracy (target: ≥ 85.5%)
2. Per-database comparison vs Run 19
3. Count databases with >2% regression
4. Count databases with >2% improvement
5. Whack-a-mole metric: abs(sum(regressions) + sum(improvements))

### Documentation
- Create `RUN{N}_PHASE2_RESULTS.md` for each run
- Compare semantic layer descriptions before/after
- Track which changes improved/regressed accuracy

---

## Phase 2 Completion Criteria

Phase 2 is complete when ONE of these is true:

**Success Path:**
- ✅ Run 20, 21, or 22 achieves ≥ 85.5% accuracy
- ✅ No databases regressed > 2% from Run 19
- ✅ Improvements are deterministic (not random luck)

**Alternative Success:**
- ✅ Achieved maximum reasonable improvement (e.g., 85.0% with diminishing returns)
- ✅ Documented why 85.5% is not achievable with current approach
- ✅ Prepared plan for Phase 3 (few-shot learning)

**Failure Path (revert to Phase 1):**
- ❌ Multiple runs show regression from Run 19
- ❌ Changes increase variance instead of reducing it
- ❌ No consistent improvement pattern observed

---

## Next Steps After Phase 2

**If successful (≥ 85.5%):**
- Document Phase 2 learnings
- Optionally try targeted database improvements (wta_1, tvshow, dog_kennels)
- Move to Week 7 (polish, documentation, presentation)

**If plateau (84.5-85.4%):**
- Decide if diminishing returns justify Phase 3
- Consider Phase 3: Few-shot learning (SQL examples in prompts)
- Or declare current accuracy acceptable and move to documentation

**If regression:**
- Revert to Run 19 state
- Re-analyze root causes
- Try alternative Phase 2 approach

---

## Resources Needed

**Time:**
- 3-5 days of development and testing
- 3-5 benchmark runs (~2 hours each)
- Analysis and documentation time

**Cost:**
- Semantic layer regeneration: $0.06 per full regeneration
- Embeddings: $0.0009 per embedding run
- Benchmark runs: Free (using existing infrastructure)
- Total estimated: < $1.00

**Tools:**
- `semantic_layer_generator.py` - Modify prompts
- `regenerate_all_semantic_layers.py` - Regenerate layers
- `embed_semantic_layers.py` - Embed vectors
- Railway admin interface - Trigger benchmarks
- Supabase - Backup/restore semantic layers

---

## Appendix: Example Prompt Changes

### A. Relationship Description Prompt

**Current:**
```
For each foreign key relationship in the table, explain:
- What it links to
- The relationship type
- When you would use this join
```

**Phase 2:**
```
For each foreign key relationship in the table, provide the following structured information:

**Format (you MUST follow this exact structure):**

Relationship: {table1} → {table2} ({foreign_key_column})
Type: [one-to-many | many-to-one | many-to-many]
Bridge table: [Yes: {table_name} | No]
Join path: {table1}.{fk_column} = {table2}.{pk_column}
When to use: {specific question patterns that need this join}
Common mistakes: {what NOT to do}

**Example:**

Relationship: Students → Addresses (permanent_address_id)
Type: many-to-one
Bridge table: No
Join path: Students.permanent_address_id = Addresses.address_id
When to use: Questions about "permanent address", "home address", "where student lives"
Common mistakes: DO NOT confuse with current_address_id (temporary address)
```

### B. Column Disambiguation Prompt

**Current:**
```
Explain what this column means and provide example values.
```

**Phase 2:**
```
For each column, analyze if it appears in multiple tables.

**If column appears in ONLY this table:**
Standard description: {meaning, synonyms, examples}

**If column appears in MULTIPLE tables:**
{column_name} in {this_table} table:
  Primary location: {table that owns this column}
  Also appears in: {list other tables}
  Use {this_table}.{column_name} when: {specific use case}
  Use {other_table}.{column_name} when: {specific use case}
  Direction: {primary_table}.{column_name} = subject, FK.{column_name} = relationship

**Example:**

student_id in Students table:
  Primary location: Students (source of truth)
  Also appears in: Enrollments, Has_Pet, Transcript_Contents
  Use Students.student_id when: Question is ABOUT a student (name, age, info)
  Use Enrollments.student_id when: Question is about courses a student IS TAKING
  Use Has_Pet.student_id when: Question is about pets a student OWNS
  Direction: Students.student_id = the student themselves, FK = things related to that student
```

---

**Status:** Plan Complete
**Next Action:** Begin implementation (Day 1)
**Target Start:** November 11, 2025
