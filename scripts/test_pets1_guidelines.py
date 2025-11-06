#!/usr/bin/env python3
"""
Test new query guidelines on pets_1 database.
"""

import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from app.config import get_settings
from app.services.semantic_layer_generator import SemanticLayerGenerator
from app.services.llm.openai_provider import OpenAIProvider

def main():
    # Initialize
    settings = get_settings()
    llm = OpenAIProvider(
        api_key=settings.openai_api_key,
        model=settings.llm_model
    )
    generator = SemanticLayerGenerator(
        llm=llm,
        database_url=os.getenv('DATABASE_URL'),
        sample_rows=10
    )

    # Generate for pets_1
    print('Generating semantic layer for pets_1 with NEW guidelines...')
    result = generator.generate('pets_1')

    # Extract and print query_guidelines
    guidelines = result['semantic_layer'].get('query_guidelines', [])
    print('\n' + '='*80)
    print('QUERY GUIDELINES FOR pets_1:')
    print('='*80)
    for i, guideline in enumerate(guidelines, 1):
        print(f'{i}. {guideline}')
    print('='*80)

    # Also show table count
    tables = result['semantic_layer'].get('tables', [])
    print(f'\nTable count: {len(tables)}')
    print(f'Tables: {[t["name"] for t in tables]}')

if __name__ == '__main__':
    main()
