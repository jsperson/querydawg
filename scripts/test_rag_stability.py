#!/usr/bin/env python3
"""
Test B: RAG Retrieval Stability Tester

Tests if RAG retrieval is stable across runs by:
1. Selecting 5 test questions from different databases
2. Running RAG retrieval 10 times per question
3. Measuring variance in:
   - Query embeddings (do they change?)
   - Retrieved chunks (do chunk IDs change?)
   - Similarity scores (do scores vary?)
   - Chunk order (does ranking change?)

Expected Result:
- If retrieval varies: RAG is source of whack-a-mole effect
- If retrieval is stable: Variance is elsewhere (LLM, other factors)
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import json
import numpy as np
from collections import defaultdict

# Load environment
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.embedding_service import EmbeddingService
from app.config import get_settings


# Same test questions as Test A
TEST_QUESTIONS = [
    {
        "database": "car_1",
        "question": "What is the maximum horsepower of all cars?"
    },
    {
        "database": "flight_2",
        "question": "How many flights are there?"
    },
    {
        "database": "pets_1",
        "question": "Find the average weight of pets"
    },
    {
        "database": "world_1",
        "question": "What are the top 5 most populous countries?"
    },
    {
        "database": "dog_kennels",
        "question": "How many dogs are in the database?"
    }
]


def cosine_similarity(vec1: list, vec2: list) -> float:
    """Calculate cosine similarity between two vectors."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def test_query_embedding_stability(embedding_service: EmbeddingService, question: str, iterations: int = 10) -> dict:
    """
    Test if query embeddings are deterministic.

    Args:
        embedding_service: EmbeddingService instance
        question: Query to embed
        iterations: Number of times to embed the same query

    Returns:
        Dictionary with embedding stability metrics
    """
    print(f"  Testing query embedding stability ({iterations} iterations)...")

    embeddings = []
    for i in range(iterations):
        embedding = embedding_service.embed_text(question)
        embeddings.append(embedding)

    # Check if all embeddings are identical
    first_embedding = embeddings[0]
    all_identical = all(embedding == first_embedding for embedding in embeddings)

    # Calculate pairwise cosine similarities
    similarities = []
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            similarities.append(sim)

    avg_similarity = np.mean(similarities) if similarities else 1.0
    min_similarity = np.min(similarities) if similarities else 1.0
    max_similarity = np.max(similarities) if similarities else 1.0

    print(f"    ✓ All embeddings identical: {all_identical}")
    if not all_identical:
        print(f"    ⚠ Similarity range: {min_similarity:.6f} - {max_similarity:.6f} (avg: {avg_similarity:.6f})")

    return {
        "all_identical": all_identical,
        "avg_similarity": avg_similarity,
        "min_similarity": min_similarity,
        "max_similarity": max_similarity
    }


