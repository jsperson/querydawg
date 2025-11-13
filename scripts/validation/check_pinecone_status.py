#!/usr/bin/env python3
"""
Check current Pinecone index status to see if Phase 2 embeddings are present.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from pinecone import Pinecone

def check_pinecone():
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'querydawg-semantic')
    
    if not api_key:
        print("ERROR: PINECONE_API_KEY not found")
        return
    
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    stats = index.describe_index_stats()
    
    print("=" * 70)
    print("PINECONE INDEX STATUS")
    print("=" * 70)
    print(f"Index: {index_name}")
    print(f"Total vectors: {stats.total_vector_count}")
    print(f"Dimensions: {stats.dimension}")
    
    if hasattr(stats, 'namespaces') and stats.namespaces:
        print("\nNamespaces:")
        for ns_name, ns_summary in stats.namespaces.items():
            ns_display = ns_name if ns_name else "(default)"
            count = ns_summary.vector_count if hasattr(ns_summary, 'vector_count') else 0
            print(f"  {ns_display}: {count} vectors")
    
    print("\n" + "=" * 70)
    print("EXPECTED FOR PHASE 2:")
    print("  - Should have ~180 vectors (20 databases × ~9 chunks each)")
    print("  - Vectors should be regenerated after semantic layer changes")
    print("=" * 70)

if __name__ == '__main__':
    check_pinecone()
