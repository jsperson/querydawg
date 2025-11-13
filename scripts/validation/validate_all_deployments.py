#!/usr/bin/env python3
"""
Comprehensive validation script for semantic layers and embeddings.

Checks:
1. Local semantic layer files
2. Supabase semantic layers
3. Pinecone embeddings
4. Case sensitivity in generated layers
5. Query best practices inclusion
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

import psycopg2
from pinecone import Pinecone


# 20 benchmark databases
BENCHMARK_DATABASES = [
    'battle_death', 'car_1', 'concert_singer', 'course_teach',
    'cre_doc_template_mgt', 'dog_kennels', 'employee_hire_evaluation',
    'flight_2', 'museum_visit', 'network_1', 'orchestra', 'pets_1',
    'poker_player', 'real_estate_properties', 'singer',
    'student_transcripts_tracking', 'tvshow', 'voter_1', 'world_1', 'wta_1'
]


def check_local_semantic_layers():
    """Check if semantic layers exist locally."""
    print("=" * 80)
    print("1. CHECKING LOCAL SEMANTIC LAYERS")
    print("=" * 80)

    local_dir = Path("data/semantic_layers")
    found = []
    missing = []

    for db in BENCHMARK_DATABASES:
        filepath = local_dir / f"{db}.json"
        if filepath.exists():
            found.append(db)
        else:
            missing.append(db)

    print(f"\n✅ Found: {len(found)}/20 semantic layers locally")
    if missing:
        print(f"❌ Missing: {missing}")

    return found, missing


def check_semantic_layer_quality(databases: List[str]):
    """Check quality of semantic layers (case sensitivity, best practices)."""
    print("\n" + "=" * 80)
    print("2. CHECKING SEMANTIC LAYER QUALITY")
    print("=" * 80)

    local_dir = Path("data/semantic_layers")

    results = {
        'case_sensitive': [],
        'has_best_practices': [],
        'missing_best_practices': [],
        'errors': []
    }

    # Test cases for case sensitivity
    case_tests = {
        'network_1': ['Friend', 'Highschooler', 'Likes'],
        'flight_2': ['Abbreviation'],
        'singer': ['Singer']
    }

    for db in databases:
        filepath = local_dir / f"{db}.json"
        if not filepath.exists():
            continue

        try:
            with open(filepath) as f:
                data = json.load(f)

            semantic_layer = data.get('semantic_layer', {})
            tables = semantic_layer.get('tables', [])

            # Check case sensitivity for specific databases
            if db in case_tests:
                table_names = [t['name'] for t in tables]
                expected_names = case_tests[db]

                has_correct_case = all(name in table_names for name in expected_names)
                if has_correct_case:
                    results['case_sensitive'].append(db)
                else:
                    print(f"⚠️  {db}: Expected {expected_names}, found {table_names}")

            # Check for query best practices
            query_guidelines = semantic_layer.get('query_guidelines', [])
            if query_guidelines:
                guidelines_text = ' '.join(query_guidelines).lower()

                has_select = 'select *' in guidelines_text or 'explicit column' in guidelines_text
                has_group_by = 'group by' in guidelines_text and 'id' in guidelines_text
                has_join = 'inner join' in guidelines_text or 'left join' in guidelines_text

                if has_select and has_group_by and has_join:
                    results['has_best_practices'].append(db)
                else:
                    results['missing_best_practices'].append(db)
            else:
                results['missing_best_practices'].append(db)

        except Exception as e:
            results['errors'].append((db, str(e)))

    print(f"\n✅ Case sensitivity correct: {len(results['case_sensitive'])}/{len(case_tests)} tested")
    for db in results['case_sensitive']:
        print(f"   - {db}")

    print(f"\n✅ Has query best practices: {len(results['has_best_practices'])}/{len(databases)}")

    if results['missing_best_practices']:
        print(f"\n⚠️  Missing best practices: {len(results['missing_best_practices'])}")
        for db in results['missing_best_practices'][:5]:
            print(f"   - {db}")

    if results['errors']:
        print(f"\n❌ Errors: {len(results['errors'])}")
        for db, error in results['errors'][:5]:
            print(f"   - {db}: {error}")

    return results


def check_supabase_semantic_layers():
    """Check if semantic layers are stored in Supabase."""
    print("\n" + "=" * 80)
    print("3. CHECKING SUPABASE SEMANTIC LAYERS")
    print("=" * 80)

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set, skipping Supabase check")
        return []

    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        # Check if semantic_layers table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'semantic_layers'
            )
        """)

        table_exists = cur.fetchone()[0]

        if not table_exists:
            print("⚠️  semantic_layers table doesn't exist in Supabase")
            cur.close()
            conn.close()
            return []

        # Get all semantic layers
        cur.execute("SELECT database_name FROM semantic_layers ORDER BY database_name")
        found = [row[0] for row in cur.fetchall()]

        cur.close()
        conn.close()

        print(f"\n✅ Found: {len(found)} semantic layers in Supabase")

        missing = [db for db in BENCHMARK_DATABASES if db not in found]
        if missing:
            print(f"❌ Missing from Supabase: {len(missing)}")
            for db in missing[:5]:
                print(f"   - {db}")

        return found

    except Exception as e:
        print(f"❌ Error checking Supabase: {e}")
        return []