def test_rag_retrieval_stability(test_case: dict, iterations: int = 10, top_k: int = 10) -> dict:
    """
    Test RAG retrieval stability for a single question.

    Args:
        test_case: Dictionary with database and question
        iterations: Number of times to run retrieval (default: 10)
        top_k: Number of chunks to retrieve per iteration

    Returns:
        Dictionary with stability metrics
    """
    database = test_case["database"]
    question = test_case["question"]

    print(f"\n{'=' * 80}")
    print(f"Testing: {database} - {question}")
    print(f"{'=' * 80}")

    # Initialize embedding service
    settings = get_settings()
    embedding_service = EmbeddingService(
        openai_api_key=settings.openai_api_key,
        pinecone_api_key=settings.pinecone_api_key,
        pinecone_environment=settings.pinecone_environment,
        pinecone_index_name=settings.pinecone_index_name
    )

    # Test 1: Query embedding stability
    embedding_stability = test_query_embedding_stability(embedding_service, question, iterations=iterations)

    # Test 2: RAG retrieval stability
    print(f"  Testing RAG retrieval stability ({iterations} iterations)...")

    all_retrievals = []
    for i in range(iterations):
        chunks = embedding_service.search_semantic_context(
            query=question,
            database_name=database,
            top_k=top_k
        )
        all_retrievals.append(chunks)

        # Show first iteration details
        if i == 0:
            print(f"    ✓ Retrieved {len(chunks)} chunks")

    # Analyze retrieval variance
    # 1. Check if chunk types are consistent
    chunk_type_sequences = []
    for retrieval in all_retrievals:
        chunk_types = [chunk['chunk_type'] for chunk in retrieval]
        chunk_type_sequences.append(tuple(chunk_types))

    unique_sequences = set(chunk_type_sequences)
    sequence_stability = len(unique_sequences) == 1

    # 2. Check if chunk text is consistent
    chunk_text_sequences = []
    for retrieval in all_retrievals:
        chunk_texts = [chunk['text'][:100] for chunk in retrieval]  # First 100 chars
        chunk_text_sequences.append(tuple(chunk_texts))

    unique_text_sequences = set(chunk_text_sequences)
    text_stability = len(unique_text_sequences) == 1

    # 3. Check score variance
    all_scores = []
    for retrieval in all_retrievals:
        scores = [chunk['score'] for chunk in retrieval]
        all_scores.append(scores)

    # Calculate score variance for each position
    position_variances = []
    for pos in range(len(all_scores[0]) if all_scores else 0):
        scores_at_pos = [scores[pos] for scores in all_scores if len(scores) > pos]
        if scores_at_pos:
            variance = np.var(scores_at_pos)
            position_variances.append(variance)

    avg_score_variance = np.mean(position_variances) if position_variances else 0.0
    max_score_variance = np.max(position_variances) if position_variances else 0.0

    # 4. Overall stability assessment
    is_fully_stable = sequence_stability and text_stability and avg_score_variance < 1e-6

    print(f"\n{'=' * 80}")
    print(f"RESULTS:")
    print(f"{'=' * 80}")
    print(f"Embedding Stability:")
    print(f"  All embeddings identical: {embedding_stability['all_identical']}")
    if not embedding_stability['all_identical']:
        print(f"  Avg similarity: {embedding_stability['avg_similarity']:.6f}")
    print(f"\nRetrieval Stability:")
    print(f"  Chunk type sequences: {len(unique_sequences)} unique (out of {iterations})")
    print(f"  Chunk text sequences: {len(unique_text_sequences)} unique (out of {iterations})")
    print(f"  Score variance (avg): {avg_score_variance:.8f}")
    print(f"  Score variance (max): {max_score_variance:.8f}")

    if is_fully_stable:
        print(f"\n✅ FULLY STABLE: RAG retrieval is deterministic")
        print(f"   → Whack-a-mole is NOT caused by RAG variance")
    elif sequence_stability and text_stability:
        print(f"\n⚠️  MOSTLY STABLE: Same chunks retrieved, but scores vary slightly")
        print(f"   → Score variance: {avg_score_variance:.8f}")
        print(f"   → May cause minor ranking differences")
    else:
        print(f"\n❌ UNSTABLE: RAG retrieval varies between runs")
        print(f"   → Chunk sequences vary: {len(unique_sequences)} different patterns")
        print(f"   → Text sequences vary: {len(unique_text_sequences)} different patterns")
        print(f"   → This is likely causing whack-a-mole effect")

    # Show variance details if unstable
    if not sequence_stability:
        print(f"\n  Chunk type sequence variance:")
        seq_freq = defaultdict(int)
        for seq in chunk_type_sequences:
            seq_freq[seq] += 1
        for i, (seq, count) in enumerate(sorted(seq_freq.items(), key=lambda x: x[1], reverse=True)[:3]):
            print(f"    Pattern {i+1} ({count}/{iterations} times): {seq}")

    return {
        "database": database,
        "question": question,
        "iterations": iterations,
        "embedding_stability": embedding_stability,
        "chunk_type_sequences": len(unique_sequences),
        "chunk_text_sequences": len(unique_text_sequences),
        "avg_score_variance": float(avg_score_variance),
        "max_score_variance": float(max_score_variance),
        "is_fully_stable": is_fully_stable,
        "is_sequence_stable": sequence_stability,
        "is_text_stable": text_stability,
        "sample_retrieval": [
            {
                "chunk_type": chunk['chunk_type'],
                "table_name": chunk.get('table_name'),
                "score": chunk['score'],
                "original_score": chunk.get('original_score'),
                "weight": chunk.get('weight')
            }
            for chunk in all_retrievals[0]
        ] if all_retrievals else []
    }


