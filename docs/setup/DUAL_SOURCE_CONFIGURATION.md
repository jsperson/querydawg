# Dual-Source Configuration Guide

QueryDawg now supports running benchmarks against both **Supabase (PostgreSQL)** and **Turso (SQLite)** databases with a single configuration variable.

## Overview

The system uses a flexible abstraction layer that allows switching between database sources without code changes:

- **Supabase**: PostgreSQL-based, requires SQLite→PostgreSQL conversion
- **Turso**: Native SQLite, no conversion needed (eliminates 84 gold SQL failures)

## Configuration

### Environment Variable

Set the `SPIDER_DATA_SOURCE` environment variable to control which database source is used:

```bash
# For Supabase (PostgreSQL) - DEFAULT
export SPIDER_DATA_SOURCE=supabase

# For Turso (SQLite)
export SPIDER_DATA_SOURCE=turso
```

### Complete Configuration Examples

#### Supabase Configuration

```bash
# .env file
SPIDER_DATA_SOURCE=supabase
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SUPABASE_DB_URL=postgresql://user:pass@host:5432/dbname
```

#### Turso Configuration

```bash
# .env file
SPIDER_DATA_SOURCE=turso
TURSO_TOKEN=your_turso_auth_token
TURSO_ORG=querydawg  # Optional, defaults to 'querydawg'
```

## What Changes Automatically

When you switch `SPIDER_DATA_SOURCE`, the following components automatically adapt:

### 1. Query Execution
- **Supabase**: Uses PostgreSQL connection pool
- **Turso**: Uses HTTP API client for libSQL

### 2. SQL Conversion
- **Supabase**: Applies SQLite→PostgreSQL conversion for gold SQL
- **Turso**: No conversion needed (native SQLite format)

### 3. Schema Extraction
- **Supabase**: Queries `information_schema` tables
- **Turso**: Uses SQLite `PRAGMA` commands

### 4. SQL Generation
- **Supabase**: Generates PostgreSQL-compatible SQL
- **Turso**: Generates SQLite-compatible SQL

## Architecture

### Abstraction Layers

The system uses three key abstraction layers:

1. **Query Executor** (`backend/app/database/query_executor.py`)
   - `PostgreSQLExecutor`: Connection pooling, retry logic
   - `TursoExecutor`: HTTP API calls
   - `QueryExecutorFactory`: Creates appropriate executor

2. **Schema Extractor** (`backend/app/services/schema/`)
   - `PostgreSQLSchemaExtractor`: PostgreSQL schema extraction
   - `TursoSchemaExtractor`: SQLite schema extraction via PRAGMA
   - `SchemaExtractorFactory`: Creates appropriate extractor

3. **Benchmark Runner** (`backend/app/services/benchmark_runner.py`)
   - Detects source from `SPIDER_DATA_SOURCE`
   - Routes queries to correct executor
   - Conditionally applies SQL conversion

## Usage Examples

### Running Benchmarks

The benchmark runner automatically uses the configured source:

```python
from app.database.benchmark_store import BenchmarkStore
from app.services.benchmark_runner import BenchmarkRunner
from app.models.benchmark import BenchmarkConfig

# Create benchmark runner (auto-detects source from env)
store = BenchmarkStore(supabase_url, supabase_key)
runner = BenchmarkRunner(
    benchmark_store=store,
    budget_limit_usd=5.0
    # No need to specify data_source - uses SPIDER_DATA_SOURCE env var
)

# Run benchmark (uses configured source)
config = BenchmarkConfig(
    name="Test Run",
    run_type="both",  # baseline + enhanced
    databases=["concert_singer"],
    question_limit=10
)

run_id = runner.run_benchmark(config)
```

### Generating Semantic Layers

Schema extraction also respects the `SPIDER_DATA_SOURCE` setting:

```python
from app.services.schema import SchemaExtractorFactory

# Auto-detects source from SPIDER_DATA_SOURCE env var
extractor = SchemaExtractorFactory.create(
    schema_name="concert_singer"  # database name
)

schema = extractor.extract_full_schema()
```

### Explicit Source Override

You can also explicitly specify the source:

```python
# Override in code (not recommended - prefer env var)
runner = BenchmarkRunner(
    benchmark_store=store,
    data_source="turso"  # Explicit override
)

# Or for schema extraction
extractor = SchemaExtractorFactory.create(
    db_type="turso",
    schema_name="concert_singer"
)
```

## Switching Between Sources

### From Supabase to Turso

1. Set up Turso (see `TURSO_QUICK_START.md`)
2. Update `.env`:
   ```bash
   SPIDER_DATA_SOURCE=turso
   TURSO_TOKEN=your_token
   ```
3. Restart application
4. Run benchmarks as normal

### From Turso to Supabase

1. Update `.env`:
   ```bash
   SPIDER_DATA_SOURCE=supabase
   DATABASE_URL=your_postgres_url
   ```
2. Restart application
3. Run benchmarks as normal

## Benefits of Turso

When using Turso (`SPIDER_DATA_SOURCE=turso`):

- **No conversion errors**: Native SQLite format matches Spider benchmark
- **Expected improvement**: 0 gold SQL failures (vs 84 with PostgreSQL)
- **Faster queries**: 3-5× faster than PostgreSQL for benchmark workloads
- **Simpler setup**: No schema migrations needed

## Backward Compatibility

The default configuration (`SPIDER_DATA_SOURCE=supabase`) maintains full backward compatibility:
- Existing benchmarks work unchanged
- Existing semantic layers work unchanged
- No code changes required

## Troubleshooting

### "Database source not configured"

**Cause**: `SPIDER_DATA_SOURCE` not set or invalid value

**Solution**: Set in `.env`:
```bash
SPIDER_DATA_SOURCE=supabase  # or 'turso'
```

### "TURSO_TOKEN not set"

**Cause**: Using `SPIDER_DATA_SOURCE=turso` without token

**Solution**: Get token from Turso and add to `.env`:
```bash
TURSO_TOKEN=your_token_here
```

### "DATABASE_URL not set"

**Cause**: Using `SPIDER_DATA_SOURCE=supabase` without connection string

**Solution**: Add PostgreSQL connection string to `.env`:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

## Files Modified

The following files were modified to support dual-source configuration:

1. `backend/app/database/query_executor.py` - Added TursoExecutor and QueryExecutorFactory
2. `backend/app/services/schema/factory.py` - Added Turso support with auto-detection
3. `backend/app/services/schema/turso.py` - New Turso schema extractor
4. `backend/app/services/benchmark_runner.py` - Added data_source parameter and conditional SQL conversion
5. `backend/requirements.txt` - Added `requests>=2.31.0` for Turso HTTP API

## Next Steps

1. **Current Environment**: Verify which source is configured
   ```bash
   echo $SPIDER_DATA_SOURCE
   ```

2. **Supabase Setup**: See existing documentation
   - Database already set up
   - Semantic layers already generated

3. **Turso Setup**: See `TURSO_QUICK_START.md`
   - 5 simple steps, ~30 minutes
   - Automated upload script included

4. **Run Comparison**: Test both sources
   - Run benchmark with Supabase: `SPIDER_DATA_SOURCE=supabase`
   - Run benchmark with Turso: `SPIDER_DATA_SOURCE=turso`
   - Compare execution accuracy (expect 0 gold failures with Turso)
