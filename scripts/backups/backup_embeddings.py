#!/usr/bin/env python3
"""
Backup current semantic layer embeddings to a timestamped backup table.
This allows comparing embeddings before and after regeneration.
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database.supabase_client import SupabaseClient

def backup_embeddings():
    """Backup semantic_layer_chunks to a timestamped backup table"""

    # Get credentials
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not service_role_key:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)

    # Initialize client
    sb_client = SupabaseClient(supabase_url, service_role_key)
    supabase = sb_client.client

    # Generate backup table name with timestamp
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_table = f"semantic_layer_chunks_backup_{timestamp}"

    print(f"Creating backup table: {backup_table}")

    # Get current row count
    result = supabase.table('semantic_layer_chunks').select('id', count='exact').execute()
    total_rows = result.count
    print(f"Total rows to backup: {total_rows}")

    if total_rows == 0:
        print("WARNING: No rows found in semantic_layer_chunks")
        return

    # SQL to create backup table (run via SQL editor or use RPC)
    create_table_sql = f"""
CREATE TABLE {backup_table} AS
SELECT * FROM semantic_layer_chunks;

-- Add comment to explain what this is
COMMENT ON TABLE {backup_table} IS 'Backup of semantic_layer_chunks before Phase 2 regeneration at {timestamp}';
"""

    print("\nTo create the backup table, run this SQL in your Supabase SQL Editor:")
    print("=" * 70)
    print(create_table_sql)
    print("=" * 70)

    # Alternative: Export to JSON file
    print("\nAlternatively, exporting embeddings to JSON file...")

    # Fetch all chunks (paginate if needed)
    all_chunks = []
    page_size = 1000
    offset = 0

    while offset < total_rows:
        result = supabase.table('semantic_layer_chunks')\
            .select('*')\
            .range(offset, offset + page_size - 1)\
            .execute()

        all_chunks.extend(result.data)
        offset += page_size
        print(f"Exported {len(all_chunks)}/{total_rows} rows...")

    # Save to JSON
    import json
    backup_file = f"data/semantic_layer_chunks_backup_{timestamp}.json"

    # Make data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)

    with open(backup_file, 'w') as f:
        json.dump({
            'backup_timestamp': timestamp,
            'total_rows': len(all_chunks),
            'chunks': all_chunks
        }, f, indent=2)

    print(f"\n✅ Backup saved to: {backup_file}")
    print(f"   Total rows: {len(all_chunks)}")
    print(f"   File size: {os.path.getsize(backup_file) / 1024 / 1024:.2f} MB")

    return backup_file

if __name__ == '__main__':
    backup_file = backup_embeddings()

    print("\n" + "=" * 70)
    print("BACKUP COMPLETE")
    print("=" * 70)
    print(f"Git tag: phase1-semantic-layers")
    print(f"Embeddings backup: {backup_file}")
    print("\nTo restore from this backup:")
    print("1. Git: git checkout phase1-semantic-layers -- data/semantic_layers/")
    print(f"2. Embeddings: Use the JSON file to restore or rerun embed_semantic_layers.py")
