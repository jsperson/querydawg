#!/usr/bin/env python3
"""
Test Turso connection and verify setup

This script validates:
1. Turso environment variables are configured
2. Can connect to Turso databases
3. Can query databases
4. Schema extraction works
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.database.turso_client import TursoClient
from backend.app.database.turso_schema_extractor import TursoSchemaExtractor


def test_environment():
    """Test environment variables are set"""
    print("="*60)
    print("Testing Environment Configuration")
    print("="*60)

    errors = []

    # Check for Turso token
    token = os.getenv("TURSO_TOKEN")
    if not token:
        errors.append("❌ TURSO_TOKEN not set")
    else:
        print(f"✅ TURSO_TOKEN: {token[:20]}...")

    # Check for org (optional)
    org = os.getenv("TURSO_ORG", "querydawg")
    print(f"✅ TURSO_ORG: {org}")

    # Check for base URL (optional)
    base_url = os.getenv("TURSO_BASE_URL", f"{org}.turso.io")
    print(f"✅ TURSO_BASE_URL: {base_url}")

    if errors:
        print("\nConfiguration errors:")
        for error in errors:
            print(f"  {error}")
        print("\nSet missing environment variables in .env file")
        return False

    return True


def test_connection(db_name="concert_singer"):
    """Test connection to a specific database"""
    print(f"\n{'='*60}")
    print(f"Testing Connection to {db_name}")
    print(f"{'='*60}")

    try:
        client = TursoClient(db_name)
        print(f"✅ TursoClient initialized for {db_name}")

        # Test connection
        print("Testing connection...")
        if client.test_connection():
            print("✅ Connection successful")
        else:
            print("❌ Connection failed")
            return False

        # Get table names
        print("\nFetching table names...")
        tables = client.get_table_names()
        print(f"✅ Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

        # Test query
        if tables:
            print(f"\nTesting query on {tables[0]}...")
            count = client.get_row_count(tables[0])
            print(f"✅ Query successful: {count} rows in {tables[0]}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schema_extraction(db_name="concert_singer"):
    """Test schema extraction"""
    print(f"\n{'='*60}")
    print(f"Testing Schema Extraction for {db_name}")
    print(f"{'='*60}")

    try:
        extractor = TursoSchemaExtractor(db_name)
        print(f"✅ TursoSchemaExtractor initialized")

        # Extract schema
        print("Extracting schema...")
        schema = extractor.extract_schema()

        print(f"✅ Schema extracted successfully")
        print(f"\nDatabase: {schema['database']}")
        print(f"Tables: {len(schema['tables'])}")

        for table in schema['tables']:
            print(f"\n  Table: {table['name']}")
            print(f"    Rows: {table['row_count']}")
            print(f"    Columns: {len(table['columns'])}")
            print(f"    Foreign Keys: {len(table['foreign_keys'])}")

            # Show columns
            for col in table['columns'][:3]:  # First 3 columns
                pk = " (PK)" if col['primary_key'] else ""
                null = " NULL" if col['nullable'] else " NOT NULL"
                print(f"      - {col['name']}: {col['type']}{pk}{null}")

            if len(table['columns']) > 3:
                print(f"      ... and {len(table['columns']) - 3} more columns")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_sampling(db_name="concert_singer"):
    """Test data sampling"""
    print(f"\n{'='*60}")
    print(f"Testing Data Sampling for {db_name}")
    print(f"{'='*60}")

    try:
        extractor = TursoSchemaExtractor(db_name)

        # Sample all tables
        print("Sampling data from all tables...")
        samples = extractor.sample_all_tables(limit=3)

        print(f"✅ Sampled data from {len(samples)} tables")

        for table_name, rows in samples.items():
            print(f"\n  {table_name}: {len(rows)} sample rows")
            if rows:
                # Show first row
                print(f"    Sample: {list(rows[0].keys())}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Turso Connection Test Suite")
    print("="*60)

    results = {}

    # Test 1: Environment
    results["Environment"] = test_environment()

    if not results["Environment"]:
        print("\n❌ Environment not configured. Fix errors and try again.")
        sys.exit(1)

    # Test 2: Connection
    results["Connection"] = test_connection()

    # Test 3: Schema Extraction
    results["Schema Extraction"] = test_schema_extraction()

    # Test 4: Data Sampling
    results["Data Sampling"] = test_data_sampling()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())

    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nTurso is configured correctly!")
        print("\nNext steps:")
        print("1. Run: python scripts/upload_to_turso.py (if not done)")
        print("2. Regenerate semantic layers from Turso")
        print("3. Run benchmark against Turso")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nCheck the errors above and fix configuration.")
    print("="*60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
