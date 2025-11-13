#!/usr/bin/env python3
"""
Check if schema is being passed in prompts
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

    # Get Turso run
    runs = store.list_runs(limit=20)
    turso_4_run = next((r for r in runs if "Full Spider 1.0 on Turso 4" in r.name), None)

    if not turso_4_run:
        print("Could not find 'Full Spider 1.0 on Turso 4' run")
        return

    # Get first result
    results, _ = store.get_run_results(turso_4_run.run_id, limit=1)

    if not results:
        print("No results found")
        return

    first = results[0]

    print(f"=== TURSO RUN: {turso_4_run.name} ===")
    print(f"Question: {first.question}")
    print(f"Database: {first.database}")
    print(f"Gold SQL: {first.gold_sql}")
    print(f"Baseline SQL: {first.baseline_sql}")
    print(f"Baseline Error: {first.baseline_error}")

    if first.baseline_user_prompt:
        print(f"\n--- BASELINE USER PROMPT ---")
        print(first.baseline_user_prompt)
    else:
        print("\n⚠ No baseline_user_prompt found!")

    # Check Supabase run for comparison
    supabase_runs = [r for r in runs if 'supabase' in r.name.lower() or ('turso' not in r.name.lower() and 'sqlite' not in r.name.lower())]
    if supabase_runs:
        recent_supabase = supabase_runs[0]
        print(f"\n\n=== SUPABASE RUN: {recent_supabase.name} ===")

        supabase_results, _ = store.get_run_results(recent_supabase.run_id, limit=1)
        if supabase_results:
            sb_first = supabase_results[0]
            print(f"Question: {sb_first.question}")
            print(f"Database: {sb_first.database}")
            print(f"Gold SQL: {sb_first.gold_sql}")
            print(f"Baseline SQL: {sb_first.baseline_sql}")

            if sb_first.baseline_user_prompt:
                print(f"\n--- BASELINE USER PROMPT ---")
                print(sb_first.baseline_user_prompt)
            else:
                print("\n⚠ No baseline_user_prompt found!")

if __name__ == "__main__":
    main()
