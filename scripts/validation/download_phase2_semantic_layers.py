#!/usr/bin/env python3
"""
Download Phase 2 semantic layers from Supabase for local validation.
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database.supabase_client import SupabaseClient

def download_semantic_layers():
    """Download semantic layers from Supabase"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not service_role_key:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)
    
    sb_client = SupabaseClient(supabase_url, service_role_key)
    supabase = sb_client.client
    
    print("=" * 70)
    print("DOWNLOADING PHASE 2 SEMANTIC LAYERS FROM SUPABASE")
    print("=" * 70)
    
    # Get all semantic layers
    print("\nFetching semantic_layers from Supabase...")
    result = supabase.table('semantic_layers').select('*').execute()
    
    semantic_layers = result.data
    print(f"Found {len(semantic_layers)} semantic layers")
    
    # Create output directory
    output_dir = Path('data/semantic_layers')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save each semantic layer as a JSON file
    for layer in semantic_layers:
        db_name = layer['database_name']
        semantic_layer_data = layer['semantic_layer']
        
        output_file = output_dir / f'{db_name}.json'
        with open(output_file, 'w') as f:
            json.dump(semantic_layer_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ {db_name}.json")
    
    print(f"\n✅ Downloaded {len(semantic_layers)} semantic layers to {output_dir}")
    
    # Create a summary
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    summary_file = output_dir / f'_download_summary_{timestamp}.txt'
    
    with open(summary_file, 'w') as f:
        f.write(f"Phase 2 Semantic Layers Downloaded from Supabase\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Total files: {len(semantic_layers)}\n")
        f.write(f"\nDatabases:\n")
        for layer in semantic_layers:
            f.write(f"  - {layer['database_name']}\n")
    
    print(f"\nSummary saved: {summary_file}")
    
    return len(semantic_layers)

if __name__ == '__main__':
    count = download_semantic_layers()
    print("\n" + "=" * 70)
    print(f"DOWNLOAD COMPLETE - {count} files")
    print("=" * 70)
