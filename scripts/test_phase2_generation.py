#!/usr/bin/env python3
"""
Test Phase 2 semantic layer generation on a few databases.

This script regenerates semantic layers for 2-3 test databases to validate
the new structured relationship and column disambiguation formats.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import get_settings
from app.services.llm.openai_provider import OpenAIProvider
from app.services.semantic_layer_generator import SemanticLayerGenerator

# Test databases (Phase 2 plan recommends these 3)
TEST_DATABASES = [
    "student_transcripts_tracking",  # Complex, many relationships
    "network_1",                      # FK direction is critical here
    "pets_1"                          # Has bridge table (Has_Pet)
]

def main():
    """Test semantic layer generation with Phase 2 enhancements."""

    print("=" * 70)
    print("PHASE 2 SEMANTIC LAYER GENERATION TEST")
    print("=" * 70)
    print(f"Testing {len(TEST_DATABASES)} databases:")
    for db in TEST_DATABASES:
        print(f"  • {db}")
    print()

    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print('ERROR: DATABASE_URL not set in environment')
        return False

    # Get OpenAI API key
    settings = get_settings()

    # Initialize LLM
    print('\nInitializing OpenAI LLM...')
    llm = OpenAIProvider(
        api_key=settings.openai_api_key,
        model=settings.llm_model
    )

    # Initialize generator
    print('Initializing Semantic Layer Generator...')
    generator = SemanticLayerGenerator(
        llm=llm,
        database_url=db_url,
        sample_rows=10
    )

    # Create output directory
    output_dir = Path('data/phase2_test_layers')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Track results
    results = {
        'success': [],
        'failed': [],
        'total_cost': 0.0,
        'total_tokens': 0
    }

    # Process each test database
    for i, db_name in enumerate(TEST_DATABASES, 1):
        print(f'\n{"=" * 70}')
        print(f'[{i}/{len(TEST_DATABASES)}] Testing: {db_name}')
        print(f'{"=" * 70}')

        try:
            # Generate semantic layer
            result = generator.generate(
                database_name=db_name,
                anonymize=True,
                save_prompt=True
            )

            # Save to output file
            output_file = output_dir / f'{db_name}.json'
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            # Extract semantic layer for analysis
            semantic_layer = result['semantic_layer']
            tables = semantic_layer.get('tables', [])

            print(f'✅ SUCCESS: {db_name}')
            print(f'   File: {output_file}')
            print(f'   Tables: {len(tables)}')
            print(f'   Tokens: {result["metadata"]["tokens_used"]}')
            print(f'   Cost: ${result["metadata"]["cost_usd"]:.4f}')

            # Analyze Phase 2 fields
            print('\n   📋 PHASE 2 FIELD ANALYSIS:')

            # Check for Phase 2 relationship fields
            phase2_rel_count = 0
            for table in tables:
                for rel in table.get("relationships", []):
                    if rel.get("join_pattern") or rel.get("when_to_use") or rel.get("vs_confusion"):
                        phase2_rel_count += 1

            if phase2_rel_count > 0:
                print(f'   ✅ Relationships with Phase 2 fields: {phase2_rel_count}')
            else:
                print(f'   ⚠️  No Phase 2 relationship fields found!')

            # Check for Phase 2 column disambiguation fields
            phase2_col_count = 0
            for table in tables:
                for col in table.get("columns", []):
                    disamb = col.get("disambiguation", {})
                    if disamb.get("primary_location") or disamb.get("directional_guidance"):
                        phase2_col_count += 1

            if phase2_col_count > 0:
                print(f'   ✅ Columns with Phase 2 disambiguation: {phase2_col_count}')
            else:
                print(f'   ⚠️  No Phase 2 column disambiguation found!')

            # Show sample relationship
            for table in tables:
                if table.get("relationships"):
                    sample_rel = table["relationships"][0]
                    print(f'\n   📝 Sample relationship from {table["name"]}:')
                    print(f'      {sample_rel.get("column")} → {sample_rel.get("references_table")}')
                    if sample_rel.get("join_pattern"):
                        print(f'      Join: {sample_rel.get("join_pattern")}')
                    if sample_rel.get("when_to_use"):
                        when = sample_rel.get("when_to_use")
                        print(f'      When: {when[0] if isinstance(when, list) and when else when}')
                    break

            results['success'].append(db_name)
            results['total_cost'] += result['metadata']['cost_usd']
            results['total_tokens'] += result['metadata']['tokens_used']

        except Exception as e:
            print(f'❌ FAILED: {db_name}')
            print(f'   Error: {e}')
            results['failed'].append(db_name)
            import traceback
            traceback.print_exc()

    # Summary
    print('\n' + '=' * 70)
    print('TEST SUMMARY')
    print('=' * 70)
    print(f'✅ Successful: {len(results["success"])}/{len(TEST_DATABASES)}')
    print(f'❌ Failed: {len(results["failed"])}/{len(TEST_DATABASES)}')
    print(f'💰 Total cost: ${results["total_cost"]:.4f}')
    print(f'📊 Total tokens: {results["total_tokens"]:,}')

    if results['success']:
        print(f'\n✅ Generated semantic layers saved to: {output_dir}')

    print('\nNext steps:')
    print('1. Manually review the generated files in data/phase2_test_layers/')
    print('2. Check that relationships have join_pattern, when_to_use, vs_confusion')
    print('3. Check that columns have primary_location, directional_guidance')
    print('4. If quality is good, proceed with full regeneration')
    print('5. If issues found, refine prompts in semantic_layer_generator.py and re-test')

    return len(results['failed']) == 0

if __name__ == "__main__":
    main()
