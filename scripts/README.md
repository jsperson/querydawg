# Scripts Directory

Utility scripts for data processing, database loading, and automation.

## Scripts

### Data Loading
- `load_spider_to_supabase.py` - Convert SQLite to PostgreSQL and load into Supabase
- `create_schemas.py` - Create database schemas in Supabase
- `verify_data.py` - Verify data integrity after loading

### Semantic Layer Generation
- `generate_semantic_layer.py` - Generate semantic documentation for all databases
- `embed_documents.py` - Create embeddings and upload to Pinecone

### Evaluation
- `run_evaluation.py` - Run Spider benchmark evaluation
- `analyze_results.py` - Analyze evaluation results
- `calculate_metrics.py` - Calculate accuracy and cost metrics

### Utilities
- `test_connections.py` - Test all service connections
- `estimate_costs.py` - Estimate OpenAI API costs
- `backup_data.py` - Backup Supabase data

## Usage

Run scripts from project root:
```bash
python scripts/script_name.py
```

All scripts use environment variables from `.env` file.

## Dependencies

Scripts use the same dependencies as backend. Install with:
```bash
pip install -r backend/requirements.txt
```