def main():
    print("=" * 80)
    print("TEST B: RAG RETRIEVAL STABILITY TESTER")
    print("=" * 80)
    print(f"\nGoal: Measure RAG retrieval variance across runs")
    print(f"Method: Run 5 questions × 10 iterations, measure chunk/score variance")
    print(f"\nTest Questions: {len(TEST_QUESTIONS)}")

    results = []

    # Test each question
    for test_case in TEST_QUESTIONS:
        try:
            result = test_rag_retrieval_stability(test_case, iterations=10, top_k=10)
            results.append(result)
        except Exception as e:
            print(f"\n❌ Error testing {test_case['database']}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "database": test_case["database"],
                "question": test_case["question"],
                "error": str(e),
                "is_fully_stable": False
            })

    # Overall summary
    print(f"\n{'=' * 80}")
    print(f"OVERALL SUMMARY")
    print(f"{'=' * 80}")

    stable_count = sum(1 for r in results if r.get("is_fully_stable", False))
    sequence_stable_count = sum(1 for r in results if r.get("is_sequence_stable", False))
    total_count = len(results)

    print(f"\nFully stable questions: {stable_count}/{total_count}")
    print(f"Sequence stable (chunks consistent): {sequence_stable_count}/{total_count}")

    # Calculate average score variance across all questions
    avg_score_variances = [r.get("avg_score_variance", 0) for r in results if "avg_score_variance" in r]
    overall_avg_variance = np.mean(avg_score_variances) if avg_score_variances else 0.0

    print(f"Overall avg score variance: {overall_avg_variance:.8f}")

    # Conclusion
    if stable_count == total_count:
        print(f"\n✅ CONCLUSION: RAG retrieval is FULLY DETERMINISTIC")
        print(f"   → Embeddings are stable")
        print(f"   → Retrieved chunks are consistent")
        print(f"   → Scores are consistent")
        print(f"   → Whack-a-mole is NOT caused by RAG variance")
        print(f"   → Consider: Model non-determinism, prompt variance, or natural variance")
    elif sequence_stable_count == total_count:
        print(f"\n⚠️  CONCLUSION: RAG retrieval is SEQUENCE STABLE but scores vary")
        print(f"   → Same chunks retrieved every time")
        print(f"   → But similarity scores vary slightly")
        print(f"   → May cause minor ranking differences")
        print(f"   → Avg variance: {overall_avg_variance:.8f}")
        print(f"   → Impact on whack-a-mole: LOW (same chunks, just different scores)")
    else:
        print(f"\n❌ CONCLUSION: RAG retrieval is UNSTABLE")
        print(f"   → {total_count - sequence_stable_count} questions had varying chunk sequences")
        print(f"   → This IS causing whack-a-mole effect")
        print(f"   → Recommendations:")
        print(f"      1. Add semantic layer caching (cache retrieved chunks per question)")
        print(f"      2. Use deterministic re-ranking")
        print(f"      3. Fix embedding variance (if embeddings are unstable)")

    # Save results
    output_file = Path(__file__).parent.parent / "logs" / "test_rag_stability_results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump({
            "test": "rag_stability",
            "total_questions": total_count,
            "fully_stable_count": stable_count,
            "sequence_stable_count": sequence_stable_count,
            "overall_avg_score_variance": overall_avg_variance,
            "results": results
        }, f, indent=2)

    print(f"\n✓ Results saved to: {output_file}")


if __name__ == "__main__":
    main()
