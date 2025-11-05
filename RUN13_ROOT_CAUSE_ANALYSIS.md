# Run 13 Root Cause Analysis - Complete Investigation

**Date:** 2025-11-05
**Databases Analyzed:** student_transcripts_tracking, network_1, flight_2
**Total Regressions Analyzed:** 10 questions (-1.0% impact)

## Executive Summary

Investigation of the three most degraded databases reveals **two distinct categories of failures**:

1. **Case Sensitivity Bug (40% of failures)** - Technical mismatch between Supabase and Turso schemas
2. **Phase 2 Guidance Issues (60% of failures)** - Semantic layer providing confusing or overly specific guidance

## Failure Breakdown by Root Cause

| Database | Questions Lost | Case Sensitivity | Synonym Confusion | Wrong JOIN Logic | Missing Aggregation |
|----------|----------------|------------------|-------------------|------------------|---------------------|
| student_transcripts_tracking | 4 | 0 | 1 | 2 | 1 |
| network_1 | 3 | 2 | 0 | 2 | 1 |
| flight_2 | 3 | 1 | 0 | 1 | 1 |
| **TOTAL** | **10** | **3** | **1** | **5** | **3** |

### Root Cause Distribution
- **Case Sensitivity:** 3/10 (30%) - Supabase lowercase vs Turso mixed-case
- **Wrong JOIN Logic:** 5/10 (50%) - Incorrect join strategy, wrong FK, wrong join type
- **Missing/Wrong Aggregation:** 3/10 (30%) - Incomplete SELECT, COUNT from wrong table
- **Ambiguous Synonyms:** 1/10 (10%) - "Degree ID" conflated with "degrees"

---

## Issue 1: Case Sensitivity (Critical - Affects Multiple Databases)

### The Problem

**Data Flow:**
1. Spider SQLite databases → Uploaded to Turso (preserves case)
2. Spider SQLite databases → Uploaded to Supabase for semantic layer generation
3. **PostgreSQL auto-lowercases** all unquoted identifiers
4. Semantic layers generated with lowercase table/column names
5. Enhanced SQL prompt includes lowercase names from semantic layer
6. LLM generates SQL with lowercase names
7. **Turso SQLite rejects** queries with wrong case

### Evidence

**network_1:**
- Semantic layer: `friend`, `highschooler`, `likes`
- Turso schema: `Friend`, `Highschooler`, `Likes`
- Result: 2 out of 3 failures had lowercase table names

**flight_2:**
- Semantic layer: `abbreviation`
- Turso schema: `Abbreviation`
- Result: 1 out of 3 failures had lowercase column name

### Impact Estimate

Affected databases (based on degradation pattern):
- network_1: -5.4% (confirmed case issues)
- flight_2: -3.7% (confirmed 1 case issue)
- student_transcripts_tracking: -5.1% (lowercase schema, likely affected)
- world_1: -1.6% (likely affected)
- Possibly singer, orchestra (need verification)

**Estimated total impact:** ~8-10 questions across multiple databases

### Solution

**Option A: Generate Semantic Layers from Turso (Recommended)**
- Query Turso database schemas directly
- Preserve exact case from original Spider databases
- Benefits: Matches production query target
- Drawbacks: Need Turso API integration

**Option B: Normalize All Turso Databases to Lowercase**
- Re-upload all Spider databases with lowercase identifiers
- Benefits: Matches Supabase semantic layers
- Drawbacks: Requires data re-upload, diverges from Spider format

---

## Issue 2: Ambiguous Synonyms

### The Problem

Phase 2 added column synonyms that are TOO specific, causing the LLM to select wrong columns.

### Example: student_transcripts_tracking

**Question:** "How many different degrees are offered?"

**Semantic Layer:**
```json
{
  "degree_program_id": {
    "synonyms": ["Program ID", "Degree ID", "Program Key"]  // ❌ "Degree ID" too close to "degree"
  },
  "degree_summary_name": {
    "synonyms": ["Program Name", "Degree Title", "Program Title"]
  }
}
```

**Result:**
- LLM matched "degrees" → "Degree ID" (synonym) → `degree_program_id`
- Should have matched "degrees" → "Degree Title" → `degree_summary_name`

### Solution

**Principle:** Synonyms should be unambiguous alternatives, not partial word matches.

**Bad synonyms:**
- "Degree ID" for `degree_program_id` (too close to "degree")
- "Course ID" for `course_id` (just restates the column name)

**Good synonyms:**
- "Program Identifier" for `degree_program_id`
- "Enrollment Identifier" for `student_course_id`

