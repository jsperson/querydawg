# Turso Integration Proposal: Hybrid Database Architecture

**Date**: 2025-11-03
**Proposal**: Add Turso (libSQL) for Spider benchmark databases, keep Supabase for metadata

---

## Executive Summary

**Current Architecture**: All-Supabase (PostgreSQL)
- Spider datasets: Supabase PostgreSQL
- Metadata/results: Supabase PostgreSQL
- Semantic layers: Pinecone

**Proposed Architecture**: Hybrid (Turso + Supabase)
- **Spider datasets**: **Turso (SQLite/libSQL)** ← NEW
- Metadata/results: Supabase PostgreSQL
- Semantic layers: Pinecone

**Key Benefits**:
1. ✅ **Higher fidelity**: Spider is natively SQLite, no conversion needed
2. ✅ **Faster benchmarks**: Edge replicas + SQLite performance
3. ✅ **Easier updates**: Drop SQLite files directly into Turso
4. ✅ **Cost effective**: Generous free tier (500 DBs, 9GB storage)
5. ✅ **Better for research**: Matches Spider's original environment

**Implementation**: 1-2 weeks, low risk (keeps Supabase for metadata)

---

## Problem with Current Architecture

### Issue 1: SQLite → PostgreSQL Conversion

**Spider datasets are SQLite**:
```
data/spider/database/
├── concert_singer/
│   └── concert_singer.sqlite
├── wta_1/
│   └── wta_1.sqlite
└── ...
```

**Current process**:
1. Parse SQLite schema
2. Convert SQLite types to PostgreSQL types
3. Load data into Supabase PostgreSQL
4. Schema differences cause issues:
   - Type mismatches (REAL → NUMERIC)
   - Quote handling (backticks → double quotes)
   - SQL dialect differences

**Problems**:
- ❌ Conversion errors (seen in past runs)
- ❌ Schema inconsistencies
- ❌ Gold SQL may fail (written for SQLite, run on PostgreSQL)
- ❌ Extra maintenance burden

### Issue 2: Benchmark Fidelity

**Spider benchmark is designed for SQLite**:
- All gold SQL written for SQLite
- Schema designed for SQLite data types
- Sample queries assume SQLite functions

**Running on PostgreSQL**:
- Need to convert SQL syntax
- Need to qualify table names (schema.table vs just table)
- Some queries fail due to dialect differences

**Result**: Less faithful to original benchmark

### Issue 3: Slow Data Loading

**Current Supabase loading**:
- Parse SQLite → Generate PostgreSQL schema → Insert data
- For 20 databases: ~5-10 minutes
- For 100+ databases: Could be hours

**With Turso**:
- Upload SQLite file directly
- No conversion needed
- For 20 databases: ~1-2 minutes
- For 100+ databases: ~10 minutes

---

## What is Turso?

### Overview
- **libSQL**: Fork of SQLite with server capabilities
- **Edge replicas**: Databases replicated to edge locations
- **HTTP API**: Query via HTTP/REST (no TCP connection needed)
- **Compatible with SQLite**: Can import .sqlite files directly

### Pricing (Free Tier)
```
Free Plan:
- 500 databases
- 9 GB total storage
- 1 billion row reads/month
- Unlimited edge replicas

For QueryDawg:
- 20 databases (Spider 1.0)
- ~100 MB storage
- ~10M row reads/month (benchmarks)
→ Well within free tier
```

### Key Features for Benchmarks

1. **Direct SQLite import**:
```bash
turso db create concert_singer --from-file concert_singer.sqlite
```

2. **Edge replication**:
```
Primary: US (Railway deployment region)
Replicas: Auto-deployed to nearest edge
→ Faster query execution
```

3. **HTTP API**:
```typescript
const result = await turso.execute({
  sql: "SELECT * FROM concerts WHERE year > ?",
  args: [2010]
})
```

4. **Compatible with SQLite**:
- Same SQL syntax
- Same data types
- Same functions
- Gold SQL runs without modification

---

## Proposed Hybrid Architecture

### Database Responsibilities

| Database | Purpose | Why |
|----------|---------|-----|
| **Turso (libSQL)** | Spider benchmark datasets | Native SQLite, high fidelity |
| **Supabase (PostgreSQL)** | Metadata, results, semantic layers | Relational queries, joins |
| **Pinecone** | Vector embeddings | Semantic search |

