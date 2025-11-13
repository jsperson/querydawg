#!/usr/bin/env python3
"""Check latest benchmark run in Supabase"""
import sys
import os
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

from app.database.benchmark_store import get_benchmark_store

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

store = get_benchmark_store(supabase_url, supabase_key)

# Get all runs
runs = store.list_runs(limit=5)

if runs:
    print("Latest benchmark runs:")
    for run in runs:
        print(f"  - Run ID: {run.run_id}")
        print(f"    Name: {run.name}")
        print(f"    Created: {run.created_at}")
        print(f"    Status: {run.status}")
        print(f"    Total Questions: {run.total_questions}")
        print(f"    Completed: {run.completed}")
        print()
else:
    print("No runs found")
