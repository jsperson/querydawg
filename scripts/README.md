# Scripts Directory

This directory contains utility scripts for managing the QueryDawg text-to-SQL system.

## Core Scripts (Main Directory)

These are the actively used scripts for day-to-day operations:

### Data Management
- **`download_spider.py`** - Downloads the Spider dataset
- **`load_spider_databases.py`** - Loads Spider databases into the system
- **`verify_spider.py`** - Verifies Spider data integrity
- **`upload_spider_to_turso_cli.py`** - Uploads Spider databases to Turso

### Semantic Layer Operations
- **`generate_semantic_layer.py`** - Generates a semantic layer for a single database
- **`regenerate_all_semantic_layers.py`** - Regenerates semantic layers for all databases
- **`embed_semantic_layers.py`** - Embeds semantic layers into Pinecone for RAG
- **`upload_semantic_layers_to_supabase.py`** - Uploads semantic layers to Supabase

### Benchmarking
- **`run_full_benchmark.py`** - Runs the full benchmark evaluation

## Subdirectories

### `migrations/`
Database migration scripts (already run, kept for reference):
- apply_data_source_migration.py
- apply_migration.py
- apply_prompt_logging_migration.py
- deploy_metadata_schema.py
- init_metadata_schema.py
- run_migration.py

### `backups/`
Backup utilities for Phase 1 data:
- backup_embeddings.py
- backup_phase1_data.py

### `validation/`
One-off validation and inspection scripts used during Phase 1/2:
- check_battle_death_phase2.py
- check_battle_death_supabase.py
- check_phase2_in_pinecone.py
- compare_phase1_phase2.py
- download_phase2_semantic_layers.py
- inspect_battle_death_vector.py
- inspect_pinecone_vectors.py
- validate_all_deployments.py
- validate_phase2_changes.py
- validate_pinecone_phase2.py
- supabase_status_summary.py
- check_pinecone_status.py
- find_gold_sql_error.py

### `debug/`
Debug, test, and diagnostic scripts (kept for troubleshooting):
- **check_*.py** - Various data/database checks (11 scripts)
- **debug_*.py** - Turso connection debugging (3 scripts)
- **test_*.py** - Test scripts for various components (13 scripts)
- compare_benchmark_prompts.py
- clean_turso_databases.py

### `archive/`
Deprecated/one-off scripts no longer in active use:
- cancel_run.py
- regenerate_car1_layer.py
- upload_spider_to_turso.py (old version)
- upload_to_turso.py (old version)
- upload_to_turso_api.py (old version)

## Usage

Run scripts from the project root directory:

```bash
# Example: Regenerate all semantic layers
python scripts/regenerate_all_semantic_layers.py

# Example: Run full benchmark
python scripts/run_full_benchmark.py
```

## Environment

All scripts require the appropriate environment variables set in `.env` file at the project root.
