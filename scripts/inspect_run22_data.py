#!/usr/bin/env python3
"""
Inspect what fields are available in Run 22 results.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import json

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

    # Get Run 22 ID
    print("Fetching runs...")
    runs = supabase.table("benchmark_runs").select("*").execute()

    print("\nAvailable runs:")
    for i, r in enumerate(runs.data):
        print(f"{i}: {r['name']} (ID: {r['id']})")

    # Find Run 22
    run22 = None
    for r in runs.data:
        if "22" in r['name'] and "Full Spider" in r['name']:
            run22 = r
            break

    if not run22:
        print("\n❌ Run 22 not found!")
        return

    print(f"\n✅ Found Run 22: {run22['name']}")
    print(f"   ID: {run22['id']}")

    # Get first result to see fields
    print(f"\nFetching first result...")
    results = supabase.table('benchmark_results').select('*').eq('run_id', run22['id']).limit(1).execute()

    if results.data:
        print("\nAvailable fields in benchmark_results:")
        for key, value in sorted(results.data[0].items()):
            val_str = str(value)[:50] if value else "None"
            print(f"  {key}: {val_str}")

if __name__ == "__main__":
    main()
