#!/usr/bin/env python3
"""
Backup Phase 1 semantic layer data before Phase 2 regeneration.

Backs up:
1. Supabase semantic_layers table
2. Pinecone index metadata
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

def backup_supabase_semantic_layers():
    """Backup semantic_layers table from Supabase"""

    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not service_role_key:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)

    sb_client = SupabaseClient(supabase_url, service_role_key)
    supabase = sb_client.client

    print("=" * 70)
    print("BACKING UP PHASE 1 DATA")
    print("=" * 70)

    # Get all semantic layers
    print("\n1. Fetching semantic_layers from Supabase...")
    result = supabase.table('semantic_layers').select('*').execute()

    semantic_layers = result.data
    print(f"   Found {len(semantic_layers)} semantic layers")

    # Create backup file
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    os.makedirs('data/backups', exist_ok=True)
    backup_file = f'data/backups/semantic_layers_phase1_{timestamp}.json'

    with open(backup_file, 'w') as f:
        json.dump({
            'backup_timestamp': timestamp,
            'backup_phase': 'phase1',
            'total_records': len(semantic_layers),
            'semantic_layers': semantic_layers
        }, f, indent=2)

    file_size_mb = os.path.getsize(backup_file) / 1024 / 1024
    print(f"   ✅ Backup saved: {backup_file}")
    print(f"   File size: {file_size_mb:.2f} MB")

    return backup_file, semantic_layers

def document_pinecone_state():
    """Document current Pinecone index state"""

    print("\n2. Documenting Pinecone index state...")

    pinecone_api_key = os.getenv('PINECONE_API_KEY')
    pinecone_index_name = os.getenv('PINECONE_INDEX_NAME', 'semantic-layers')

    if not pinecone_api_key:
        print("   WARNING: PINECONE_API_KEY not found")
        return None

    try:
        from pinecone import Pinecone

        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index(pinecone_index_name)
        stats = index.describe_index_stats()

        print(f"   Index: {pinecone_index_name}")
        print(f"   Total vectors: {stats.total_vector_count}")
        print(f"   Dimensions: {stats.dimension}")

        # Convert namespace summaries to dict
        namespaces_dict = {}
        if hasattr(stats, 'namespaces') and stats.namespaces:
            for ns_name, ns_summary in stats.namespaces.items():
                namespaces_dict[ns_name] = {
                    'vector_count': ns_summary.vector_count if hasattr(ns_summary, 'vector_count') else 0
                }

        pinecone_info = {
            'index_name': pinecone_index_name,
            'total_vectors': stats.total_vector_count,
            'dimensions': stats.dimension,
            'namespaces': namespaces_dict
        }

        return pinecone_info

    except Exception as e:
        print(f"   WARNING: Could not connect to Pinecone: {e}")
        return {'index_name': pinecone_index_name, 'error': str(e)}

def main():
    # Backup Supabase data
    backup_file, semantic_layers = backup_supabase_semantic_layers()

    # Document Pinecone state
    pinecone_info = document_pinecone_state()

    # Create summary file
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    summary_file = f'data/backups/phase1_backup_summary_{timestamp}.json'

    summary = {
        'backup_timestamp': timestamp,
        'backup_phase': 'phase1',
        'git_tag': 'phase1-semantic-layers',
        'supabase_backup': backup_file,
        'supabase_records': len(semantic_layers),
        'pinecone_info': pinecone_info
    }

    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 70)
    print("BACKUP COMPLETE")
    print("=" * 70)
    print(f"\nGit tag: phase1-semantic-layers")
    print(f"Supabase backup: {backup_file}")
    print(f"Summary: {summary_file}")

    if pinecone_info:
        print(f"\nPinecone index: {pinecone_info['index_name']}")
        print(f"  Vectors: {pinecone_info.get('total_vectors', 'unknown')}")

    print("\n" + "=" * 70)
    print("RESTORATION INSTRUCTIONS")
    print("=" * 70)
    print("\nTo restore Phase 1 state:")
    print("1. Git: git checkout phase1-semantic-layers -- data/semantic_layers/")
    print(f"2. Supabase: Restore from {backup_file}")
    print("3. Pinecone: Re-run scripts/embed_semantic_layers.py")
    print()

if __name__ == '__main__':
    main()
