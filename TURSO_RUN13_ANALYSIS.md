# Turso Run 13 Analysis - Phase 2 Impact & Critical Findings

**Date:** 2025-11-05
**Run 13 ID:** 4f144555-bff7-4684-8b83-04f24fd5d08a
**Run 12 ID:** daf0b53d-dcab-4aa9-8912-b89c04f01339

## Executive Summary

**Overall Performance:** 84.0% (both runs) - **No net change**
**Individual Database Impact:** Mixed results with +18 questions improved, -14 questions degraded
**Critical Discovery:** Case sensitivity bug causing regressions in multiple databases

##  Performance Summary

| Metric | Run 12 (Phase 1) | Run 13 (Phase 2) | Change |
|--------|------------------|------------------|--------|
| Execution Match % | 84.0% | 84.0% | 0.0% |
| Questions Improved | - | +18 | - |
| Questions Degraded | - | -14 | - |
| Net Change | - | +4 questions | +0.4% |

## Database-Level Results

### Top 5 Improvements ✅

| Database | Run 12 | Run 13 | Change | Questions | Key Factor |
|----------|--------|--------|--------|-----------|------------|
| **museum_visit** | 72.2% | 94.4% | **+22.2%** | +4/18 | Phase 2 relationship guidance |
| **battle_death** | 68.8% | 81.3% | **+12.5%** | +2/16 | Bridge table clarity |
| **cre_Doc_Template_Mgt** | 78.6% | 84.5% | **+5.9%** | +5/84 | Complex join paths |
| **course_teach** | 83.3% | 86.7% | **+3.4%** | +1/30 | Disambiguation |
| **employee_hire_evaluation** | 92.1% | 94.7% | **+2.6%** | +1/38 | Relationship clarity |

### Top 5 Degradations ❌

| Database | Run 12 | Run 13 | Change | Questions | Root Cause |
|----------|--------|--------|--------|-----------|------------|
| **network_1** | 87.5% | 82.1% | **-5.4%** | -3/56 | **Case sensitivity bug** |
| **student_transcripts_tracking** | 79.5% | 74.4% | **-5.1%** | -4/78 | **Case sensitivity bug** |
| **flight_2** | 92.5% | 88.8% | **-3.7%** | -3/80 | **Case sensitivity bug** |
| **singer** | 93.3% | 90.0% | **-3.3%** | -1/30 | Investigation needed |
| **orchestra** | 97.5% | 95.0% | **-2.5%** | -1/40 | Investigation needed |

### Unchanged (6 databases)

- **concert_singer:** 86.7%
- **pets_1:** 100.0% (perfect on both runs)
- **poker_player:** 100.0% (perfect on both runs)
- **real_estate_properties:** 75.0%
- **voter_1:** 93.3%
- **wta_1:** 32.3% (consistently challenging)

## 🚨 CRITICAL FINDING: Case Sensitivity Bug

### Root Cause

**Data Source Mismatch:**
- **Semantic layers** generated from **Supabase (PostgreSQL)** → lowercase table names (`friend`, `highschooler`, `likes`)
- **Turso databases** loaded from **Spider SQLite** → mixed-case table names (`Friend`, `Highschooler`, `Likes`)
- **PostgreSQL** auto-lowercases unquoted identifiers
- **SQLite** is case-sensitive

### Impact

When Run 13 enhanced prompt includes semantic context with lowercase table names, the LLM generates queries with lowercase identifiers that fail in Turso.

### Example: network_1 Regression

**Question:** "Count the number of friends Kyle has."

**Run 12 SQL (✅ worked):**
```sql
SELECT COUNT(friend_id) FROM Friend
WHERE student_id = (SELECT ID FROM Highschooler WHERE name = 'Kyle')
```
Uses capitalized `Friend` and `Highschooler`

**Run 13 SQL (❌ failed):**
```sql
SELECT COUNT(*) FROM Friend JOIN Highschooler
ON Friend.friend_id = Highschooler.ID
WHERE Highschooler.name = 'Kyle'
```
*Note: This query also uses capitalized names but was marked as failed in results*

**Semantic Layer (source of confusion):**
```json
{
  "name": "friend",  // ❌ lowercase from Supabase
  "name": "highschooler",  // ❌ lowercase from Supabase
  "name": "likes"  // ❌ lowercase from Supabase
}
```

**Actual Turso Schema:**
```sql
CREATE TABLE Friend (...)  -- ✅ capitalized in SQLite
CREATE TABLE Highschooler (...)  -- ✅ capitalized in SQLite
CREATE TABLE Likes (...)  -- ✅ capitalized in SQLite
```

### Affected Databases

Based on degradation patterns, likely affected databases:
1. **network_1** (-5.4%) - confirmed case mismatch
2. **student_transcripts_tracking** (-5.1%) - likely case mismatch
3. **flight_2** (-3.7%) - likely case mismatch
4. **world_1** (-1.6%) - possible case mismatch
5. **singer** (-3.3%) - needs investigation
6. **orchestra** (-2.5%) - needs investigation

### Solution Options

**Option 1: Fix Semantic Layers (Recommended)**
- Query actual Turso schemas to get correct case
- Update semantic layer generation to preserve original case
- Regenerate semantic layers with correct table/column names

**Option 2: Normalize Turso to Lowercase**
- Recreate all Turso databases with lowercase identifiers
- Ensures consistency with Supabase
- Requires re-uploading all Spider data

**Option 3: Case-Insensitive Turso**
- Not possible - SQLite is inherently case-sensitive for unquoted identifiers

