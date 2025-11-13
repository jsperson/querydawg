# Semantic Layer Prompt Modifications
## Based on Benchmark Analysis Recommendations

**File**: `backend/app/services/semantic_layer_generator.py`
**Method**: `_build_prompt()` (lines 181-338)

---

## Current Prompt Structure

The semantic layer is generated using an LLM prompt with these sections:
1. **Task description** (lines 207-209)
2. **Critical constraints** (lines 210-215)
3. **Foreign key rules** (lines 216-226)
4. **Analysis approach** (lines 228-235)
5. **Schema structure** (formatted, lines 240-242)
6. **Sample data** (formatted, lines 244-245)
7. **Output format** (JSON schema, lines 247-323)
8. **Quality requirements** (lines 325-335)

---

## Recommendation #1: Fix Case Sensitivity
**Priority**: HIGH | **Impact**: +3 questions | **Effort**: LOW

### Problem
SQLite column/table names are case-sensitive. The current prompt doesn't emphasize preserving exact case from schema.

### Current State
No explicit instruction about case preservation. The schema is formatted showing exact case (line 358):
```python
lines.append(f"  • {col['name']}: {col['type']}{pk}{nullable}")
```

But there's no instruction telling the LLM to preserve this case in semantic layer output.

### Proposed Modification

**Location**: After line 215 (CRITICAL CONSTRAINTS section)

**Add new constraint**:
```
CASE SENSITIVITY (CRITICAL FOR SQLite):
- Database uses SQLite which is CASE-SENSITIVE for all identifiers
- You MUST preserve the EXACT case of table and column names shown in the schema
- Example: If schema shows "Stadium_ID", use "Stadium_ID" NOT "stadium_id" or "StadiumID"
- VERIFY: Every table/column name in your output EXACTLY matches the schema case
```

**Location**: In columns section of OUTPUT FORMAT (after line 270)

**Modify the column schema**:
```json
{
  "name": "string - EXACT technical column name (PRESERVE CASE from schema)",
  "business_name": "string - human-friendly name",
  "business_meaning": "string - what this represents in plain English",
  ...
}
```

**Location**: In QUALITY REQUIREMENTS (after line 328)

**Add new requirement**:
```
- Case preservation: ALL table and column names MUST match the exact case shown in the schema above
```

---

## Recommendation #2: Add Aggregation Guidance
**Priority**: HIGH | **Impact**: +8-10 questions | **Effort**: MEDIUM

### Problem
LLM adds unnecessary MIN/MAX/SUM with GROUP BY when questions ask for superlatives (e.g., "which model has minimum horsepower?")

### Current State
The prompt mentions aggregations in the column schema (line 275):
```
"aggregations": ["string - common aggregation patterns if numeric/date, e.g., 'AVG(column)', 'SUM(column)'"]
```

But doesn't distinguish between when to aggregate vs when to use ORDER BY + LIMIT.

### Proposed Modification

**Location**: New section after line 226 (after FOREIGN KEY RELATIONSHIPS)

**Add new section**:
```
AGGREGATION VS SORTING (CRITICAL PATTERN):
Understanding when to aggregate vs when to sort is essential for correct query generation.

**DO NOT AGGREGATE when:**
- Question asks for "which", "what", "who" followed by a superlative (min, max, highest, lowest, most, least)
- Examples: "Which car has the minimum horsepower?" → ORDER BY horsepower LIMIT 1
- Examples: "What city has the most customers?" → GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1 (returns CITY not COUNT)
- Pattern: Superlative questions want the IDENTIFIER, not the aggregated value

**DO AGGREGATE when:**
- Question explicitly asks for quantities: "how many", "what is the total", "what is the average"
- Examples: "How many cars?" → SELECT COUNT(*)
- Examples: "What is the total revenue?" → SELECT SUM(revenue)
- Pattern: Quantity questions want the AGGREGATED VALUE, not identifiers
```

**Location**: In columns OUTPUT FORMAT (replace line 275)

**Modify aggregations field**:
```json
"aggregation_guidance": {
  "description": "When and how to aggregate this column",
  "superlative_pattern": "For 'which/what X has min/max Y' use ORDER BY + LIMIT, NOT MIN/MAX aggregation",
  "quantity_pattern": "For 'how many/what total/what average' use COUNT/SUM/AVG aggregation",
  "common_aggregations": ["string - patterns like 'COUNT(column)', 'AVG(column)' with usage context"]
}
```

**Location**: New entry in query_guidelines (line 318-322)

**Add guideline**:
```
"CRITICAL: Distinguish 'Which X has max Y?' (ORDER BY Y DESC LIMIT 1) from 'What is the max Y?' (SELECT MAX(Y))"
```

---

## Recommendation #3: Document Bridge Tables
**Priority**: MEDIUM | **Impact**: +5-7 questions | **Effort**: MEDIUM

### Problem
Many-to-many relationships require bridge tables, but the current prompt doesn't emphasize when a table serves as a bridge.

### Current State
Foreign keys are documented (lines 360-372) but don't identify bridge table patterns.

### Proposed Modification

**Location**: After line 226 (after FOREIGN KEY RELATIONSHIPS)

