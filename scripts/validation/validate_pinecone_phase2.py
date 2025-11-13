#!/usr/bin/env python3
"""
Validate that Pinecone vectors contain Phase 2 semantic layer content.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from pinecone import Pinecone

def validate_pinecone_phase2():
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'querydawg-semantic')
    
    if not api_key:
        print("ERROR: PINECONE_API_KEY not found")
        return
    
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    
    print("=" * 70)
    print("VALIDATING PINECONE PHASE 2 EMBEDDINGS")
    print("=" * 70)
    
    # Query for a specific database that should have Phase 2 features
    # Let's check concert_singer which has bridge tables
    results = index.query(
        vector=[0.0] * 1536,  # Dummy vector
        filter={'database_name': 'concert_singer'},
        top_k=10,
        include_metadata=True
    )
    
    print(f"\nQueried for concert_singer chunks:")
    print(f"Found {len(results['matches'])} chunks")
    
    if not results['matches']:
        print("⚠️  WARNING: No concert_singer chunks found in Pinecone")
        return
    
    # Check metadata for Phase 2 indicators
    phase2_indicators = {
        'has_bridge_table_content': False,
        'has_disambiguation_content': False,
        'chunks_checked': 0
    }
    
    for match in results['matches']:
        metadata = match.get('metadata', {})
        content = metadata.get('content', '')
        chunk_type = metadata.get('chunk_type', '')
        
        phase2_indicators['chunks_checked'] += 1
        
        # Check for Phase 2 keywords
        if 'is_bridge_table' in content or 'bridge table' in content.lower():
            phase2_indicators['has_bridge_table_content'] = True
            print(f"\n✓ Found bridge table content in {chunk_type} chunk")
            print(f"  Excerpt: {content[:200]}...")
        
        if 'disambiguation' in content.lower() or 'appears_in_tables' in content:
            phase2_indicators['has_disambiguation_content'] = True
            print(f"\n✓ Found disambiguation content in {chunk_type} chunk")
            print(f"  Excerpt: {content[:200]}...")
    
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    print(f"Chunks checked: {phase2_indicators['chunks_checked']}")
    print(f"Bridge table content: {'✅ Found' if phase2_indicators['has_bridge_table_content'] else '❌ Not found'}")
    print(f"Disambiguation content: {'✅ Found' if phase2_indicators['has_disambiguation_content'] else '❌ Not found'}")
    
    if phase2_indicators['has_bridge_table_content'] or phase2_indicators['has_disambiguation_content']:
        print("\n✅ PHASE 2 EMBEDDINGS CONFIRMED IN PINECONE")
    else:
        print("\n⚠️  WARNING: Phase 2 features not detected in Pinecone vectors")
        print("This suggests Pinecone still has Phase 1 embeddings")
        print("You need to run embeddings with the updated script")
    
    print("=" * 70)

if __name__ == '__main__':
    validate_pinecone_phase2()