def check_pinecone_embeddings():
    """Check if embeddings exist in Pinecone."""
    print("\n" + "=" * 80)
    print("4. CHECKING PINECONE EMBEDDINGS")
    print("=" * 80)

    pinecone_api_key = os.environ.get('PINECONE_API_KEY')
    if not pinecone_api_key:
        print("❌ PINECONE_API_KEY not set, skipping Pinecone check")
        return {}

    try:
        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index("querydawg-semantic")

        # Get stats
        stats = index.describe_index_stats()

        print(f"\n✅ Pinecone index stats:")
        print(f"   Total vectors: {stats.total_vector_count}")
        print(f"   Dimension: {stats.dimension}")

        # Check for each database by querying metadata
        found_databases = set()

        for db in BENCHMARK_DATABASES:
            # Try to fetch a vector for this database
            try:
                # Query with database filter
                results = index.query(
                    vector=[0.0] * 1536,  # Dummy vector
                    top_k=1,
                    include_metadata=True,
                    filter={"database": db}
                )

                if results.matches:
                    found_databases.add(db)
            except:
                pass

        print(f"\n✅ Found embeddings for: {len(found_databases)}/20 databases")

        missing = [db for db in BENCHMARK_DATABASES if db not in found_databases]
        if missing:
            print(f"❌ Missing from Pinecone: {len(missing)}")
            for db in missing[:5]:
                print(f"   - {db}")

        return {
            'total_vectors': stats.total_vector_count,
            'found_databases': list(found_databases),
            'missing_databases': missing
        }

    except Exception as e:
        print(f"❌ Error checking Pinecone: {e}")
        return {}


def generate_report(local_found, local_missing, quality_results, supabase_found, pinecone_results):
    """Generate final validation report."""
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    print(f"\n📁 LOCAL SEMANTIC LAYERS:")
    print(f"   ✅ Found: {len(local_found)}/20")
    print(f"   ❌ Missing: {len(local_missing)}/20")

    print(f"\n🗄️  SUPABASE SEMANTIC LAYERS:")
    print(f"   ✅ Found: {len(supabase_found)}/20")

    print(f"\n🔍 PINECONE EMBEDDINGS:")
    if pinecone_results:
        print(f"   ✅ Total vectors: {pinecone_results.get('total_vectors', 0)}")
        print(f"   ✅ Databases: {len(pinecone_results.get('found_databases', []))}/20")
    else:
        print(f"   ⚠️  Not checked")

    print(f"\n✅ QUALITY CHECKS:")
    print(f"   Case sensitivity: {len(quality_results.get('case_sensitive', []))} tested")
    print(f"   Query best practices: {len(quality_results.get('has_best_practices', []))}/{len(local_found)}")

    # Overall status
    print(f"\n" + "=" * 80)

    all_local = len(local_missing) == 0
    all_supabase = len(supabase_found) == 20
    all_pinecone = len(pinecone_results.get('found_databases', [])) == 20

    if all_local and all_supabase and all_pinecone:
        print("✅ ALL SYSTEMS VALIDATED - READY FOR BENCHMARK")
    else:
        print("⚠️  SOME ISSUES FOUND - SEE DETAILS ABOVE")

        if not all_local:
            print(f"   - {len(local_missing)} semantic layers missing locally")
        if not all_supabase:
            print(f"   - {20 - len(supabase_found)} semantic layers missing in Supabase")
        if not all_pinecone:
            missing_count = 20 - len(pinecone_results.get('found_databases', []))
            print(f"   - {missing_count} databases missing embeddings in Pinecone")

    print("=" * 80)


def main():
    print("\n" + "=" * 80)
    print("SEMANTIC LAYER & EMBEDDING VALIDATION")
    print("=" * 80)
    print(f"\nValidating 20 benchmark databases across all services...")

    # Run all checks
    local_found, local_missing = check_local_semantic_layers()

    quality_results = check_semantic_layer_quality(local_found)

    supabase_found = check_supabase_semantic_layers()

    pinecone_results = check_pinecone_embeddings()

    # Generate final report
    generate_report(local_found, local_missing, quality_results, supabase_found, pinecone_results)


if __name__ == '__main__':
    main()
