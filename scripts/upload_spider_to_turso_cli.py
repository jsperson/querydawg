#!/usr/bin/env python3
"""
Upload Spider SQLite databases to Turso using CLI (simpler and more reliable)

Uses the Turso CLI's db shell and .dump features to upload data.
"""
import os
import sys
import subprocess
from pathlib import Path
import time

# Load environment
from dotenv import load_dotenv
load_dotenv()


def normalize_db_name(db_name):
    """Convert database name to Turso-compatible format"""
    return db_name.replace("_", "-").lower()


def get_official_spider_databases():
    """Get the official list of 20 Spider databases from dev.json"""
    import json
    dev_json = Path('data/spider/dev.json')

    if not dev_json.exists():
        print("❌ dev.json not found")
        return []

    with open(dev_json) as f:
        data = json.load(f)

    databases = sorted(set(item['db_id'] for item in data))
    return databases


def find_sqlite_file(db_name):
    """Find the SQLite file for a database"""
    spider_dir = Path("data/spider/database")
    db_dir = spider_dir / db_name

    if not db_dir.exists():
        return None

    sqlite_files = list(db_dir.glob("*.sqlite"))
    if sqlite_files:
        return sqlite_files[0]

    return None


def check_database_exists(db_name):
    """Check if database exists using CLI"""
    normalized = normalize_db_name(db_name)

    result = subprocess.run(
        ["turso", "db", "list"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return normalized in result.stdout

    return False


def create_database(db_name):
    """Create database using CLI"""
    normalized = normalize_db_name(db_name)

    result = subprocess.run(
        ["turso", "db", "create", normalized, "--group", "default"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return True
    else:
        print(f"     Error: {result.stderr}")
        return False


def upload_sqlite_file(db_name, sqlite_path):
    """Upload SQLite file using CLI dump and restore"""
    normalized = normalize_db_name(db_name)

    try:
        # Create SQL dump from source SQLite file
        print(f"     Creating SQL dump...")
        dump_result = subprocess.run(
            ["sqlite3", str(sqlite_path), ".dump"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if dump_result.returncode != 0:
            print(f"     ❌ Dump failed: {dump_result.stderr}")
            return False

        # Execute dump via turso db shell
        print(f"     Uploading to Turso...")
        upload_result = subprocess.run(
            ["turso", "db", "shell", normalized],
            input=dump_result.stdout,
            capture_output=True,
            text=True,
            timeout=300
        )

        if upload_result.returncode == 0:
            return True
        else:
            print(f"     ❌ Upload failed: {upload_result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"     ❌ Upload timed out")
        return False
    except Exception as e:
        print(f"     ❌ Upload failed: {e}")
        return False


def main():
    """Main upload process"""
    print("="*70)
    print("Spider → Turso Upload via CLI (20 Official Databases)")
    print("="*70)

    # Check CLI is available
    try:
        result = subprocess.run(["turso", "--version"], capture_output=True)
        if result.returncode != 0:
            print("❌ Turso CLI not found")
            sys.exit(1)
    except FileNotFoundError:
        print("❌ Turso CLI not installed")
        sys.exit(1)

    print("\n✅ Turso CLI available")

    # Get databases
    print("\n" + "="*70)
    print("Loading official Spider databases...")
    print("="*70)

    spider_dbs = get_official_spider_databases()

    if not spider_dbs:
        print("❌ Could not load Spider databases")
        sys.exit(1)

    print(f"\n✅ Found {len(spider_dbs)} official Spider databases")

    # Find SQLite files
    db_info = []
    for db_name in spider_dbs:
        sqlite_file = find_sqlite_file(db_name)
        if sqlite_file:
            db_info.append({
                "name": db_name,
                "path": sqlite_file,
                "size": sqlite_file.stat().st_size
            })
        else:
            print(f"⚠️  SQLite file not found for: {db_name}")

    if not db_info:
        print("❌ No SQLite files found")
        sys.exit(1)

    # Show summary
    total_size = sum(db["size"] for db in db_info)
    print(f"\nDatabases to upload:")
    for i, db in enumerate(db_info, 1):
        print(f"  {i:2d}. {db['name']:40s} ({db['size'] / 1024:8.1f} KB)")

    print(f"\nTotal size: {total_size / (1024 * 1024):.2f} MB")

    # Upload
    print("\n" + "="*70)
    print("Uploading to Turso...")
    print("="*70)

    success_count = 0
    skipped_count = 0
    failed = []

    for i, db in enumerate(db_info, 1):
        db_name = db["name"]

        print(f"\n[{i}/{len(db_info)}] {db_name}")

        # Check if exists
        if check_database_exists(db_name):
            print(f"  ⚠️  Already exists - skipping")
            skipped_count += 1
            continue

        # Create database
        print(f"  🔨 Creating database...")
        if not create_database(db_name):
            print(f"  ❌ Failed to create")
            failed.append(db_name)
            continue

        # Wait for database to be ready
        time.sleep(2)

        # Upload data
        print(f"  📤 Uploading data from {db['path'].name}...")
        if upload_sqlite_file(db_name, db["path"]):
            success_count += 1
            print(f"  ✅ Complete!")
        else:
            failed.append(db_name)

        # Small delay between uploads
        time.sleep(0.5)

    # Summary
    print("\n" + "="*70)
    print("UPLOAD SUMMARY")
    print("="*70)
    print(f"✅ Successfully uploaded: {success_count}/{len(db_info)}")
    print(f"⏭️  Skipped (existing):   {skipped_count}")

    if failed:
        print(f"❌ Failed:              {len(failed)}")
        for name in failed:
            print(f"   - {name}")

    print("\n" + "="*70)
    print("Next Steps:")
    print("1. Test connection: python scripts/test_turso_connection.py")
    print("2. Use GUI: Select 'Turso (SQLite)' when creating benchmark")
    print("3. Expected: 0 gold SQL conversion failures!")
    print("="*70)


if __name__ == "__main__":
    main()
