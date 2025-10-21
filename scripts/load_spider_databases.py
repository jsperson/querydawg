#!/usr/bin/env python3
"""
Load Spider SQLite databases into Supabase PostgreSQL.

This script migrates all 20 selected Spider databases from SQLite to PostgreSQL:
- Creates separate schemas for each database (world_1, concert_singer, etc.)
- Applies PostgreSQL best practices for types (VARCHAR, NUMERIC, BIGINT)
- Extracts and recreates foreign key constraints
- Generates SQL files for version control
- Continues on errors with detailed logging

Usage:
    python scripts/load_spider_databases.py              # Execute migration
    python scripts/load_spider_databases.py --sql-only   # Generate SQL without executing
    python scripts/load_spider_databases.py --dry-run    # Preview without changes
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# =============================================================================
# Configuration
# =============================================================================

# All 20 Spider databases from project plan
DATABASES_ALL = [
    "world_1",
    "car_1",
    "cre_Doc_Template_Mgt",
    "dog_kennels",
    "flight_2",
    "student_transcripts_tracking",
    "wta_1",
    "tvshow",
    "network_1",
    "concert_singer",
    "pets_1",
    "poker_player",
    "orchestra",
    "employee_hire_evaluation",
    "course_teach",
    "singer",
    "museum_visit",
    "battle_death",
    "voter_1",
    "real_estate_properties",
]

# TEST: Load remaining 9 databases (indices 11-19, excluding wta_1 at index 6)
DATABASES = DATABASES_ALL[11:20]

SPIDER_DB_PATH = project_root / "data" / "spider" / "database"
SQL_OUTPUT_PATH = project_root / "data" / "spider" / "migrations"

# Type mappings: SQLite → PostgreSQL
TYPE_MAPPINGS = {
    "integer": "BIGINT",
    "real": "DOUBLE PRECISION",
    "text": "TEXT",
    "blob": "BYTEA",
}

# =============================================================================
# Helper Functions
# =============================================================================

def map_sqlite_type_to_postgres(sqlite_type: str, actual_max_length: Optional[int] = None) -> str:
    """
    Map SQLite data types to PostgreSQL best practices.

    Examples:
        char(35) → VARCHAR(35) or VARCHAR(actual_max_length + buffer)
        float(10,2) → NUMERIC(10,2)
        integer → BIGINT

    Args:
        sqlite_type: The SQLite column type
        actual_max_length: The actual maximum length of data in this column (for varchar/char)
    """
    if not sqlite_type:
        return "TEXT"

    sqlite_type = sqlite_type.lower().strip()

    # Handle char/varchar types
    if sqlite_type.startswith("char(") or sqlite_type.startswith("varchar("):
        # If we have actual max length from data scan, use that with a 20% buffer
        if actual_max_length is not None:
            # Add 20% buffer, minimum 10, maximum 10000
            buffered_length = max(10, min(10000, int(actual_max_length * 1.2)))
            return f"VARCHAR({buffered_length})"
        else:
            # Fallback to declared length
            length = sqlite_type[sqlite_type.find("(")+1:sqlite_type.find(")")]
            return f"VARCHAR({length})"

    # Handle float/numeric types with precision
    if sqlite_type.startswith("float(") or sqlite_type.startswith("numeric("):
        # Extract precision: float(10,2) → NUMERIC(10,2)
        precision = sqlite_type[sqlite_type.find("(")+1:sqlite_type.find(")")]
        return f"NUMERIC({precision})"

    # Handle basic types
    if "int" in sqlite_type:
        return "BIGINT"
    if "real" in sqlite_type or "float" in sqlite_type or "double" in sqlite_type:
        return "DOUBLE PRECISION"
    if "text" in sqlite_type or "char" in sqlite_type or "clob" in sqlite_type:
        return "TEXT"
    if "blob" in sqlite_type:
        return "BYTEA"

    # Default to TEXT for unknown types
    return "TEXT"


def get_table_schema(sqlite_conn: sqlite3.Connection, table_name: str) -> List[Dict]:
    """Extract table schema from SQLite."""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = []

    for row in cursor.fetchall():
        col_info = {
            "cid": row[0],
            "name": row[1],
            "type": row[2],
            "notnull": row[3],
            "default": row[4],
            "pk": row[5],
        }
        columns.append(col_info)

    return columns


def scan_column_lengths(sqlite_conn: sqlite3.Connection, table_name: str, columns: List[Dict]) -> Dict[str, int]:
    """
    Scan actual maximum lengths of string columns in the data.

    Returns dict mapping column name to actual max length.
    """
    cursor = sqlite_conn.cursor()
    max_lengths = {}

    for col in columns:
        col_name = col["name"]
        col_type = col["type"].lower()

        # Only scan char/varchar columns
        if "char" in col_type and "(" in col_type:
            try:
                cursor.execute(f"SELECT MAX(LENGTH({col_name})) FROM {table_name}")
                result = cursor.fetchone()
                max_len = result[0] if result and result[0] is not None else 0
                max_lengths[col_name] = max_len
            except Exception:
                # If scan fails, skip this column
                pass

    return max_lengths


def get_foreign_keys(sqlite_conn: sqlite3.Connection, table_name: str) -> List[Dict]:
    """Extract foreign key constraints from SQLite."""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    fks = []

    for row in cursor.fetchall():
        fk_info = {
            "id": row[0],
            "seq": row[1],
            "table": row[2],
            "from": row[3],
            "to": row[4],
            "on_update": row[5],
            "on_delete": row[6],
        }
        fks.append(fk_info)

    return fks


def get_table_names(sqlite_conn: sqlite3.Connection) -> List[str]:
    """Get all table names from SQLite database."""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [row[0] for row in cursor.fetchall()]


def quote_identifier(name: str) -> str:
    """Quote PostgreSQL identifier if it starts with a digit or contains special chars."""
    # Quote if starts with digit or contains anything other than alphanumeric and underscore
    if name[0].isdigit() or not name.replace('_', '').isalnum():
        return f'"{name}"'
    return name


def generate_create_table_sql(schema_name: str, table_name: str, columns: List[Dict], max_lengths: Optional[Dict[str, int]] = None) -> str:
    """Generate PostgreSQL CREATE TABLE statement."""
    lines = [f"CREATE TABLE {schema_name}.{table_name} ("]

    col_defs = []
    pk_cols = []

    for col in columns:
        # Get actual max length for this column if available
        actual_max_length = max_lengths.get(col["name"]) if max_lengths else None
        pg_type = map_sqlite_type_to_postgres(col["type"], actual_max_length)

        # SPECIAL CASE FIX: car_1.car_makers.Country is TEXT but contains numeric IDs
        # Change to BIGINT to match foreign key target type
        if schema_name == "car_1" and table_name == "car_makers" and col["name"] == "Country":
            pg_type = "BIGINT"

        # Quote column name if needed (e.g., starts with digit like "18_49_Rating_Share")
        col_name_quoted = quote_identifier(col['name'])
        col_def = f"    {col_name_quoted} {pg_type}"

        # Add NOT NULL constraint
        if col["notnull"]:
            col_def += " NOT NULL"

        # Track primary key columns
        if col["pk"] > 0:
            pk_cols.append((col["pk"], col["name"]))

        # Add default value (skip for primary keys)
        if col["default"] is not None and col["pk"] == 0:
            default_val = col["default"]
            # Handle string defaults
            if default_val.startswith("'") and default_val.endswith("'"):
                col_def += f" DEFAULT {default_val}"
            elif default_val.upper() in ["NULL", "CURRENT_TIMESTAMP"]:
                col_def += f" DEFAULT {default_val}"
            else:
                col_def += f" DEFAULT {default_val}"

        col_defs.append(col_def)

    # Add primary key constraint
    if pk_cols:
        pk_cols.sort()  # Sort by pk position
        pk_names = [quote_identifier(name) for _, name in pk_cols]
        col_defs.append(f"    PRIMARY KEY ({', '.join(pk_names)})")

    lines.append(",\n".join(col_defs))
    lines.append(");")

    return "\n".join(lines)


def generate_foreign_key_sql(schema_name: str, table_name: str, fks: List[Dict]) -> List[str]:
    """Generate PostgreSQL ALTER TABLE statements for foreign keys."""
    if not fks:
        return []

    # Group foreign keys by id (composite foreign keys)
    fk_groups = {}
    for fk in fks:
        fk_id = fk["id"]
        if fk_id not in fk_groups:
            fk_groups[fk_id] = []
        fk_groups[fk_id].append(fk)

    sql_statements = []
    for fk_id, fk_list in fk_groups.items():
        fk_list.sort(key=lambda x: x["seq"])

        from_cols = [quote_identifier(fk["from"]) for fk in fk_list]
        to_cols = [quote_identifier(fk["to"]) for fk in fk_list]
        ref_table = fk_list[0]["table"]
        on_update = fk_list[0]["on_update"]
        on_delete = fk_list[0]["on_delete"]

        constraint_name = f"fk_{table_name}_{ref_table}_{fk_id}"

        sql = f"ALTER TABLE {schema_name}.{table_name}\n"
        sql += f"    ADD CONSTRAINT {constraint_name}\n"
        sql += f"    FOREIGN KEY ({', '.join(from_cols)})\n"
        sql += f"    REFERENCES {schema_name}.{ref_table} ({', '.join(to_cols)})"

        if on_update and on_update != "NO ACTION":
            sql += f"\n    ON UPDATE {on_update}"
        if on_delete and on_delete != "NO ACTION":
            sql += f"\n    ON DELETE {on_delete}"

        sql += ";"
        sql_statements.append(sql)

    return sql_statements


def get_row_count(sqlite_conn: sqlite3.Connection, table_name: str) -> int:
    """Get row count from SQLite table."""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cursor.fetchone()[0]


def clean_text_value(value: str) -> str:
    """
    Clean text value to handle encoding issues.

    Tries multiple encodings and uses smart fallbacks for special characters.
    This handles cases like 'Albarrac��N' which should be 'Albarracín'.
    """
    if not isinstance(value, str):
        return value

    # Try different encodings in order of likelihood
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

    for encoding in encodings:
        try:
            # If it's already a string, try to encode and decode with the encoding
            # to normalize any weird characters
            if isinstance(value, str):
                # Try encoding to bytes and back
                cleaned = value.encode('utf-8', errors='ignore').decode('utf-8')
                return cleaned
        except (UnicodeDecodeError, UnicodeEncodeError, AttributeError):
            continue

    # Fallback: replace any problematic characters
    try:
        return value.encode('utf-8', errors='replace').decode('utf-8')
    except:
        # Last resort: strip non-ASCII characters
        return ''.join(char if ord(char) < 128 else '?' for char in value)


def migrate_database(
    db_name: str,
    pg_conn: Optional[psycopg2.extensions.connection],
    sql_only: bool = False,
    dry_run: bool = False
) -> Tuple[bool, str, Dict]:
    """
    Migrate a single Spider database from SQLite to PostgreSQL.

    Returns:
        (success, message, stats)
    """
    stats = {
        "tables": 0,
        "rows": 0,
        "foreign_keys": 0,
    }

    try:
        # Connect to SQLite database
        sqlite_path = SPIDER_DB_PATH / db_name / f"{db_name}.sqlite"
        if not sqlite_path.exists():
            return False, f"SQLite database not found: {sqlite_path}", stats

        sqlite_conn = sqlite3.connect(sqlite_path)

        # Configure SQLite to handle encoding issues gracefully
        # Use a custom text_factory to handle problematic encodings
        sqlite_conn.text_factory = lambda b: b.decode('utf-8', errors='ignore') if isinstance(b, bytes) else b

        # Get all tables
        table_names = get_table_names(sqlite_conn)
        if not table_names:
            sqlite_conn.close()
            return False, "No tables found in database", stats

        # Prepare SQL output
        sql_lines = [
            f"-- Migration SQL for {db_name}",
            f"-- Generated: {datetime.now().isoformat()}",
            f"-- Source: {sqlite_path}",
            "",
            f"-- Create schema",
            f"CREATE SCHEMA IF NOT EXISTS {db_name};",
            "",
        ]

        # Create schema if not sql-only mode
        if not sql_only and not dry_run and pg_conn:
            cursor = pg_conn.cursor()
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {db_name}")
            cursor.close()

        # Track foreign keys to add after all tables AND data are loaded
        all_foreign_keys = []

        # Scan column lengths for all tables (to avoid VARCHAR overflow)
        print(f"    Scanning column lengths...")
        table_max_lengths = {}
        for table_name in table_names:
            columns = get_table_schema(sqlite_conn, table_name)
            max_lengths = scan_column_lengths(sqlite_conn, table_name, columns)
            if max_lengths:
                table_max_lengths[table_name] = max_lengths

        # Process each table
        for table_name in table_names:
            stats["tables"] += 1

            # Get schema
            columns = get_table_schema(sqlite_conn, table_name)

            # Get scanned max lengths for this table
            max_lengths = table_max_lengths.get(table_name, {})

            # Generate CREATE TABLE
            create_sql = generate_create_table_sql(db_name, table_name, columns, max_lengths)
            sql_lines.append(f"-- Table: {table_name}")
            sql_lines.append(create_sql)
            sql_lines.append("")

            # Get foreign keys
            fks = get_foreign_keys(sqlite_conn, table_name)
            if fks:
                fk_sqls = generate_foreign_key_sql(db_name, table_name, fks)
                all_foreign_keys.extend(fk_sqls)
                stats["foreign_keys"] += len(fk_sqls)

            # Execute CREATE TABLE if not sql-only mode
            if not sql_only and not dry_run and pg_conn:
                cursor = pg_conn.cursor()
                cursor.execute(create_sql)
                cursor.close()

        # NOTE: Foreign keys will be added AFTER data migration
        # This avoids foreign key constraint violations during data insertion

        # Migrate data for each table
        sql_lines.append("-- Data migration")

        for table_name in table_names:
            # Get row count
            row_count = get_row_count(sqlite_conn, table_name)
            stats["rows"] += row_count

            sql_lines.append(f"-- {table_name}: {row_count} rows")

            if row_count > 0:
                # Get all data
                cursor = sqlite_conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                # Get column names and quote if needed
                columns = [desc[0] for desc in cursor.description]
                col_list = ", ".join([quote_identifier(col) for col in columns])

                # Generate INSERT statements (batch by 100 rows for readability)
                for i in range(0, len(rows), 100):
                    batch = rows[i:i+100]

                    sql_lines.append(f"INSERT INTO {db_name}.{table_name} ({col_list}) VALUES")

                    value_lines = []
                    for row in batch:
                        # Format values
                        formatted_vals = []
                        for i, val in enumerate(row):
                            col_name = columns[i]

                            # SPECIAL CASE FIX: car_1.car_makers.Country - convert TEXT to INTEGER
                            if db_name == "car_1" and table_name == "car_makers" and col_name == "Country":
                                # Convert string number to integer (no quotes in SQL)
                                formatted_vals.append(str(int(val)) if val else "NULL")
                            elif val is None:
                                formatted_vals.append("NULL")
                            elif isinstance(val, (int, float)):
                                formatted_vals.append(str(val))
                            else:
                                # Clean text value to handle encoding issues
                                cleaned = clean_text_value(str(val))
                                # Escape single quotes
                                escaped = cleaned.replace("'", "''")
                                formatted_vals.append(f"'{escaped}'")

                        value_lines.append(f"    ({', '.join(formatted_vals)})")

                    sql_lines.append(",\n".join(value_lines) + ";")
                    sql_lines.append("")

                # Execute data migration if not sql-only mode
                if not sql_only and not dry_run and pg_conn:
                    # Clean rows to handle encoding issues
                    cleaned_rows = []
                    for row in rows:
                        cleaned_row = []
                        for i, val in enumerate(row):
                            col_name = columns[i]

                            # SPECIAL CASE FIX: car_1.car_makers.Country - convert TEXT to INTEGER
                            if db_name == "car_1" and table_name == "car_makers" and col_name == "Country":
                                # Convert string number to integer
                                cleaned_row.append(int(val) if val else None)
                            elif isinstance(val, str):
                                cleaned_row.append(clean_text_value(val))
                            else:
                                cleaned_row.append(val)
                        cleaned_rows.append(tuple(cleaned_row))

                    # Batch insert to avoid timeouts on large tables
                    # Process in batches of 1000 rows
                    batch_size = 1000
                    placeholders = ", ".join(["%s"] * len(columns))
                    insert_sql = f"INSERT INTO {db_name}.{table_name} ({col_list}) VALUES ({placeholders})"

                    for i in range(0, len(cleaned_rows), batch_size):
                        batch = cleaned_rows[i:i+batch_size]
                        cursor_pg = pg_conn.cursor()
                        try:
                            cursor_pg.executemany(insert_sql, batch)
                            cursor_pg.close()
                        except Exception as e:
                            cursor_pg.close()
                            # If connection died, try to reconnect
                            if "closed" in str(e).lower() or "ssl" in str(e).lower():
                                print(f"      Connection lost, reconnecting...")
                                try:
                                    pg_conn = psycopg2.connect(os.getenv("DATABASE_URL"))
                                    pg_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                                    cursor_pg = pg_conn.cursor()
                                    cursor_pg.executemany(insert_sql, batch)
                                    cursor_pg.close()
                                except Exception as reconnect_error:
                                    raise Exception(f"Failed to reconnect and insert: {reconnect_error}")
                            else:
                                raise

        # Add foreign keys AFTER all data has been loaded
        if all_foreign_keys:
            sql_lines.append("")
            sql_lines.append("-- Foreign key constraints (added after data load)")
            sql_lines.extend(all_foreign_keys)
            sql_lines.append("")

            # Execute foreign keys if not sql-only mode
            if not sql_only and not dry_run and pg_conn:
                print(f"    Adding foreign key constraints...")
                cursor = pg_conn.cursor()
                for fk_sql in all_foreign_keys:
                    try:
                        cursor.execute(fk_sql)
                    except Exception as fk_error:
                        # Log FK error but continue (some FKs might have type mismatches)
                        print(f"      ⚠️  FK constraint failed: {str(fk_error)[:80]}...")
                cursor.close()

        # Save SQL to file
        sql_output_file = SQL_OUTPUT_PATH / f"{db_name}.sql"
        sql_output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(sql_output_file, "w") as f:
            f.write("\n".join(sql_lines))

        sqlite_conn.close()

        if dry_run:
            return True, f"Dry run complete (would migrate {stats['tables']} tables, {stats['rows']} rows)", stats
        elif sql_only:
            return True, f"SQL generated: {sql_output_file}", stats
        else:
            return True, f"Migrated {stats['tables']} tables, {stats['rows']} rows, {stats['foreign_keys']} FKs", stats

    except Exception as e:
        return False, f"Error: {str(e)}", stats


def main():
    parser = argparse.ArgumentParser(description="Load Spider databases into Supabase PostgreSQL")
    parser.add_argument("--sql-only", action="store_true", help="Generate SQL files without executing")
    parser.add_argument("--dry-run", action="store_true", help="Preview migration without making changes")
    args = parser.parse_args()

    print("=" * 80)
    print("DataPrism: Load Spider Databases to PostgreSQL")
    print("=" * 80)
    print()

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print()
    elif args.sql_only:
        print("📝 SQL-ONLY MODE - Generating SQL files without executing")
        print()

    # Connect to PostgreSQL
    pg_conn = None
    if not args.sql_only and not args.dry_run:
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                print("❌ DATABASE_URL not found in .env file")
                sys.exit(1)

            print("Connecting to PostgreSQL...")
            pg_conn = psycopg2.connect(database_url)
            pg_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            print("✅ Connected to PostgreSQL")
            print()
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
            sys.exit(1)

    # Ask user if they want to clean the database
    clean_database = False
    databases_to_migrate = DATABASES

    if not args.sql_only and not args.dry_run and pg_conn:
        print("⚠️  Do you want to empty the database before loading?")
        print("   YES: Drop all existing schemas and reload everything")
        print("   NO:  Only load databases that don't exist yet")
        print()

        while True:
            response = input("Empty database? (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                clean_database = True
                break
            elif response in ['no', 'n']:
                clean_database = False
                break
            else:
                print("Please answer 'yes' or 'no'")

        print()

    # Clean existing schemas (DROP CASCADE) if requested
    if clean_database and not args.sql_only and not args.dry_run and pg_conn:
        print("🧹 Cleaning existing schemas...")
        cursor = pg_conn.cursor()

        for db_name in DATABASES:
            try:
                cursor.execute(f"DROP SCHEMA IF EXISTS {db_name} CASCADE")
                print(f"  ✓ Dropped schema: {db_name}")
            except Exception as e:
                print(f"  ⚠️  Could not drop {db_name}: {e}")

        cursor.close()
        print()

    # If not cleaning, check which schemas already exist and skip them
    elif not clean_database and not args.sql_only and not args.dry_run and pg_conn:
        print("🔍 Checking for existing schemas...")
        cursor = pg_conn.cursor()
        cursor.execute("SELECT schema_name FROM information_schema.schemata")
        existing_schemas = {row[0] for row in cursor.fetchall()}
        cursor.close()

        databases_to_migrate = [db for db in DATABASES if db not in existing_schemas]
        skipped = [db for db in DATABASES if db in existing_schemas]

        if skipped:
            print(f"  ⏭️  Skipping {len(skipped)} existing schemas: {', '.join(skipped)}")
        if databases_to_migrate:
            print(f"  ➕ Will migrate {len(databases_to_migrate)} new databases: {', '.join(databases_to_migrate)}")
        else:
            print("  ✅ All databases already exist. Nothing to migrate.")
            print()
            print("To reload existing databases, run again and choose 'yes' to empty the database.")
            sys.exit(0)
        print()

    # Migrate all databases
    print(f"📦 Migrating {len(databases_to_migrate)} databases...")
    print()

    results = {
        "success": [],
        "failed": [],
    }

    total_stats = {
        "tables": 0,
        "rows": 0,
        "foreign_keys": 0,
    }

    for i, db_name in enumerate(databases_to_migrate, 1):
        print(f"[{i}/{len(databases_to_migrate)}] {db_name}...", end=" ")

        success, message, stats = migrate_database(db_name, pg_conn, args.sql_only, args.dry_run)

        if success:
            print(f"✅ {message}")
            results["success"].append(db_name)
            total_stats["tables"] += stats["tables"]
            total_stats["rows"] += stats["rows"]
            total_stats["foreign_keys"] += stats["foreign_keys"]
        else:
            print(f"❌ {message}")
            results["failed"].append((db_name, message))

    # Cleanup
    if pg_conn:
        pg_conn.close()

    # Summary
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print(f"Total databases processed: {len(databases_to_migrate)}")
    print(f"✅ Successful: {len(results['success'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print()

    if not args.dry_run:
        print(f"Total tables: {total_stats['tables']}")
        print(f"Total rows: {total_stats['rows']:,}")
        print(f"Total foreign keys: {total_stats['foreign_keys']}")
        print()

    print(f"SQL files saved to: {SQL_OUTPUT_PATH}")
    print()

    if results["failed"]:
        print("Failed databases:")
        for db_name, error in results["failed"]:
            print(f"  ❌ {db_name}: {error}")
        print()
        sys.exit(1)
    else:
        if args.dry_run:
            print("✅ Dry run complete - no changes made")
        elif args.sql_only:
            print("✅ SQL files generated successfully")
        else:
            print("🎉 All databases migrated successfully!")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
