# Semantic Layers

This directory contains automatically generated semantic layers for Spider databases.

## What is a Semantic Layer?

A semantic layer is natural language documentation that describes a database in business terms, bridging the gap between technical schemas and human understanding. It includes:

- **Table descriptions**: What each table represents in business terms
- **Column descriptions**: What each column means, with synonyms and sample values
- **Relationships**: Semantic meaning of foreign keys and joins
- **Common query patterns**: Typical questions asked of this data
- **Domain terminology**: Business-specific terms and definitions

## Generating Semantic Layers

### Quick Start

Generate for a single database:
```bash
python scripts/generate_semantic_layer.py --database world_1
```

Generate for all databases:
```bash
python scripts/generate_semantic_layer.py --all
```

### View the Prompt

To see the exact prompt that will be sent to the LLM without generating:
```bash
python scripts/generate_semantic_layer.py --database world_1 --show-prompt-only
```

This is useful for:
- Verifying the prompt doesn't include dataset-specific information
- Understanding what context the LLM receives
- Debugging generation issues

### Custom Instructions

You can provide custom instructions that will be included in every generation:

**Via command line:**
```bash
python scripts/generate_semantic_layer.py --database world_1 \
  --instructions "Focus on e-commerce query patterns and include pricing analysis examples"
```

**Via file (default location: data/semantic_layer_instructions.txt):**
```bash
# Edit the instructions file
nano data/semantic_layer_instructions.txt

# Generate using the instructions
python scripts/generate_semantic_layer.py --database world_1
```

**Via custom file:**
```bash
python scripts/generate_semantic_layer.py --database world_1 \
  --instructions-file path/to/my-instructions.txt
```

### Options

- `--database NAME`: Generate for specific database (e.g., world_1, car_1)
- `--all`: Generate for all databases
- `--show-prompt-only`: Display the prompt without generating
- `--instructions "text"`: Custom instructions (inline)
- `--instructions-file PATH`: Custom instructions from file
- `--no-anonymize`: Use actual database name in prompt (not recommended)
- `--output-dir PATH`: Output directory (default: data/semantic_layers)
- `--sample-rows N`: Number of sample rows per table (default: 10)

## Output Format

Each generated semantic layer is saved as JSON:

```
data/semantic_layers/
├── world_1.json
├── car_1.json
└── ...
```

Each file contains:
```json
{
  "database": "world_1",
  "semantic_layer": {
    "database": "world_1",
    "domain": "Geography and Demographics",
    "description": "...",
    "tables": [...],
    "cross_table_insights": [...],
    "domain_terminology": {...},
    "query_guidelines": [...]
  },
  "metadata": {
    "generated_at": "2025-10-22T10:00:00",
    "llm_model": "gpt-4o-mini",
    "anonymized": true,
    "sample_rows_per_table": 10
  },
  "prompt_used": "You are a database documentation expert..."
}
```

## Research Methodology

### Preventing Dataset-Specific Knowledge

To ensure the semantic layer represents what can be **automatically inferred** rather than **memorized**:

1. **Anonymized prompts**: Database names are anonymized (e.g., "database_unknown") to prevent LLM from recognizing specific datasets
2. **Schema + samples only**: LLM receives only table structures and sample data, not external documentation
3. **General knowledge allowed**: LLM may use domain knowledge (e.g., "population means count of people") but not dataset-specific facts

### Verification

To verify the methodology:
```bash
# Generate and inspect the prompt
python scripts/generate_semantic_layer.py --database world_1 --show-prompt-only

# Check that:
# - Database name is anonymized
# - No reference to "Spider" dataset
# - Only schema and sample data included
```

## Editing Semantic Layers

Generated semantic layers can be manually refined:

1. Generate initial version
2. Review for accuracy
3. Edit the JSON file
4. Update version number in the file
5. Commit to git

**Note:** Manual edits will be overwritten if you regenerate. Consider:
- Using custom instructions instead of manual edits
- Saving manual edits with a different filename
- Documenting manual changes in metadata

## Usage in Text-to-SQL

Semantic layers are loaded and injected into text-to-SQL prompts:

```python
# Load semantic layer
semantic_layer = load_semantic_layer("world_1")

# Build enhanced prompt
prompt = f"""
Database: {semantic_layer['database']}
Domain: {semantic_layer['domain']}

Tables:
{format_semantic_tables(semantic_layer['tables'])}

Question: {user_question}

Generate SQL:
"""
```

## Cost Estimation

Generating semantic layers costs approximately:
- **Per database**: $0.01 - $0.05 (depending on size)
- **19 Spider databases**: ~$0.50 - $1.00 total

Using GPT-4o-mini (recommended) vs GPT-4 can reduce costs by ~10x.

## See Also

- [Semantic Layer Schema Documentation](../../docs/semantic_layer_schema.md) - Full schema specification
- [Custom Instructions File](../semantic_layer_instructions.txt) - Default generation instructions
