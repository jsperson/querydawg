#!/usr/bin/env python3
"""
Analyze Run 22 results comparing baseline vs enhanced accuracy,
excluding questions where gold SQL had issues.
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

    # Get Run 22 ID (ID: 52294c6d-fb67-495d-a60b-ff333349f294)
    run22_id = "52294c6d-fb67-495d-a60b-ff333349f294"

    print("Fetching Run 22 metadata...")
    run22 = supabase.table("benchmark_runs").select("*").eq('id', run22_id).execute()

    if not run22.data:
        print("❌ Run 22 not found!")
        return

    print(f"✅ Found: {run22.data[0]['name']}")

    # Get all results for Run 22
    print(f"\nFetching results...")
    results = supabase.table('benchmark_results').select('*').eq('run_id', run22_id).execute()

    print(f"Total questions: {len(results.data)}")

    # Identify potentially problematic questions (both failed or both have errors)
    problematic = []
    for r in results.data:
        # If both baseline and enhanced failed, it might indicate a gold SQL issue
        baseline_ok = r.get('baseline_exec_match') == True
        enhanced_ok = r.get('enhanced_exec_match') == True
        baseline_err = r.get('baseline_error') is not None
        enhanced_err = r.get('enhanced_error') is not None

        # Flag if both failed or both errored
        if (not baseline_ok and not enhanced_ok) or (baseline_err and enhanced_err):
            if baseline_err and enhanced_err and r.get('baseline_error') == r.get('enhanced_error'):
                problematic.append(r)

    print(f"Potentially problematic questions (both failed with same error): {len(problematic)}")

    # Get baseline and enhanced results for ALL questions
    baseline_correct = sum(1 for r in results.data if r.get('baseline_exec_match') == True)
    enhanced_correct = sum(1 for r in results.data if r.get('enhanced_exec_match') == True)

    print(f"\n{'='*90}")
    print(f"ALL QUESTIONS ({len(results.data)} questions):")
    print(f"{'='*90}")
    print(f"Baseline:  {baseline_correct:4d}/{len(results.data)} = {baseline_correct/len(results.data)*100:5.2f}%")
    print(f"Enhanced:  {enhanced_correct:4d}/{len(results.data)} = {enhanced_correct/len(results.data)*100:5.2f}%")
    print(f"Improvement: {enhanced_correct-baseline_correct:+d} ({(enhanced_correct-baseline_correct)/len(results.data)*100:+.2f}%)")

    # Exclude problematic questions if any
    if problematic:
        valid_results = [r for r in results.data if r not in problematic]
        baseline_correct_valid = sum(1 for r in valid_results if r.get('baseline_exec_match') == True)
        enhanced_correct_valid = sum(1 for r in valid_results if r.get('enhanced_exec_match') == True)

        print(f"\n{'='*90}")
        print(f"EXCLUDING PROBLEMATIC QUESTIONS ({len(valid_results)} questions):")
        print(f"{'='*90}")
        print(f"Baseline:  {baseline_correct_valid:4d}/{len(valid_results)} = {baseline_correct_valid/len(valid_results)*100:5.2f}%")
        print(f"Enhanced:  {enhanced_correct_valid}/{len(valid_results)} = {enhanced_correct_valid/len(valid_results)*100:5.2f}%")
        print(f"Improvement: {enhanced_correct_valid-baseline_correct_valid:+d} ({(enhanced_correct_valid-baseline_correct_valid)/len(valid_results)*100:+.2f}%)")
    else:
        valid_results = results.data

    # Get per-database breakdown
    print(f"\n{'='*90}")
    print(f"PER-DATABASE BREAKDOWN:")
    print(f"{'='*90}")
    print(f"{'Database':<35s} | {'Q':>3s} | {'Baseline':>15s} | {'Enhanced':>15s} | {'Δ':>10s}")
    print(f"{'-'*35} | {'-'*3} | {'-'*15} | {'-'*15} | {'-'*10}")

    databases = {}
    for r in valid_results:
        db = r['database']
        if db not in databases:
            databases[db] = {'total': 0, 'baseline': 0, 'enhanced': 0}
        databases[db]['total'] += 1
        if r.get('baseline_exec_match') == True:
            databases[db]['baseline'] += 1
        if r.get('enhanced_exec_match') == True:
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

    print(f"\n{'='*90}")
    print(f"SUMMARY:")
    print(f"{'='*90}")
    print(f"Databases where enhanced > baseline:  {improved_dbs}")
    print(f"Databases where enhanced < baseline:  {regressed_dbs}")
    print(f"Databases with no change:             {same_dbs}")
    print(f"\nTotal question swings: {sum(abs(s['enhanced'] - s['baseline']) for s in databases.values())}")

if __name__ == "__main__":
    main()
