#!/usr/bin/env python3
"""
Test A: Temperature Determinism Checker

Tests if temperature=0.0 produces deterministic results by:
1. Selecting 5 test questions from different databases
2. Running each question 10 times with IDENTICAL semantic context
3. Checking if SQL output is 100% identical across all 10 runs

Expected Result:
- If 100% identical: Temperature=0.0 is deterministic, variance is from RAG
- If variance exists: Model has inherent randomness even at temp=0.0
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import json
from collections import defaultdict

# Load environment
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.llm.config import LLMConfig
from app.services.llm.prompts import PromptTemplates
from app.services.text_to_sql.enhanced import EnhancedSQLGenerator
from app.database.metadata_store import get_metadata_store
from app.config import get_settings


# Test questions from different databases
TEST_QUESTIONS = [
    {
        "database": "car_1",
        "question": "What is the maximum horsepower of all cars?",
        "db_type": "sqlite"
    },
    {
        "database": "flight_2",
        "question": "How many flights are there?",
        "db_type": "sqlite"
    },
    {
        "database": "pets_1",
        "question": "Find the average weight of pets",
        "db_type": "sqlite"
    },
    {
        "database": "world_1",
        "question": "What are the top 5 most populous countries?",
        "db_type": "sqlite"
    },
    {
        "database": "dog_kennels",
        "question": "How many dogs are in the database?",
        "db_type": "sqlite"
    }
]


def test_question_determinism(test_case: dict, iterations: int = 10) -> dict:
    """
    Test determinism for a single question by running it multiple times
    with FIXED semantic context.

    Args:
        test_case: Dictionary with database, question, db_type
        iterations: Number of times to run the test (default: 10)

    Returns:
        Dictionary with test results
    """
    database = test_case["database"]
    question = test_case["question"]
    db_type = test_case["db_type"]

    print(f"\n{'=' * 80}")
    print(f"Testing: {database} - {question}")
    print(f"{'=' * 80}")

    # Initialize generator (this will cache schema and semantic layer)
    # Use use_vector_search=False to get FULL semantic layer (not RAG retrieval)
    generator = EnhancedSQLGenerator(
        database_url=f"file:data/spider/database/{database}/{database}.sqlite",
        database_name=database,
        connection_name="Supabase",
        use_vector_search=False,  # Use full semantic layer for consistency
        db_type=db_type
    )

    # Get schema and semantic context ONCE
    schema = generator._get_schema()
    semantic_context = generator._get_semantic_context(question)

    print(f"✓ Retrieved schema ({len(schema.get('tables', []))} tables)")
    if semantic_context:
        print(f"✓ Retrieved semantic context ({len(semantic_context)} chars)")
    else:
        print(f"⚠ No semantic context available")

    # Build prompts ONCE (these will be identical for all iterations)
    system_prompt = PromptTemplates.enhanced_sql_system(db_type=db_type)
    user_prompt = PromptTemplates.enhanced_sql_user_with_context(
        question, schema, semantic_context, db_type=db_type
    )

    print(f"✓ Built prompts (system: {len(system_prompt)} chars, user: {len(user_prompt)} chars)")

    # Get LLM provider and config
    llm = LLMConfig.get_provider_for_task("enhanced_sql")
    config = LLMConfig.get_task_config("enhanced_sql")

    print(f"✓ LLM: {config.get('model')} (temp={config.get('temperature')})")
    print(f"\nRunning {iterations} iterations with IDENTICAL prompts...")

    # Run iterations with IDENTICAL prompts
    sql_outputs = []
    for i in range(iterations):
        response = llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=config["temperature"],
            max_tokens=config.get("max_tokens")
        )
        sql_outputs.append(response.content.strip())
        print(f"  Iteration {i+1}/{iterations}: {len(response.content)} chars")

    # Analyze variance
    unique_outputs = set(sql_outputs)
    is_deterministic = len(unique_outputs) == 1

    print(f"\n{'=' * 80}")
    print(f"RESULTS:")
    print(f"{'=' * 80}")
    print(f"Total iterations: {iterations}")
    print(f"Unique SQL outputs: {len(unique_outputs)}")

    if is_deterministic:
        print(f"✅ DETERMINISTIC: All {iterations} iterations produced identical SQL")
    else:
        print(f"❌ NON-DETERMINISTIC: {len(unique_outputs)} different SQL outputs")
        print(f"\nOutput frequency:")
        output_freq = defaultdict(int)
        for sql in sql_outputs:
            output_freq[sql] = output_freq[sql] + 1

        for i, (sql, count) in enumerate(sorted(output_freq.items(), key=lambda x: x[1], reverse=True)):
            print(f"\n  Variant {i+1} (appeared {count}/{iterations} times):")
            print(f"  {sql[:200]}{'...' if len(sql) > 200 else ''}")

    return {
        "database": database,
        "question": question,
        "iterations": iterations,
        "unique_outputs": len(unique_outputs),
        "is_deterministic": is_deterministic,
        "outputs": sql_outputs,
        "temperature": config.get("temperature")
    }


def main():
    print("=" * 80)
    print("TEST A: TEMPERATURE DETERMINISM CHECKER")
    print("=" * 80)
    print(f"\nGoal: Verify if temperature=0.0 produces deterministic results")
    print(f"Method: Run 5 questions × 10 iterations with FIXED semantic context")
    print(f"\nTest Questions: {len(TEST_QUESTIONS)}")

    results = []

    # Test each question
    for test_case in TEST_QUESTIONS:
        try:
            result = test_question_determinism(test_case, iterations=10)
            results.append(result)
        except Exception as e:
            print(f"\n❌ Error testing {test_case['database']}: {e}")
            results.append({
                "database": test_case["database"],
                "question": test_case["question"],
                "error": str(e),
                "is_deterministic": False
            })

    # Overall summary
    print(f"\n{'=' * 80}")
    print(f"OVERALL SUMMARY")
    print(f"{'=' * 80}")

    deterministic_count = sum(1 for r in results if r.get("is_deterministic", False))
    total_count = len(results)

    print(f"\nDeterministic questions: {deterministic_count}/{total_count}")

    if deterministic_count == total_count:
        print(f"\n✅ CONCLUSION: Temperature=0.0 is FULLY DETERMINISTIC")
        print(f"   → Whack-a-mole effect is caused by RAG retrieval variance, NOT LLM randomness")
        print(f"   → Next step: Test B (RAG Stability)")
    elif deterministic_count > 0:
        print(f"\n⚠️  CONCLUSION: Temperature=0.0 is PARTIALLY DETERMINISTIC")
        print(f"   → {deterministic_count} questions were deterministic, {total_count - deterministic_count} were not")
        print(f"   → May indicate edge cases or specific prompt patterns causing variance")
    else:
        print(f"\n❌ CONCLUSION: Temperature=0.0 is NON-DETERMINISTIC")
        print(f"   → Model has inherent randomness even at temp=0.0")
        print(f"   → Consider testing 'seed' parameter or different model")

    # Save results
    output_file = Path(__file__).parent.parent / "logs" / "test_temperature_determinism_results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump({
            "test": "temperature_determinism",
            "temperature": results[0].get("temperature", 0.0) if results else 0.0,
            "total_questions": total_count,
            "deterministic_count": deterministic_count,
            "results": results
        }, f, indent=2)

    print(f"\n✓ Results saved to: {output_file}")


if __name__ == "__main__":
    main()
