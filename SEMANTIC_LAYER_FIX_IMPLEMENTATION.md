# Semantic Layer Fix - Implementation Plan

## ROOT CAUSE

**Semantic layers are causing -0.8% accuracy drop** because we're not using Spider's documented foreign key relationships.

### What We Found

1. **Spider's tables.json** documents all FK relationships (car_1 has 5 FKs)
2. **PostgreSQL schemas** don't have FK constraints declared (car_1 has 0 FKs)
3. **Our semantic layer generator** only queries PostgreSQL → misses critical relationships
4. **Result**: LLM can't infer joins → enhanced queries fail

###Example: car_1

**Spider's tables.json shows:**
```
cars_data.Id -> car_names.MakeId  (THE CRITICAL JOIN!)
```

**Our semantic layer shows:**
```json
"car_names": {
    "relationships": []  ← EMPTY!
}
```

**Impact:**
Enhanced tries to `SELECT model FROM cars_data` (wrong table) instead of joining with `car_names`.

---

## THE FIX

### Phase 1: Create Spider Metadata Loader ✅ DONE

Created: `backend/app/services/spider_metadata_loader.py`

**Functionality:**
- Load Spider's tables.json
- Extract FK relationships per database
- Normalize names to match PostgreSQL (lowercase)
- Provide singleton access

### Phase 2: Integrate into Schema Extraction (30 minutes)

**File:** `backend/app/database/supabase_schema_extractor.py`

**Changes:**
```python
from ..services.spider_metadata_loader import get_spider_metadata_loader

class SupabaseSchemaExtractor:
    def __init__(self, connection_string: str, use_spider_metadata: bool = True):
        self.connection_string = connection_string
        self.use_spider_metadata = use_spider_metadata
        if use_spider_metadata:
            self.spider_loader = get_spider_metadata_loader()

    def extract_schema(self, schema_name: str) -> Dict[str, Any]:
        """Extract schema with Spider FK metadata enrichment."""

        # Get base schema from PostgreSQL
        schema = self._query_postgresql_schema(schema_name)

        # Enrich with Spider metadata if available
        if self.use_spider_metadata and self.spider_loader.database_exists(schema_name):
            spider_fks = self.spider_loader.get_foreign_keys(schema_name)

            # Add Spider FKs to schema
            for table in schema['tables']:
                # Find FKs for this table
                table_fks = [fk for fk in spider_fks if fk['from_table'] == table['name']]

                # Add to foreign_keys list
                for fk in table_fks:
                    table['foreign_keys'].append({
                        'column': fk['from_column'],
                        'referenced_table': fk['to_table'],
                        'referenced_column': fk['to_column'],
                        'source': 'spider_metadata'  # Mark source
                    })

        return schema
```

### Phase 3: Update Semantic Layer Generator (15 minutes)

**File:** `backend/app/services/semantic_layer_generator.py`

**Changes:**

1. **Update prompt to emphasize FK importance:**

```python
# In _build_prompt() method, add:

FOREIGN KEY RELATIONSHIPS (CRITICAL):
The schema below includes documented foreign key relationships.
These are MANDATORY for correct query generation.

When documenting relationships in your output:
1. INCLUDE ALL foreign keys shown in the schema
2. Document the exact join pattern
3. Explain when this join is needed
4. Do NOT invent relationships not in the schema
5. Do NOT skip documented relationships

Missing a foreign key relationship will cause query failures!
```

2. **Improve schema formatting to highlight FKs:**

```python
def _format_schema(self, schema_info: Dict[str, Any]) -> str:
    """Format schema information for the prompt."""
    lines = []

    for table in schema_info["tables"]:
        lines.append(f"\n===== Table: {table['name']} =====")
        lines.append(f"Row count: {table['row_count']}")
        lines.append(f"Primary key: {table.get('primary_key', 'unknown')}")
        lines.append("\nColumns:")

        for col in table["columns"]:
            pk = " [PRIMARY KEY]" if col["primary_key"] else ""
            nullable = " NULL" if col["nullable"] else " NOT NULL"
            lines.append(f"  • {col['name']}: {col['type']}{pk}{nullable}")

        if table["foreign_keys"]:
            lines.append("\n🔗 FOREIGN KEYS (MANDATORY):")
            for fk in table["foreign_keys"]:
                source = fk.get('source', 'database')
                lines.append(
                    f"  → {fk['column']} REFERENCES {fk['referenced_table']}.{fk['referenced_column']} (source: {source})"
                )
                lines.append(
                    f"     JOIN PATTERN: JOIN {fk['referenced_table']} ON {table['name']}.{fk['column']} = {fk['referenced_table']}.{fk['referenced_column']}"
                )
        else:
            lines.append("\n(No foreign keys)")

    return "\n".join(lines)
```

