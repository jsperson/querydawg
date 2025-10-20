#!/usr/bin/env python3
"""
Verify the Spider dataset installation.

This script checks:
- All required files exist
- Database count is correct
- JSON files are valid
- Sample database can be opened

Usage:
    python scripts/verify_spider.py
"""

import json
import sqlite3
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
spider_dir = project_root / "data" / "spider"

print("=" * 70)
print("Spider Dataset Verification")
print("=" * 70)
print()

all_checks_passed = True

# Check 1: Directory exists
print("[ 1/5 ] Checking directory structure...")
if not spider_dir.exists():
    print(f"❌ Spider directory not found: {spider_dir}")
    print()
    print("Please run: python scripts/download_spider.py")
    sys.exit(1)
print(f"✅ Spider directory exists: {spider_dir}")
print()

# Check 2: Required files
print("[ 2/5 ] Checking required files...")
required_files = {
    "README.txt": 5000,          # ~5KB
    "dev.json": 3000000,         # ~3MB
    "train_spider.json": 20000000,  # ~24MB
    "train_others.json": 7000000,   # ~7.6MB
    "tables.json": 900000,       # ~980KB
    "dev_gold.sql": 100000,      # ~124KB
    "train_gold.sql": 1000000,   # ~1.2MB
}

for filename, min_size in required_files.items():
    filepath = spider_dir / filename
    if not filepath.exists():
        print(f"❌ Missing: {filename}")
        all_checks_passed = False
    elif filepath.stat().st_size < min_size:
        print(f"⚠️  {filename} is smaller than expected")
        all_checks_passed = False
    else:
        size_mb = filepath.stat().st_size / (1024 * 1024)
        print(f"✅ {filename:<25} ({size_mb:.1f} MB)")

print()

# Check 3: Database directory
print("[ 3/5 ] Checking databases...")
database_dir = spider_dir / "database"

if not database_dir.exists():
    print(f"❌ Database directory not found: {database_dir}")
    all_checks_passed = False
else:
    databases = [d for d in database_dir.iterdir() if d.is_dir()]
    db_count = len(databases)

    print(f"✅ Found {db_count} databases")

    if db_count != 166:
        print(f"⚠️  Expected 166 databases, found {db_count}")
        all_checks_passed = False

    # Check a few sample databases
    sample_dbs = ["academic", "car_1", "concert_singer", "world_1"]
    for db_name in sample_dbs:
        db_dir = database_dir / db_name
        db_file = db_dir / f"{db_name}.sqlite"

        if db_dir.exists() and db_file.exists():
            print(f"   ✅ {db_name}")
        else:
            print(f"   ❌ {db_name} - missing or incomplete")
            all_checks_passed = False

print()

# Check 4: JSON validation
print("[ 4/5 ] Validating JSON files...")

json_files = ["dev.json", "train_spider.json", "train_others.json", "tables.json"]
for filename in json_files:
    filepath = spider_dir / filename
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        if filename == "dev.json":
            expected_count = 1034
            actual_count = len(data)
            if actual_count == expected_count:
                print(f"✅ {filename:<25} ({actual_count} examples)")
            else:
                print(f"⚠️  {filename:<25} ({actual_count} examples, expected {expected_count})")
                all_checks_passed = False

        elif filename == "train_spider.json":
            expected_count = 7000
            actual_count = len(data)
            if actual_count == expected_count:
                print(f"✅ {filename:<25} ({actual_count} examples)")
            else:
                print(f"⚠️  {filename:<25} ({actual_count} examples, expected {expected_count})")
                all_checks_passed = False

        elif filename == "train_others.json":
            expected_count = 1659
            actual_count = len(data)
            if actual_count == expected_count:
                print(f"✅ {filename:<25} ({actual_count} examples)")
            else:
                print(f"⚠️  {filename:<25} ({actual_count} examples, expected {expected_count})")
                all_checks_passed = False

        elif filename == "tables.json":
            expected_count = 166
            actual_count = len(data)
            if actual_count == expected_count:
                print(f"✅ {filename:<25} ({actual_count} databases)")
            else:
                print(f"⚠️  {filename:<25} ({actual_count} databases, expected {expected_count})")
                all_checks_passed = False

    except json.JSONDecodeError as e:
        print(f"❌ {filename:<25} Invalid JSON: {e}")
        all_checks_passed = False
    except Exception as e:
        print(f"❌ {filename:<25} Error: {e}")
        all_checks_passed = False

print()

# Check 5: Test database connection
print("[ 5/5 ] Testing database connectivity...")

test_db = database_dir / "academic" / "academic.sqlite"
if test_db.exists():
    try:
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Get table list
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        cursor.close()
        conn.close()

        print(f"✅ Successfully opened academic.sqlite")
        print(f"   Found {len(tables)} tables: {', '.join([t[0] for t in tables[:5]])}")

    except Exception as e:
        print(f"❌ Failed to open academic.sqlite: {e}")
        all_checks_passed = False
else:
    print(f"❌ Test database not found: {test_db}")
    all_checks_passed = False

print()
print("=" * 70)

if all_checks_passed:
    print("✅ All checks passed! Spider dataset is properly installed.")
    print("=" * 70)
    print()
    print("Dataset summary:")
    print("  • 166 databases")
    print("  • 8,659 training examples")
    print("  • 1,034 dev/test examples")
    print()
    sys.exit(0)
else:
    print("⚠️  Some checks failed. Please review the errors above.")
    print("=" * 70)
    print()
    print("Try re-downloading the dataset:")
    print("  python scripts/download_spider.py")
    print()
    sys.exit(1)
