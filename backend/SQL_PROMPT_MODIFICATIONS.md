# SQL Generation Prompt Modifications
## Based on Turso Benchmark Run 9 Analysis

**Date**: November 3, 2025
**Benchmark**: Run ID 1ed7f2ac-7a91-4bd8-87c2-6424caf9b905
**Issue**: Enhanced underperformed on 34 questions despite +1.26% overall improvement

---

## Executive Summary

The benchmark analysis revealed that most improvement opportunities are in the **SQL generation prompts** (both baseline and enhanced), not in the semantic layer generation prompt. The key issues are:

1. **Over-aggregation** (30 cases) - Adding MIN/MAX with GROUP BY when ORDER BY + LIMIT is correct
2. **Case sensitivity** (3 cases) - Using wrong case for SQLite identifiers
3. **Column disambiguation** (1 case) - Ambiguous column references in JOINs

These issues affect **SQL generation behavior**, not metadata quality. Therefore, fixes belong in `backend/app/services/llm/prompts.py`, not in `backend/app/services/semantic_layer_generator.py`.

---

## Current State: baseline_sql_system()

**File**: `backend/app/services/llm/prompts.py`
**Method**: `baseline_sql_system()` (lines 78-107)

### Current Guidelines (lines 89-99):

```python
Guidelines:
1. {db_info['syntax_instruction']}
2. {db_info['table_qualification']}
3. Use appropriate JOIN types (INNER, LEFT, etc.) based on the question
4. Include proper WHERE clauses for filtering
5. Use aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
6. Add ORDER BY and LIMIT clauses when relevant
7. Use table aliases for clarity in multi-table queries
8. Ensure column references are unambiguous
9. **When the question explicitly asks for quantities ("how many", "what is the total", "what is the average"), INCLUDE the aggregation (COUNT, SUM, AVG) in the SELECT clause.** Only exclude aggregations when the question asks for superlatives or identifiers (e.g., "which year had the most concerts?" wants the year, not the count).
10. Return ONLY the SQL query without explanations or markdown formatting
```

### Current Examples (lines 100-105):

```python
Examples:
- Question: "What city has the most customers?"
  - WRONG: SELECT city, COUNT(*) FROM customers GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1
  - CORRECT: SELECT city FROM customers GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1
- Question: "How many orders were placed each month?"
  - WRONG: SELECT month FROM orders GROUP BY month ORDER BY month
  - CORRECT: SELECT month, COUNT(*) FROM orders GROUP BY month
```

---

## Current State: enhanced_sql_system()

**File**: `backend/app/services/llm/prompts.py`
**Method**: `enhanced_sql_system()` (lines 239-282)

### Current Guidelines (lines 264-274):

**IDENTICAL to baseline guidelines** - Same 10 guidelines, same guideline #9 about aggregation

### Current Examples (lines 276-282):

**IDENTICAL to baseline examples** - Same 2 examples about city/customers and orders

---

## Problem Analysis

### Issue #1: Guideline #9 is Too Weak

**Current guideline #9:**
> When the question explicitly asks for quantities ("how many", "what is the total", "what is the average"), INCLUDE the aggregation (COUNT, SUM, AVG) in the SELECT clause. Only exclude aggregations when the question asks for superlatives or identifiers (e.g., "which year had the most concerts?" wants the year, not the count).

**Why it fails:**

1. **Not explicit enough** - Doesn't clearly state "DO NOT use MIN/MAX for superlative questions"
2. **Missing key pattern** - Doesn't distinguish "which X has min/max Y" from "what is the min/max Y"
3. **Insufficient examples** - Only 2 examples, neither covering MIN/MAX misuse

**Benchmark evidence** (8+ failures in car_1 alone):

```sql
-- Question: "Which model has minimum horsepower?"

-- Gold SQL (CORRECT):
SELECT T1.Model FROM CAR_NAMES AS T1
JOIN CARS_DATA AS T2 ON T1.MakeId = T2.Id
ORDER BY T2.horsepower ASC LIMIT 1

-- Enhanced SQL (WRONG):
SELECT model_names.model, MIN(cars_data.horsepower)
FROM car_names AS model_names
JOIN cars_data ON model_names.MakeId = cars_data.Id
GROUP BY model_names.model
ORDER BY MIN(cars_data.horsepower) ASC LIMIT 1
```

**The problem:** Enhanced sees "minimum" and incorrectly adds `MIN()` + `GROUP BY` when the question asks for the **identifier** (which model), not the **value** (what is the minimum).

---

### Issue #2: No Case Sensitivity Guidance for SQLite

**Current state:** No guideline addresses case sensitivity

**Benchmark evidence** (3 failures):

