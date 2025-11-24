#!/usr/bin/env python3
"""
Analyze Run 24 results (Post-Reversion Baseline)
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


def analyze_results(run24_results, run22_results):
    """Analyze Run 24 vs Run 22."""

    # Group by database
    run24_by_db = defaultdict(list)
    run22_by_db = defaultdict(list)

    for r in run24_results:
        run24_by_db[r['database']].append(r)

    for r in run22_results:
        run22_by_db[r['database']].append(r)

    # Calculate overall stats
    run24_correct = sum(1 for r in run24_results if r.get('enhanced_exec_match'))
    run24_total = len(run24_results)
    run24_accuracy = (run24_correct / run24_total * 100) if run24_total > 0 else 0

    run22_correct = sum(1 for r in run22_results if r.get('enhanced_exec_match'))
    run22_total = len(run22_results)
    run22_accuracy = (run22_correct / run22_total * 100) if run22_total > 0 else 0

    print("="*80)
    print("RUN 24 ANALYSIS: Post-Reversion Baseline")
    print("="*80)
    print()

    print("OVERALL RESULTS:")
    print(f"  Run 22 (baseline):  {run22_correct}/{run22_total} ({run22_accuracy:.2f}%)")
    print(f"  Run 24 (baseline):  {run24_correct}/{run24_total} ({run24_accuracy:.2f}%)")
    print()

    change = run24_correct - run22_correct
    change_pct = run24_accuracy - run22_accuracy

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

    all_databases = sorted(set(list(run24_by_db.keys()) + list(run22_by_db.keys())))

    for db in all_databases:
        run24_db = run24_by_db.get(db, [])
        run22_db = run22_by_db.get(db, [])

        run24_db_correct = sum(1 for r in run24_db if r.get('enhanced_exec_match'))
        run22_db_correct = sum(1 for r in run22_db if r.get('enhanced_exec_match'))

        run24_db_total = len(run24_db)
        run22_db_total = len(run22_db)

        db_change = run24_db_correct - run22_db_correct

        if db_change > 0:
            improvements.append((db, db_change, run24_db_correct, run24_db_total, run22_db_correct, run22_db_total))
        elif db_change < 0:
            regressions.append((db, db_change, run24_db_correct, run24_db_total, run22_db_correct, run22_db_total))
        else:
            no_change.append((db, db_change, run24_db_correct, run24_db_total, run22_db_correct, run22_db_total))

    print(f"IMPROVEMENTS ({len(improvements)} databases):")
    for db, change, r24_correct, r24_total, r22_correct, r22_total in sorted(improvements, key=lambda x: -x[1]):
        print(f"  {db:30s} {r22_correct:3d}/{r22_total:3d} → {r24_correct:3d}/{r24_total:3d}  (+{change})")
    print()

    print(f"REGRESSIONS ({len(regressions)} databases):")
    for db, change, r24_correct, r24_total, r22_correct, r22_total in sorted(regressions, key=lambda x: x[1]):
        print(f"  {db:30s} {r22_correct:3d}/{r22_total:3d} → {r24_correct:3d}/{r24_total:3d}  ({change})")
    print()

    print(f"NO CHANGE ({len(no_change)} databases):")
    for db, change, r24_correct, r24_total, r22_correct, r22_total in sorted(no_change):
        print(f"  {db:30s} {r24_correct:3d}/{r24_total:3d}")
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

    # Summary
    print("="*80)
    print("SUMMARY:")
    print("="*80)
    print(f"  Configuration: top_k=10, baseline weights (same as Run 22)")
    print(f"  Result: {run24_accuracy:.2f}% ({change_pct:+.2f}%)")
    print(f"  Status: {'✅ SUCCESS' if change > 0 else '❌ REGRESSION' if change < 0 else '➖ NO CHANGE'}")
    print("="*80)


def main():
    """Main analysis."""

    # Get Run 24 and Run 22
    print("Fetching Run 24 results...")
    run24_id = get_run_id("Full Spider 1.0 Turso 24 - return to baseline code")
    if not run24_id:
        print("❌ Run 24 not found!")
        return

    print("Fetching Run 22 results...")
    run22_id = get_run_id("Full Spider 1.0 Turso 22")
    if not run22_id:
        print("❌ Run 22 not found!")
        return

    print(f"Run 24 ID: {run24_id}")
    print(f"Run 22 ID: {run22_id}")
    print()

    run24_results = get_run_results(run24_id)
    run22_results = get_run_results(run22_id)

    print(f"Loaded {len(run24_results)} results for Run 24")
    print(f"Loaded {len(run22_results)} results for Run 22")
    print()

    # Analyze
    analyze_results(run24_results, run22_results)


if __name__ == "__main__":
    main()
