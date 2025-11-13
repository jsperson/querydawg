#!/usr/bin/env python3
"""
Inspect actual Pinecone vector metadata to see structure.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from pinecone import Pinecone

def inspect_vectors():
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'querydawg-semantic')
    
    if not api_key:
        print("ERROR: PINECONE_API_KEY not found")
        return
    
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    
    print("=" * 70)
    print("INSPECTING PINECONE VECTOR METADATA")
    print("=" * 70)
    
    # Fetch some vectors to see their structure
    results = index.query(
        vector=[0.0] * 1536,
        top_k=5,
        include_metadata=True
    )
    
    print(f"\nFetched {len(results['matches'])} sample vectors\n")
    
    for i, match in enumerate(results['matches'], 1):
        print(f"Vector {i}:")
        print(f"  ID: {match['id']}")
        print(f"  Score: {match['score']:.4f}")
        
        metadata = match.get('metadata', {})
        print(f"  Metadata keys: {list(metadata.keys())}")
        
        # Print key metadata fields
        for key in ['database_name', 'database', 'chunk_type', 'chunk_index']:
            if key in metadata:
                print(f"    {key}: {metadata[key]}")
        
        # Check content for Phase 2 indicators
        content = metadata.get('content', '')
        if content:
            print(f"  Content length: {len(content)} chars")
            # Look for Phase 2 keywords
            if 'is_bridge_table' in content:
                print(f"    ✓ Contains 'is_bridge_table'")
            if 'disambiguation' in content.lower():
                print(f"    ✓ Contains 'disambiguation'")
            if 'complete_join_path' in content:
                print(f"    ✓ Contains 'complete_join_path'")
            
            # Show a snippet
            print(f"  Content preview: {content[:150]}...")
        
        print()

if __name__ == '__main__':
    inspect_vectors()