```sql
-- Question: "Names and locations of stadiums with concerts in 2014 and 2015"

-- Baseline SQL (CORRECT):
SELECT DISTINCT s.Name, s.Location
FROM stadium s
JOIN concert c ON s.Stadium_ID = c.Stadium_ID
WHERE c.Year IN ('2014', '2015')

-- Enhanced SQL (WRONG):
SELECT DISTINCT s.name, st.location  -- lowercase 'name'
FROM concert c
JOIN stadium st ON c.stadium_id = st.stadium_id
WHERE c.year IN ('2014', '2015')

-- Error: no such column: s.name
```

**The problem:** SQLite is case-sensitive for identifiers. Schema has `Name` but enhanced uses `name`.

---

### Issue #3: No Column Disambiguation Guidance

**Current guideline #8:** "Ensure column references are unambiguous" - too vague

**Benchmark evidence** (1 failure):

```sql
-- Question: "Which airline has most number of flights?"

-- Baseline SQL (CORRECT - no JOIN needed):
SELECT Airline FROM flights
GROUP BY Airline
ORDER BY COUNT(*) DESC LIMIT 1

-- Enhanced SQL (WRONG - ambiguous column):
SELECT airline, COUNT(*) AS flight_count
FROM flights
JOIN airlines ON flights.airline = airlines.uid
GROUP BY airline  -- ERROR: which table's 'airline'?
ORDER BY flight_count DESC LIMIT 1

-- Error: ambiguous column name: airline
```

**The problem:** Column `airline` exists in both `flights` and `airlines` tables. When joined, must use `flights.airline` or `airlines.airline`.

---

## Proposed Modifications

### Modification 1: Replace Guideline #9 with Stronger Aggregation Rules

**Location**: Lines 96 in `baseline_sql_system()`, lines 273 in `enhanced_sql_system()`

**Current (WEAK):**
```python
9. **When the question explicitly asks for quantities ("how many", "what is the total", "what is the average"), INCLUDE the aggregation (COUNT, SUM, AVG) in the SELECT clause.** Only exclude aggregations when the question asks for superlatives or identifiers (e.g., "which year had the most concerts?" wants the year, not the count).
```

**Proposed (STRONG):**
```python
9. **AGGREGATION vs SORTING (CRITICAL):**
   - **DO NOT use MIN/MAX/SUM/AVG when questions ask "which/what/who X has the min/max/most/least Y"**
     - These questions want the IDENTIFIER (X), not the aggregated value
     - Use ORDER BY + LIMIT instead
     - Example: "Which car has minimum horsepower?" → ORDER BY horsepower ASC LIMIT 1 (NOT MIN(horsepower))
   - **DO use aggregations when questions explicitly ask for quantities:**
     - "How many..." → COUNT(*)
     - "What is the total..." → SUM(column)
     - "What is the average..." → AVG(column)
     - "What is the maximum..." (asking for the value, not the identifier) → MAX(column)
   - **Key distinction:**
     - "Which model has minimum horsepower?" → wants model name (ORDER BY + LIMIT)
     - "What is the minimum horsepower?" → wants the value (SELECT MIN)
```

---

### Modification 2: Add New Guideline #11 for Case Sensitivity

**Location**: After line 99 in `baseline_sql_system()`, after line 274 in `enhanced_sql_system()`

**New guideline:**
```python
11. **CASE SENSITIVITY (SQLite CRITICAL):**
    - SQLite is CASE-SENSITIVE for all table and column identifiers
    - You MUST use the EXACT case shown in the schema
    - Example: If schema shows "Stadium_ID", use "Stadium_ID" NOT "stadium_id" or "StadiumID"
    - Always verify your SQL uses exact case from the schema before responding
    - **This does not apply to PostgreSQL** (case-insensitive), but doesn't hurt to be precise
```

---

### Modification 3: Strengthen Guideline #8 for Column Disambiguation

**Location**: Line 95 in `baseline_sql_system()`, line 272 in `enhanced_sql_system()`

**Current (VAGUE):**
```python
8. Ensure column references are unambiguous
```

**Proposed (SPECIFIC):**
```python
8. **Ensure column references are unambiguous:**
   - When a column name exists in multiple tables in a JOIN, ALWAYS qualify it
   - Use table.column or alias.column syntax
   - Example: If both `flights` and `airlines` have an `airline` column, use `flights.airline`
   - Check the schema carefully for duplicate column names across tables
```

---

### Modification 4: Expand Examples Section

**Location**: Lines 100-105 in `baseline_sql_system()`, lines 276-282 in `enhanced_sql_system()`

