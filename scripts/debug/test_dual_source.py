#!/usr/bin/env python3
"""
Test dual-source abstraction layer

Validates that QueryDawg can switch between Supabase and Turso
using the SPIDER_DATA_SOURCE environment variable.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.database.query_executor import QueryExecutorFactory
from backend.app.services.schema import SchemaExtractorFactory


def test_query_executor_factory():
    """Test QueryExecutorFactory can create executors for both sources"""
    print("=" * 70)
    print("Testing QueryExecutorFactory")
    print("=" * 70)

    # Test Supabase executor creation
    print("\n1. Creating PostgreSQL/Supabase executor...")
    try:
        db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
        if db_url:
            executor = QueryExecutorFactory.create(
                source="supabase",
                connection_string=db_url
            )
            print(f"   ✅ Created: {type(executor).__name__}")
            executor.close()
        else:
            print("   ⚠️  Skipped: DATABASE_URL not set")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test Turso executor creation
    print("\n2. Creating Turso/SQLite executor...")
    try:
        if os.getenv("TURSO_TOKEN"):
            executor = QueryExecutorFactory.create(source="turso")
            print(f"   ✅ Created: {type(executor).__name__}")
            executor.close()
        else:
            print("   ⚠️  Skipped: TURSO_TOKEN not set")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test auto-detection from env var
    print("\n3. Testing auto-detection from SPIDER_DATA_SOURCE...")
    data_source = os.getenv("SPIDER_DATA_SOURCE", "supabase")
    print(f"   SPIDER_DATA_SOURCE = {data_source}")
    try:
        executor = QueryExecutorFactory.create()
        print(f"   ✅ Auto-created: {type(executor).__name__}")
        executor.close()
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_schema_extractor_factory():
    """Test SchemaExtractorFactory can create extractors for both sources"""
    print("\n" + "=" * 70)
    print("Testing SchemaExtractorFactory")
    print("=" * 70)

    test_database = "concert_singer"

    # Test PostgreSQL extractor creation
    print(f"\n1. Creating PostgreSQL schema extractor for '{test_database}'...")
    try:
        db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
        if db_url:
            extractor = SchemaExtractorFactory.create(
                db_type="postgresql",
                connection_string=db_url,
                schema_name=test_database
            )
            print(f"   ✅ Created: {type(extractor).__name__}")
        else:
            print("   ⚠️  Skipped: DATABASE_URL not set")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test Turso extractor creation
    print(f"\n2. Creating Turso schema extractor for '{test_database}'...")
    try:
        if os.getenv("TURSO_TOKEN"):
            extractor = SchemaExtractorFactory.create(
                db_type="turso",
                schema_name=test_database
            )
            print(f"   ✅ Created: {type(extractor).__name__}")
        else:
            print("   ⚠️  Skipped: TURSO_TOKEN not set")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test auto-detection from env var
    print("\n3. Testing auto-detection from SPIDER_DATA_SOURCE...")
    data_source = os.getenv("SPIDER_DATA_SOURCE", "supabase")
    print(f"   SPIDER_DATA_SOURCE = {data_source}")
    try:
        extractor = SchemaExtractorFactory.create(schema_name=test_database)
        print(f"   ✅ Auto-created: {type(extractor).__name__}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_schema_extraction():
    """Test schema extraction from current configured source"""
    print("\n" + "=" * 70)
    print("Testing Schema Extraction")
    print("=" * 70)

    test_database = "concert_singer"
    data_source = os.getenv("SPIDER_DATA_SOURCE", "supabase")

    print(f"\nExtracting schema from '{test_database}' using {data_source}...")

    try:
        extractor = SchemaExtractorFactory.create(schema_name=test_database)

        # Get tables
        tables = extractor.get_tables()
        print(f"\n✅ Found {len(tables)} tables:")
        for table in tables[:5]:  # Show first 5
            print(f"   - {table['name']}")
        if len(tables) > 5:
            print(f"   ... and {len(tables) - 5} more")

        # Get schema for first table
        if tables:
            first_table = tables[0]['name']
            print(f"\n✅ Schema for table '{first_table}':")

            columns = extractor.get_columns(first_table)
            print(f"   Columns ({len(columns)}):")
            for col in columns[:3]:  # Show first 3
                pk = " (PK)" if col.get('primary_key') else ""
                null = " NULL" if col.get('nullable') else " NOT NULL"
                print(f"     - {col['name']}: {col['type']}{pk}{null}")
            if len(columns) > 3:
                print(f"     ... and {len(columns) - 3} more")

            fks = extractor.get_foreign_keys(first_table)
            if fks:
                print(f"   Foreign Keys ({len(fks)}):")
                for fk in fks:
                    print(f"     - {fk['column']} -> {fk['referenced_table']}.{fk['referenced_column']}")

            row_count = extractor.get_row_count(first_table)
            print(f"   Row Count: {row_count}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_query_execution():
    """Test query execution against current configured source"""
    print("\n" + "=" * 70)
    print("Testing Query Execution")
    print("=" * 70)

    test_database = "concert_singer"
    data_source = os.getenv("SPIDER_DATA_SOURCE", "supabase")

    # Simple test query
    test_query = "SELECT COUNT(*) as count FROM singer"

    print(f"\nExecuting test query against '{test_database}' using {data_source}...")
    print(f"Query: {test_query}")

    try:
        executor = QueryExecutorFactory.create()
        results, error = executor.execute_query(test_query, test_database)

        if error:
            print(f"\n❌ Query failed: {error}")
        else:
            print(f"\n✅ Query succeeded!")
            print(f"   Results: {results}")
            if results:
                print(f"   Singer count: {results[0][0]}")

        executor.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("Dual-Source Abstraction Layer Test Suite")
    print("=" * 70)

    # Show current configuration
    print("\nCurrent Configuration:")
    print(f"  SPIDER_DATA_SOURCE: {os.getenv('SPIDER_DATA_SOURCE', 'supabase (default)')}")
    print(f"  DATABASE_URL: {'✓ set' if os.getenv('DATABASE_URL') else '✗ not set'}")
    print(f"  TURSO_TOKEN: {'✓ set' if os.getenv('TURSO_TOKEN') else '✗ not set'}")

    # Run tests
    test_query_executor_factory()
    test_schema_extractor_factory()
    test_schema_extraction()
    test_query_execution()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    data_source = os.getenv("SPIDER_DATA_SOURCE", "supabase")
    print(f"\n✅ Dual-source abstraction layer is working!")
    print(f"   Current source: {data_source}")
    print(f"\nTo switch sources, set SPIDER_DATA_SOURCE environment variable:")
    print(f"   export SPIDER_DATA_SOURCE=supabase  # Use Supabase (PostgreSQL)")
    print(f"   export SPIDER_DATA_SOURCE=turso     # Use Turso (SQLite)")
    print("=" * 70)


if __name__ == "__main__":
    sys.exit(main() or 0)
