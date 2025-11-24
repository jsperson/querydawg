#!/usr/bin/env python3
"""
Analyze Run 23 results (Phase 2 RAG Optimization)
Compare to Run 22 baseline
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from supabase import create_client
from app.config import get_settings

settings = get_settings()
supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_run_id(run_name: str):
    """Get run ID by exact name."""
    response = supabase.table('benchmark_runs')\
        .select('id, name, created_at')\
        .eq('name', run_name)\
        .order('created_at', desc=True)\
        .limit(1)\
        .execute()

    if response.data:
        return response.data[0]['id']
    return None


def get_run_results(run_id: str):
    """Get all results for a run."""
    results = []
    offset = 0
    limit = 1000

    while True:
        response = supabase.table('benchmark_results')\
            .select('*')\
            .eq('run_id', run_id)\
            .range(offset, offset + limit - 1)\
            .execute()

        if not response.data:
            break

        results.extend(response.data)

        if len(response.data) < limit:
            break

        offset += limit

    return results


def analyze_results(run23_results, run22_results):
    """Analyze Run 23 vs Run 22."""

    # Group by database
    run23_by_db = defaultdict(list)
    run22_by_db = defaultdict(list)

    for r in run23_results:
        run23_by_db[r['database']].append(r)

    for r in run22_results:
        run22_by_db[r['database']].append(r)

    # Calculate overall stats
    run23_correct = sum(1 for r in run23_results if r.get('enhanced_exec_match'))
    run23_total = len(run23_results)
    run23_accuracy = (run23_correct / run23_total * 100) if run23_total > 0 else 0

    run22_correct = sum(1 for r in run22_results if r.get('enhanced_exec_match'))
    run22_total = len(run22_results)
    run22_accuracy = (run22_correct / run22_total * 100) if run22_total > 0 else 0

    print("="*80)
    print("RUN 23 ANALYSIS: Phase 2 RAG Optimization")
    print("="*80)
    print()

    print("OVERALL RESULTS:")
    print(f"  Run 22 (baseline):  {run22_correct}/{run22_total} ({run22_accuracy:.2f}%)")
    print(f"  Run 23 (optimized): {run23_correct}/{run23_total} ({run23_accuracy:.2f}%)")
    print()

    change = run23_correct - run22_correct
    change_pct = run23_accuracy - run22_accuracy

    if change > 0:
        print(f"  ✅ IMPROVEMENT: +{change} questions (+{change_pct:.2f}%)")
    elif change < 0:
        print(f"  ❌ REGRESSION: {change} questions ({change_pct:.2f}%)")
    else:
        print(f"  ➖ NO CHANGE: {change} questions ({change_pct:.2f}%)")
    print()

    # Per-database analysis
    print("="*80)
    print("PER-DATABASE CHANGES:")
    print("="*80)
    print()

    improvements = []
    regressions = []
    no_change = []

    all_databases = sorted(set(list(run23_by_db.keys()) + list(run22_by_db.keys())))

    for db in all_databases:
        run23_db = run23_by_db.get(db, [])
        run22_db = run22_by_db.get(db, [])

        run23_db_correct = sum(1 for r in run23_db if r.get('enhanced_exec_match'))
        run22_db_correct = sum(1 for r in run22_db if r.get('enhanced_exec_match'))

        run23_db_total = len(run23_db)
        run22_db_total = len(run22_db)

        db_change = run23_db_correct - run22_db_correct

        if db_change > 0:
            improvements.append((db, db_change, run23_db_correct, run23_db_total, run22_db_correct, run22_db_total))
        elif db_change < 0:
            regressions.append((db, db_change, run23_db_correct, run23_db_total, run22_db_correct, run22_db_total))
        else:
            no_change.append((db, db_change, run23_db_correct, run23_db_total, run22_db_correct, run22_db_total))

    print(f"IMPROVEMENTS ({len(improvements)} databases):")
    for db, change, r23_correct, r23_total, r22_correct, r22_total in sorted(improvements, key=lambda x: -x[1]):
        print(f"  {db:30s} {r22_correct:3d}/{r22_total:3d} → {r23_correct:3d}/{r23_total:3d}  (+{change})")
    print()

    print(f"REGRESSIONS ({len(regressions)} databases):")
    for db, change, r23_correct, r23_total, r22_correct, r22_total in sorted(regressions, key=lambda x: x[1]):
        print(f"  {db:30s} {r22_correct:3d}/{r22_total:3d} → {r23_correct:3d}/{r23_total:3d}  ({change})")
    print()

    print(f"NO CHANGE ({len(no_change)} databases):")
    for db, change, r23_correct, r23_total, r22_correct, r22_total in sorted(no_change):
        print(f"  {db:30s} {r23_correct:3d}/{r23_total:3d}")
    print()

    # Whack-a-mole analysis
    total_swings = sum(abs(change) for _, change, *_ in improvements) + sum(abs(change) for _, change, *_ in regressions)
    print("="*80)
    print("WHACK-A-MOLE ANALYSIS:")
    print("="*80)
    print(f"  Total question swings: {total_swings}")
    print(f"  Net change: {change} questions")
    print(f"  Efficiency: {(abs(change) / total_swings * 100):.1f}%" if total_swings > 0 else "  Efficiency: N/A")
    print()

    # Test database comparison (pets_1, car_1, dog_kennels)
    print("="*80)
    print("TEST DATABASE COMPARISON:")
    print("="*80)
    print("(These were the 3 databases used for hyperparameter tuning)")
    print()

    for test_db in ['pets_1', 'car_1', 'dog_kennels']:
        if test_db in run23_by_db and test_db in run22_by_db:
            run23_db = run23_by_db[test_db]
            run22_db = run22_by_db[test_db]

            run23_db_correct = sum(1 for r in run23_db if r.get('enhanced_exec_match'))
            run22_db_correct = sum(1 for r in run22_db if r.get('enhanced_exec_match'))

            run23_db_total = len(run23_db)
            run22_db_total = len(run22_db)

            db_change = run23_db_correct - run22_db_correct

            run23_pct = (run23_db_correct / run23_db_total * 100) if run23_db_total > 0 else 0
            run22_pct = (run22_db_correct / run22_db_total * 100) if run22_db_total > 0 else 0

            status = "✅" if db_change > 0 else "❌" if db_change < 0 else "➖"

            print(f"{test_db:15s} Run 22: {run22_db_correct:2d}/{run22_db_total:2d} ({run22_pct:5.1f}%)  →  Run 23: {run23_db_correct:2d}/{run23_db_total:2d} ({run23_pct:5.1f}%)  {status} {db_change:+d}")
    print()

    # Summary
    print("="*80)
    print("SUMMARY:")
    print("="*80)
    print(f"  Changes: top_k 10→5, aggressive chunk weights")
    print(f"  Result: {run23_accuracy:.2f}% ({change_pct:+.2f}%)")
    print(f"  Status: {'✅ SUCCESS' if change > 0 else '❌ REGRESSION' if change < 0 else '➖ NO CHANGE'}")
    print("="*80)


def main():
    """Main analysis."""

    # Get Run 23 and Run 22
    print("Fetching Run 23 results...")
    run23_id = get_run_id("Full Spider 1.0 Turso 23")
    if not run23_id:
        print("❌ Run 23 not found!")
        return

    print("Fetching Run 22 results...")
    run22_id = get_run_id("Full Spider 1.0 Turso 22")
    if not run22_id:
        print("❌ Run 22 not found!")
        return

    print(f"Run 23 ID: {run23_id}")
    print(f"Run 22 ID: {run22_id}")
    print()

    run23_results = get_run_results(run23_id)
    run22_results = get_run_results(run22_id)

    print(f"Loaded {len(run23_results)} results for Run 23")
    print(f"Loaded {len(run22_results)} results for Run 22")
    print()

    # Analyze
    analyze_results(run23_results, run22_results)


if __name__ == "__main__":
    main()
