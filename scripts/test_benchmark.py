#!/usr/bin/env python3
"""
CLI test script for benchmark system
Tests with 5-10 questions (smoke test)
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

from app.database.benchmark_store import get_benchmark_store
from app.services.benchmark_runner import BenchmarkRunner
from app.models.benchmark import BenchmarkConfig


def main():
    print("=" * 70)
    print("Benchmark System Smoke Test")
    print("=" * 70)
    print()

    # Get environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    database_url = os.getenv("DATABASE_URL")

    if not all([supabase_url, supabase_key, database_url]):
        print("❌ Missing environment variables")
        print("   Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL")
        return 1

    # Initialize store
    print("[ 1/4 ] Initializing benchmark store...")
    store = get_benchmark_store(supabase_url, supabase_key)
    print("✅ Store initialized")
    print()

    # Initialize runner
    print("[ 2/4 ] Initializing benchmark runner...")
    runner = BenchmarkRunner(
        benchmark_store=store,
        budget_limit_usd=0.50,  # Small budget for test
        connection_string=database_url
    )
    print("✅ Runner initialized")
    print()

    # Configure test run
    print("[ 3/4 ] Configuring test run...")
    config = BenchmarkConfig(
        name="Smoke Test - 5 Questions",
        run_type="both",  # Test both baseline and enhanced
        databases=["concert_singer"],  # Single database for speed
        question_limit=5  # Just 5 questions
    )
    print(f"   Name: {config.name}")
    print(f"   Type: {config.run_type}")
    print(f"   Database: {config.databases}")
    print(f"   Limit: {config.question_limit} questions")
    print()

    # Run benchmark
    print("[ 4/4 ] Running benchmark...")
    print("-" * 70)
    try:
        run_id = runner.run_benchmark(config)
        print("-" * 70)
        print()
        print("✅ Benchmark completed successfully!")
        print(f"   Run ID: {run_id}")
        print()

        # Get summary
        summary = store.get_run_summary(run_id)
        if summary:
            print("📊 Results Summary:")
            print(f"   Status: {summary.status}")
            print(f"   Completed: {summary.completed}/{summary.total_questions}")
            print(f"   Failed: {summary.failed}")
            print()

            if summary.baseline_exact_match_rate is not None:
                print(f"   Baseline Exact Match: {summary.baseline_exact_match_rate * 100:.1f}%")
                print(f"   Baseline Total Cost: ${summary.baseline_total_cost:.4f}")

            if summary.enhanced_exact_match_rate is not None:
                print(f"   Enhanced Exact Match: {summary.enhanced_exact_match_rate * 100:.1f}%")
                print(f"   Enhanced Total Cost: ${summary.enhanced_total_cost:.4f}")
            print()

        print("🎉 Test passed!")
        return 0

    except Exception as e:
        print("-" * 70)
        print()
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