### Data Flow

```
┌─────────────────────────────────────────────────────┐
│ BENCHMARK EXECUTION                                  │
└─────────────────────────────────────────────────────┘

1. User initiates benchmark
   ↓
2. Fetch questions from Supabase
   │
   ├── Question: "How many concerts in 2020?"
   ├── Database: "concert_singer"
   └── Gold SQL: "SELECT COUNT(*) FROM concerts WHERE year = 2020"
   ↓
3. Generate SQL (LLM + semantic layer from Pinecone)
   ↓
4. Execute queries against Turso (Spider data)
   │
   ├── Baseline SQL → Turso
   ├── Enhanced SQL → Turso
   └── Gold SQL → Turso
   ↓
5. Compare results
   ↓
6. Store results in Supabase
   │
   └── benchmark_results table (PostgreSQL)
```

### Schema Extraction Flow

```
┌─────────────────────────────────────────────────────┐
│ SEMANTIC LAYER GENERATION                           │
└─────────────────────────────────────────────────────┘

1. Extract schema from Turso (SQLite)
   ↓
2. Sample data from Turso
   ↓
3. Generate semantic layer (LLM)
   ↓
4. Store semantic layer in Supabase
   ↓
5. Embed and upload to Pinecone
```

### Advantages

**Data Separation**:
- ✅ Spider data isolated (Turso)
- ✅ Application data isolated (Supabase)
- ✅ Clear separation of concerns

**Best Tool for Each Job**:
- ✅ SQLite (Turso) for benchmark fidelity
- ✅ PostgreSQL (Supabase) for relational metadata
- ✅ Vector DB (Pinecone) for semantic search

**Scalability**:
- ✅ Easy to add new Spider databases (upload .sqlite)
- ✅ Free tier supports 500 databases (Spider 2.0 ready)
- ✅ Edge replicas for global performance

---

## Implementation Plan

### Phase 1: Turso Setup (Day 1)

**1. Create Turso account & organization**
```bash
# Install Turso CLI
curl -sSfL https://get.tur.so/install.sh | bash

# Login
turso auth login

# Create organization (if needed)
turso org create querydawg
```

**2. Upload Spider databases**
```bash
# Script to upload all Spider databases
for db in data/spider/database/*/; do
  db_name=$(basename "$db")
  turso db create "$db_name" --from-file "$db/${db_name}.sqlite"
done

# Result: 20 databases in Turso
```

**3. Get connection tokens**
```bash
# Get database URLs
turso db show concert_singer --url
# libsql://concert_singer-querydawg.turso.io

# Create auth token
turso db tokens create concert_singer
# eyJhbGc...
```

### Phase 2: Backend Integration (Days 2-3)

**1. Add Turso SDK**
```bash
cd backend
pip install libsql-client
```

**2. Create Turso client wrapper**
```python
# backend/app/database/turso_client.py
from libsql_client import create_client
from typing import List, Dict, Any
import os

class TursoClient:
    """Client for querying Turso (libSQL) databases"""

    def __init__(self, db_name: str):
        """
        Initialize Turso client for a specific database

        Args:
            db_name: Name of the Turso database (e.g., 'concert_singer')
        """
        self.db_name = db_name

        # Get URL and token from environment
        turso_base_url = os.getenv("TURSO_BASE_URL", "https://querydawg.turso.io")
        turso_token = os.getenv(f"TURSO_TOKEN_{db_name.upper()}")

        if not turso_token:
            # Try fallback to shared token
            turso_token = os.getenv("TURSO_TOKEN")

        if not turso_token:
            raise ValueError(f"No Turso token found for {db_name}")

        # Create client
        self.client = create_client(
            url=f"libsql://{db_name}-{turso_base_url.split('//')[1]}",
            auth_token=turso_token
        )

    def execute(self, sql: str, params: List[Any] = None) -> Dict[str, Any]:
        """
        Execute SQL query

        Args:
            sql: SQL query string
            params: Optional query parameters

        Returns:
            Query results
        """
        result = self.client.execute(sql, params or [])

        return {
            "columns": result.columns,
            "rows": result.rows,
            "rows_affected": result.rows_affected
        }

    def execute_batch(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute multiple queries in a transaction"""
        return [self.execute(q) for q in queries]
```

