#!/usr/bin/env python3
"""
Check if Pinecone has Phase 2 content.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from pinecone import Pinecone

def check_phase2():
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'querydawg-semantic')
    
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    
    print("=" * 70)
    print("CHECKING PINECONE FOR PHASE 2 CONTENT")
    print("=" * 70)
    
    # Fetch concert_singer and network_1 (databases with bridge tables)
    results = index.query(
        vector=[0.0] * 1536,
        filter={'database': {'$in': ['concert_singer', 'network_1']}},
        top_k=20,
        include_metadata=True
    )
    
    print(f"\nFetched {len(results['matches'])} chunks from concert_singer & network_1\n")
    
    phase2_found = {
        'bridge_table': False,
        'disambiguation': False,
        'complete_join_path': False,
        'common_mistakes': False
    }
    
    for match in results['matches']:
        metadata = match.get('metadata', {})
        text = metadata.get('text', '')
        db = metadata.get('database', '')
        chunk_type = metadata.get('chunk_type', '')
        
        # Check for Phase 2 indicators
        if 'is_bridge_table' in text:
            phase2_found['bridge_table'] = True
            print(f"✓ Found 'is_bridge_table' in {db} ({chunk_type})")
            print(f"  Excerpt: {text[:200]}...\n")
        
        if 'disambiguation' in text.lower():
            phase2_found['disambiguation'] = True
            print(f"✓ Found 'disambiguation' in {db} ({chunk_type})")
            print(f"  Excerpt: {text[:200]}...\n")
        
        if 'complete_join_path' in text:
            phase2_found['complete_join_path'] = True
            print(f"✓ Found 'complete_join_path' in {db} ({chunk_type})")
        
        if 'common_mistakes' in text.lower() and 'do not skip' in text.lower():
            phase2_found['common_mistakes'] = True
            print(f"✓ Found 'common_mistakes' in {db} ({chunk_type})")
    
    print("\n" + "=" * 70)
    print("PHASE 2 INDICATORS")
    print("=" * 70)
    print(f"Bridge table markers: {'✅ Found' if phase2_found['bridge_table'] else '❌ Not found'}")
    print(f"Column disambiguation: {'✅ Found' if phase2_found['disambiguation'] else '❌ Not found'}")
    print(f"Complete join paths: {'✅ Found' if phase2_found['complete_join_path'] else '❌ Not found'}")
    print(f"Common mistakes: {'✅ Found' if phase2_found['common_mistakes'] else '❌ Not found'}")
    
    if any(phase2_found.values()):
        print("\n✅ PHASE 2 CONTENT CONFIRMED IN PINECONE")
    else:
        print("\n❌ PHASE 2 CONTENT NOT FOUND IN PINECONE")
        print("Embeddings need to be regenerated with Phase 2 semantic layers")
    
    print("=" * 70)

if __name__ == '__main__':
    check_phase2()
