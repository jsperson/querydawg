#!/usr/bin/env python3
"""
Check if benchmark results contain actual query execution data
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

    # Get recent runs
    runs = store.list_runs(limit=20)

    # Find Turso run
    turso_run = next((r for r in runs if "Full Spider 1.0 on Turso 4" in r.name), None)

    if not turso_run:
        print("Could not find Turso 4 run")
        return

    print(f"Analyzing: {turso_run.name}")
    print(f"Status: {turso_run.status}")
    print(f"Progress: {turso_run.completed}/{turso_run.total_questions}")

    # Get sample results
    results, total = store.get_run_results(turso_run.run_id, limit=20)

    print(f"\nChecking {len(results)} sample results...\n")

    for i, result in enumerate(results[:5]):
        print(f"=== Result {i+1}: {result.question_id} ===")
        print(f"Question: {result.question}")
        print(f"Database: {result.database}")
        print(f"Gold SQL: {result.gold_sql}")
        print(f"Enhanced SQL: {result.enhanced_sql}")
        print(f"Enhanced exec_match: {result.enhanced_exec_match}")
        print(f"Enhanced error: {result.enhanced_error}")

        # Check if this was affected by the TursoClient bug
        if result.enhanced_exec_match and result.enhanced_error is None:
            print("⚠️  SUSPICIOUS: Marked as pass but might be false positive from TursoClient bug")
        elif result.enhanced_error and "no such table" in str(result.enhanced_error):
            print("✓ EXPECTED: Failed due to missing schema (TursoClient bug)")
        print()

    # Count patterns
    total_enhanced = len([r for r in results if r.enhanced_sql is not None])
    exec_match_count = len([r for r in results if r.enhanced_exec_match is True])
    no_table_errors = len([r for r in results if r.enhanced_error and "no such table" in str(r.enhanced_error)])

    print(f"=== SUMMARY (sample of {len(results)}) ===")
    print(f"Enhanced attempts: {total_enhanced}")
    print(f"Marked as exec_match=True: {exec_match_count} ({exec_match_count/max(total_enhanced,1)*100:.1f}%)")
    print(f"'no such table' errors: {no_table_errors} ({no_table_errors/max(total_enhanced,1)*100:.1f}%)")

    if exec_match_count > 0 and no_table_errors > 0:
        print("\n⚠️  DIAGNOSIS: TursoClient bug caused false positives!")
        print("    - Queries returned empty results []")
        print("    - Gold [] == Enhanced [] → exec_match=True")
        print("    - But actual queries failed with 'no such table'")
        print("\n✓ FIX: TursoClient now correctly parses Turso v2 API responses")
        print("   → New benchmark runs should show correct pass/fail")

if __name__ == "__main__":
    main()
