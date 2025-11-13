#!/usr/bin/env python3
"""
Investigate why car_1 and world_1 regressed in Run 20 (Phase 2).
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from supabase import create_client

def analyze_semantic_layer(database_name, semantic_layer):
    """Analyze Phase 2 content quality for a database."""
    print(f"\n{'=' * 80}")
    print(f"ANALYZING: {database_name}")
    print(f"{'=' * 80}")

    tables = semantic_layer.get('tables', [])
    print(f"\nTables: {len(tables)}")

    # Analyze relationships
    total_rels = 0
    phase2_rels = 0
    rel_issues = []

    for table in tables:
        table_name = table.get('name', 'Unknown')
        relationships = table.get('relationships', [])
        total_rels += len(relationships)

        for rel in relationships:
            # Check Phase 2 fields
            has_join_pattern = 'join_pattern' in rel
            has_when_to_use = 'when_to_use' in rel
            has_vs_confusion = 'vs_confusion' in rel
            has_relationship_type = 'relationship_type' in rel
            has_is_bridge_table = 'is_bridge_table' in rel
            has_complete_join_path = 'complete_join_path' in rel

            if all([has_join_pattern, has_when_to_use, has_vs_confusion,
                   has_relationship_type, has_is_bridge_table, has_complete_join_path]):
                phase2_rels += 1
            else:
                rel_issues.append(f"Table {table_name}, FK {rel.get('column', 'Unknown')}: Missing Phase 2 fields")

            # Check for overly long or confusing descriptions
            vs_confusion = rel.get('vs_confusion', '')
            when_to_use = rel.get('when_to_use', [])

            if len(vs_confusion) > 200:
                rel_issues.append(f"Table {table_name}, FK {rel.get('column', 'Unknown')}: vs_confusion too long ({len(vs_confusion)} chars)")

            if len(when_to_use) > 5:
                rel_issues.append(f"Table {table_name}, FK {rel.get('column', 'Unknown')}: too many when_to_use items ({len(when_to_use)})")

    print(f"\nRelationships:")
    print(f"  Total: {total_rels}")
    print(f"  With Phase 2 fields: {phase2_rels}")
    print(f"  Coverage: {100 * phase2_rels / total_rels if total_rels > 0 else 0:.1f}%")

    if rel_issues:
        print(f"\n⚠️  Relationship Issues:")
        for issue in rel_issues[:5]:  # Show first 5
            print(f"  - {issue}")
        if len(rel_issues) > 5:
            print(f"  ... and {len(rel_issues) - 5} more")

    # Analyze columns
    total_cols = 0
    disambiguated_cols = 0
    col_issues = []

    for table in tables:
        table_name = table.get('name', 'Unknown')
        columns = table.get('columns', [])
        total_cols += len(columns)

        for col in columns:
            disamb = col.get('disambiguation', {})

            if disamb:
                has_primary_location = 'primary_location' in disamb
                has_foreign_key_locations = 'foreign_key_locations' in disamb
                has_directional_guidance = 'directional_guidance' in disamb
                has_subject_vs_relationship = 'subject_vs_relationship' in disamb

                if all([has_primary_location, has_foreign_key_locations,
                       has_directional_guidance, has_subject_vs_relationship]):
                    disambiguated_cols += 1
                else:
                    col_issues.append(f"Table {table_name}, Col {col.get('name', 'Unknown')}: Incomplete disambiguation")

                # Check for overly long guidance
                guidance = disamb.get('directional_guidance', '')
                if len(guidance) > 300:
                    col_issues.append(f"Table {table_name}, Col {col.get('name', 'Unknown')}: directional_guidance too long ({len(guidance)} chars)")

    print(f"\nColumns:")
    print(f"  Total: {total_cols}")
    print(f"  With Phase 2 disambiguation: {disambiguated_cols}")
    print(f"  Coverage: {100 * disambiguated_cols / total_cols if total_cols > 0 else 0:.1f}%")

    if col_issues:
        print(f"\n⚠️  Column Issues:")
        for issue in col_issues[:5]:  # Show first 5
            print(f"  - {issue}")
        if len(col_issues) > 5:
            print(f"  ... and {len(col_issues) - 5} more")

    # Sample a relationship to show content
    print(f"\n{'=' * 80}")
    print(f"SAMPLE RELATIONSHIP (first one with Phase 2 fields):")
    print(f"{'=' * 80}")

    for table in tables:
        for rel in table.get('relationships', []):
            if 'join_pattern' in rel and 'when_to_use' in rel:
                print(f"\nTable: {table.get('name', 'Unknown')}")
                print(f"FK Column: {rel.get('column', 'Unknown')}")
                print(f"References: {rel.get('references_table', 'Unknown')}")
                print(f"\nrelationship_type: {rel.get('relationship_type', 'N/A')}")
                print(f"is_bridge_table: {rel.get('is_bridge_table', 'N/A')}")
                print(f"\njoin_pattern:")
                print(f"  {rel.get('join_pattern', 'N/A')}")
                print(f"\nwhen_to_use:")
                for item in rel.get('when_to_use', [])[:3]:  # First 3
                    print(f"  - {item}")
                print(f"\nvs_confusion:")
                print(f"  {rel.get('vs_confusion', 'N/A')[:200]}...")
                print(f"\ncomplete_join_path:")
                print(f"  {rel.get('complete_join_path', 'N/A')}")

                # Also show business_meaning if it exists
                if 'business_meaning' in rel:
                    print(f"\nbusiness_meaning:")
                    print(f"  {rel.get('business_meaning', 'N/A')[:200]}...")

                return  # Just show one

    print("  (No relationships with Phase 2 fields found)")

def main():
    # Connect to Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials!")
        print(f"SUPABASE_URL: {supabase_url}")
        print(f"SUPABASE_SERVICE_ROLE_KEY: {'set' if supabase_key else 'not set'}")
        return

    supabase = create_client(supabase_url, supabase_key)

    # Databases that regressed
    databases = ["car_1", "world_1"]

    print("=" * 80)
    print("PHASE 2 REGRESSION INVESTIGATION")
    print("=" * 80)
    print(f"\nInvestigating databases that regressed in Run 20:")
    print(f"  - car_1: -4 questions (72.8% → 68.5%)")
    print(f"  - world_1: -4 questions (76.7% → 73.3%)")

    for db_name in databases:
        # Fetch semantic layer
        result = supabase.table("semantic_layers").select("database_name, updated_at, semantic_layer").eq("database_name", db_name).execute()

        if not result.data:
            print(f"\n❌ {db_name} not found in Supabase!")
            continue

        layer = result.data[0]
        analyze_semantic_layer(db_name, layer['semantic_layer'])

    print(f"\n{'=' * 80}")
    print("INVESTIGATION COMPLETE")
    print(f"{'=' * 80}")
    print("\nNext Steps:")
    print("1. Review sample relationships above for quality issues")
    print("2. Check if descriptions are too long/verbose")
    print("3. Look for confusing vs_confusion or directional_guidance")
    print("4. Consider comparing to Phase 1 versions if available")

if __name__ == "__main__":
    main()
