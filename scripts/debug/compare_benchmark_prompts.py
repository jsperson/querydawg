#!/usr/bin/env python3
"""
Compare benchmark runs to identify prompt issues between Turso and Supabase
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
    print("Fetching recent benchmark runs...")
    runs = store.list_runs(limit=20)

    # Find Turso and Supabase runs
    turso_runs = [r for r in runs if 'turso' in r.name.lower() or 'sqlite' in r.name.lower()]
    supabase_runs = [r for r in runs if 'supabase' in r.name.lower() or ('turso' not in r.name.lower() and 'sqlite' not in r.name.lower())]

    print(f"\nFound {len(turso_runs)} Turso runs and {len(supabase_runs)} Supabase runs")

    if turso_runs:
        print("\n=== TURSO RUNS ===")
        for i, run in enumerate(turso_runs[:5]):
            print(f"{i+1}. {run.name} ({run.status})")
            print(f"   ID: {run.run_id}")
            print(f"   Questions: {run.completed}/{run.total_questions}")
            if run.baseline_exec_match_rate is not None:
                print(f"   Baseline exec match: {run.baseline_exec_match_rate:.2%}")
            if run.enhanced_exec_match_rate is not None:
                print(f"   Enhanced exec match: {run.enhanced_exec_match_rate:.2%}")

    if supabase_runs:
        print("\n=== SUPABASE RUNS ===")
        for i, run in enumerate(supabase_runs[:5]):
            print(f"{i+1}. {run.name} ({run.status})")
            print(f"   ID: {run.run_id}")
            print(f"   Questions: {run.completed}/{run.total_questions}")
            if run.baseline_exec_match_rate is not None:
                print(f"   Baseline exec match: {run.baseline_exec_match_rate:.2%}")
            if run.enhanced_exec_match_rate is not None:
                print(f"   Enhanced exec match: {run.enhanced_exec_match_rate:.2%}")

    # Find the specific Turso run the user mentioned
    turso_4_run = next((r for r in runs if "Full Spider 1.0 on Turso 4" in r.name), None)

    if turso_4_run:
        print(f"\n=== ANALYZING: {turso_4_run.name} ===")
        print(f"Status: {turso_4_run.status}")
        print(f"Progress: {turso_4_run.completed}/{turso_4_run.total_questions}")

        # Get first few results to examine prompts
        print("\nFetching sample results to analyze prompts...")
        results, total = store.get_run_results(turso_4_run.run_id, limit=10)

        if results:
            print(f"\nAnalyzing first result:")
            first = results[0]
            print(f"Question: {first.question}")
            print(f"Database: {first.database}")

            if first.baseline_system_prompt:
                print(f"\n--- BASELINE SYSTEM PROMPT (first 500 chars) ---")
                print(first.baseline_system_prompt[:500])

                # Check for database-specific markers
                if 'SQLite' in first.baseline_system_prompt:
                    print("\n✓ Prompt mentions SQLite")
                elif 'PostgreSQL' in first.baseline_system_prompt:
                    print("\n✗ ERROR: Prompt mentions PostgreSQL but this is a Turso (SQLite) run!")

                # Check for schema qualification instructions
                if 'schema name' in first.baseline_system_prompt.lower():
                    print("✗ ERROR: Prompt includes schema qualification (PostgreSQL-specific)")
                elif 'directly by name' in first.baseline_system_prompt.lower():
                    print("✓ Prompt says to reference tables directly (SQLite)")

            if first.baseline_error:
                print(f"\nBaseline Error: {first.baseline_error[:200]}")

            # Count errors
            error_count = sum(1 for r in results if r.baseline_error)
            print(f"\nErrors in sample: {error_count}/{len(results)}")

            # Show common errors
            if error_count > 0:
                error_types = {}
                for r in results:
                    if r.baseline_error:
                        # Extract first line of error
                        error_line = r.baseline_error.split('\n')[0][:100]
                        error_types[error_line] = error_types.get(error_line, 0) + 1

                print("\nCommon error types:")
                for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {count}x: {error}")

        # Compare with most recent Supabase run
        if supabase_runs:
            recent_supabase = supabase_runs[0]
            print(f"\n=== COMPARING WITH: {recent_supabase.name} ===")
            print(f"Status: {recent_supabase.status}")
            print(f"Progress: {recent_supabase.completed}/{recent_supabase.total_questions}")

            # Get sample
            supabase_results, _ = store.get_run_results(recent_supabase.run_id, limit=10)

            if supabase_results:
                first_supabase = supabase_results[0]

                if first_supabase.baseline_system_prompt:
                    print(f"\n--- SUPABASE BASELINE SYSTEM PROMPT (first 500 chars) ---")
                    print(first_supabase.baseline_system_prompt[:500])

                    if 'PostgreSQL' in first_supabase.baseline_system_prompt:
                        print("\n✓ Supabase prompt mentions PostgreSQL")
                    if 'schema name' in first_supabase.baseline_system_prompt.lower():
                        print("✓ Supabase prompt includes schema qualification")

                # Count errors
                supabase_error_count = sum(1 for r in supabase_results if r.baseline_error)
                print(f"\nSupabase errors in sample: {supabase_error_count}/{len(supabase_results)}")

                print("\n=== COMPARISON ===")
                print(f"Turso errors: {error_count}/{len(results)} ({error_count/len(results)*100:.1f}%)")
                print(f"Supabase errors: {supabase_error_count}/{len(supabase_results)} ({supabase_error_count/len(supabase_results)*100:.1f}%)")

if __name__ == "__main__":
    main()
