#!/usr/bin/env python3
"""
Check which database source a benchmark is actually using
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

    # Find Turso 6 run
    turso_6_run = next((r for r in runs if "Full Spider 1.0 Turso 6" in r.name or "Turso 6" in r.name), None)

    if not turso_6_run:
        print("Could not find 'Full Spider 1.0 Turso 6' run")
        print("\nRecent runs:")
        for r in runs[:10]:
            print(f"  - {r.name} ({r.status})")
        return

    print(f"=== Analyzing: {turso_6_run.name} ===")
    print(f"Run ID: {turso_6_run.run_id}")
    print(f"Status: {turso_6_run.status}")
    print(f"Progress: {turso_6_run.completed}/{turso_6_run.total_questions}")
    print()

    # Get sample results to check
    results, total = store.get_run_results(turso_6_run.run_id, limit=5)

    if not results:
        print("No results found yet")
        return

    print(f"Examining {len(results)} sample results...\n")

    # Check first result in detail
    first = results[0]

    print("=== Evidence Check ===")
    print()

    # Check 1: System prompt mentions SQLite or PostgreSQL?
    if first.baseline_system_prompt:
        if 'SQLite' in first.baseline_system_prompt:
            print("✓ System prompt mentions SQLite (Turso)")
        elif 'PostgreSQL' in first.baseline_system_prompt:
            print("✗ System prompt mentions PostgreSQL (Supabase)")
        else:
            print("? System prompt doesn't clearly indicate database type")

        # Show snippet
        print(f"\nPrompt snippet: {first.baseline_system_prompt[:200]}...")
    else:
        print("⚠️  No system prompt stored")

    print()

    # Check 2: Look at generated SQL - does it use schema qualification?
    if first.baseline_sql:
        print(f"Baseline SQL: {first.baseline_sql}")

        # PostgreSQL requires schema.table, SQLite uses direct table references
        if '.' in first.baseline_sql and first.database in first.baseline_sql:
            print("✗ SQL uses schema qualification (database.table) → PostgreSQL/Supabase")
        else:
            print("✓ SQL uses direct table references → SQLite/Turso")

    print()

    # Check 3: Look at errors
    print("=== Error Pattern Analysis ===")

    error_types = {}
    for result in results:
        if result.baseline_error:
            error_line = result.baseline_error.split('\n')[0][:100]
            error_types[error_line] = error_types.get(error_line, 0) + 1

    if error_types:
        print("Common errors:")
        for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {count}x: {error}")

            # Analyze error type
            if "SQLite error" in error:
                print("     → This is a Turso/SQLite error")
            elif "permission denied" in error.lower() or "does not exist" in error.lower():
                print("     → This looks like a PostgreSQL error")
    else:
        print("No errors in sample (all queries succeeded)")

    print()

    # Check 4: Look at execution match rate
    exec_match_count = sum(1 for r in results if r.baseline_exec_match is True)
    print(f"=== Execution Matches: {exec_match_count}/{len(results)} ===")

    if exec_match_count == len(results):
        print("⚠️  100% match rate - might indicate empty result bug (old TursoClient)")
    elif exec_match_count == 0:
        print("⚠️  0% match rate - might indicate all queries failing")
    else:
        print(f"✓ Normal match rate: {exec_match_count/len(results)*100:.1f}%")

    print()
    print("=== CONCLUSION ===")

    # Final determination
    evidence = []

    if first.baseline_system_prompt:
        if 'SQLite' in first.baseline_system_prompt:
            evidence.append("✓ Prompt says SQLite")
        elif 'PostgreSQL' in first.baseline_system_prompt:
            evidence.append("✗ Prompt says PostgreSQL")

    if first.baseline_sql:
        if first.database in first.baseline_sql and '.' in first.baseline_sql:
            evidence.append("✗ SQL uses schema qualification")
        else:
            evidence.append("✓ SQL uses direct table references")

    if any("SQLite error" in str(r.baseline_error or "") for r in results):
        evidence.append("✓ Errors are SQLite errors")

    print("Evidence:")
    for e in evidence:
        print(f"  {e}")

    turso_evidence = sum(1 for e in evidence if e.startswith("✓"))
    supabase_evidence = sum(1 for e in evidence if e.startswith("✗"))

    print()
    if turso_evidence > supabase_evidence:
        print("🎯 VERDICT: Running on TURSO (SQLite)")
    elif supabase_evidence > turso_evidence:
        print("🎯 VERDICT: Running on SUPABASE (PostgreSQL)")
    else:
        print("🤷 VERDICT: Unclear - need more evidence")

if __name__ == "__main__":
    main()
