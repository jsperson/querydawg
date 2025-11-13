#!/usr/bin/env python3
"""
Check if Phase 2 semantic layers are deployed to Supabase and Pinecone.
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
from pinecone import Pinecone
import json

def check_supabase():
    """Check Supabase for Phase 2 fields."""
    print("=" * 70)
    print("CHECKING SUPABASE")
    print("=" * 70)

    # Connect to Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials!")
        return False

    supabase = create_client(supabase_url, supabase_key)

    # Get network_1 semantic layer
    result = supabase.table("semantic_layers").select("database_name, updated_at, semantic_layer").eq("database_name", "network_1").execute()

    if not result.data:
        print("❌ network_1 not found in Supabase!")
        return False

    layer = result.data[0]
    print(f"\nDatabase: {layer['database_name']}")
    print(f"Updated at: {layer['updated_at']}")

    # Check for Phase 2 fields
    sl = layer['semantic_layer']
    tables = sl.get('tables', [])

    # Look for Phase 2 relationship fields
    phase2_rel_found = False
    for table in tables:
        for rel in table.get('relationships', []):
            if 'join_pattern' in rel:
                phase2_rel_found = True
                print("\n✅ Phase 2 RELATIONSHIP fields found!")
                print(f"   join_pattern: {rel.get('join_pattern')}")
                print(f"   when_to_use: {rel.get('when_to_use', [])[:1]}")
                print(f"   vs_confusion: {rel.get('vs_confusion', 'N/A')[:50]}...")
                break
        if phase2_rel_found:
            break

    if not phase2_rel_found:
        print("\n⚠️  Phase 2 RELATIONSHIP fields NOT found!")
        print("   (Looking for: join_pattern, when_to_use, vs_confusion)")

    # Look for Phase 2 column disambiguation fields
    phase2_col_found = False
    for table in tables:
        for col in table.get('columns', []):
            disamb = col.get('disambiguation', {})
            if 'primary_location' in disamb:
                phase2_col_found = True
                print("\n✅ Phase 2 COLUMN disambiguation found!")
                print(f"   primary_location: {disamb.get('primary_location')}")
                print(f"   directional_guidance: {disamb.get('directional_guidance', 'N/A')[:50]}...")
                break
        if phase2_col_found:
            break

    if not phase2_col_found:
        print("\n⚠️  Phase 2 COLUMN disambiguation NOT found!")
        print("   (Looking for: primary_location, directional_guidance)")

    return phase2_rel_found and phase2_col_found

def check_pinecone():
    """Check Pinecone vector count."""
    print("\n" + "=" * 70)
    print("CHECKING PINECONE")
    print("=" * 70)

    # Connect to Pinecone
    pinecone_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_key:
        print("❌ Missing Pinecone API key!")
        return False

    pc = Pinecone(api_key=pinecone_key)
    index = pc.Index("querydawg-semantic-layers")

    # Get stats
    stats = index.describe_index_stats()
    total_vectors = stats.get('total_vector_count', 0)

    print(f"\nTotal vectors: {total_vectors}")

    # Query for network_1 to check embedding
    results = index.query(
        vector=[0.1] * 1536,  # Dummy vector
        filter={"database": {"$eq": "network_1"}},
        top_k=1,
        include_metadata=True
    )

    if results['matches']:
        match = results['matches'][0]
        print(f"\n✅ network_1 vectors found in Pinecone")
        print(f"   Chunk type: {match['metadata'].get('chunk_type')}")
        print(f"   Sample text: {match['metadata'].get('text', '')[:100]}...")
    else:
        print(f"\n⚠️  No network_1 vectors found in Pinecone!")

    # Expected: ~140 vectors (7 per database × 20 databases)
    if total_vectors >= 130 and total_vectors <= 150:
        print(f"\n✅ Vector count looks good ({total_vectors} vectors)")
        return True
    else:
        print(f"\n⚠️  Unexpected vector count: {total_vectors} (expected ~140)")
        return False

if __name__ == "__main__":
    supabase_ok = check_supabase()
    pinecone_ok = check_pinecone()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if supabase_ok and pinecone_ok:
        print("✅ Phase 2 deployment successful!")
        print("   - Supabase has Phase 2 semantic layers")
        print("   - Pinecone has embedded vectors")
        sys.exit(0)
    else:
        print("⚠️  Phase 2 deployment incomplete:")
        if not supabase_ok:
            print("   - Supabase missing Phase 2 fields")
        if not pinecone_ok:
            print("   - Pinecone vector count unexpected")
        sys.exit(1)