**Current (2 examples):**
```python
Examples:
- Question: "What city has the most customers?"
  - WRONG: SELECT city, COUNT(*) FROM customers GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1
  - CORRECT: SELECT city FROM customers GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1
- Question: "How many orders were placed each month?"
  - WRONG: SELECT month FROM orders GROUP BY month ORDER BY month
  - CORRECT: SELECT month, COUNT(*) FROM orders GROUP BY month
```

**Proposed (6 examples covering all major patterns):**
```python
Examples:

AGGREGATION PATTERNS:
1. Question: "What city has the most customers?"
   - WRONG: SELECT city, COUNT(*) FROM customers GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1
   - CORRECT: SELECT city FROM customers GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1
   - Why: Question asks for "what city" (identifier), not "how many customers" (quantity)

2. Question: "Which model has the minimum horsepower?"
   - WRONG: SELECT model, MIN(horsepower) FROM cars GROUP BY model ORDER BY MIN(horsepower) LIMIT 1
   - CORRECT: SELECT model FROM cars ORDER BY horsepower ASC LIMIT 1
   - Why: Question asks for "which model" (identifier), not "what is the minimum" (value)

3. Question: "What is the maximum horsepower?"
   - WRONG: SELECT model FROM cars ORDER BY horsepower DESC LIMIT 1
   - CORRECT: SELECT MAX(horsepower) FROM cars
   - Why: Question asks for the value itself, not which car has it

4. Question: "How many orders were placed each month?"
   - WRONG: SELECT month FROM orders GROUP BY month ORDER BY month
   - CORRECT: SELECT month, COUNT(*) FROM orders GROUP BY month
   - Why: "How many" explicitly asks for the count

CASE SENSITIVITY (SQLite):
5. Given schema: Stadium(Stadium_ID, Name, Location)
   - WRONG: SELECT name FROM stadium WHERE stadium_id = 1
   - CORRECT: SELECT Name FROM stadium WHERE Stadium_ID = 1
   - Why: SQLite is case-sensitive; must match exact schema case

COLUMN DISAMBIGUATION:
6. Given: flights(airline, ...) and airlines(uid, airline, ...)
   Question: "Which airline has most flights?"
   - WRONG: SELECT airline FROM flights JOIN airlines ON flights.airline = airlines.uid GROUP BY airline ORDER BY COUNT(*) DESC
   - CORRECT: SELECT flights.airline FROM flights GROUP BY flights.airline ORDER BY COUNT(*) DESC LIMIT 1
   - Why: Column 'airline' exists in both tables; must qualify or avoid JOIN if not needed
```

---

## Proposed Modifications to Semantic Layer Generation Prompt

**File**: `backend/app/services/semantic_layer_generator.py`
**Method**: `_build_prompt()` (lines 181-338)

### Modification 5: Add Bridge Table Documentation

**Location**: New section after line 226 (after FOREIGN KEY RELATIONSHIPS)

**Add:**
```
BRIDGE TABLES (MANY-TO-MANY RELATIONSHIPS):
Some tables exist solely to connect two other tables in many-to-many relationships.

Identifying characteristics:
- Table has 2+ foreign keys and few/no other meaningful columns
- Often named like "table1_table2", "junction_*", or similar
- Required for queries that connect the two referenced tables

When documenting relationships, identify which tables are bridges and explain the complete join path.

Example: If model_list bridges car_makers to car_names:
- Relationship: car_makers → model_list → car_names → cars_data
- Purpose: Enables queries connecting car makers to actual car specifications
- Common mistake: Trying to join car_makers directly to car_names (will fail or give wrong results)
```

**Location**: In relationships output schema (modify lines 280-286)

**Current:**
```json
"relationships": [
  {
    "column": "string - FK column name",
    "references_table": "string - target table",
    "business_meaning": "string - what this relationship represents"
  }
]
```

**Proposed:**
```json
"relationships": [
  {
    "column": "string - FK column name",
    "references_table": "string - target table",
    "relationship_type": "string - 'one-to-many', 'many-to-one', or 'many-to-many'",
    "is_bridge_table": "boolean - true if this table bridges a many-to-many relationship",
    "complete_join_path": "string - if multi-hop join required, show full path (e.g., 'table1 → bridge → table2')",
    "business_meaning": "string - what this relationship represents",
    "common_mistakes": ["string - typical errors when using this relationship (e.g., 'DO NOT skip bridge_table')"]
  }
]
```

---

### Modification 6: Add Column Name Disambiguation

**Location**: New section after bridge tables section

**Add:**
```
COLUMN NAME DISAMBIGUATION:
Some column names appear in multiple tables with different meanings.

When documenting columns:
1. Identify column names that appear in 2+ tables
2. Explain the semantic difference between each occurrence
3. Provide guidance on when to use which table's version
```

