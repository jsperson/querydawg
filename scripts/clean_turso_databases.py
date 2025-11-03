#!/usr/bin/env python3
"""
Clean all tables from Turso databases to prepare for fresh upload
"""
import os
import sys
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from backend.app.database.turso_client import TursoClient


def normalize_db_name(db_name):
    """Convert database name to Turso-compatible format"""
    return db_name.replace("_", "-").lower()


def create_database_token(db_name, token, org):
    """Create a database-specific token"""
    normalized = normalize_db_name(db_name)
    url = f"https://api.turso.tech/v1/organizations/{org}/databases/{normalized}/auth/tokens"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json={}, timeout=30)
    if response.status_code in [200, 201]:
        return response.json().get("jwt")
    return None


def clean_database(db_name, token, org):
    """Drop all tables from a database"""
    print(f"Cleaning {db_name}...")

    # Get database-specific token
    db_token = create_database_token(db_name, token, org)
    if not db_token:
        print(f"  ❌ Failed to create token")
        return False

    # Temporarily set the token
    original_token = os.getenv("TURSO_TOKEN")
    os.environ["TURSO_TOKEN"] = db_token

    try:
        normalized = normalize_db_name(db_name)
        client = TursoClient(db_name=normalized)

        # Get all tables
        result = client.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in result["rows"]]

        if not tables:
            print(f"  ✅ Already empty (0 tables)")
            return True

        # Drop each table
        for table in tables:
            try:
                client.execute(f'DROP TABLE IF EXISTS "{table}"')
            except Exception as e:
                print(f"  ⚠️  Error dropping table {table}: {str(e)}")

        print(f"  ✅ Dropped {len(tables)} tables")
        return True

    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False
    finally:
        # Restore original token
        if original_token:
            os.environ["TURSO_TOKEN"] = original_token
        elif "TURSO_TOKEN" in os.environ:
            del os.environ["TURSO_TOKEN"]


def get_official_spider_databases():
    """Get the official list of 20 Spider databases"""
    import json
    dev_json = Path('data/spider/dev.json')

    if not dev_json.exists():
        return []

    with open(dev_json) as f:
        data = json.load(f)

    return sorted(set(item['db_id'] for item in data))


def main():
    """Clean all Turso databases"""
    print("="*70)
    print("Clean Turso Databases")
    print("="*70)

    token = os.getenv("TURSO_TOKEN")
    org = os.getenv("TURSO_ORG", "jsperson")

    if not token:
        print("\n❌ TURSO_TOKEN not set")
        sys.exit(1)

    # Get databases
    spider_dbs = get_official_spider_databases()

    if not spider_dbs:
        print("❌ Could not load Spider databases")
        sys.exit(1)

    print(f"\n✅ Found {len(spider_dbs)} databases to clean")

    # Clean each database
    success_count = 0
    for i, db_name in enumerate(spider_dbs, 1):
        print(f"\n[{i}/{len(spider_dbs)}] ", end="")
        if clean_database(db_name, token, org):
            success_count += 1

    print("\n" + "="*70)
    print(f"✅ Cleaned {success_count}/{len(spider_dbs)} databases")
    print("="*70)
    print("\nReady for fresh upload!")


if __name__ == "__main__":
    main()