**3. Update schema extractor**
```python
# backend/app/database/turso_schema_extractor.py
from .turso_client import TursoClient
from typing import Dict, Any, List

class TursoSchemaExtractor:
    """Extract schema from Turso (SQLite) databases"""

    def __init__(self, db_name: str):
        self.db_name = db_name
        self.client = TursoClient(db_name)

    def extract_schema(self) -> Dict[str, Any]:
        """Extract full schema information"""

        # Get all tables
        tables_result = self.client.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )

        tables = []
        for row in tables_result["rows"]:
            table_name = row[0]

            # Get table info
            table_info = self.client.execute(f"PRAGMA table_info({table_name})")

            # Get foreign keys
            fk_info = self.client.execute(f"PRAGMA foreign_key_list({table_name})")

            # Get row count
            count_result = self.client.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = count_result["rows"][0][0]

            # Build table schema
            columns = []
            for col in table_info["rows"]:
                columns.append({
                    "name": col[1],  # column name
                    "type": col[2],  # data type
                    "nullable": not col[3],  # notnull flag (inverted)
                    "default": col[4],  # default value
                    "primary_key": bool(col[5])  # pk flag
                })

            # Build foreign keys
            foreign_keys = []
            for fk in fk_info["rows"]:
                foreign_keys.append({
                    "column": fk[3],  # from column
                    "referenced_table": fk[2],  # to table
                    "referenced_column": fk[4],  # to column
                })

            tables.append({
                "name": table_name,
                "row_count": row_count,
                "columns": columns,
                "foreign_keys": foreign_keys
            })

        return {
            "database": self.db_name,
            "tables": tables
        }

    def sample_table(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Sample rows from a table"""
        result = self.client.execute(f"SELECT * FROM {table_name} LIMIT {limit}")

        # Convert to list of dicts
        rows = []
        for row in result["rows"]:
            rows.append(dict(zip(result["columns"], row)))

        return rows
```

**4. Update benchmark runner**
```python
# backend/app/services/benchmark_runner.py

# Add Turso support
def _execute_sql(self, sql: str, database: str) -> tuple[Any, str | None]:
    """Execute SQL against Turso database"""
    try:
        from ..database.turso_client import TursoClient

        client = TursoClient(database)
        result = client.execute(sql)

        # Convert to comparable format
        return result["rows"], None

    except Exception as e:
        return None, str(e)
```

### Phase 3: Configuration (Day 4)

**1. Environment variables**
```bash
# .env
TURSO_BASE_URL=https://querydawg.turso.io
TURSO_TOKEN=<shared-token>  # Fallback token

# Database-specific tokens (optional, for fine-grained access)
TURSO_TOKEN_CONCERT_SINGER=<token>
TURSO_TOKEN_WTA_1=<token>
# ...
```

**2. Railway deployment**
```bash
# Add to Railway environment variables
railway variables set TURSO_BASE_URL=https://querydawg.turso.io
railway variables set TURSO_TOKEN=<token>
```

### Phase 4: Testing & Migration (Days 5-7)

**1. Test schema extraction**
```python
# scripts/test_turso_schema.py
from backend.app.database.turso_schema_extractor import TursoSchemaExtractor

extractor = TursoSchemaExtractor("concert_singer")
schema = extractor.extract_schema()

print(f"Tables: {len(schema['tables'])}")
for table in schema['tables']:
    print(f"  - {table['name']}: {table['row_count']} rows")
```

**2. Test query execution**
```python
# scripts/test_turso_query.py
from backend.app.database.turso_client import TursoClient

client = TursoClient("concert_singer")
result = client.execute("SELECT COUNT(*) FROM concerts")
print(f"Concert count: {result['rows'][0][0]}")
```

**3. Regenerate semantic layers from Turso**
```bash
# Use Turso as source for schema extraction
python scripts/regenerate_all_semantic_layers.py --source=turso
```

**4. Run benchmark against Turso**
```bash
# Test on subset first
python scripts/run_benchmark.py --databases concert_singer,wta_1 --limit 50

# Then full benchmark
python scripts/run_benchmark.py --full
```

---

## Benefits Analysis

### Benefit 1: Higher Benchmark Fidelity

