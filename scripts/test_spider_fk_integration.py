#!/usr/bin/env python3
"""
Test script to verify Spider FK integration
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import get_settings
from app.database.supabase_schema_extractor import SupabaseSchemaExtractor

def main():
    print('Testing Schema Extractor with Spider FKs...')
    print('=' * 60)

    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print('ERROR: DATABASE_URL not set in environment')
        return False

    # Create extractor WITH Spider metadata
    extractor = SupabaseSchemaExtractor(db_url, use_spider_metadata=True)

    # Extract car_1 schema
    print('\nExtracting car_1 schema...')
    schema = extractor.extract_schema('car_1')

    # Check specific tables that should have new FKs
    print('\nChecking cars_data table (should have FK to car_names):')
    cars_data = [t for t in schema['tables'] if t['name'] == 'cars_data'][0]
    print(f'  Foreign Keys: {len(cars_data["foreign_keys"])}')
    for fk in cars_data['foreign_keys']:
        source = fk.get('source', 'unknown')
        print(f'    • {fk["column"]} -> {fk["referenced_table"]}.{fk["referenced_column"]} (source: {source})')

    print('\nChecking car_names table (should have FK to model_list):')
    car_names = [t for t in schema['tables'] if t['name'] == 'car_names'][0]
    print(f'  Foreign Keys: {len(car_names["foreign_keys"])}')
    for fk in car_names['foreign_keys']:
        source = fk.get('source', 'unknown')
        print(f'    • {fk["column"]} -> {fk["referenced_table"]}.{fk["referenced_column"]} (source: {source})')

    print('\n' + '=' * 60)
    if len(cars_data['foreign_keys']) > 0:
        print('✅ Schema Extractor enrichment working!')
        print(f'\nTotal FKs added from Spider metadata: {sum(1 for fk in cars_data["foreign_keys"] if fk.get("source") == "spider_metadata")}')
        return True
    else:
        print('❌ No FKs added - check Spider loader integration')
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
