#!/usr/bin/env python3
"""
Find the actual Run 22 that matches the 83.82% accuracy mentioned in documentation.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from supabase import create_client

def main():
    # Connect to Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials!")
        return

    supabase = create_client(supabase_url, supabase_key)

    # Get all runs
    print("Fetching all runs...")
    runs = supabase.table("benchmark_runs").select("*").execute()

    print(f"\nSearching for runs with ~83.82% accuracy (867/1034)...")
    print(f"\nRuns sorted by enhanced_exec_match:")
    print(f"{'='*100}")

    # Sort by enhanced accuracy
    sorted_runs = sorted(runs.data, key=lambda x: x.get('enhanced_exec_match', 0) or 0, reverse=True)

    for r in sorted_runs[:20]:  # Top 20
        enhanced = r.get('enhanced_exec_match', 0) or 0
        baseline = r.get('baseline_exec_match', 0) or 0
        if enhanced > 0:
            enhanced_pct = enhanced * 100
            baseline_pct = baseline * 100
            enhanced_count = round(enhanced * 1034)  # Assuming 1034 questions
            baseline_count = round(baseline * 1034)

            print(f"{r['name']:<60s}")
            print(f"  Baseline:  {baseline_count:4d}/1034 ({baseline_pct:5.2f}%)")
            print(f"  Enhanced:  {enhanced_count:4d}/1034 ({enhanced_pct:5.2f}%)")
            print(f"  ID: {r['id']}")
            print()

if __name__ == "__main__":
    main()
