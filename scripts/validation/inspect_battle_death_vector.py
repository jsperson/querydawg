#!/usr/bin/env python3
"""
Inspect the actual content of battle_death vectors to see what's there.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from pinecone import Pinecone

def inspect_battle_death():
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'querydawg-semantic')
    
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    
    # Fetch battle_death vectors
    results = index.query(
        vector=[0.0] * 1536,
        filter={'database': 'battle_death'},
        top_k=3,
        include_metadata=True
    )
    
    print("=" * 70)
    print("BATTLE_DEATH VECTOR CONTENT INSPECTION")
    print("=" * 70)
    
    for i, match in enumerate(results['matches'], 1):
        metadata = match.get('metadata', {})
        text = metadata.get('text', '')
        chunk_type = metadata.get('chunk_type', '')
        timestamp = metadata.get('timestamp', 'unknown')
        
        print(f"\nVector {i}:")
        print(f"  Chunk type: {chunk_type}")
        print(f"  Timestamp: {timestamp}")
        print(f"  Text length: {len(text)} chars")
        print(f"  First 300 chars:")
        print(f"  {text[:300]}")
        print(f"  ...")
        
        # Check for specific Phase 2 keywords
        if 'is_bridge_table' in text:
            print(f"  ✓ HAS Phase 2: is_bridge_table")
        if 'disambiguation' in text.lower():
            print(f"  ✓ HAS Phase 2: disambiguation")
        if 'relationship_type' in text:
            print(f"  ? Has relationship_type (could be Phase 1 or 2)")

if __name__ == '__main__':
    inspect_battle_death()
