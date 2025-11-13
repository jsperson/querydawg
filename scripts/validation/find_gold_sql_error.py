#!/usr/bin/env python3
"""
Find specific gold SQL in benchmark and show error
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database.benchmark_store import get_benchmark_store
from dotenv import load_dotenv

# Load environment
load_dotenv()

def main():
    # Initialize store
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_role_key:
        print("Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
        return

    store = get_benchmark_store(supabase_url, service_role_key)

    # Get Turso 6 run
    runs = store.list_runs(20)
    turso_6 = next((r for r in runs if "Turso 6" in r.name), None)

    if not turso_6:
        print("Could not find Turso 6 run")
        return

    print(f"Searching in: {turso_6.name}")
    print(f"Progress: {turso_6.completed}/{turso_6.total_questions}\n")

    # Search for the problematic SQL
    search_sql = "GROUP BY T1.stadium_id"

    # Get all results (in batches)
    all_results = []
    page_size = 100
    offset = 0

    while True:
        results, total = store.get_run_results(turso_6.run_id, limit=page_size, offset=offset)
        if not results:
            break
        all_results.extend(results)
        offset += page_size
        print(f"Loaded {len(all_results)} results...")
        if len(all_results) >= total:
            break

    print(f"\nSearching through {len(all_results)} results for: {search_sql}\n")

    # Find matching queries
    matches = [r for r in all_results if search_sql in r.gold_sql]

    if not matches:
        print("❌ Query not found in results")
        return

    print(f"✓ Found {len(matches)} matching queries\n")

    for i, result in enumerate(matches[:3]):  # Show first 3 matches
        print(f"=== Match {i+1}: {result.question_id} ===")
        print(f"Question: {result.question}")
        print(f"Database: {result.database}")
        print(f"\nGold SQL:")
        print(result.gold_sql)
        print(f"\nBaseline Error: {result.baseline_error}")
        print(f"Enhanced Error: {result.enhanced_error}")
        print()

        # Try to execute it directly
        print("Testing direct execution...")
        from app.database.turso_client import TursoClient

        try:
            client = TursoClient(db_name=result.database)
            exec_result = client.execute(result.gold_sql)
            print(f"✓ Direct execution succeeded!")
            print(f"  Rows returned: {len(exec_result['rows'])}")
            if exec_result['rows']:
                print(f"  Sample: {exec_result['rows'][0]}")
        except Exception as e:
            print(f"✗ Direct execution failed:")
            print(f"  {str(e)}")

        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
