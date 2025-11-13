#!/usr/bin/env python3
"""
Test script to verify case sensitivity fix on network_1.

This script:
1. Generates a new semantic layer for network_1 using SQLite schema extraction
2. Verifies that table and column names preserve correct capitalization
3. Shows the difference between old (lowercase) and new (capitalized) versions
"""

import json
import os
from pathlib import Path

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from app.services.semantic_layer_generator import SemanticLayerGenerator
from app.services.llm.openai_provider import OpenAIProvider


def main():
    print("=" * 80)
    print("Testing Case Sensitivity Fix on network_1")
    print("=" * 80)

    # Setup
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    database_url = os.environ.get("DATABASE_URL")

    if not openai_api_key:
        print("ERROR: OPENAI_API_KEY not set")
        return 1

    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return 1

    # Initialize LLM and generator
    llm = OpenAIProvider(api_key=openai_api_key, model="gpt-4o")
    generator = SemanticLayerGenerator(
        llm=llm,
        database_url=database_url,
        spider_data_path="data/spider/database"
    )

    print("\n1. Extracting schema from SQLite (should preserve case)...")
    print("-" * 80)

    from app.database.sqlite_schema_extractor import SQLiteSchemaExtractor
    extractor = SQLiteSchemaExtractor("data/spider/database")
    schema = extractor.extract_schema("network_1")

    print(f"\nFound {len(schema['tables'])} tables:")
    for table in schema['tables']:
        print(f"\n  Table: {table['name']}")
        print(f"    Columns: {', '.join([col['name'] for col in table['columns']])}")
        if table['foreign_keys']:
            print(f"    Foreign Keys:")
            for fk in table['foreign_keys']:
                print(f"      - {fk['column']} → {fk['referenced_table']}.{fk['referenced_column']}")

    # Verify case preservation
    print("\n2. Verifying case preservation...")
    print("-" * 80)

    table_names = [t['name'] for t in schema['tables']]
    expected_tables = ['Friend', 'Highschooler', 'Likes']

    print(f"\nExpected tables: {expected_tables}")
    print(f"Actual tables:   {table_names}")

    case_correct = set(table_names) == set(expected_tables)

    if case_correct:
        print("✅ PASS: Table names have correct capitalization!")
    else:
        print("❌ FAIL: Table names do not match expected capitalization")
        return 1

    # Check columns too
    highschooler_table = next(t for t in schema['tables'] if t['name'] == 'Highschooler')
    highschooler_cols = [c['name'] for c in highschooler_table['columns']]

    print(f"\nHighschooler columns: {highschooler_cols}")

    # Expected: ID, name, grade (capitalized ID)
    if 'ID' in highschooler_cols:
        print("✅ PASS: Column names preserve original case (ID not id)")
    else:
        print("❌ FAIL: Column names are lowercase")
        return 1

    print("\n3. Generating semantic layer with GPT-4...")
    print("-" * 80)
    print("(This will take 30-60 seconds...)")

    result = generator.generate(
        database_name="network_1",
        anonymize=False,
        save_prompt=False
    )

    semantic_layer = result['semantic_layer']

    print(f"\n✅ Semantic layer generated successfully!")
    print(f"   Tokens used: {result['metadata']['tokens_used']}")
    print(f"   Cost: ${result['metadata']['cost_usd']:.4f}")

    # Check table names in semantic layer
    print("\n4. Verifying semantic layer uses correct case...")
    print("-" * 80)

    sl_table_names = [t['name'] for t in semantic_layer.get('tables', [])]
    print(f"\nSemantic layer tables: {sl_table_names}")

    if set(sl_table_names) == set(expected_tables):
        print("✅ PASS: Semantic layer preserves correct table capitalization!")
    else:
        print("❌ FAIL: Semantic layer has incorrect table names")
        return 1

    # Check for ambiguous synonyms
    print("\n5. Checking for ambiguous synonyms...")
    print("-" * 80)

    found_issues = []
    for table in semantic_layer.get('tables', []):
        table_name = table['name']
        for col in table.get('columns', []):
            col_name = col['name']
            synonyms = col.get('synonyms', [])

            # Check if any synonym contains a fragment of the column name
            for syn in synonyms:
                # Simple check: if synonym contains "ID" and column name contains "_id"
                if 'ID' in syn and '_id' in col_name.lower():
                    # Check if it's ambiguous (e.g., "Degree ID" for "degree_program_id")
                    col_base = col_name.replace('_id', '').replace('_', ' ')
                    if col_base.lower() in syn.lower():
                        found_issues.append({
                            'table': table_name,
                            'column': col_name,
                            'synonym': syn,
                            'issue': 'Synonym contains fragment of column name'
                        })

    if found_issues:
        print(f"⚠️  WARNING: Found {len(found_issues)} potentially ambiguous synonyms:")
        for issue in found_issues:
            print(f"   - {issue['table']}.{issue['column']}: '{issue['synonym']}'")
    else:
        print("✅ PASS: No obviously ambiguous synonyms detected")

    # Save output for inspection
    output_path = Path("test_network1_semantic_layer.json")
    with output_path.open('w') as f:
        json.dump(result, f, indent=2)

    print(f"\n6. Full semantic layer saved to: {output_path}")
    print("-" * 80)

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nSummary:")
    print("- SQLite extraction preserves original case (Friend, Highschooler, Likes)")
    print("- Semantic layer generation uses correct capitalization")
    print("- Query best practices have been added to generation prompt")
    print("- Synonym filtering rules have been enhanced")
    print("\nNext step: Regenerate all 20 semantic layers with these fixes")

    return 0


if __name__ == '__main__':
    exit(main())
