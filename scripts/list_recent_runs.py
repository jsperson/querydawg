#!/usr/bin/env python3
"""
List recent benchmark runs
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from supabase import create_client
from app.config import get_settings

settings = get_settings()
supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)

# Get recent runs
response = supabase.table('benchmark_runs')\
    .select('id, name, created_at')\
    .order('created_at', desc=True)\
    .limit(10)\
    .execute()

print("Recent benchmark runs:")
print("="*80)
for run in response.data:
    print(f"{run['created_at'][:19]}  {run['name']}")
    print(f"  ID: {run['id']}")
    print()