**Current (Supabase)**:
- Spider gold SQL written for SQLite
- Running on PostgreSQL
- Syntax conversion needed
- Type mismatches possible
- ~84 gold SQL failures (cre_Doc_Template_Mgt)

**With Turso**:
- Spider gold SQL written for SQLite
- Running on SQLite (libSQL)
- No conversion needed
- Exact type matching
- Expected: 0 gold SQL failures

**Impact**: More accurate benchmark results

### Benefit 2: Easier Data Management

**Current (Supabase)**:
```bash
# Update Spider data: Complex multi-step process
1. Parse SQLite schema
2. Convert to PostgreSQL DDL
3. Load data
4. Fix conversion errors
5. Validate
Time: 30-60 minutes
```

**With Turso**:
```bash
# Update Spider data: One command
turso db create concert_singer --from-file concert_singer.sqlite
Time: 30 seconds
```

**Impact**: 60× faster data updates

### Benefit 3: Performance Improvements

**Current (Supabase)**:
- PostgreSQL connection overhead
- Network latency to Supabase servers
- Query parsing overhead
- Average query time: ~50-100ms

**With Turso**:
- Edge replicas (near Railway deployment)
- SQLite query performance
- HTTP API (connection pooling)
- Expected query time: ~10-30ms

**Impact**: 3-5× faster benchmark execution

### Benefit 4: Cost Savings

**Current (Supabase)**:
- Free tier: 500 MB database
- Current usage: ~100 MB (Spider data)
- Room for growth: ~400 MB

**With Turso**:
- Free tier: 9 GB storage, 500 databases
- Current usage: ~100 MB
- Room for growth: 8.9 GB (90× more!)

**Impact**: Can support Spider 2.0 (100+ databases) on free tier

### Benefit 5: Better Research Methodology

**Current**:
- "We converted SQLite to PostgreSQL for deployment convenience"
- Reviewers: "This changes the benchmark environment"

**With Turso**:
- "We used Turso (libSQL) to maintain SQLite compatibility"
- Reviewers: "Good - maintains benchmark fidelity"

**Impact**: Stronger research contribution

---

## Architecture Comparison

### Current: All-Supabase

```
┌─────────────────────────────────────────┐
│           Supabase PostgreSQL           │
├─────────────────────────────────────────┤
│ • Spider datasets (converted)           │
│ • Benchmark results                     │
│ • Semantic layers                       │
│ • Metadata                              │
└─────────────────────────────────────────┘

Pros:
+ Single database to manage
+ All data in one place

Cons:
- SQLite → PostgreSQL conversion
- Schema differences
- Gold SQL failures
- Harder to update datasets
```

### Proposed: Hybrid (Turso + Supabase)

```
┌─────────────────────┐  ┌─────────────────────┐
│    Turso (libSQL)   │  │ Supabase PostgreSQL │
├─────────────────────┤  ├─────────────────────┤
│ • Spider datasets   │  │ • Benchmark results │
│   (native SQLite)   │  │ • Semantic layers   │
│ • Fast queries      │  │ • Metadata          │
│ • Edge replicas     │  │ • Joins/aggregates  │
└─────────────────────┘  └─────────────────────┘
         ↑                         ↑
         └─────────────┬───────────┘
                       │
              ┌────────┴────────┐
              │  QueryDawg API  │
              └─────────────────┘

Pros:
+ Native SQLite (high fidelity)
+ No conversion needed
+ Faster benchmarks
+ Easy to update datasets
+ Best tool for each job

Cons:
- Two databases to manage
- Slightly more complex
```

---

## Risk Analysis

### Risk 1: Added Complexity ⚠️ LOW
**Concern**: Managing two databases instead of one

**Mitigation**:
- Clear separation: Turso = data, Supabase = metadata
- Both have simple APIs
- Can be abstracted in data access layer

**Assessment**: LOW - Complexity is manageable

### Risk 2: Turso Service Availability ⚠️ LOW
**Concern**: Dependency on Turso service

**Mitigation**:
- Turso is backed by Cloudflare (reliable)
- Can export SQLite files anytime
- Can fall back to local SQLite if needed
- Open source (libSQL) - can self-host

**Assessment**: LOW - Multiple fallback options