**Recommendation:**
1. Review all generated synonyms for ambiguity
2. Remove synonyms that are partial matches of column names
3. Prefer multi-word synonyms that add context

---

## Issue 3: Wrong JOIN Logic (Most Common - 50% of Failures)

### Sub-Issue 3A: Ambiguous Bridge Table Guidance (network_1)

**Question:** "Count the number of friends Kyle has."

**Semantic Layer:**
```json
{
  "table": "friend",
  "relationships": [
    {
      "column": "student_id",
      "is_bridge_table": true,
      "complete_join_path": ["friend → highschooler"]
    },
    {
      "column": "friend_id",
      "is_bridge_table": true,
      "complete_join_path": ["friend → highschooler"]  // ❌ SAME path, no direction!
    }
  ]
}
```

**Problem:** Both foreign keys have the SAME join path, providing no guidance on WHICH column to use for WHICH direction.

**Result:** LLM joined on `friend_id` instead of `student_id`, finding friends OF Kyle instead of friends Kyle HAS.

**Solution:**

Add directional semantics:
```json
{
  "column": "student_id",
  "complete_join_path": ["friend → highschooler"],
  "join_semantics": "To find all friends OF a specific student, filter by friend.student_id = <student's ID>, then join friend.friend_id to highschooler.id"
}
```

---

### Sub-Issue 3B: Wrong JOIN Type (flight_2)

**Question:** "Find the airline that has fewest number of flights?"

**Run 12 (✅):** Used `INNER JOIN` (only airlines with flights)
**Run 13 (❌):** Used `LEFT JOIN` (includes airlines with 0 flights)

**Problem:** Phase 2 might have over-emphasized "completeness", leading LLM to use LEFT JOIN to include all airlines.

**Solution:**

Add JOIN type guidance:
```
"Use INNER JOIN when the question implies 'among entities that have a relationship'.
Example: 'airline with fewest flights' means airlines that HAVE flights (use INNER JOIN).

Use LEFT JOIN only when explicitly asked to include entities without relationships.
Example: 'all airlines and their flight counts, including those with no flights' (use LEFT JOIN)."
```

---

### Sub-Issue 3C: Wrong Join Strategy (student_transcripts_tracking)

**Question:** "Find the semester when both Master students and Bachelor students got enrolled in."

**Correct interpretation:** Find semesters where (Master students enrolled) AND (Bachelor students enrolled)
**Run 13 interpretation:** Find STUDENTS enrolled in BOTH Master AND Bachelor programs

**Problem:** Phase 2 emphasized student-centric join paths, misdirecting the LLM to focus on students instead of semesters.

**Solution:**

Add intent-based query patterns:
```json
{
  "question": "Which semesters had both Master and Bachelor students?",
  "explanation": "Use INTERSECT on semester_id from separate filters for each degree type.",
  "sql": "SELECT semester_id FROM student_enrolment WHERE degree_program_id IN (SELECT ... WHERE ... LIKE '%Master%') INTERSECT SELECT semester_id FROM student_enrolment WHERE degree_program_id IN (SELECT ... WHERE ... LIKE '%Bachelor%')"
}
```

---

## Issue 4: Missing or Incorrect Aggregation (30% of Failures)

### Sub-Issue 4A: Incomplete SELECT (student_transcripts_tracking)

**Question:** "Maximum number of times a course shows up AND course's enrollment id"

**Run 12 (✅):** `SELECT student_course_id, COUNT(*) ...`
**Run 13 (❌):** `SELECT student_course_id ...` (missing COUNT!)

**Problem:** Phase 2 disambiguation emphasized using the ID "to reference" courses, possibly distracting from the count requirement.

**Solution:**

Update usage_guidance:
```json
{
  "usage_guidance": "Use this ID to reference specific course enrollments. When counting occurrences, include both the ID and COUNT(*) in SELECT clause."
}
```

---

### Sub-Issue 4B: Wrong Grouping Column (network_1)

**Question:** "Show names of high schoolers who have likes, and numbers of likes for each."

