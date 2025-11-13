#!/usr/bin/env python3
"""
Test script to regenerate car_1 semantic layer with Spider FK metadata.
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

def main():
    print('Regenerating car_1 semantic layer with Spider FK metadata...')
    print('=' * 60)

    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print('ERROR: DATABASE_URL not set in environment')
        return False

    # Get OpenAI API key
    settings = get_settings()

    # Initialize LLM
    llm = OpenAIProvider(
        api_key=settings.openai_api_key,
        model=settings.llm_model
    )

    # Initialize generator (with Spider metadata enabled by default)
    generator = SemanticLayerGenerator(
        llm=llm,
        database_url=db_url,
        sample_rows=10
    )

    # Generate semantic layer for car_1
    print('\nGenerating semantic layer for car_1...')
    result = generator.generate(
        database_name='car_1',
        anonymize=True,
        save_prompt=True
    )

    # Save to output file
    output_dir = Path('data/semantic_layers_test')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'car_1.json'

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f'\n✓ Semantic layer saved to: {output_file}')

    # Analyze FK documentation
    print('\n' + '=' * 60)
    print('ANALYZING FK DOCUMENTATION IN SEMANTIC LAYER')
    print('=' * 60)

    semantic_layer = result['semantic_layer']
    tables = semantic_layer.get('tables', [])

    total_fks = 0
    for table in tables:
        table_name = table.get('name', 'unknown')
        relationships = table.get('relationships', [])

        # Count foreign key relationships
        fk_relationships = [r for r in relationships if r.get('type') == 'foreign_key']

        if fk_relationships:
            print(f'\n{table_name}: {len(fk_relationships)} FK(s) documented')
            for fk in fk_relationships:
                col = fk.get('column', '?')
                ref_table = fk.get('references_table', '?')
                ref_col = fk.get('references_column', '?')
                print(f'  • {col} -> {ref_table}.{ref_col}')
                total_fks += 1

    print('\n' + '=' * 60)
    print(f'TOTAL FK RELATIONSHIPS DOCUMENTED: {total_fks}')
    print('Expected: 5 FKs from Spider metadata')

    if total_fks >= 5:
        print('✅ SUCCESS: All expected FKs documented!')
        return True
    else:
        print(f'❌ MISSING FKs: Only {total_fks}/5 documented')
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