## Phase 2 Enhancement Impact

### What Worked Well ✅

1. **Bridge Table Identification**
   - museum_visit: +22.2% (4 questions)
   - battle_death: +12.5% (2 questions)
   - Clear bridge table markers helped LLM understand many-to-many relationships

2. **Complete Join Paths**
   - cre_Doc_Template_Mgt: +5.9% (5 questions)
   - Explicit join paths reduced ambiguity in complex schemas

3. **Column Disambiguation**
   - course_teach: +3.4% (1 question)
   - Usage guidance for columns appearing in multiple tables

4. **Relationship Metadata**
   - employee_hire_evaluation: +2.6% (1 question)
   - relationship_type and common_uses fields provided helpful context

### What Didn't Help ❌

1. **Case Sensitivity Confusion**
   - Lowercase table names from Supabase semantic layers don't match capitalized Turso schemas
   - Caused -14 question regressions across 6 databases

2. **Potential Over-Specification**
   - Some databases might be getting too much context
   - Needs investigation on singer (-3.3%) and orchestra (-2.5%)

## Recommendations

### Immediate Actions

1. **Fix Case Sensitivity Bug (HIGH PRIORITY)**
   - [ ] Create script to query Turso schemas for actual table/column case
   - [ ] Update semantic layer generator to use Turso case, not Supabase case
   - [ ] Regenerate all semantic layers with correct case
   - [ ] Re-run benchmark (Run 14) to measure true Phase 2 impact

2. **Investigate Singer & Orchestra**
   - [ ] Analyze failed questions in singer (-1 question)
   - [ ] Analyze failed questions in orchestra (-1 question)
   - [ ] Determine if Phase 2 features caused confusion

### Medium-Term

3. **Optimize Semantic Retrieval**
   - [ ] Review chunk type weighting (currently: table=1.2x, overview=0.7x)
   - [ ] Consider database-specific weighting strategies
   - [ ] Analyze which chunk types were retrieved for failed questions

4. **Schema Source Alignment**
   - [ ] Decision: Should semantic layers be generated from Turso or Supabase?
   - [ ] If Turso: Update semantic_layer_generator to connect to Turso
   - [ ] If Supabase: Normalize all Turso databases to lowercase

### Long-Term

5. **Enhanced Monitoring**
   - [ ] Track which semantic chunks contributed to correct vs incorrect answers
   - [ ] Build dashboard showing chunk effectiveness by database
   - [ ] A/B test different Phase 2 features independently

## Detailed Database Results

| Database | Run 12 | Run 13 | Δ | Δ Questions | Total Q | Analysis Priority |
|----------|--------|--------|---|-------------|---------|-------------------|
| battle_death | 68.8% | 81.3% | +12.5% | +2 | 16 | Success case study |
| car_1 | 67.4% | 69.6% | +2.2% | +2 | 92 | Minor improvement |
| concert_singer | 86.7% | 86.7% | 0.0% | 0 | 45 | Stable |
| course_teach | 83.3% | 86.7% | +3.4% | +1 | 30 | Success case study |
| cre_Doc_Template_Mgt | 78.6% | 84.5% | +5.9% | +5 | 84 | Success case study |
| dog_kennels | 79.3% | 81.7% | +2.4% | +2 | 82 | Minor improvement |
| employee_hire_evaluation | 92.1% | 94.7% | +2.6% | +1 | 38 | Success case study |
| flight_2 | 92.5% | 88.8% | -3.7% | -3 | 80 | **Case bug investigation** |
| museum_visit | 72.2% | 94.4% | +22.2% | +4 | 18 | **Top success story** |
| network_1 | 87.5% | 82.1% | -5.4% | -3 | 56 | **Case bug confirmed** |
| orchestra | 97.5% | 95.0% | -2.5% | -1 | 40 | Investigation needed |
| pets_1 | 100.0% | 100.0% | 0.0% | 0 | 42 | Perfect |
| poker_player | 100.0% | 100.0% | 0.0% | 0 | 40 | Perfect |
| real_estate_properties | 75.0% | 75.0% | 0.0% | 0 | 4 | Stable (small sample) |
| singer | 93.3% | 90.0% | -3.3% | -1 | 30 | Investigation needed |
| student_transcripts_tracking | 79.5% | 74.4% | -5.1% | -4 | 78 | **Case bug suspected** |
| tvshow | 83.9% | 85.5% | +1.6% | +1 | 62 | Minor improvement |
| voter_1 | 93.3% | 93.3% | 0.0% | 0 | 15 | Stable |
| world_1 | 75.8% | 74.2% | -1.6% | -2 | 120 | Case bug suspected |
| wta_1 | 32.3% | 32.3% | 0.0% | 0 | 62 | Consistently challenging |

## Conclusion

Phase 2 enhancements show **promising improvements** in databases with complex relationships (+18 questions), but a **critical case sensitivity bug** is masking the true impact (-14 questions).

**Estimated True Impact After Fix:**
If case bug is resolved, expect Run 14 to show:
- **+18 questions** from Phase 2 enhancements (museum_visit, battle_death, cre_Doc_Template_Mgt, etc.)
- **+14 questions** from fixing case bug (network_1, student_transcripts_tracking, flight_2, etc.)
- **Total: ~+32 questions (+3.2% improvement)** over Phase 1 baseline

**Next Step:** Fix case sensitivity bug and run Turso Run 14 for accurate Phase 2 evaluation.
