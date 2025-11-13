#!/usr/bin/env python3
"""
Apply a SQL migration file to the database
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import psycopg2

def apply_migration(migration_file: str):
    """Apply a SQL migration file"""
    # Read migration file
    with open(migration_file, 'r') as f:
        sql = f.read()

    # Connect to database
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

    conn = psycopg2.connect(database_url)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        with conn.cursor() as cur:
            print(f"Applying migration: {migration_file}")
            cur.execute(sql)
            print("✓ Migration applied successfully")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python apply_migration.py <migration_file.sql>")
        sys.exit(1)

    migration_file = sys.argv[1]
    if not Path(migration_file).exists():
        print(f"Error: Migration file not found: {migration_file}")
        sys.exit(1)

    apply_migration(migration_file)
