#!/usr/bin/env python3
"""
Check if battle_death has Phase 2 embeddings in Pinecone.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from pinecone import Pinecone

def check_battle_death():
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'querydawg-semantic')
    
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    
    print("=" * 70)
    print("CHECKING BATTLE_DEATH FOR PHASE 2 CONTENT")
    print("=" * 70)
    
    # Fetch battle_death chunks
    results = index.query(
        vector=[0.0] * 1536,
        filter={'database': 'battle_death'},
        top_k=20,
        include_metadata=True
    )
    
    print(f"\nFetched {len(results['matches'])} chunks for battle_death\n")
    
    if not results['matches']:
        print("⚠️  No battle_death chunks found in Pinecone")
        return
    
    phase2_found = {
        'is_bridge_table': False,
        'disambiguation': False,
        'complete_join_path': False,
        'common_mistakes': False
    }
    
    print("Checking chunks for Phase 2 indicators:\n")
    
    for match in results['matches']:
        metadata = match.get('metadata', {})
        text = metadata.get('text', '')
        chunk_type = metadata.get('chunk_type', '')
        
        print(f"  Chunk type: {chunk_type}")
        
        # Check for Phase 2 indicators
        if 'is_bridge_table' in text:
            phase2_found['is_bridge_table'] = True
            print(f"    ✓ Found 'is_bridge_table'")
        
        if 'disambiguation' in text.lower():
            phase2_found['disambiguation'] = True
            print(f"    ✓ Found 'disambiguation'")
        
        if 'complete_join_path' in text:
            phase2_found['complete_join_path'] = True
            print(f"    ✓ Found 'complete_join_path'")
        
        if 'common_mistakes' in text.lower():
            phase2_found['common_mistakes'] = True
            print(f"    ✓ Found 'common_mistakes'")
        
        # Show a snippet if Phase 2 content found
        if any([
            'is_bridge_table' in text,
            'disambiguation' in text.lower(),
            'complete_join_path' in text
        ]):
            print(f"    Preview: {text[:150]}...")
        
        print()
    
    print("=" * 70)
    print("PHASE 2 INDICATORS IN BATTLE_DEATH")
    print("=" * 70)
    print(f"Bridge table markers: {'✅ Found' if phase2_found['is_bridge_table'] else '❌ Not found'}")
    print(f"Column disambiguation: {'✅ Found' if phase2_found['disambiguation'] else '❌ Not found'}")
    print(f"Complete join paths: {'✅ Found' if phase2_found['complete_join_path'] else '❌ Not found'}")
    print(f"Common mistakes: {'✅ Found' if phase2_found['common_mistakes'] else '❌ Not found'}")
    
    if any(phase2_found.values()):
        print("\n✅ PHASE 2 CONTENT CONFIRMED FOR BATTLE_DEATH")
    else:
        print("\n❌ PHASE 2 CONTENT NOT FOUND FOR BATTLE_DEATH")
    
    print("=" * 70)

if __name__ == '__main__':
    check_battle_death()
