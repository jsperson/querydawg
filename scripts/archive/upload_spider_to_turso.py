#!/usr/bin/env python3
"""
Upload the 20 official Spider databases to Turso

Non-interactive version that uploads only the databases used in Spider benchmark.
"""

import os
import sys
import json
import requests
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
from dotenv import load_dotenv
load_dotenv()


def get_official_spider_databases():
    """Get the official list of 20 Spider databases from dev.json"""
    dev_json = Path('data/spider/dev.json')

    if not dev_json.exists():
        print("❌ dev.json not found")
        return []

    with open(dev_json) as f:
        data = json.load(f)

    # Get unique database IDs
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


def normalize_db_name(db_name):
    """Convert database name to Turso-compatible format (lowercase, dashes only)"""
    return db_name.replace("_", "-").lower()


def ensure_group_exists(token, org, group_name="default"):
    """Create group if it doesn't exist"""
    url = f"https://api.turso.tech/v1/organizations/{org}/groups"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Check if group exists
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        groups = response.json().get("groups", [])
        if any(g.get("name") == group_name for g in groups):
            return True

    # Create group (use primary region)
    payload = {
        "name": group_name,
        "location": "aws-us-east-1"  # AWS US East (Virginia)
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code in [200, 201]:
        print(f"  ✅ Created group '{group_name}'")
        return True
    else:
        print(f"  ⚠️  Warning creating group: {response.status_code} - {response.text}")
        return False


def check_database_exists(db_name, token, org):
    """Check if database already exists in Turso"""
    url = f"https://api.turso.tech/v1/organizations/{org}/databases"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            databases = data.get("databases", [])
            # Check for normalized name
            normalized = normalize_db_name(db_name)
            return any(db["Name"] == normalized for db in databases)
    except Exception as e:
        print(f"  ⚠️  Error checking database: {e}")

    return False


def create_database(db_name, token, org):
    """Create a new Turso database (name will be normalized to use dashes)"""
    url = f"https://api.turso.tech/v1/organizations/{org}/databases"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Normalize database name (underscores -> dashes)
    normalized_name = normalize_db_name(db_name)

    payload = {
        "name": normalized_name,
        "group": "default"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code in [200, 201]:
            return True
        else:
            print(f"     Error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"     Exception: {e}")
        return False


def create_database_token(db_name, token, org):
    """Create an access token for a specific database"""
    normalized_name = normalize_db_name(db_name)
    url = f"https://api.turso.tech/v1/organizations/{org}/databases/{normalized_name}/auth/tokens"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Create a full-access token (no permissions restrictions)
    try:
        response = requests.post(url, headers=headers, json={}, timeout=30)

        if response.status_code in [200, 201]:
            data = response.json()
            return data.get("jwt")
        else:
            print(f"     ⚠️  Token creation error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"     ⚠️  Exception creating token: {e}")
        return None


def upload_sqlite_data(db_name, sqlite_path, token, org, db_token=None):
    """Upload SQLite file content to Turso database (using normalized name)"""
    import sqlite3

    # Create database-specific token if not provided
    if not db_token:
        print(f"  🔑 Creating database token...")
        db_token = create_database_token(db_name, token, org)
        if not db_token:
            print(f"     ❌ Failed to create database token")
            return False

    try:
        # Connect to source SQLite file
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            print(f"     ⚠️  No tables found in {sqlite_path.name}")
            conn.close()
            return False

        # Set database token in environment temporarily for TursoClient
        import os as temp_os
        original_token = temp_os.getenv("TURSO_TOKEN")
        temp_os.environ["TURSO_TOKEN"] = db_token

        # Create Turso client with normalized database name
        from backend.app.database.turso_client import TursoClient
        normalized_name = normalize_db_name(db_name)
        turso_client = TursoClient(db_name=normalized_name)

        # Upload each table
        for table in tables:
            # Get CREATE TABLE statement
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
            create_sql = cursor.fetchone()[0]

            # Create table in Turso (handle "already exists" gracefully)
            try:
                result = turso_client.execute(create_sql)
            except RuntimeError as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower():
                    pass  # Table already exists, continue
                else:
                    print(f"     ⚠️  Warning creating table {table}: {error_msg}")

            # Get all data
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()

            if rows:
                # Get column names
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]

                # Insert data in batches
                batch_size = 50
                total_inserted = 0

                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i+batch_size]

                    for row in batch:
                        # Build INSERT with placeholders
                        placeholders = ','.join(['?' for _ in columns])
                        cols_str = ','.join([f'"{col}"' for col in columns])
                        insert_sql = f'INSERT INTO "{table}" ({cols_str}) VALUES ({placeholders})'

                        # Convert row values to proper types
                        values = [v if v is not None else None for v in row]

                        try:
                            result = turso_client.execute(insert_sql, values)
                            total_inserted += 1
                        except RuntimeError as e:
                            print(f"     ⚠️  Warning inserting into {table}: {str(e)}")
                            break

                print(f"     📊 {table}: {total_inserted} rows")

        conn.close()

        # Restore original token
        import os as temp_os
        if original_token:
            temp_os.environ["TURSO_TOKEN"] = original_token
        elif "TURSO_TOKEN" in temp_os.environ:
            del temp_os.environ["TURSO_TOKEN"]

        return True

    except Exception as e:
        print(f"     ❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()

        # Restore original token even on error
        import os as temp_os
        if 'original_token' in locals():
            if original_token:
                temp_os.environ["TURSO_TOKEN"] = original_token
            elif "TURSO_TOKEN" in temp_os.environ:
                del temp_os.environ["TURSO_TOKEN"]

        return False


def main():
    """Main upload process"""
    print("="*70)
    print("Spider → Turso Upload (20 Official Databases)")
    print("="*70)

    # Get credentials
    token = os.getenv("TURSO_TOKEN")
    org = os.getenv("TURSO_ORG", "jsperson")

    if not token:
        print("\n❌ TURSO_TOKEN not set in environment")
        sys.exit(1)

    print(f"\n✅ Organization: {org}")
    print(f"✅ Token: configured")

    # Ensure default group exists
    print("\n" + "="*70)
    print("Checking Turso group...")
    print("="*70)
    if not ensure_group_exists(token, org):
        print("❌ Failed to create or find default group")
        sys.exit(1)

    # Get official Spider databases
    print("\n" + "="*70)
    print("Loading official Spider databases...")
    print("="*70)

    spider_dbs = get_official_spider_databases()

    if not spider_dbs:
        print("❌ Could not load Spider databases from dev.json")
        sys.exit(1)

    print(f"\n✅ Found {len(spider_dbs)} official Spider databases")

    # Find corresponding SQLite files
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

        # Check if exists and has data
        if check_database_exists(db_name, token, org):
            # Create database token to check if it has tables
            db_token = create_database_token(db_name, token, org)
            if db_token:
                import os as check_os
                original_token = check_os.getenv("TURSO_TOKEN")
                check_os.environ["TURSO_TOKEN"] = db_token

                try:
                    from backend.app.database.turso_client import TursoClient
                    normalized = normalize_db_name(db_name)
                    client = TursoClient(db_name=normalized)
                    result = client.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                    table_count = result["rows"][0][0] if result["rows"] else 0

                    if table_count > 0:
                        print(f"  ⚠️  Already exists with {table_count} tables - skipping")
                        skipped_count += 1
                        continue
                    else:
                        print(f"  ⚠️  Exists but empty - will upload data")
                except:
                    print(f"  ⚠️  Could not check tables - will try to upload")
                finally:
                    if original_token:
                        check_os.environ["TURSO_TOKEN"] = original_token

            # Database exists but may be empty, continue to upload
            print(f"  🔨 Database exists, uploading data...")
        else:
            # Create database
            print(f"  🔨 Creating database...")
            if not create_database(db_name, token, org):
                print(f"  ❌ Failed to create")
                failed.append(db_name)
                continue

            # Wait a moment for database to be ready
            time.sleep(1)

        # Upload data
        print(f"  📤 Uploading data from {db['path'].name}...")
        if upload_sqlite_data(db_name, db["path"], token, org):
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