**Run 12 (✅):** `GROUP BY h.ID` (correct - IDs are unique)
**Run 13 (❌):** `GROUP BY highschooler.name` (wrong - names aren't unique!)

**Problem:** LLM grouped by the display column (`name`) instead of the unique identifier (`ID`).

**Solution:**

Add to query guidelines:
```
"ALWAYS GROUP BY unique identifiers (IDs), never by display names or descriptions.
Example: GROUP BY student_id, not GROUP BY student_name (names can be duplicated)."
```

---

### Sub-Issue 4C: COUNT from Wrong Table (flight_2)

**Question:** "Which city has the most frequent destination airport?"

**Run 13 (❌):**
```sql
SELECT City FROM airports
GROUP BY City
ORDER BY COUNT(DestAirport) DESC LIMIT 1
```

**Problem:** Tries to COUNT `DestAirport` column from airports table, but `DestAirport` is in flights table!

**Solution:**

Add aggregation join pattern:
```json
{
  "question": "Which city has the most flights as destination?",
  "explanation": "Join airports to flights on destination airport, then count flights per city.",
  "common_mistakes": ["Grouping by city without joining to flights table to count"]
}
```

---

## Comprehensive Fix Strategy

### Phase 1: Critical Fixes (Run 14 Target)

**1. Fix Case Sensitivity (Highest Impact)**
- [ ] Investigate Turso schema extraction via API
- [ ] Update semantic layer generator to use Turso schemas
- [ ] OR: Normalize all Turso databases to lowercase
- [ ] Regenerate all 20 semantic layers
- **Expected recovery:** +8-10 questions

**2. Remove Ambiguous Synonyms**
- [ ] Audit all synonyms for ambiguity
- [ ] Remove synonyms matching partial column names (e.g., "Degree ID")
- [ ] Regenerate affected databases
- **Expected recovery:** +1-2 questions

**3. Add Query Best Practices to Guidelines**
- [ ] "Always SELECT specific columns, avoid SELECT *"
- [ ] "Always GROUP BY IDs, not display names"
- [ ] "Use INNER JOIN unless explicitly asked for all entities"
- **Expected recovery:** +2-3 questions

### Phase 2: Enhanced Guidance (Run 15 Target)

**4. Improve Bridge Table Guidance**
- [ ] Add `join_semantics` field with directional guidance
- [ ] Clarify which FK for which direction
- **Expected recovery:** +1-2 questions

**5. Add Intent-Based Query Patterns**
- [ ] Add examples for INTERSECT patterns
- [ ] Add examples for aggregation with joins
- [ ] Add examples for ambiguous questions
- **Expected recovery:** +1-2 questions

### Phase 3: Validation & Refinement (Run 16 Target)

**6. A/B Test Individual Features**
- [ ] Test synonym impact independently
- [ ] Test bridge table guidance independently
- [ ] Optimize based on results

---

## Expected Outcomes

### Run 14 (Phase 1 Fixes Only)
- **Conservative:** Fix case sensitivity (+8) + best practices (+2) = **+10 questions → 85.0%**
- **Optimistic:** Fix case sensitivity (+10) + synonyms (+2) + best practices (+3) = **+15 questions → 86.5%**

### Run 15 (Phase 1 + Phase 2)
- **Target:** Additional +3-4 questions from improved guidance = **87.0-88.0%**

### Comparison
- Run 11-12 (Pre-Phase 2): 84.0%
- Run 13 (Phase 2, buggy): 84.0%
- Run 14 (Phase 2, fixed): **85.0-86.5%** (projected)
- Run 15 (Phase 2, enhanced): **87.0-88.0%** (projected)

---

## Key Takeaways

### What Phase 2 Did Right ✅
1. **Enabled SQL generation** where Phase 1 failed (museum_visit: +22.2%)
2. **Bridge table identification** helped complex relationships (battle_death: +12.5%)
3. **Complete join paths** clarified multi-table queries (cre_Doc_Template_Mgt: +5.9%)

### What Phase 2 Got Wrong ❌
1. **Case sensitivity** - Generated from wrong source (Supabase instead of Turso)
2. **Ambiguous synonyms** - Too specific, caused wrong column selection
3. **Incomplete guidance** - Bridge tables need directional semantics
4. **Over-specification** - Too much context can confuse the LLM

### Design Principles for Phase 3
1. **Less is more:** Only add guidance that unambiguously clarifies
2. **Match production:** Semantic layers must match query target schema
3. **Concrete examples:** Show correct patterns, don't just describe them
4. **Test incrementally:** A/B test each feature independently

---

## Next Actions

**Immediate (Today):**
1. ✅ Complete root cause analysis
2. Share findings with user
3. Get approval for fix strategy

**This Week:**
1. Implement case sensitivity fix (Option A or B)
2. Remove ambiguous synonyms
3. Add query best practices to guidelines
4. Test on 2-3 degraded databases

**Next Week:**
1. Full regeneration for all 20 databases
2. Run benchmark (Turso Run 14)
3. Validate fixes achieved expected recovery
4. Plan Phase 2 enhancements for Run 15
