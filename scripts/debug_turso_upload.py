#!/usr/bin/env python3
"""
Debug script to investigate Turso upload failures

Tests uploading a single database with detailed logging
"""
import os
import sys
import sqlite3
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from backend.app.database.turso_client import TursoClient


def normalize_db_name(db_name):
    """Convert database name to Turso-compatible format"""
    return db_name.replace("_", "-").lower()


def create_database_token(db_name, token, org):
    """Create an access token for a specific database"""
    import requests

    normalized_name = normalize_db_name(db_name)
    url = f"https://api.turso.tech/v1/organizations/{org}/databases/{normalized_name}/auth/tokens"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json={}, timeout=30)

        if response.status_code in [200, 201]:
            data = response.json()
            return data.get("jwt")
        else:
            print(f"Token creation error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Exception creating token: {e}")
        return None


def debug_upload(db_name):
    """Upload a single database with detailed logging"""
    print(f"="*70)
    print(f"DEBUG: Uploading {db_name}")
    print(f"="*70)

    # Get config
    token = os.getenv("TURSO_TOKEN")
    org = os.getenv("TURSO_ORG", "jsperson")

    if not token:
        print("❌ TURSO_TOKEN not set")
        return

    # Find SQLite file
    spider_dir = Path("data/spider/database")
    db_dir = spider_dir / db_name
    sqlite_files = list(db_dir.glob("*.sqlite"))

    if not sqlite_files:
        print(f"❌ SQLite file not found for {db_name}")
        return

    sqlite_path = sqlite_files[0]
    print(f"\n✅ Found SQLite file: {sqlite_path}")

    # Connect to SQLite
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()

    # Get first table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' LIMIT 1")
    result = cursor.fetchone()

    if not result:
        print(f"❌ No tables found")
        return

    table_name = result[0]
    print(f"\n✅ Testing with table: {table_name}")

    # Get CREATE TABLE statement
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    create_sql = cursor.fetchone()[0]

    print(f"\n📝 CREATE TABLE SQL:")
    print("="*70)
    print(create_sql)
    print("="*70)

    # Create database token
    print(f"\n🔑 Creating database token...")
    db_token = create_database_token(db_name, token, org)

    if not db_token:
        print("❌ Failed to create token")
        return

    print("✅ Token created")

    # Set token in environment
    original_token = os.getenv("TURSO_TOKEN")
    os.environ["TURSO_TOKEN"] = db_token

    # Create Turso client
    normalized_name = normalize_db_name(db_name)
    print(f"\n🔌 Connecting to Turso database: {normalized_name}")

    try:
        turso_client = TursoClient(db_name=normalized_name)
        print(f"✅ Connected to: {turso_client.db_url}")

        # Try to execute CREATE TABLE
        print(f"\n📤 Executing CREATE TABLE...")
        result = turso_client.execute(create_sql)

        print(f"\n✅ Table created successfully!")
        print(f"Result: {result}")

    except Exception as e:
        print(f"\n❌ EXCEPTION:")
        print("="*70)
        print(str(e))
        print("="*70)
        import traceback
        traceback.print_exc()

    finally:
        # Restore original token
        if original_token:
            os.environ["TURSO_TOKEN"] = original_token
        elif "TURSO_TOKEN" in os.environ:
            del os.environ["TURSO_TOKEN"]

        conn.close()


if __name__ == "__main__":
    # Test with one of the failing databases
    db_name = "poker_player"

    if len(sys.argv) > 1:
        db_name = sys.argv[1]

    debug_upload(db_name)
