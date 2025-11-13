#!/usr/bin/env python3
"""
Quick summary of what's in Supabase.
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database.supabase_client import SupabaseClient

supabase_url = os.getenv('SUPABASE_URL')
service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

sb_client = SupabaseClient(supabase_url, service_role_key)
supabase = sb_client.client

result = supabase.table('semantic_layers').select('database_name').execute()

print("=" * 70)
print("SUPABASE SEMANTIC_LAYERS TABLE")
print("=" * 70)
print(f"\nTotal records: {len(result.data)}")
print(f"\nDatabases:")
for layer in sorted(result.data, key=lambda x: x['database_name']):
    print(f"  - {layer['database_name']}")
print()
