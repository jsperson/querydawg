#!/usr/bin/env python3
"""
Full Spider Benchmark Runner

Runs the complete Spider 1.0 benchmark on all databases.
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
    print("=" * 80)
    print("FULL SPIDER 1.0 BENCHMARK - RUN 19")
    print("Testing semantic layers with Spider FK metadata enrichment")
    print("=" * 80)
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
        budget_limit_usd=5.00,  # Increased budget for full run
        connection_string=database_url
    )
    print("✅ Runner initialized")
    print()

    # Configure full run
    print("[ 3/4 ] Configuring Full Spider 1.0 Run 19...")
    config = BenchmarkConfig(
        name="Full Spider 1.0 Run 19 - Spider FK Metadata",
        run_type="both",  # Both baseline and enhanced
        databases=None,  # All databases
        question_limit=None  # All questions (1,034 total)
    )
    print(f"   Name: {config.name}")
    print(f"   Type: {config.run_type}")
    print(f"   Databases: All Spider 1.0 databases (20)")
    print(f"   Questions: All questions (1,034 total)")
    print(f"   Budget limit: $5.00")
    print()

    print("Expected improvements from Spider FK enrichment:")
    print("  - car_1: FK relationships now documented (cars_data.id -> car_names.makeid)")
    print("  - flight_2: FK relationships now documented")
    print("  - All databases: More complete relationship documentation")
    print()

    # Run benchmark
    print("[ 4/4 ] Running full benchmark...")
    print("This will take approximately 45-90 minutes")
    print("-" * 80)
    try:
        run_id = runner.run_benchmark(config)
        print("-" * 80)
        print()
        print("✅ Benchmark completed successfully!")
        print(f"   Run ID: {run_id}")
        print()

        # Get summary
        summary = store.get_run_summary(run_id)
        if summary:
            print("=" * 80)
            print("📊 RUN 19 RESULTS SUMMARY")
            print("=" * 80)
            print(f"Status: {summary.status}")
            print(f"Completed: {summary.completed}/{summary.total_questions}")
            print(f"Failed: {summary.failed}")
            print()

            if summary.baseline_exact_match_rate is not None:
                baseline_pct = summary.baseline_exact_match_rate * 100
                print(f"BASELINE:")
                print(f"  Exact Match: {baseline_pct:.2f}%")
                print(f"  Total Cost: ${summary.baseline_total_cost:.4f}")
                print()

            if summary.enhanced_exact_match_rate is not None:
                enhanced_pct = summary.enhanced_exact_match_rate * 100
                print(f"ENHANCED (with Spider FK metadata):")
                print(f"  Exact Match: {enhanced_pct:.2f}%")
                print(f"  Total Cost: ${summary.enhanced_total_cost:.4f}")
                print()

                if summary.baseline_exact_match_rate is not None:
                    delta = enhanced_pct - baseline_pct
                    delta_str = f"+{delta:.2f}%" if delta >= 0 else f"{delta:.2f}%"
                    print(f"IMPROVEMENT: {delta_str}")
                    print()

            print("=" * 80)
            print()

        print("🎉 Run 19 completed!")
        print(f"   View detailed results at: benchmark_reports/run_{run_id}.md")
        return 0

    except Exception as e:
        print("-" * 80)
        print()
        print(f"❌ Benchmark failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
