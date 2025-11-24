#!/usr/bin/env python3
"""
Analyze Run 22 results comparing baseline vs enhanced accuracy,
excluding questions with gold SQL errors.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

# Load environment
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from supabase import create_client

def main():
    # Connect to Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials!")
        return

    supabase = create_client(supabase_url, supabase_key)

    # Get Run 22 ID
    print("Fetching Run 22...")
    runs = supabase.table("benchmark_runs").select("*").execute()
    run22 = None
    for r in runs.data:
        if "22" in r['name'] and "Full Spider" in r['name']:
            run22 = r
            break

    if not run22:
        print("❌ Run 22 not found!")
        return

    print(f"✅ Found: {run22['name']}")

    # Get all results for Run 22
    print(f"\nFetching results for run_id={run22['id']}...")
    results = supabase.table('benchmark_results').select('*').eq('run_id', run22['id']).execute()

    print(f"Total questions: {len(results.data)}")

    # Count gold SQL errors
    gold_errors = [r for r in results.data if r.get('gold_error')]
    print(f"Questions with gold SQL errors: {len(gold_errors)}")

    # Get baseline and enhanced results
    baseline_correct = sum(1 for r in results.data if r.get('baseline_execution_match'))
    enhanced_correct = sum(1 for r in results.data if r.get('enhanced_execution_match'))

    print(f"\n{'='*80}")
    print(f"WITH GOLD ERRORS INCLUDED ({len(results.data)} questions):")
    print(f"{'='*80}")
    print(f"Baseline:  {baseline_correct:4d}/{len(results.data)} = {baseline_correct/len(results.data)*100:5.2f}%")
    print(f"Enhanced:  {enhanced_correct:4d}/{len(results.data)} = {enhanced_correct/len(results.data)*100:5.2f}%")
    print(f"Improvement: {enhanced_correct-baseline_correct:+d} ({(enhanced_correct-baseline_correct)/len(results.data)*100:+.2f}%)")

    # Exclude gold errors
    valid_results = [r for r in results.data if not r.get('gold_error')]
    baseline_correct_valid = sum(1 for r in valid_results if r.get('baseline_execution_match'))
    enhanced_correct_valid = sum(1 for r in valid_results if r.get('enhanced_execution_match'))

    print(f"\n{'='*80}")
    print(f"EXCLUDING GOLD ERRORS ({len(valid_results)} questions):")
    print(f"{'='*80}")
    print(f"Baseline:  {baseline_correct_valid:4d}/{len(valid_results)} = {baseline_correct_valid/len(valid_results)*100:5.2f}%")
    print(f"Enhanced:  {enhanced_correct_valid}/{len(valid_results)} = {enhanced_correct_valid/len(valid_results)*100:5.2f}%")
    print(f"Improvement: {enhanced_correct_valid-baseline_correct_valid:+d} ({(enhanced_correct_valid-baseline_correct_valid)/len(valid_results)*100:+.2f}%)")

    # Get per-database breakdown
    print(f"\n{'='*80}")
    print(f"PER-DATABASE BREAKDOWN (excluding gold errors):")
    print(f"{'='*80}")
    print(f"{'Database':<35s} | {'Q':>3s} | {'Baseline':>8s} | {'Enhanced':>8s} | {'Δ':>6s}")
    print(f"{'-'*35} | {'-'*3} | {'-'*8} | {'-'*8} | {'-'*6}")

    databases = {}
    for r in valid_results:
        db = r['database']
        if db not in databases:
            databases[db] = {'total': 0, 'baseline': 0, 'enhanced': 0}
        databases[db]['total'] += 1
        if r.get('baseline_execution_match'):
            databases[db]['baseline'] += 1
        if r.get('enhanced_execution_match'):
            databases[db]['enhanced'] += 1

    for db in sorted(databases.keys()):
        stats = databases[db]
        baseline_pct = stats['baseline'] / stats['total'] * 100
        enhanced_pct = stats['enhanced'] / stats['total'] * 100
        diff = stats['enhanced'] - stats['baseline']
        diff_pct = enhanced_pct - baseline_pct

        print(f"{db:<35s} | {stats['total']:3d} | "
              f"{stats['baseline']:3d} ({baseline_pct:5.1f}%) | "
              f"{stats['enhanced']:3d} ({enhanced_pct:5.1f}%) | "
              f"{diff:+3d} ({diff_pct:+5.1f}%)")

    # Summary stats
    improved_dbs = sum(1 for s in databases.values() if s['enhanced'] > s['baseline'])
    regressed_dbs = sum(1 for s in databases.values() if s['enhanced'] < s['baseline'])
    same_dbs = sum(1 for s in databases.values() if s['enhanced'] == s['baseline'])

    print(f"\n{'='*80}")
    print(f"SUMMARY:")
    print(f"{'='*80}")
    print(f"Improved databases:  {improved_dbs}")
    print(f"Regressed databases: {regressed_dbs}")
    print(f"No change:           {same_dbs}")

if __name__ == "__main__":
    main()
