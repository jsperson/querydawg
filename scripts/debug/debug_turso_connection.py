#!/usr/bin/env python3
"""
Debug Turso connection and table listing
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database.turso_client import TursoClient
from dotenv import load_dotenv

# Load environment
load_dotenv()

def main():
    print("Testing direct TursoClient connection...\n")

    try:
        # Test with original name
        print("1. Testing with 'concert_singer' (underscores)...")
        client1 = TursoClient(db_name="concert_singer")
        print(f"   Normalized name: {client1.db_name}")
        print(f"   Database URL: {client1.db_url}")

        # Test connection
        try:
            result = client1.execute("SELECT 1")
            print(f"   ✓ Connection test passed: {result}")
        except Exception as e:
            print(f"   ✗ Connection test failed: {e}")

        # Try to list tables
        try:
            result = client1.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            print(f"   Tables query result: {result}")
            if result and 'rows' in result:
                table_names = [row[0] for row in result['rows']]
                print(f"   Found {len(table_names)} tables: {table_names}")
            else:
                print(f"   No tables found or invalid result structure")
        except Exception as e:
            print(f"   ✗ Tables query failed: {e}")

        # Test with dashed name
        print("\n2. Testing with 'concert-singer' (dashes)...")
        client2 = TursoClient(db_name="concert-singer")
        print(f"   Normalized name: {client2.db_name}")
        print(f"   Database URL: {client2.db_url}")

        try:
            result = client2.execute("SELECT 1")
            print(f"   ✓ Connection test passed: {result}")
        except Exception as e:
            print(f"   ✗ Connection test failed: {e}")

        try:
            result = client2.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            print(f"   Tables query result: {result}")
            if result and 'rows' in result:
                table_names = [row[0] for row in result['rows']]
                print(f"   Found {len(table_names)} tables: {table_names}")
            else:
                print(f"   No tables found or invalid result structure")
        except Exception as e:
            print(f"   ✗ Tables query failed: {e}")

        # Try a direct table query
        print("\n3. Testing direct table query (SELECT * FROM singer LIMIT 1)...")
        try:
            result = client1.execute("SELECT * FROM singer LIMIT 1")
            print(f"   Result: {result}")
            if result and 'rows' in result and result['rows']:
                print(f"   ✓ Table 'singer' exists and has data")
                print(f"   Columns: {result.get('columns', [])}")
                print(f"   First row: {result['rows'][0]}")
            else:
                print(f"   Table might be empty")
        except Exception as e:
            print(f"   ✗ Query failed: {e}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