### Phase 4: Testing (1 hour)

1. **Unit test the Spider loader:**
```bash
python3 -c "
from backend.app.services.spider_metadata_loader import get_spider_metadata_loader

loader = get_spider_metadata_loader()
fks = loader.get_foreign_keys('car_1')
print('car_1 foreign keys:', fks)
assert len(fks) == 5, 'Expected 5 FKs for car_1'
"
```

2. **Regenerate car_1 semantic layer:**
```python
# Test that FKs are now included
from backend.app.services.semantic_layer_generator import SemanticLayerGenerator
# ... generate semantic layer for car_1
# ... verify relationships array is populated
```

3. **Run targeted benchmark:**
```bash
# Run only car_1 queries to validate
# Expected: car_1 improvement from 53.26% → ~60%+
```

### Phase 5: Full Deployment (2 hours)

1. **Regenerate all 20 semantic layers** with Spider FK metadata
2. **Upload to Supabase** (replace existing layers)
3. **Re-embed and upload to Pinecone** (with corrected relationships)
4. **Run full benchmark** (Run 19)

---

## Expected Impact

### Before (Run 18):
- car_1: -4.35% (4 queries lost)
- flight_2: -5.00% (4 queries lost)
- Overall: 68.6% (710/1034)

### After (Run 19 - Conservative):
- car_1: +2% (2 queries gained) - now has FKs
- flight_2: +2.5% (2 queries gained) - now has FKs
- Other databases: 0% change (already had correct FKs)
- **Overall: 69.0%+ (714+/1034)** - **+0.4% improvement over Run 18, neutral vs baseline**

### After (Run 19 - Optimistic):
- car_1: +5% (5 queries gained)
- flight_2: +7% (5 queries gained)
- Other improving databases benefit from clearer FK documentation
- **Overall: 70.0%+ (724/1034)** - **+1.4% improvement, beating baseline!**

---

## Implementation Steps

### Step 1: Apply Code Changes (45 min)
1. ✅ Create `spider_metadata_loader.py`
2. ⏳ Update `supabase_schema_extractor.py`
3. ⏳ Update `semantic_layer_generator.py` prompt
4. ⏳ Update `_format_schema()` to highlight FKs

### Step 2: Test Integration (30 min)
5. ⏳ Test Spider loader with car_1
6. ⏳ Regenerate car_1 semantic layer
7. ⏳ Verify FKs are documented

### Step 3: Targeted Validation (30 min)
8. ⏳ Run mini-benchmark on car_1 only
9. ⏳ Verify joins are working
10. ⏳ Compare to baseline

### Step 4: Full Deployment (2 hours)
11. ⏳ Regenerate all 20 semantic layers
12. ⏳ Upload to Supabase
13. ⏳ Re-embed and upload to Pinecone
14. ⏳ Run Benchmark Run 19
15. ⏳ Analyze results

---

## Validation Criteria

**Minimum Success:**
- car_1 semantic layer has 5 documented relationships ✓
- car_1 accuracy improves by at least +2%
- No other databases regress by >1%

**Target Success:**
- car_1 accuracy improves by +5%
- flight_2 accuracy improves by +5%
- Overall: 69.5%+ (neutral to baseline)

**Stretch Success:**
- Overall: 70.5%+ (+1% over baseline)
- 12+ databases benefit from semantic layers
- <3 databases hurt by >2%

---

## Next Steps

**Ready to implement?**
1. I can apply Phase 2 changes to `supabase_schema_extractor.py`
2. I can apply Phase 3 changes to `semantic_layer_generator.py`
3. We can test on car_1 to validate the approach
4. If successful, regenerate all 20 semantic layers

**Want me to proceed with Phase 2?**
