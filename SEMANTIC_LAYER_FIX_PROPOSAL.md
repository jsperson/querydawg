# Semantic Layer Generation Fix

## Root Cause Analysis

**Problem:** Semantic layers are causing -0.8% overall accuracy drop because they're missing critical relationship information.

### Specific Issues Found

1. **Missing Relationships:**
   - `car_1`: `cars_data` and `car_names` tables show `relationships: []`
   - Actual relationship: `cars_data.id` ↔ `car_names.makeid`
   - Without this, enhanced queries try to SELECT columns from wrong tables

2. **Why This Happens:**
   - Spider databases have **NO declared foreign keys** in schema
   - Current prompt says "use ONLY the provided schema"
   - LLM can't infer relationships without explicit instructions

3. **Impact:**
   - 5/20 databases benefit (+10 queries)
   - 7/20 databases hurt (-17 queries)
   - 8/20 databases unchanged (0 queries)
   - **Net: -7 queries (net negative value)**

### Example Failures

**Question:** "What is the model of the car with the smallest horsepower?"

**Gold SQL:**
```sql
SELECT T1.Model FROM CAR_NAMES AS T1
JOIN CARS_DATA AS T2 ON T1.MakeId = T2.Id
ORDER BY T2.horsepower ASC LIMIT 1;
```

**Baseline (Correct):**
```sql
SELECT car_names.model FROM cars_data
JOIN car_names ON cars_data.id = car_names.makeid
ORDER BY cars_data.horsepower ASC LIMIT 1;
```

**Enhanced (Wrong - Missing Join):**
```sql
SELECT model FROM cars_data
ORDER BY horsepower ASC LIMIT 1;
-- ERROR: column "model" does not exist in cars_data
```

---

## Proposed Fix

### Option 1: Enhanced Prompt (Quick Fix - 30 minutes)

Modify `semantic_layer_generator.py` prompt to:

1. **Add explicit relationship inference instructions:**

```
RELATIONSHIP INFERENCE (CRITICAL):
Since this database may not have declared foreign keys, you MUST infer implicit relationships by:

1. Column Naming Patterns:
   - Columns ending in '_id', 'id', or matching another table's name → likely FK
   - Example: 'makeid' in car_names → likely references 'id' in another table
   - Example: 'country' column with bigint type → likely references countries.countryid

2. Data Type Matching:
   - If Table A has 'customer_id bigint' and Table B has 'id bigint' as PK → likely FK
   - Match on similar column names + compatible data types

3. Semantic Analysis:
   - If table name is plural and column name is singular (e.g., cars_data.id, car_names.makeid)
   - Compound table names suggest many-to-many (e.g., course_arrangement)

4. MANDATORY: For EVERY inferred relationship, document:
   - Join pattern (exact SQL syntax)
   - Business meaning
   - Which queries require this join

**You MUST document ALL implicit relationships even without explicit FK constraints.**
```

2. **Strengthen relationship documentation requirements:**

```
RELATIONSHIP REQUIREMENTS:
- Document AT LEAST 1-3 relationships per table (unless truly standalone)
- If you see column name patterns suggesting FKs, ASSUME they are FKs
- Be AGGRESSIVE in inferring relationships - missing a join is worse than suggesting an incorrect one
- For each relationship, provide the EXACT join syntax users would need
```

3. **Add validation step:**

```
VALIDATION CHECKLIST:
Before finalizing your output, verify:
✓ Every table with '_id' or 'id' columns has documented relationships
✓ Tables with similar names (e.g., car_names, cars_data) have documented joins
✓ Primary keys of one table are referenced in other tables' relationships
✓ Each relationship includes explicit join_pattern with table.column syntax
```

### Option 2: Two-Phase Generation (Better - 2 hours)

**Phase 1: Relationship Discovery**
- Separate LLM call focused ONLY on finding relationships
- Use schema + sample data to infer implicit FKs
- Validate by checking if suggested joins would work
- Output: List of discovered relationships

**Phase 2: Full Semantic Layer**
- Use Phase 1 relationships as input
- Generate full semantic layer WITH known relationships
- More accurate, less guessing

### Option 3: Spider Metadata Integration (Best - 4 hours)

Spider benchmark includes relationship metadata in its original dataset. We could:
1. Load Spider's `tables.json` which has FK information
2. Inject this into semantic layer generation
3. LLM validates/enhances rather than inferring from scratch

---

## Recommended Approach

**Start with Option 1 (Enhanced Prompt)** because:
- Quick to implement (30 minutes)
- Low risk - just improves LLM instructions
- Can iterate based on results
- Immediate testable impact

**Implementation Steps:**

1. Update `semantic_layer_generator.py` prompt (lines 204-343)
2. Regenerate semantic layers for the 7 failing databases:
   - `flight_2`, `tvshow`, `car_1`, `wta_1`, `dog_kennels`, `network_1`, `student_transcripts_tracking`
3. Run targeted benchmark on these 7 databases
4. Compare results

**Expected Improvement:**
- Fix missing joins in car_1, flight_2, etc.
- Reduce -17 query loss to ~-5
- Combined with case sensitivity fix: **+1-2% overall improvement**

---

## Alternative: Relationship Post-Processor

Instead of relying on LLM inference, create a rule-based post-processor:

```python
def infer_relationships(semantic_layer, schema_info):
    """Infer implicit FK relationships from naming patterns."""
    for table in semantic_layer['tables']:
        for column in table['columns']:
            # Pattern 1: Column ends with 'id' or '_id'
            if column['name'].lower().endswith('id'):
                # Look for matching table with same prefix
                ref_table = find_matching_table(column['name'], schema_info)
                if ref_table:
                    table['relationships'].append({
                        'type': 'foreign_key',
                        'column': column['name'],
                        'references_table': ref_table,
                        'references_column': 'id',  # assume PK is 'id'
                        'confidence': 'inferred',
                        'join_pattern': f"JOIN {ref_table} ON {table['name']}.{column['name']} = {ref_table}.id"
                    })
```

This combines:
- Rule-based relationship detection (deterministic)
- LLM-based semantic meaning (flexible)

---

## Testing Strategy

1. **Regenerate 7 failing databases** with improved prompt
2. **Run targeted benchmark** (just those ~512 queries)
3. **Compare metrics:**
   - Before: -17 queries
   - Target: -5 or better
4. **If successful**, regenerate all 20 databases
5. **Run full benchmark** (Run 19)

---

## Success Criteria

**Minimum Viable:**
- Net queries: -7 → 0 (neutral)
- No databases hurt by more than -2%

**Target:**
- Net queries: +5 to +10 (positive value)
- 10/20 databases benefit (currently 5/20)
- <5 databases hurt by >2%

**Stretch Goal:**
- Net queries: +15 to +20
- 15/20 databases benefit
- Overall: 69.4% → 70.5%+ (1%+ improvement)

---

## Next Steps

**Immediate (30 min):**
1. Update semantic layer generator prompt
2. Test on car_1 database
3. Validate relationships are captured

**Short-term (2 hours):**
4. Regenerate 7 failing databases
5. Run targeted benchmark
6. Analyze results

**If successful (4 hours):**
7. Regenerate all 20 databases
8. Run full benchmark (Run 19)
9. Compare vs Run 18

**Want me to implement Option 1 now?**
