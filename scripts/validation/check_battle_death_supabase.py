#!/usr/bin/env python3
"""
Check if battle_death in Supabase has Phase 2 content.
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import json

load_dotenv()

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database.supabase_client import SupabaseClient

supabase_url = os.getenv('SUPABASE_URL')
service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

sb_client = SupabaseClient(supabase_url, service_role_key)
supabase = sb_client.client

result = supabase.table('semantic_layers').select('*').eq('database_name', 'battle_death').execute()

if not result.data:
    print("❌ battle_death not found in Supabase")
else:
    semantic_layer = result.data[0]['semantic_layer']
    
    print("=" * 70)
    print("BATTLE_DEATH SEMANTIC LAYER IN SUPABASE")
    print("=" * 70)
    
    # Check for Phase 2 features
    json_str = json.dumps(semantic_layer)
    
    phase2_checks = {
        'is_bridge_table': 'is_bridge_table' in json_str,
        'disambiguation': 'disambiguation' in json_str,
        'complete_join_path': 'complete_join_path' in json_str,
        'common_mistakes': 'common_mistakes' in json_str
    }
    
    print(f"\nPhase 2 Features in Supabase:")
    print(f"  is_bridge_table: {'✅ Found' if phase2_checks['is_bridge_table'] else '❌ Not found'}")
    print(f"  disambiguation: {'✅ Found' if phase2_checks['disambiguation'] else '❌ Not found'}")
    print(f"  complete_join_path: {'✅ Found' if phase2_checks['complete_join_path'] else '❌ Not found'}")
    print(f"  common_mistakes: {'✅ Found' if phase2_checks['common_mistakes'] else '❌ Not found'}")
    
    if any(phase2_checks.values()):
        print("\n✅ PHASE 2 CONTENT IN SUPABASE")
        print("\n⚠️  But NOT in Pinecone - embeddings didn't run properly")
    else:
        print("\n❌ NO PHASE 2 CONTENT IN SUPABASE EITHER")
        print("The semantic layer wasn't regenerated with Phase 2 prompts")
