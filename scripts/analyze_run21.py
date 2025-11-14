#!/usr/bin/env python3
"""
Analyze Run 21 results and compare to Run 20 (Phase 2.1 vs Phase 2).
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

    # Fetch Run 21 results
    print("Fetching Run 21 results...")
    run21 = supabase.table("benchmark_runs").select("*").ilike("name", "%Full Spider 1.0 Turso 21%").execute()

    if not run21.data:
        print("❌ Run 21 not found!")
        return

    run21_data = run21.data[0]
    run21_accuracy_decimal = run21_data['enhanced_exec_match']
    run21_accuracy = run21_accuracy_decimal * 100  # Convert to percentage
    run21_total = 1034  # Spider 1.0 has 1034 questions
    run21_correct = round(run21_accuracy_decimal * run21_total)

    print(f"\n✅ Run 21 found!")
    print(f"   Name: {run21_data['name']}")
    print(f"   Date: {run21_data['created_at']}")
    print(f"   Accuracy: {run21_accuracy:.2f}% ({run21_correct}/{run21_total})")

    # Fetch Run 20 for comparison
    print("\nFetching Run 20 for comparison...")
    run20 = supabase.table("benchmark_runs").select("*").ilike("name", "%Full Spider 1.0 Turso 20%").execute()

    if not run20.data:
        print("❌ Run 20 not found!")
        return

    run20_data = run20.data[0]
    run20_accuracy_decimal = run20_data['enhanced_exec_match']
    run20_accuracy = run20_accuracy_decimal * 100
    run20_total = 1034
    run20_correct = round(run20_accuracy_decimal * run20_total)

    # Fetch Run 19 for baseline
    print("Fetching Run 19 for baseline...")
    run19 = supabase.table("benchmark_runs").select("*").ilike("name", "%Full Spider 1.0 Turso 19%").execute()

    run19_accuracy = 0
    run19_correct = 0
    if run19.data:
        run19_data = run19.data[0]
        run19_accuracy_decimal = run19_data['enhanced_exec_match']
        run19_accuracy = run19_accuracy_decimal * 100
        run19_correct = round(run19_accuracy_decimal * 1034)

    # Overall comparison
    print(f"\n{'=' * 80}")
    print(f"OVERALL RESULTS COMPARISON")
    print(f"{'=' * 80}")
    print(f"\nRun 19 (Phase 1 Baseline):  {run19_accuracy:.2f}% ({run19_correct}/{run21_total})")
    print(f"Run 20 (Phase 2):           {run20_accuracy:.2f}% ({run20_correct}/{run21_total})")
    print(f"Run 21 (Phase 2.1):         {run21_accuracy:.2f}% ({run21_correct}/{run21_total})")

    change_20_to_21 = run21_accuracy - run20_accuracy
    change_19_to_21 = run21_accuracy - run19_accuracy

    print(f"\nRun 20 → Run 21: {change_20_to_21:+.2f}% ({run21_correct - run20_correct:+d} questions)")
    print(f"Run 19 → Run 21: {change_19_to_21:+.2f}% ({run21_correct - run19_correct:+d} questions)")

    # Check if target met
    target_min = 84.2
    target_max = 84.7

    print(f"\n{'=' * 80}")
    print(f"TARGET ASSESSMENT")
    print(f"{'=' * 80}")
    print(f"Target: {target_min}-{target_max}%")
    print(f"Actual: {run21_accuracy:.2f}%")

    if run21_accuracy >= target_min:
        print(f"✅ TARGET MET! Run 21 >= {target_min}%")
    else:
        print(f"❌ Target not met. Run 21 < {target_min}% (gap: {target_min - run21_accuracy:.2f}%)")

    # Database-level analysis
    print(f"\n{'=' * 80}")
    print(f"DATABASE-LEVEL CHANGES (Run 21 vs Run 20)")
    print(f"{'=' * 80}")

    # Get database-level results for Run 21 and Run 20
    run21_id = run21_data['id']
    run20_id = run20_data['id']

    # Aggregate by database
    run21_db_results = supabase.table("benchmark_results").select("database, enhanced_exec_match").eq("run_id", run21_id).execute()
    run20_db_results = supabase.table("benchmark_results").select("database, enhanced_exec_match").eq("run_id", run20_id).execute()

    # Count correct per database
    run21_by_db = defaultdict(lambda: {'total': 0, 'correct': 0})
    run20_by_db = defaultdict(lambda: {'total': 0, 'correct': 0})

    for result in run21_db_results.data:
        db = result['database']
        run21_by_db[db]['total'] += 1
        if result['enhanced_exec_match']:
            run21_by_db[db]['correct'] += 1

    for result in run20_db_results.data:
        db = result['database']
        run20_by_db[db]['total'] += 1
        if result['enhanced_exec_match']:
            run20_by_db[db]['correct'] += 1

    # Calculate changes
    improvements = []
    regressions = []
    no_change = []

    for db in sorted(run21_by_db.keys()):
        r21_total = run21_by_db[db]['total']
        r21_correct = run21_by_db[db]['correct']
        r20_correct = run20_by_db[db]['correct']

        delta = r21_correct - r20_correct

        if delta > 0:
            improvements.append((db, r21_total, r20_correct, r21_correct, delta))
        elif delta < 0:
            regressions.append((db, r21_total, r20_correct, r21_correct, delta))
        else:
            no_change.append(db)

    # Print improvements
    if improvements:
        print(f"\n✅ IMPROVEMENTS ({len(improvements)} databases, +{sum(i[4] for i in improvements)} questions):")
        print(f"\n{'Database':<30} {'Total':<6} {'R20':<5} {'R21':<5} {'Δ':<4} {'R20%':<8} {'R21%':<8} {'Δ%'}")
        print("-" * 90)
        for db, total, r20, r21, delta in improvements:
            r20_pct = 100 * r20 / total
            r21_pct = 100 * r21 / total
            delta_pct = r21_pct - r20_pct
            print(f"{db:<30} {total:<6} {r20:<5} {r21:<5} {delta:+4} {r20_pct:6.1f}% {r21_pct:6.1f}% {delta_pct:+6.1f}%")

    # Print regressions
    if regressions:
        print(f"\n❌ REGRESSIONS ({len(regressions)} databases, {sum(r[4] for r in regressions)} questions):")
        print(f"\n{'Database':<30} {'Total':<6} {'R20':<5} {'R21':<5} {'Δ':<4} {'R20%':<8} {'R21%':<8} {'Δ%'}")
        print("-" * 90)
        for db, total, r20, r21, delta in regressions:
            r20_pct = 100 * r20 / total
            r21_pct = 100 * r21 / total
            delta_pct = r21_pct - r20_pct
            print(f"{db:<30} {total:<6} {r20:<5} {r21:<5} {delta:+4} {r20_pct:6.1f}% {r21_pct:6.1f}% {delta_pct:+6.1f}%")

    print(f"\n➖ NO CHANGE: {len(no_change)} databases")

    # Whack-a-mole analysis
    total_swings = sum(abs(i[4]) for i in improvements) + sum(abs(r[4]) for r in regressions)
    net_change = sum(i[4] for i in improvements) + sum(r[4] for r in regressions)

    print(f"\n{'=' * 80}")
    print(f"WHACK-A-MOLE ANALYSIS")
    print(f"{'=' * 80}")
    print(f"Improvements: {len(improvements)} databases, +{sum(i[4] for i in improvements)} questions")
    print(f"Regressions:  {len(regressions)} databases, {sum(r[4] for r in regressions)} questions")
    print(f"Net change:   {net_change:+d} questions")
    print(f"Total swings: {total_swings} (whack-a-mole effect)")

    # Key database recoveries (car_1 and world_1)
    print(f"\n{'=' * 80}")
    print(f"KEY DATABASE RECOVERIES (car_1 and world_1)")
    print(f"{'=' * 80}")

    for db_name in ['car_1', 'world_1']:
        if db_name in run21_by_db:
            r21_total = run21_by_db[db_name]['total']
            r21_correct = run21_by_db[db_name]['correct']
            r20_correct = run20_by_db[db_name]['correct']
            delta = r21_correct - r20_correct

            print(f"\n{db_name}:")
            print(f"  Run 20 (Phase 2):   {r20_correct}/{r21_total} ({100 * r20_correct / r21_total:.1f}%)")
            print(f"  Run 21 (Phase 2.1): {r21_correct}/{r21_total} ({100 * r21_correct / r21_total:.1f}%)")
            print(f"  Change: {delta:+d} questions ({(100 * delta / r21_total):+.1f}%)")

            if delta > 0:
                print(f"  ✅ Recovered from Phase 2 regression!")
            elif delta == 0:
                print(f"  ➖ No change")
            else:
                print(f"  ❌ Further regression")

    # Recommendation
    print(f"\n{'=' * 80}")
    print(f"PHASE 2.1 ASSESSMENT")
    print(f"{'=' * 80}")

    if run21_accuracy >= target_min:
        print(f"✅ SUCCESS: Phase 2.1 achieved target ({run21_accuracy:.2f}% >= {target_min}%)")
        print(f"   Phase 2.1 conditional disambiguation fixed the regression")
        print(f"   Recommend: Proceed with Phase 3 or other optimizations")
    elif run21_accuracy > run20_accuracy:
        print(f"⚠️  PARTIAL SUCCESS: Phase 2.1 improved vs Phase 2 ({change_20_to_21:+.2f}%)")
        print(f"   But did not meet target ({run21_accuracy:.2f}% < {target_min}%)")
        print(f"   Gap to target: {target_min - run21_accuracy:.2f}%")
        print(f"   Recommend: Investigate remaining issues or try Phase 3")
    else:
        print(f"❌ FAILED: Phase 2.1 did not improve vs Phase 2 ({change_20_to_21:+.2f}%)")
        print(f"   Recommend: Revert to Phase 1 or try alternative approach")

if __name__ == "__main__":
    main()