**Location**: In columns output schema (after line 276)

**Add optional field:**
```json
"appears_in_other_tables": ["string - other tables with this column name (if applicable)"],
"disambiguation_note": "string - if this column name appears in multiple tables, explain when to use this table's version vs others"
```

**Example:**
```json
{
  "name": "airline",
  "business_meaning": "Airline identifier code",
  "appears_in_other_tables": ["airlines"],
  "disambiguation_note": "Use flights.airline when filtering/grouping by airline code. Use airlines.airline when you need the full airline name for display (requires JOIN)."
}
```

---

## Implementation Priority

### Phase 1: SQL Prompt Improvements (HIGH PRIORITY)
**Expected Impact**: +11-13 questions (34 regressions → ~21 regressions)

**Files to modify:**
- `backend/app/services/llm/prompts.py`

**Changes:**
1. Replace guideline #9 with stronger aggregation rules (Mod #1)
2. Add guideline #11 for case sensitivity (Mod #2)
3. Strengthen guideline #8 for disambiguation (Mod #3)
4. Expand examples section to 6 examples (Mod #4)

**Apply to both:**
- `baseline_sql_system()` (lines 78-107)
- `enhanced_sql_system()` (lines 239-282)

**Testing:**
- Run benchmark on car_1 database (most aggregation failures)
- Run benchmark on concert_singer (case sensitivity failures)
- Run benchmark on flight_2 (disambiguation failure)

---

### Phase 2: Semantic Layer Metadata (MEDIUM PRIORITY)
**Expected Impact**: +5-7 questions (better JOIN paths, fewer ambiguous columns)

**Files to modify:**
- `backend/app/services/semantic_layer_generator.py`

**Changes:**
1. Add BRIDGE TABLES section to prompt (Mod #5)
2. Add COLUMN DISAMBIGUATION section to prompt (Mod #6)
3. Enhance relationship schema with bridge table fields
4. Add column schema fields for disambiguation

**Testing:**
- Regenerate semantic layers for car_1, student_transcripts_tracking
- Verify bridge tables are identified
- Verify duplicate column names are documented
- Run full benchmark

---

## Expected Results

### Before Improvements:
- Enhanced: 78.92% (816/1034)
- Baseline: 77.66% (803/1034)
- Enhanced underperformance: 34 cases

### After Phase 1 (SQL Prompt Improvements):
- **Expected Enhanced**: ~82-83% (+40-50 questions)
- **Expected Baseline**: ~80-81% (+30-40 questions)
- **Expected Enhanced underperformance**: ~21 cases (down from 34)

**Rationale**: Both baseline and enhanced will benefit from clearer aggregation rules and case sensitivity warnings. Enhanced should benefit slightly more due to better semantic context.

### After Phase 2 (Semantic Layer Improvements):
- **Expected Enhanced**: ~84-86% (+60-80 questions total)
- **Expected Baseline**: ~80-81% (same as Phase 1)
- **Expected Enhanced underperformance**: ~15 cases (down from 34)

**Rationale**: Only enhanced benefits from improved semantic layer metadata (bridge tables, disambiguation notes).

---

## Key Insight: Why SQL Prompts, Not Semantic Layer?

The benchmark revealed that failures are **behavioral** (how SQL is generated) not **informational** (missing metadata):

| Issue | Root Cause | Fix Location |
|-------|-----------|--------------|
| Over-aggregation | LLM adds MIN/MAX incorrectly | SQL prompts (behavior rules) |
| Case sensitivity | LLM uses wrong case | SQL prompts (behavioral warning) |
| Column disambiguation | LLM doesn't qualify columns | Both (behavior + metadata) |
| Missing bridge tables | LLM skips intermediate tables | Semantic layer (metadata) |

**3 out of 4 issues** are behavioral → SQL prompt fixes will have the biggest impact.

---

## Summary

### SQL Prompt Changes (Apply to Both Baseline and Enhanced):
1. ✅ Strengthen guideline #9 → explicit aggregation vs sorting rules
2. ✅ Add guideline #11 → SQLite case sensitivity warning
3. ✅ Strengthen guideline #8 → column disambiguation requirements
4. ✅ Expand examples → 6 examples covering all major patterns

### Semantic Layer Prompt Changes:
5. ✅ Add bridge table documentation section
6. ✅ Add column disambiguation metadata fields

### Expected Outcome:
- **Phase 1**: Enhanced ~82-83%, Baseline ~80-81%
- **Phase 2**: Enhanced ~84-86%, Baseline ~80-81%
- **Total improvement**: +5-7% absolute improvement over current state
