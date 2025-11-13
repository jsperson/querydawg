#!/usr/bin/env python3
"""
Test Phase 2.1 conditional disambiguation on car_1 and world_1.
Verify that disambiguation is only applied to multi-table columns.
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import get_settings
from app.services.llm.openai_provider import OpenAIProvider
from app.services.semantic_layer_generator import SemanticLayerGenerator

# Test databases (the ones that regressed in Run 20)
TEST_DATABASES = [
    "car_1",     # -4 questions in Run 20
    "world_1"    # -4 questions in Run 20
]

def analyze_disambiguation_usage(semantic_layer, database_name):
    """Analyze how disambiguation was applied in the semantic layer."""
    print(f"\n{'=' * 80}")
    print(f"ANALYZING: {database_name}")
    print(f"{'=' * 80}")

    tables = semantic_layer.get('tables', [])
    print(f"\nTables: {len(tables)}")

    total_columns = 0
    columns_with_disamb = 0
    single_table_with_disamb = 0  # ERROR: single-table columns with disambiguation
    multi_table_without_disamb = 0  # ERROR: multi-table columns without disambiguation

    # First pass: identify which columns appear in multiple tables
    column_appearances = {}
    for table in tables:
        for col in table.get('columns', []):
            col_name = col.get('name', '')
            if col_name not in column_appearances:
                column_appearances[col_name] = []
            column_appearances[col_name].append(table.get('name', 'Unknown'))

    # Second pass: check disambiguation usage
    for table in tables:
        table_name = table.get('name', 'Unknown')
        columns = table.get('columns', [])
        total_columns += len(columns)

        for col in columns:
            col_name = col.get('name', '')
            has_disamb = 'disambiguation' in col
            appears_in_count = len(column_appearances.get(col_name, []))

            if has_disamb:
                columns_with_disamb += 1

                # Check if this is a single-table column (ERROR)
                if appears_in_count == 1:
                    single_table_with_disamb += 1
                    print(f"\n❌ ERROR: {table_name}.{col_name} has disambiguation but only appears in 1 table!")
                    print(f"   appears_in_tables: {col['disambiguation'].get('appears_in_tables', [])}")

            else:
                # Check if this is a multi-table column (ERROR)
                if appears_in_count > 1:
                    multi_table_without_disamb += 1
                    print(f"\n⚠️  WARNING: {table_name}.{col_name} appears in {appears_in_count} tables but has NO disambiguation!")
                    print(f"   Tables: {column_appearances[col_name]}")

    # Summary
    print(f"\n{'=' * 80}")
    print(f"SUMMARY: {database_name}")
    print(f"{'=' * 80}")
    print(f"Total columns: {total_columns}")
    print(f"Columns with disambiguation: {columns_with_disamb} ({100 * columns_with_disamb / total_columns:.1f}%)")
    print(f"Multi-table columns (expected to have disamb): {sum(1 for k, v in column_appearances.items() if len(v) > 1)}")

    # Errors
    print(f"\n{'=' * 80}")
    print(f"ERRORS:")
    print(f"{'=' * 80}")

    if single_table_with_disamb > 0:
        print(f"❌ Single-table columns with disambiguation: {single_table_with_disamb}")
        print(f"   (Phase 2.1 should have PREVENTED this)")
    else:
        print(f"✅ No single-table columns with disambiguation (Phase 2.1 working correctly!)")

    if multi_table_without_disamb > 0:
        print(f"⚠️  Multi-table columns without disambiguation: {multi_table_without_disamb}")
        print(f"   (These should have disambiguation)")
    else:
        print(f"✅ All multi-table columns have disambiguation")

    # Calculate expected vs actual
    expected_disamb = sum(1 for k, v in column_appearances.items() if len(v) > 1)
    print(f"\n{'=' * 80}")
    print(f"EXPECTED VS ACTUAL:")
    print(f"{'=' * 80}")
    print(f"Expected disambiguation count: {expected_disamb} (multi-table columns only)")
    print(f"Actual disambiguation count: {columns_with_disamb}")
    print(f"Difference: {columns_with_disamb - expected_disamb}")

    if columns_with_disamb == expected_disamb:
        print(f"✅ Perfect match! Phase 2.1 working correctly!")
    elif columns_with_disamb > expected_disamb:
        print(f"❌ Over-application: {columns_with_disamb - expected_disamb} extra disambiguation blocks")
    else:
        print(f"⚠️  Under-application: Missing {expected_disamb - columns_with_disamb} disambiguation blocks")

    # Return stats for comparison
    return {
        'database': database_name,
        'total_columns': total_columns,
        'columns_with_disamb': columns_with_disamb,
        'expected_disamb': expected_disamb,
        'single_table_errors': single_table_with_disamb,
        'multi_table_missing': multi_table_without_disamb
    }

def main():
    print("=" * 80)
    print("PHASE 2.1 CONDITIONAL DISAMBIGUATION TEST")
    print("=" * 80)
    print("\nTesting on databases that regressed in Run 20:")
    print("  - car_1 (Run 20: -4 questions)")
    print("  - world_1 (Run 20: -4 questions)")
    print("\nExpected behavior:")
    print("  - Disambiguation ONLY for columns appearing in 2+ tables")
    print("  - NO disambiguation for columns appearing in 1 table only")

    # Initialize services
    settings = get_settings()
    llm = OpenAIProvider(
        api_key=settings.openai_api_key,
        model=settings.llm_model
    )
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("\n❌ DATABASE_URL not set!")
        return

    generator = SemanticLayerGenerator(llm=llm, database_url=db_url, sample_rows=10)

    # Create output directory
    output_dir = Path(__file__).parent.parent / "data/phase21_test_layers"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_cost = 0.0

    for db_name in TEST_DATABASES:
        print(f"\n{'=' * 80}")
        print(f"GENERATING: {db_name}")
        print(f"{'=' * 80}")

        try:
            start_time = datetime.now()

            # Generate semantic layer
            result = generator.generate(
                database_name=db_name,
                anonymize=True,
                save_prompt=True
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if result.get('success'):
                # Save to file
                output_file = output_dir / f"{db_name}_phase21.json"
                with open(output_file, 'w') as f:
                    json.dump(result['semantic_layer'], f, indent=2)

                # Analyze disambiguation usage
                stats = analyze_disambiguation_usage(result['semantic_layer'], db_name)
                stats['cost'] = result.get('cost', 0.0)
                stats['tokens'] = result.get('tokens', 0)
                stats['duration'] = duration

                results.append(stats)
                total_cost += stats['cost']

                print(f"\n✅ Generated {db_name}")
                print(f"   File: {output_file}")
                print(f"   Cost: ${stats['cost']:.4f}")
                print(f"   Tokens: {stats['tokens']}")
                print(f"   Duration: {duration:.1f}s")

            else:
                print(f"\n❌ Failed to generate {db_name}")
                print(f"   Error: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"\n❌ Exception generating {db_name}: {e}")
            import traceback
            traceback.print_exc()

    # Final summary
    print(f"\n{'=' * 80}")
    print(f"PHASE 2.1 TEST SUMMARY")
    print(f"{'=' * 80}")

    for stats in results:
        print(f"\n{stats['database']}:")
        print(f"  Total columns: {stats['total_columns']}")
        print(f"  Expected disambiguation: {stats['expected_disamb']}")
        print(f"  Actual disambiguation: {stats['columns_with_disamb']}")
        print(f"  Single-table errors: {stats['single_table_errors']}")
        print(f"  Multi-table missing: {stats['multi_table_missing']}")

        if stats['single_table_errors'] == 0 and stats['multi_table_missing'] == 0:
            print(f"  ✅ PASS - Phase 2.1 working correctly!")
        else:
            print(f"  ❌ FAIL - Phase 2.1 not working as expected")

    print(f"\nTotal cost: ${total_cost:.4f}")

    # Compare to Phase 2 (Run 20)
    print(f"\n{'=' * 80}")
    print(f"COMPARISON TO PHASE 2 (Run 20):")
    print(f"{'=' * 80}")

    # Phase 2 had 100% disambiguation coverage
    for stats in results:
        if stats['database'] == 'car_1':
            print(f"\ncar_1:")
            print(f"  Phase 2: 23/23 columns with disambiguation (100%)")
            print(f"  Phase 2.1: {stats['columns_with_disamb']}/{stats['total_columns']} columns with disambiguation ({100 * stats['columns_with_disamb'] / stats['total_columns']:.1f}%)")
            reduction = ((23 - stats['columns_with_disamb']) / 23) * 100
            print(f"  Reduction: {reduction:.1f}%")

        elif stats['database'] == 'world_1':
            print(f"\nworld_1:")
            print(f"  Phase 2: 12/12 columns with disambiguation (100%)")
            print(f"  Phase 2.1: {stats['columns_with_disamb']}/{stats['total_columns']} columns with disambiguation ({100 * stats['columns_with_disamb'] / stats['total_columns']:.1f}%)")
            reduction = ((12 - stats['columns_with_disamb']) / 12) * 100
            print(f"  Reduction: {reduction:.1f}%")

    # Decision
    print(f"\n{'=' * 80}")
    print(f"RECOMMENDATION:")
    print(f"{'=' * 80}")

    all_pass = all(s['single_table_errors'] == 0 and s['multi_table_missing'] == 0 for s in results)

    if all_pass:
        print(f"✅ Phase 2.1 is working correctly!")
        print(f"   - Disambiguation only applied to multi-table columns")
        print(f"   - No single-table columns have disambiguation")
        print(f"   - Significant reduction in verbosity")
        print(f"\nRECOMMEND: Proceed with full regeneration (all 20 databases)")
    else:
        print(f"❌ Phase 2.1 has issues!")
        print(f"   - Review errors above")
        print(f"   - Consider refining prompt or adding post-processing")
        print(f"\nRECOMMEND: Fix issues before full regeneration")

if __name__ == "__main__":
    main()
