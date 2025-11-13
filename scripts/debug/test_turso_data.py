#!/usr/bin/env python3
"""
Test that Turso databases actually have data
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from backend.app.database.turso_client import TursoClient


def create_database_token(db_name):
    """Create a database-specific token"""
    import requests

    token = os.getenv("TURSO_TOKEN")
    org = os.getenv("TURSO_ORG", "jsperson")
    normalized = db_name.replace("_", "-").lower()

    url = f"https://api.turso.tech/v1/organizations/{org}/databases/{normalized}/auth/tokens"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json={}, timeout=30)
    if response.status_code in [200, 201]:
        return response.json().get("jwt")
    return None


def test_database(db_name):
    """Test querying a database"""
    print(f"Testing {db_name}...")

    # Get database-specific token
    db_token = create_database_token(db_name)
    if not db_token:
        print(f"  ❌ Failed to create token")
        return False

    # Temporarily set the token
    original_token = os.getenv("TURSO_TOKEN")
    os.environ["TURSO_TOKEN"] = db_token

    try:
        client = TursoClient(db_name=db_name)

        # List tables
        result = client.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in result["rows"]]

        print(f"  ✅ Connected")
        print(f"  📋 Tables: {len(tables)}")

        if tables:
            # Test first table
            table_name = tables[0]
            count_result = client.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            row_count = count_result["rows"][0][0] if count_result["rows"] else 0

            print(f"  📊 Table '{table_name}': {row_count} rows")

            return row_count > 0
        else:
            print(f"  ⚠️  No tables found!")
            return False

    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False
    finally:
        # Restore original token
        if original_token:
            os.environ["TURSO_TOKEN"] = original_token
        elif "TURSO_TOKEN" in os.environ:
            del os.environ["TURSO_TOKEN"]


if __name__ == "__main__":
    # Test a few databases
    test_dbs = [
        "poker_player",
        "concert_singer",
        "battle_death"
    ]

    print("="*70)
    print("Testing Turso Databases")
    print("="*70)

    success_count = 0
    for db in test_dbs:
        if test_database(db):
            success_count += 1
        print()

    print("="*70)
    print(f"✅ {success_count}/{len(test_dbs)} databases have data")
    print("="*70)