**Add new section**:
```
BRIDGE TABLES (MANY-TO-MANY RELATIONSHIPS):
Some tables exist solely to connect two other tables in many-to-many relationships.

**Identifying Bridge Tables:**
- Typically has 2+ foreign keys and few/no other meaningful columns
- Often named like "table1_table2" or similar
- Required for queries that connect the two referenced tables

**Critical Requirements:**
1. IDENTIFY all bridge tables in your analysis
2. Document the COMPLETE join path through the bridge
3. Mark as "bridge_table": true in relationships
4. Explain WHY this table is needed (what M:M relationship it represents)
5. List common mistakes (e.g., "DO NOT skip this table when joining X to Y")

**Example**: model_list bridges car_makers to cars_data
- car_makers → model_list.maker → model_list.model → car_names.model → cars_data
- Skipping model_list will give incorrect results
```

**Location**: In table relationships OUTPUT FORMAT (modify lines 280-286)

**Enhance relationships schema**:
```json
"relationships": [
  {
    "column": "string - FK column name",
    "references_table": "string - target table name",
    "relationship_type": "string - 'one-to-many', 'many-to-one', or 'many-to-many'",
    "bridge_table": "boolean - true if this table bridges a many-to-many relationship",
    "complete_join_path": ["string - full sequence of joins if multi-hop required"],
    "business_meaning": "string - what this relationship represents in business terms",
    "common_uses": ["string - when/why users would query across these tables"],
    "common_mistakes": ["string - typical errors when using this relationship"]
  }
]
```

**Location**: New top-level section in OUTPUT FORMAT (after line 297)

**Add bridge_tables section**:
```json
"bridge_tables": [
  {
    "table_name": "string - bridge table name",
    "connects": ["table1", "table2"],
    "purpose": "string - what many-to-many relationship this enables",
    "required_for": ["string - types of queries that need this bridge"],
    "join_sequence": "string - complete join path using this bridge"
  }
]
```

---

## Recommendation #4: Add Column Disambiguation
**Priority**: LOW | **Impact**: +1 question | **Effort**: LOW

### Problem
When a column name exists in multiple tables (e.g., "airline" in both "flights" and "airlines"), the semantic layer doesn't provide disambiguation guidance.

### Current State
No disambiguation information in current schema.

### Proposed Modification