### Risk 3: Migration Effort ⚠️ MEDIUM
**Concern**: Time to migrate existing setup

**Mitigation**:
- Incremental migration (test one DB first)
- Keep Supabase running during transition
- Can run both in parallel
- Well-defined migration plan (1-2 weeks)

**Assessment**: MEDIUM - Requires effort but low-risk

### Risk 4: API Differences ⚠️ LOW
**Concern**: SQLite vs PostgreSQL API differences

**Mitigation**:
- Create abstraction layer (SchemaExtractor interface)
- Both support standard SQL
- Turso SDK is well-documented

**Assessment**: LOW - Standard SQL interface

---

## Decision Matrix

### Criteria Comparison

| Criterion | Current (Supabase) | Proposed (Turso + Supabase) | Winner |
|-----------|-------------------|----------------------------|--------|
| **Benchmark Fidelity** | Medium (converted) | High (native SQLite) | ✅ Turso |
| **Setup Complexity** | Low (1 DB) | Medium (2 DBs) | ⚠️ Supabase |
| **Data Update Speed** | Slow (conversion) | Fast (direct upload) | ✅ Turso |
| **Query Performance** | Medium | High (edge replicas) | ✅ Turso |
| **Cost** | Free tier (0.5 GB) | Free tier (9 GB) | ✅ Turso |
| **Scalability** | Limited | High (500 DBs) | ✅ Turso |
| **Research Methodology** | Weak (conversion) | Strong (native) | ✅ Turso |
| **Maintenance** | Medium | Low (no conversion) | ✅ Turso |

**Score**: Turso wins 7/8 criteria

---

## Recommendation

### PRIMARY RECOMMENDATION: **Migrate to Turso** ✅

**Reasons**:
1. ✅ **Higher benchmark fidelity** - Native SQLite, no conversion
2. ✅ **Faster execution** - Edge replicas, SQLite performance
3. ✅ **Easier maintenance** - Direct .sqlite upload, no conversion
4. ✅ **Better scalability** - 500 DBs on free tier
5. ✅ **Stronger research** - Maintains benchmark environment
6. ✅ **Low risk** - Can keep Supabase for metadata
7. ✅ **Free** - Well within free tier limits

**Timeline**: 1-2 weeks for full migration

**Effort**: Medium (some code changes, but well-defined)

**ROI**: HIGH - Significant benefits for moderate effort

### Implementation Order

**Week 1: Setup & Testing**
- Day 1: Create Turso account, upload databases
- Day 2-3: Implement Turso client & schema extractor
- Day 4: Configure environment, deploy to Railway
- Day 5: Test on single database (concert_singer)

**Week 2: Migration & Validation**
- Day 6: Regenerate semantic layers from Turso
- Day 7: Run test benchmark (concert_singer, wta_1)
- Day 8-9: Migrate all 20 databases
- Day 10: Run full benchmark, validate results

**Success Criteria**:
- ✅ All 20 databases in Turso
- ✅ Zero gold SQL failures (vs 84 with Supabase)
- ✅ Benchmark runs successfully
- ✅ Semantic layers generated from Turso
- ✅ Query latency <50ms (vs ~100ms with Supabase)

---

## Alternative: Hybrid Approach

If full migration seems risky, start with hybrid:

**Phase 1: Add Turso (keep Supabase)**
- Upload Spider databases to Turso
- Keep Supabase for metadata
- Run benchmarks against Turso
- Compare results

**Phase 2: Evaluate**
- If Turso works well → full migration
- If issues arise → stay with Supabase

This de-risks the migration and allows for validation before committing.

---

## Conclusion

Turso integration is a **high-value, low-risk improvement** that:
- ✅ Improves benchmark fidelity (native SQLite)
- ✅ Increases performance (edge replicas)
- ✅ Reduces maintenance (no conversion)
- ✅ Strengthens research methodology
- ✅ Costs nothing (free tier)

**Recommendation**: Proceed with Turso integration for Spider benchmark databases.

The hybrid architecture (Turso for data, Supabase for metadata) is the best of both worlds:
- SQLite compatibility where it matters (benchmark data)
- PostgreSQL power where it matters (metadata queries)
- Clear separation of concerns
- Future-proof (ready for Spider 2.0)

**Next step**: Set up Turso account and upload one test database (concert_singer) to validate approach.
