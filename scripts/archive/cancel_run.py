#!/usr/bin/env python3
"""Cancel a benchmark run"""
import sys
import os
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

from app.database.benchmark_store import get_benchmark_store

run_id = "05f8f2b7-1178-41c3-9928-e58265df4b56"

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

store = get_benchmark_store(supabase_url, supabase_key)

print(f"Cancelling run {run_id}...")
store.update_run_status(run_id, "cancelled")
print("✅ Run cancelled")
