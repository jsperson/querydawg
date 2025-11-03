#!/usr/bin/env python3
"""
Upload Spider SQLite databases to Turso using HTTP API

Uses TURSO_TOKEN and TURSO_ORG from environment.
Works in headless environments without CLI authentication.
"""

import os
import sys
import requests
from pathlib import Path
import time

# Load environment
from dotenv import load_dotenv
load_dotenv()


def find_spider_databases():
    """Find all Spider SQLite databases (one per directory)"""
    spider_dir = Path("data/spider/database")

    if not spider_dir.exists():
        print(f"❌ Spider directory not found: {spider_dir}")
        return []

    databases = []

    for db_dir in spider_dir.iterdir():
        if not db_dir.is_dir():
            continue

        # Look for .sqlite file
        sqlite_files = list(db_dir.glob("*.sqlite"))

        if sqlite_files:
            databases.append({
                "name": db_dir.name,
                "path": sqlite_files[0],
                "size": sqlite_files[0].stat().st_size
            })

    return databases


def check_database_exists(db_name, token, org):
    """Check if database already exists in Turso"""
    url = f"https://api.turso.tech/v1/organizations/{org}/databases"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        databases = data.get("databases", [])
        return any(db["Name"] == db_name for db in databases)

    return False


def create_database(db_name, token, org, location="iad"):
    """Create a new Turso database"""
    url = f"https://api.turso.tech/v1/organizations/{org}/databases"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": db_name,
        "group": "default",
        "seed": {
            "type": "database",
            "name": db_name,
            "timestamp": "latest"
        }
    }

    # First, create an empty database
    simple_payload = {
        "name": db_name,
        "group": "default"
    }

    response = requests.post(url, headers=headers, json=simple_payload)

    if response.status_code in [200, 201]:
        print(f"  ✅ Database '{db_name}' created")
        return True
    else:
        print(f"  ❌ Failed to create '{db_name}': {response.status_code}")
        print(f"     {response.text}")
        return False


def upload_sqlite_file(db_name, sqlite_path, token, org):
    """Upload SQLite file content to Turso database using SQL dump"""
    import sqlite3

    print(f"  📤 Uploading data from {sqlite_path.name}...")

    try:
        # Read SQLite file and extract data
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]

        print(f"     Found {len(tables)} tables to upload")

        # For each table, get schema and data
        from backend.app.database.turso_client import TursoClient
        turso_client = TursoClient(db_name=db_name)

        for table in tables:
            # Get table schema
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
            create_sql = cursor.fetchone()[0]

            # Create table in Turso
            result, error = turso_client.execute(create_sql)
            if error:
                print(f"     ⚠️  Warning creating table {table}: {error}")

            # Get all data
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()

            if rows:
                # Get column info
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]

                # Insert data in batches
                batch_size = 100
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i+batch_size]

                    # Build INSERT statements
                    placeholders = ','.join(['?' for _ in columns])
                    insert_sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"

                    # Execute batch
                    for row in batch:
                        result, error = turso_client.execute(insert_sql, list(row))
                        if error:
                            print(f"     ⚠️  Warning inserting into {table}: {error}")
                            break

                print(f"     ✅ Uploaded {len(rows)} rows to {table}")

        conn.close()
        return True

    except Exception as e:
        print(f"     ❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main upload process"""
    print("="*70)
    print("Turso Upload Script - Spider Benchmark Databases (HTTP API)")
    print("="*70)

    # Get credentials from environment
    token = os.getenv("TURSO_TOKEN")
    org = os.getenv("TURSO_ORG", "querydawg")

    if not token:
        print("\n❌ TURSO_TOKEN not set in environment")
        print("   Add to .env file:")
        print("   TURSO_TOKEN=your_token_here")
        sys.exit(1)

    print(f"\n✅ Using organization: {org}")
    print(f"✅ Token configured")

    # Find databases
    print("\n" + "="*70)
    print("Finding Spider databases...")
    print("="*70)

    databases = find_spider_databases()

    if not databases:
        print("❌ No SQLite databases found in data/spider/database/")
        sys.exit(1)

    print(f"\n✅ Found {len(databases)} databases")

    # Show summary
    total_size = sum(db["size"] for db in databases)
    print(f"Total size: {total_size / (1024 * 1024):.2f} MB")
    print("\nDatabases to upload:")
    for i, db in enumerate(databases, 1):
        print(f"  {i:2d}. {db['name']:40s} ({db['size'] / 1024:8.1f} KB)")

    # Confirm
    print("\n" + "="*70)
    response = input(f"Upload {len(databases)} databases to Turso? (y/n): ")

    if response.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)

    # Upload each database
    print("\n" + "="*70)
    print("Uploading databases...")
    print("="*70)

    success_count = 0
    failed = []
    skipped = []

    for i, db_info in enumerate(databases, 1):
        db_name = db_info["name"]

        print(f"\n[{i}/{len(databases)}] Processing: {db_name}")

        # Check if exists
        if check_database_exists(db_name, token, org):
            print(f"  ⚠️  Database '{db_name}' already exists - skipping")
            skipped.append(db_name)
            continue

        # Create database
        if create_database(db_name, token, org):
            # Upload data
            if upload_sqlite_file(db_name, db_info["path"], token, org):
                success_count += 1
                print(f"  ✅ Complete: {db_name}")
            else:
                failed.append(db_name)
        else:
            failed.append(db_name)

        # Small delay between uploads
        time.sleep(0.5)

    # Summary
    print("\n" + "="*70)
    print("UPLOAD SUMMARY")
    print("="*70)
    print(f"Successful: {success_count}/{len(databases)}")
    print(f"Skipped (already exist): {len(skipped)}")

    if failed:
        print(f"Failed: {len(failed)}")
        print("\nFailed databases:")
        for name in failed:
            print(f"  - {name}")

    print("\n" + "="*70)
    print("Next steps:")
    print("1. Run: python scripts/test_turso_connection.py")
    print("2. Select 'Turso (SQLite)' in the benchmark GUI")
    print("3. Run benchmarks with native SQLite (0 conversion errors!)")
    print("="*70)


if __name__ == "__main__":
    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))
    main()
