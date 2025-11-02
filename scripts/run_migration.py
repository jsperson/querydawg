#!/usr/bin/env python3
"""
Run migration directly on Supabase using psycopg2.
"""
import os
import sys
from pathlib import Path
import psycopg2

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

def main():
    print("=" * 80)
    print("APPLYING PROMPT LOGGING MIGRATION TO SUPABASE")
    print("=" * 80)
    print()

    # Get database URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ Error: DATABASE_URL not set in environment")
        return 1

    # Read migration SQL
    migration_file = Path(__file__).parent.parent / "migrations" / "002_add_prompt_logging.sql"
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    print("Connecting to Supabase...")
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        print("Executing migration...")
        cursor.execute(migration_sql)
        conn.commit()

        print()
        print("=" * 80)
        print("✅ MIGRATION SUCCESSFUL")
        print("=" * 80)
        print()
        print("The following columns have been added to benchmark_results:")
        print("  - baseline_system_prompt")
        print("  - baseline_user_prompt")
        print("  - enhanced_system_prompt")
        print("  - enhanced_user_prompt")
        print("  - enhanced_semantic_chunks")
        print()
        print("New index created: idx_benchmark_results_run_id_prompts")
        print()
        print("✅ Ready for prompt logging in next benchmark run!")
        print("=" * 80)
        print()

        cursor.close()
        conn.close()
        return 0

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ MIGRATION FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
