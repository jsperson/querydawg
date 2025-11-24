#!/usr/bin/env python3
"""
Analyze Run 22 results (Phase 1 Prompt Optimization) and compare to Run 20 (Phase 2 baseline).
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

    # Fetch Run 22 results
    print("Fetching Run 22 results...")
    run22 = supabase.table("benchmark_runs").select("*").ilike("name", "%Full Spider 1.0 Turso 22%").execute()

    if not run22.data:
        print("❌ Run 22 not found!")
        return

    run22_data = run22.data[0]
    run22_accuracy_decimal = run22_data['enhanced_exec_match']
    run22_accuracy = run22_accuracy_decimal * 100  # Convert to percentage
    run22_total = 1034  # Spider 1.0 has 1034 questions
    run22_correct = round(run22_accuracy_decimal * run22_total)

    print(f"\n✅ Run 22 found!")
    print(f"   Name: {run22_data['name']}")
    print(f"   Date: {run22_data['created_at']}")
    print(f"   Accuracy: {run22_accuracy:.2f}% ({run22_correct}/{run22_total})")

    # Fetch Run 20 for comparison (Phase 2 baseline)
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

    # Fetch Run 19 and Run 21 for context
    print("Fetching Run 19 and Run 21 for context...")
    run19 = supabase.table("benchmark_runs").select("*").ilike("name", "%Full Spider 1.0 Turso 19%").execute()
    run21 = supabase.table("benchmark_runs").select("*").ilike("name", "%Full Spider 1.0 Turso 21%").execute()

    run19_accuracy = 0
    run19_correct = 0
    if run19.data:
        run19_data = run19.data[0]
        run19_accuracy_decimal = run19_data['enhanced_exec_match']
        run19_accuracy = run19_accuracy_decimal * 100
        run19_correct = round(run19_accuracy_decimal * 1034)

    run21_accuracy = 0
    run21_correct = 0
    if run21.data:
        run21_data = run21.data[0]
        run21_accuracy_decimal = run21_data['enhanced_exec_match']
        run21_accuracy = run21_accuracy_decimal * 100
        run21_correct = round(run21_accuracy_decimal * 1034)

    # Overall comparison
    print(f"\n{'=' * 80}")
    print(f"OVERALL RESULTS COMPARISON")
    print(f"{'=' * 80}")
    print(f"\nRun 19 (Phase 1 Baseline):  {run19_accuracy:.2f}% ({run19_correct}/{run22_total})")
    print(f"Run 20 (Phase 2):           {run20_accuracy:.2f}% ({run20_correct}/{run22_total})")
    print(f"Run 21 (Phase 2.1):         {run21_accuracy:.2f}% ({run21_correct}/{run22_total})")
    print(f"Run 22 (Phase 1 Prompt):    {run22_accuracy:.2f}% ({run22_correct}/{run22_total})")

    change_20_to_22 = run22_accuracy - run20_accuracy
    change_19_to_22 = run22_accuracy - run19_accuracy

    print(f"\nRun 20 → Run 22: {change_20_to_22:+.2f}% ({run22_correct - run20_correct:+d} questions)")
    print(f"Run 19 → Run 22: {change_19_to_22:+.2f}% ({run22_correct - run19_correct:+d} questions)")

    # Check if target met
    target_min = 84.0
    target_stretch = 84.2
    target_exceptional = 84.5

    print(f"\n{'=' * 80}")
    print(f"TARGET ASSESSMENT")
    print(f"{'=' * 80}")
    print(f"Minimum target: {target_min}%")
    print(f"Strong target: {target_stretch}%")
    print(f"Exceptional target: {target_exceptional}%")
    print(f"Actual: {run22_accuracy:.2f}%")

    if run22_accuracy >= target_exceptional:
        print(f"\n🎉 EXCEPTIONAL SUCCESS! Run 22 >= {target_exceptional}%")
    elif run22_accuracy >= target_stretch:
        print(f"\n✅ STRONG SUCCESS! Run 22 >= {target_stretch}%")
    elif run22_accuracy >= target_min:
        print(f"\n✅ MINIMUM SUCCESS! Run 22 >= {target_min}%")
    else:
        print(f"\n❌ Target not met. Run 22 < {target_min}% (gap: {target_min - run22_accuracy:.2f}%)")

    # Database-level analysis
    print(f"\n{'=' * 80}")
    print(f"DATABASE-LEVEL CHANGES (Run 22 vs Run 20)")
    print(f"{'=' * 80}")

    # Get database-level results for Run 22 and Run 20
    run22_id = run22_data['id']
    run20_id = run20_data['id']

    # Aggregate by database
    run22_db_results = supabase.table("benchmark_results").select("database, enhanced_exec_match").eq("run_id", run22_id).execute()
    run20_db_results = supabase.table("benchmark_results").select("database, enhanced_exec_match").eq("run_id", run20_id).execute()

    # Count correct per database
    run22_by_db = defaultdict(lambda: {'total': 0, 'correct': 0})
    run20_by_db = defaultdict(lambda: {'total': 0, 'correct': 0})

    for result in run22_db_results.data:
        db = result['database']
        run22_by_db[db]['total'] += 1
        if result['enhanced_exec_match']:
            run22_by_db[db]['correct'] += 1

    for result in run20_db_results.data:
        db = result['database']
        run20_by_db[db]['total'] += 1
        if result['enhanced_exec_match']:
            run20_by_db[db]['correct'] += 1

    # Calculate changes
    improvements = []
    regressions = []
    no_change = []

    for db in sorted(run22_by_db.keys()):
        r22_total = run22_by_db[db]['total']
        r22_correct = run22_by_db[db]['correct']
        r20_correct = run20_by_db[db]['correct']

        delta = r22_correct - r20_correct

        if delta > 0:
            improvements.append((db, r22_total, r20_correct, r22_correct, delta))
        elif delta < 0:
            regressions.append((db, r22_total, r20_correct, r22_correct, delta))
        else:
            no_change.append(db)

    # Print improvements
    if improvements:
        print(f"\n✅ IMPROVEMENTS ({len(improvements)} databases, +{sum(i[4] for i in improvements)} questions):")
        print(f"\n{'Database':<30} {'Total':<6} {'R20':<5} {'R22':<5} {'Δ':<4} {'R20%':<8} {'R22%':<8} {'Δ%'}")
        print("-" * 90)
        for db, total, r20, r22, delta in improvements:
            r20_pct = 100 * r20 / total
            r22_pct = 100 * r22 / total
            delta_pct = r22_pct - r20_pct
            print(f"{db:<30} {total:<6} {r20:<5} {r22:<5} {delta:+4} {r20_pct:6.1f}% {r22_pct:6.1f}% {delta_pct:+6.1f}%")

    # Print regressions
    if regressions:
        print(f"\n❌ REGRESSIONS ({len(regressions)} databases, {sum(r[4] for r in regressions)} questions):")
        print(f"\n{'Database':<30} {'Total':<6} {'R20':<5} {'R22':<5} {'Δ':<4} {'R20%':<8} {'R22%':<8} {'Δ%'}")
        print("-" * 90)
        for db, total, r20, r22, delta in regressions:
            r20_pct = 100 * r20 / total
            r22_pct = 100 * r22 / total
            delta_pct = r22_pct - r20_pct
            print(f"{db:<30} {total:<6} {r20:<5} {r22:<5} {delta:+4} {r20_pct:6.1f}% {r22_pct:6.1f}% {delta_pct:+6.1f}%")

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
    print(f"\nContext:")
    print(f"  Run 19→20: 19 swings")
    print(f"  Run 20→21: 24 swings")
    print(f"  Run 20→22: {total_swings} swings")

    if total_swings < 15:
        print(f"\n✅ Whack-a-mole REDUCED! ({total_swings} < 15 target)")
    elif total_swings < 19:
        print(f"\n✅ Whack-a-mole improved vs Run 20→21 ({total_swings} < 24)")
    else:
        print(f"\n⚠️  Whack-a-mole still high ({total_swings} swings)")

    # Key database recoveries (pets_1, car_1, world_1)
    print(f"\n{'=' * 80}")
    print(f"KEY DATABASE TARGETS (pets_1, car_1, world_1)")
    print(f"{'=' * 80}")

    for db_name in ['pets_1', 'car_1', 'world_1']:
        if db_name in run22_by_db:
            r22_total = run22_by_db[db_name]['total']
            r22_correct = run22_by_db[db_name]['correct']
            r20_correct = run20_by_db[db_name]['correct']
            delta = r22_correct - r20_correct

            print(f"\n{db_name}:")
            print(f"  Run 20 (Phase 2):        {r20_correct}/{r22_total} ({100 * r20_correct / r22_total:.1f}%)")
            print(f"  Run 22 (Phase 1 Prompt): {r22_correct}/{r22_total} ({100 * r22_correct / r22_total:.1f}%)")
            print(f"  Change: {delta:+d} questions ({(100 * delta / r22_total):+.1f}%)")

            if delta > 0:
                print(f"  ✅ Improved!")
            elif delta == 0:
                print(f"  ➖ No change")
            else:
                print(f"  ❌ Regressed")

    # Recommendation
    print(f"\n{'=' * 80}")
    print(f"PHASE 1 ASSESSMENT")
    print(f"{'=' * 80}")

    if run22_accuracy >= target_exceptional:
        print(f"🎉 EXCEPTIONAL SUCCESS: Phase 1 achieved {run22_accuracy:.2f}% (>= {target_exceptional}%)")
        print(f"   Phase 1 prompt improvements exceeded expectations")
        print(f"   Recommend: Proceed to Phase 2 (RAG hyperparameter tuning)")
        print(f"   Expected combined gain: +0.8-1.8% total")
    elif run22_accuracy >= target_stretch:
        print(f"✅ STRONG SUCCESS: Phase 1 achieved {run22_accuracy:.2f}% (>= {target_stretch}%)")
        print(f"   Phase 1 prompt improvements met strong target")
        print(f"   Recommend: Proceed to Phase 2 (RAG hyperparameter tuning)")
        print(f"   Expected combined gain: +0.6-1.5% total")
    elif run22_accuracy >= target_min:
        print(f"✅ MINIMUM SUCCESS: Phase 1 achieved {run22_accuracy:.2f}% (>= {target_min}%)")
        print(f"   Phase 1 prompt improvements met minimum target")
        print(f"   Recommend: Proceed to Phase 2 (RAG hyperparameter tuning)")
        print(f"   Expected combined gain: +0.4-1.2% total")
    elif run22_accuracy > run20_accuracy:
        print(f"⚠️  PARTIAL SUCCESS: Phase 1 improved vs Phase 2 ({change_20_to_22:+.2f}%)")
        print(f"   But did not meet minimum target ({run22_accuracy:.2f}% < {target_min}%)")
        print(f"   Gap to target: {target_min - run22_accuracy:.2f}%")
        print(f"   Recommend: Analyze specific failures, may still proceed to Phase 2")
    else:
        print(f"❌ FAILED: Phase 1 did not improve vs Phase 2 ({change_20_to_22:+.2f}%)")
        print(f"   Recommend: Analyze root cause, consider reverting prompt changes")

if __name__ == "__main__":
    main()
