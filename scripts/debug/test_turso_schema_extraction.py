#!/usr/bin/env python3
"""
Test Turso schema extraction
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.schema.turso import TursoSchemaExtractor
from dotenv import load_dotenv

# Load environment
load_dotenv()

def main():
    print("Testing Turso schema extraction for concert_singer...")

    try:
        extractor = TursoSchemaExtractor(db_name="concert_singer")

        # Test individual methods
        print("\n1. Testing get_tables()...")
        tables = extractor.get_tables()
        print(f"   Found {len(tables)} tables: {[t['name'] for t in tables]}")

        if tables:
            first_table = tables[0]['name']
            print(f"\n2. Testing get_columns('{first_table}')...")
            columns = extractor.get_columns(first_table)
            print(f"   Found {len(columns)} columns:")
            for col in columns:
                print(f"     - {col['name']}: {col['type']} (PK: {col.get('primary_key', False)})")

            print(f"\n3. Testing get_foreign_keys('{first_table}')...")
            fks = extractor.get_foreign_keys(first_table)
            print(f"   Found {len(fks)} foreign keys:")
            for fk in fks:
                print(f"     - {fk['column']} -> {fk['referenced_table']}.{fk['referenced_column']}")

            print(f"\n4. Testing get_row_count('{first_table}')...")
            row_count = extractor.get_row_count(first_table)
            print(f"   Row count: {row_count}")

        print("\n5. Testing extract_full_schema()...")
        schema = extractor.extract_full_schema()
        print(f"   Database: {schema.get('database')}")
        print(f"   Tables: {len(schema.get('tables', []))}")

        if schema.get('tables'):
            first = schema['tables'][0]
            print(f"\n   First table: {first['name']}")
            print(f"     Columns: {len(first.get('columns', []))}")
            print(f"     Foreign keys: {len(first.get('foreign_keys', []))}")
            print(f"     Row count: {first.get('row_count', 0)}")

        print("\n✅ Schema extraction working!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
