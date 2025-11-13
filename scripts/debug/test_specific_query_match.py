#!/usr/bin/env python3
"""
Test if specific queries actually return matching results
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database.turso_client import TursoClient
from dotenv import load_dotenv

# Load environment
load_dotenv()

def results_match(results1, results2):
    """Column-order-independent comparison"""
    try:
        set1 = {frozenset(row) for row in results1}
        set2 = {frozenset(row) for row in results2}
        return set1 == set2
    except TypeError:
        return results1 == results2

def main():
    print("Testing query result matching for concert_singer...\n")

    client = TursoClient(db_name="concert_singer")

    # Test case from the benchmark results
    gold_sql = "SELECT T2.name, count(*) FROM singer_in_concert AS T1 JOIN singer AS T2 ON T1.singer_id = T2.singer_id GROUP BY T2.singer_id"

    enhanced_sql = """SELECT singer.name, COUNT(singer_in_concert.concert_id) AS concert_count
FROM singer
LEFT JOIN singer_in_concert ON singer.singer_id = singer_in_concert.singer_id
GROUP BY singer.name;"""

    print("Gold SQL:")
    print(gold_sql)
    print()

    print("Enhanced SQL:")
    print(enhanced_sql)
    print()

    # Execute both
    try:
        gold_result = client.execute(gold_sql)
        print("Gold results:")
        print(f"  Columns: {gold_result['columns']}")
        print(f"  Rows ({len(gold_result['rows'])}):")
        for i, row in enumerate(gold_result['rows'][:10]):
            print(f"    {i+1}. {row}")
        if len(gold_result['rows']) > 10:
            print(f"    ... and {len(gold_result['rows']) - 10} more")
        print()

    except Exception as e:
        print(f"Gold query failed: {e}\n")
        return

    try:
        enhanced_result = client.execute(enhanced_sql)
        print("Enhanced results:")
        print(f"  Columns: {enhanced_result['columns']}")
        print(f"  Rows ({len(enhanced_result['rows'])}):")
        for i, row in enumerate(enhanced_result['rows'][:10]):
            print(f"    {i+1}. {row}")
        if len(enhanced_result['rows']) > 10:
            print(f"    ... and {len(enhanced_result['rows']) - 10} more")
        print()

    except Exception as e:
        print(f"Enhanced query failed: {e}\n")
        return

    # Convert to lists for comparison
    gold_rows = gold_result['rows']
    enhanced_rows = enhanced_result['rows']

    # Compare
    match = results_match(gold_rows, enhanced_rows)

    print("=" * 60)
    if match:
        print("✓ RESULTS MATCH")
    else:
        print("✗ RESULTS DO NOT MATCH")

        # Show differences
        gold_set = {frozenset(row) for row in gold_rows}
        enhanced_set = {frozenset(row) for row in enhanced_rows}

        only_in_gold = gold_set - enhanced_set
        only_in_enhanced = enhanced_set - gold_set

        if only_in_gold:
            print(f"\nRows only in gold ({len(only_in_gold)}):")
            for row in list(only_in_gold)[:5]:
                print(f"  {set(row)}")

        if only_in_enhanced:
            print(f"\nRows only in enhanced ({len(only_in_enhanced)}):")
            for row in list(only_in_enhanced)[:5]:
                print(f"  {set(row)}")

if __name__ == "__main__":
    main()
