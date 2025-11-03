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

**Benchmark evidence** (30 cases / 88% of failures):

```sql
-- Pattern: "Which X has minimum/maximum Y?"

-- CORRECT approach:
SELECT item_name FROM items
JOIN properties ON items.id = properties.item_id
ORDER BY properties.value ASC LIMIT 1

-- WRONG approach (what the LLM is doing):
SELECT item_name, MIN(properties.value)
FROM items
JOIN properties ON items.id = properties.item_id
GROUP BY item_name
ORDER BY MIN(properties.value) ASC LIMIT 1
```

**The problem:** LLM sees "minimum/maximum" and incorrectly adds `MIN()/MAX()` + `GROUP BY` when the question asks for the **identifier** (which item), not the **value** (what is the minimum).

---

### Issue #2: No Case Sensitivity Guidance for SQLite

**Current state:** No guideline addresses case sensitivity

**Benchmark evidence** (3 cases / 9% of failures):

```sql
-- Pattern: Using lowercase when schema has mixed case

-- Schema definition:
--   venues(Venue_ID, Name, Location)
--   events(Event_ID, Venue_ID, Year)

-- CORRECT approach (matches schema case):
SELECT DISTINCT v.Name, v.Location
FROM venues v
JOIN events e ON v.Venue_ID = e.Venue_ID
WHERE e.Year IN ('2020', '2021')

-- WRONG approach (lowercase names):
SELECT DISTINCT v.name, v.location
FROM venues v
JOIN events e ON v.venue_id = e.venue_id
WHERE e.year IN ('2020', '2021')

-- Error: no such column: v.name
```

**The problem:** SQLite is case-sensitive for identifiers. Schema has `Name` but LLM uses `name`.

---

### Issue #3: No Column Disambiguation Guidance

**Current guideline #8:** "Ensure column references are unambiguous" - too vague

**Benchmark evidence** (1 case / 3% of failures):

```sql
-- Pattern: Column name exists in multiple joined tables

-- Schema definition:
--   transactions(id, vendor_code, amount)
--   vendors(id, vendor_code, name)

-- CORRECT approach (qualified column name):
SELECT transactions.vendor_code
FROM transactions
GROUP BY transactions.vendor_code
ORDER BY COUNT(*) DESC LIMIT 1

-- WRONG approach (ambiguous column):
SELECT vendor_code, COUNT(*) AS tx_count
FROM transactions
JOIN vendors ON transactions.vendor_code = vendors.id
GROUP BY vendor_code  -- ERROR: which table's 'vendor_code'?
ORDER BY tx_count DESC LIMIT 1

-- Error: ambiguous column name: vendor_code
```

**The problem:** Column `vendor_code` exists in both tables. When joined, must use `transactions.vendor_code` or `vendors.vendor_code`.

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
     - Example: "Which product has minimum price?" → ORDER BY price ASC LIMIT 1 (NOT MIN(price))
   - **DO use aggregations when questions explicitly ask for quantities:**
     - "How many..." → COUNT(*)
     - "What is the total..." → SUM(column)
     - "What is the average..." → AVG(column)
     - "What is the maximum..." (asking for the value, not the identifier) → MAX(column)
   - **Key distinction:**
     - "Which product has minimum price?" → wants product name (ORDER BY + LIMIT)
     - "What is the minimum price?" → wants the value (SELECT MIN)
```

---

### Modification 2: Add New Guideline #11 for Case Sensitivity

**Location**: After line 99 in `baseline_sql_system()`, after line 274 in `enhanced_sql_system()`

**New guideline:**
```python
11. **CASE SENSITIVITY (SQLite CRITICAL):**
    - SQLite is CASE-SENSITIVE for all table and column identifiers
    - You MUST use the EXACT case shown in the schema
    - Example: If schema shows "Customer_ID", use "Customer_ID" NOT "customer_id" or "CustomerID"
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
   - Example: If both `orders` and `customers` have a `status` column, use `orders.status`
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
1. Question: "What region has the most stores?"
   - WRONG: SELECT region, COUNT(*) FROM stores GROUP BY region ORDER BY COUNT(*) DESC LIMIT 1
   - CORRECT: SELECT region FROM stores GROUP BY region ORDER BY COUNT(*) DESC LIMIT 1
   - Why: Question asks for "what region" (identifier), not "how many stores" (quantity)

2. Question: "Which product has the minimum price?"
   - WRONG: SELECT product_name, MIN(price) FROM products GROUP BY product_name ORDER BY MIN(price) LIMIT 1
   - CORRECT: SELECT product_name FROM products ORDER BY price ASC LIMIT 1
   - Why: Question asks for "which product" (identifier), not "what is the minimum" (value)

3. Question: "What is the maximum salary?"
   - WRONG: SELECT employee_name FROM employees ORDER BY salary DESC LIMIT 1
   - CORRECT: SELECT MAX(salary) FROM employees
   - Why: Question asks for the value itself, not which employee has it

4. Question: "How many orders were placed each month?"
   - WRONG: SELECT month FROM orders GROUP BY month ORDER BY month
   - CORRECT: SELECT month, COUNT(*) FROM orders GROUP BY month
   - Why: "How many" explicitly asks for the count

CASE SENSITIVITY (SQLite):
5. Given schema: Customers(Customer_ID, First_Name, Last_Name)
   - WRONG: SELECT first_name FROM customers WHERE customer_id = 1
   - CORRECT: SELECT First_Name FROM Customers WHERE Customer_ID = 1
   - Why: SQLite is case-sensitive; must match exact schema case

COLUMN DISAMBIGUATION:
6. Given: orders(status, ...) and customers(status, ...)
   Question: "Which customer status has most orders?"
   - WRONG: SELECT status FROM orders JOIN customers ON orders.customer_id = customers.id GROUP BY status ORDER BY COUNT(*) DESC
   - CORRECT: SELECT customers.status FROM orders JOIN customers ON orders.customer_id = customers.id GROUP BY customers.status ORDER BY COUNT(*) DESC LIMIT 1
   - Why: Column 'status' exists in both tables; must qualify to avoid ambiguity
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

Example: If order_items bridges orders to products:
- Relationship: orders → order_items → products
- Purpose: Enables queries connecting orders to product details (many-to-many relationship)
- Common mistake: Trying to join orders directly to products (will fail or give wrong results)
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
  "name": "status",
  "business_meaning": "Current status code",
  "appears_in_other_tables": ["customers"],
  "disambiguation_note": "Use orders.status when filtering by order status (pending, shipped, etc.). Use customers.status when filtering by customer account status (active, inactive, etc.)."
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
- Run benchmark focusing on databases with aggregation pattern failures
- Run benchmark focusing on databases with case sensitivity issues (SQLite)
- Run benchmark focusing on databases with column disambiguation issues
- Compare results before and after changes

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
- Regenerate semantic layers for databases with many-to-many relationships
- Verify bridge tables are identified with complete join paths
- Verify duplicate column names are documented with disambiguation notes
- Run full benchmark and compare with Phase 1 results

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
