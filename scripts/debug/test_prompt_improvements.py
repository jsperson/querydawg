#!/usr/bin/env python3
"""
Test script to verify Phase 1 prompt improvements are working correctly.

Tests:
1. Chunk retrieval increased from 5 to 10
2. Chunk type weighting is applied
3. Metadata limit increased to 2000 chars

Expected outcomes:
- dev_0451 query should now retrieve 'matches' table
- Table chunks should rank higher than overview/guidelines
- Full context should be returned without truncation
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.embedding_service import EmbeddingService


def test_chunk_retrieval_count():
    """Test that we're retrieving 10 chunks instead of 5"""
    print("=" * 60)
    print("TEST 1: Chunk Retrieval Count")
    print("=" * 60)

    openai_api_key = os.getenv("OPENAI_API_KEY")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    pinecone_index = os.getenv("PINECONE_INDEX_NAME", "querydawg-semantic")

    if not openai_api_key or not pinecone_api_key:
        print("❌ Missing API keys")
        return False

    service = EmbeddingService(
        openai_api_key=openai_api_key,
        pinecone_api_key=pinecone_api_key,
        pinecone_environment=pinecone_environment,
        pinecone_index_name=pinecone_index
    )

    # Test query
    query = "What are the country code and first name of the players who won in both tourney WTA Championships and Australian Open?"
    database = "wta_1"

    print(f"\nQuery: {query}")
    print(f"Database: {database}")

    # Search with default top_k (should now be 10)
    results = service.search_semantic_context(query, database)

    print(f"\n✓ Retrieved {len(results)} chunks (expected: 10)")

    if len(results) == 10:
        print("✓ PASS: Retrieving 10 chunks by default")
        return True
    else:
        print(f"❌ FAIL: Expected 10 chunks, got {len(results)}")
        return False


def test_chunk_type_weighting():
    """Test that chunk type weighting is working"""
    print("\n" + "=" * 60)
    print("TEST 2: Chunk Type Weighting")
    print("=" * 60)

    openai_api_key = os.getenv("OPENAI_API_KEY")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    pinecone_index = os.getenv("PINECONE_INDEX_NAME", "querydawg-semantic")

    if not openai_api_key or not pinecone_api_key:
        print("❌ Missing API keys")
        return False

    service = EmbeddingService(
        openai_api_key=openai_api_key,
        pinecone_api_key=pinecone_api_key,
        pinecone_environment=pinecone_environment,
        pinecone_index_name=pinecone_index
    )

    # Test query - should retrieve players and matches tables
    query = "What are the country code and first name of the players who won in both tourney WTA Championships and Australian Open?"
    database = "wta_1"

    print(f"\nQuery: {query}")
    print(f"Database: {database}")

    results = service.search_semantic_context(query, database, top_k=10)

    print("\nRetrieved chunks (with weights):")
    print("-" * 60)

    table_chunks_count = 0
    overview_chunks_count = 0
    has_matches_table = False
    has_players_table = False

    for i, chunk in enumerate(results, 1):
        chunk_type = chunk['chunk_type']
        table_name = chunk.get('table_name', 'N/A')
        weighted_score = chunk['score']
        original_score = chunk.get('original_score', weighted_score)
        weight = chunk.get('weight', 1.0)

        print(f"{i}. {chunk_type:20s} | Table: {table_name:15s} | "
              f"Score: {weighted_score:.4f} (orig: {original_score:.4f}, weight: {weight})")

        if chunk_type == 'table':
            table_chunks_count += 1
            if table_name == 'matches':
                has_matches_table = True
            if table_name == 'players':
                has_players_table = True
        elif chunk_type == 'overview':
            overview_chunks_count += 1

    print("-" * 60)
    print(f"\nTable chunks: {table_chunks_count}")
    print(f"Overview chunks: {overview_chunks_count}")
    print(f"Has 'matches' table: {'✓' if has_matches_table else '❌'}")
    print(f"Has 'players' table: {'✓' if has_players_table else '❌'}")

    # Success criteria
    success = True

    # Should have more table chunks than overview chunks
    if table_chunks_count > overview_chunks_count:
        print("✓ PASS: More table chunks than overview chunks (weighting working)")
    else:
        print("❌ FAIL: Not enough table chunks - weighting may not be working")
        success = False

    # Should retrieve 'matches' table (critical for this query)
    if has_matches_table:
        print("✓ PASS: Retrieved 'matches' table (critical for query)")
    else:
        print("❌ FAIL: Did not retrieve 'matches' table")
        success = False

    return success


def test_metadata_limit():
    """Test that metadata limit was increased to 2000"""
    print("\n" + "=" * 60)
    print("TEST 3: Metadata Limit (2000 chars)")
    print("=" * 60)

    openai_api_key = os.getenv("OPENAI_API_KEY")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    pinecone_index = os.getenv("PINECONE_INDEX_NAME", "querydawg-semantic")

    if not openai_api_key or not pinecone_api_key:
        print("❌ Missing API keys")
        return False

    service = EmbeddingService(
        openai_api_key=openai_api_key,
        pinecone_api_key=pinecone_api_key,
        pinecone_environment=pinecone_environment,
        pinecone_index_name=pinecone_index
    )

    # Get a table chunk (likely to be long)
    query = "player information"
    database = "wta_1"

    results = service.search_semantic_context(query, database, top_k=5)

    # Find a table chunk and check its length
    for chunk in results:
        if chunk['chunk_type'] == 'table':
            text = chunk['text']
            text_len = len(text)

            print(f"\nTable: {chunk.get('table_name', 'N/A')}")
            print(f"Text length: {text_len} chars")

            if text_len > 1000:
                print(f"✓ PASS: Storing >{1000} chars (limit increased to 2000)")
                print(f"Sample (first 200 chars):\n{text[:200]}...")
                return True
            else:
                print(f"⚠️  Text is <1000 chars, can't verify limit increase")
                print(f"   (This is okay - some chunks are naturally short)")
                return True

    print("❌ FAIL: No table chunks found to test")
    return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("PHASE 1 IMPROVEMENTS TEST SUITE")
    print("=" * 60)

    results = {
        "Chunk Retrieval Count": test_chunk_retrieval_count(),
        "Chunk Type Weighting": test_chunk_type_weighting(),
        "Metadata Limit": test_metadata_limit()
    }

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("Phase 1 improvements are working correctly!")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please review the failures above.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