**Location**: New section after aggregation guidance (see Recommendation #2)

**Add new section**:
```
COLUMN NAME DISAMBIGUATION:
Some column names appear in multiple tables. Document which table's column to use in different contexts.

**When documenting columns:**
1. Identify all column names that appear in 2+ tables
2. Explain the semantic difference between each occurrence
3. Provide usage guidance (when to use table1.column vs table2.column)
4. Warn about ambiguous references that need table qualification
```

**Location**: In columns OUTPUT FORMAT (after line 276)

**Add new optional field**:
```json
"disambiguation": {
  "appears_in_tables": ["string - other tables with this column name"],
  "this_table_meaning": "string - what this column means in THIS table",
  "other_table_meanings": {
    "table_name": "string - what it means in that table"
  },
  "usage_guidance": "string - when to use which table's version"
}
```

**Example**:
```json
{
  "name": "airline",
  "disambiguation": {
    "appears_in_tables": ["flights", "airlines"],
    "this_table_meaning": "The airline code/ID for this flight (foreign key)",
    "other_table_meanings": {
      "airlines.airline": "The full display name of the airline company"
    },
    "usage_guidance": "Use flights.airline for filtering/grouping by airline. Use airlines.airline when you need the full name for display."
  }
}
```

---

## Recommendation #5: Anti-Pattern Database
**Priority**: MEDIUM | **Impact**: +10-15 questions | **Effort**: HIGH

### Problem
LLM makes systematic mistakes that are specific to database structure (e.g., always adding MIN with GROUP BY for car_1 database).

### Current State
No database-specific anti-pattern documentation.

### Proposed Modification

**Location**: New top-level section in OUTPUT FORMAT (after line 297, before query_guidelines)

**Add new section**:
```json
"common_mistakes": [
  {
    "mistake_pattern": "string - description of common error",
    "wrong_approach": "string - incorrect SQL pattern",
    "correct_approach": "string - correct SQL pattern",
    "example_question": "string - natural language question that triggers this",
    "why_wrong": "string - explanation of why the wrong approach fails",
    "affected_tables": ["string - tables where this mistake commonly occurs"]
  }
]
```

**Location**: New section in prompt ANALYSIS APPROACH (after line 234)

**Add step**:
```
7. Anti-patterns: Based on schema structure, what SQL mistakes might an LLM make?
   - Look for structures that might confuse text-to-SQL systems
   - Identify when aggregation would be incorrectly added
   - Note cases where JOINs might be skipped or done incorrectly
   - Document any counter-intuitive patterns in this schema
```

**Location**: New section in prompt (after line 245, before OUTPUT FORMAT)

**Add guidance**:
```
ANTI-PATTERN ANALYSIS:
Think about common mistakes an LLM might make when generating SQL for this schema:

1. **Aggregation Mistakes**: Columns that might incorrectly trigger MIN/MAX instead of ORDER BY
2. **Join Mistakes**: Multi-hop joins that might be short-circuited incorrectly
3. **Column Selection**: Cases where an aggregate is included when only the identifier is needed
4. **Filter Mistakes**: Columns with values that look like they should be filtered differently

Document these in the "common_mistakes" section so future LLMs can avoid them.
```

**Examples to include in prompt**:
```
Example anti-patterns for a car database:
- WRONG: SELECT model, MIN(horsepower) ... GROUP BY model ORDER BY MIN(horsepower) LIMIT 1
- RIGHT: SELECT model FROM ... ORDER BY horsepower ASC LIMIT 1
- Why: "Which model has minimum X" asks for the model, not the minimum value

- WRONG: car_makers JOIN car_names ON car_makers.id = car_names.makeid
- RIGHT: car_makers → model_list → car_names → cars_data (must use bridge table)
- Why: model_list is the many-to-many bridge between makers and actual car data
```

---

## Implementation Strategy

### Phase 1: Quick Wins (Priority 1 & 2)
**Files to modify**:
- `backend/app/services/semantic_layer_generator.py` - `_build_prompt()` method

**Changes**:
1. Add CASE SENSITIVITY section
2. Add AGGREGATION VS SORTING section
3. Modify column schema to include aggregation_guidance
4. Add case preservation to QUALITY REQUIREMENTS

**Testing**:
- Regenerate semantic layer for concert_singer (has case sensitivity issues)
- Regenerate semantic layer for car_1 (has aggregation issues)
- Verify output JSON includes new fields

**Expected Impact**: +11-13 questions

### Phase 2: Structural Improvements (Priority 3 & 4)
**Changes**:
1. Add BRIDGE TABLES section
2. Add COLUMN NAME DISAMBIGUATION section
3. Modify relationships schema
4. Add bridge_tables top-level section
5. Add disambiguation field to columns

**Testing**:
- Regenerate semantic layer for car_1 (has bridge table issues)
- Regenerate semantic layer for flight_2 (has disambiguation issues)

**Expected Impact**: +6-8 questions

### Phase 3: Anti-Pattern Database (Priority 5)
**Changes**:
1. Add ANTI-PATTERN ANALYSIS section to prompt
2. Add common_mistakes to output schema
3. Add anti-pattern detection to analysis approach

**Testing**:
- Regenerate all semantic layers
- Review generated anti-patterns for accuracy
- Run new benchmark to validate improvements

**Expected Impact**: +10-15 questions

---

## Validation Checklist

After implementing each phase, validate that generated semantic layers include:

**Phase 1**:
- [ ] All column names match exact case from schema
- [ ] aggregation_guidance field present for numeric columns
- [ ] Clear distinction between superlative vs quantity queries

**Phase 2**:
- [ ] Bridge tables identified with bridge_table: true
- [ ] complete_join_path documented for multi-hop joins
- [ ] Disambiguation guidance for duplicate column names

**Phase 3**:
- [ ] common_mistakes array populated
- [ ] Database-specific anti-patterns documented
- [ ] Examples show wrong vs right SQL patterns

---

## Regeneration Plan

After implementing all changes, regenerate semantic layers for:

**Priority Databases** (most issues):
1. car_1 (aggregation + bridge table issues)
2. real_estate_properties (worst performer: -25%)
3. concert_singer (case sensitivity)
4. student_transcripts_tracking (case sensitivity)
5. world_1 (case sensitivity + improved +7.5%)

**Order**:
1. Regenerate priority databases after Phase 1
2. Run quick benchmark (50 questions) to validate improvement
3. If positive, regenerate all 20 databases
4. Run full benchmark to measure total impact

**Expected Timeline**:
- Phase 1 implementation: 2-3 hours
- Phase 1 regeneration + testing: 1-2 hours
- Phase 2 implementation: 3-4 hours
- Phase 2 regeneration + testing: 1-2 hours
- Phase 3 implementation: 4-6 hours
- Phase 3 regeneration + testing: 2-3 hours
- **Total**: 13-20 hours for complete implementation and validation

---

## Summary of Changes

| Recommendation | Prompt Section | Lines to Modify | New Fields Added |
|----------------|----------------|-----------------|------------------|
| 1. Case Sensitivity | CRITICAL CONSTRAINTS, OUTPUT FORMAT, QUALITY REQUIREMENTS | After 215, 270, 328 | None (clarification only) |
| 2. Aggregation Guidance | New section, column schema | After 226, modify 275 | aggregation_guidance |
| 3. Bridge Tables | New section, relationships schema, new top-level | After 226, 280-286, after 297 | bridge_tables, complete_join_path |
| 4. Disambiguation | New section, column schema | After new aggregation section, after 276 | disambiguation |
| 5. Anti-Patterns | New sections, output schema, analysis approach | After 234, 245, after 297 | common_mistakes |

**Total new prompt length**: +1500-2000 characters
**New JSON fields**: 4 (aggregation_guidance, bridge_tables, disambiguation, common_mistakes)
**Structural changes**: 5 new sections + 3 schema modifications
