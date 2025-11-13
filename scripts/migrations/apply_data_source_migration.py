#!/usr/bin/env python3
"""
Apply migration 008: Add data_source column to benchmark_runs
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import psycopg2
from dotenv import load_dotenv

# Load environment
load_dotenv()

def main():
    # Get Supabase connection
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        return

    print("Applying migration 008: Add data_source column...")

    # Read migration file
    migration_file = Path(__file__).parent.parent / "data/spider/migrations/008_add_data_source.sql"
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    # Apply migration
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        print("\nExecuting SQL...")
        cur.execute(migration_sql)
        conn.commit()

        print("✓ Migration applied successfully!")

        # Verify
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'benchmark_runs'
            AND column_name = 'data_source'
        """)

        result = cur.fetchone()
        if result:
            print(f"\n✓ Verified column exists:")
            print(f"  Name: {result[0]}")
            print(f"  Type: {result[1]}")
            print(f"  Nullable: {result[2]}")
            print(f"  Default: {result[3]}")
        else:
            print("\n⚠ Column not found after migration!")

        cur.close()

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
