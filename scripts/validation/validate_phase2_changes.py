#!/usr/bin/env python3
"""
Validate that Phase 2 changes are present in semantic layers.
Checks for:
1. Bridge table documentation (is_bridge_table, complete_join_path)
2. Column disambiguation (disambiguation object)
"""
import json
from pathlib import Path

def validate_phase2_changes():
    """Validate Phase 2 enhancements in semantic layers"""
    
    semantic_dir = Path('data/semantic_layers')
    json_files = list(semantic_dir.glob('*.json'))
    
    # Exclude the summary file
    json_files = [f for f in json_files if not f.name.startswith('_')]
    
    print("=" * 70)
    print("VALIDATING PHASE 2 CHANGES")
    print("=" * 70)
    print(f"\nChecking {len(json_files)} semantic layer files\n")
    
    # Track statistics
    stats = {
        'total_dbs': len(json_files),
        'has_bridge_tables': 0,
        'has_disambiguation': 0,
        'has_complete_join_path': 0,
        'has_common_mistakes': 0,
        'bridge_table_examples': [],
        'disambiguation_examples': []
    }
    
    for json_file in sorted(json_files):
        db_name = json_file.stem
        
        with open(json_file) as f:
            data = json.load(f)
        
        tables = data.get('tables', [])
        
        # Check each table for Phase 2 features
        for table in tables:
            table_name = table.get('name', '')
            
            # Check relationships for bridge table markers
            relationships = table.get('relationships', [])
            for rel in relationships:
                # Check for is_bridge_table
                if rel.get('is_bridge_table'):
                    stats['has_bridge_tables'] += 1
                    stats['bridge_table_examples'].append({
                        'db': db_name,
                        'table': table_name,
                        'relationship': rel
                    })
                
                # Check for complete_join_path
                if rel.get('complete_join_path'):
                    stats['has_complete_join_path'] += 1
                
                # Check for common_mistakes
                if rel.get('common_mistakes'):
                    stats['has_common_mistakes'] += 1
            
            # Check columns for disambiguation
            columns = table.get('columns', [])
            for col in columns:
                if col.get('disambiguation'):
                    stats['has_disambiguation'] += 1
                    stats['disambiguation_examples'].append({
                        'db': db_name,
                        'table': table_name,
                        'column': col.get('name', ''),
                        'disambiguation': col['disambiguation']
                    })
    
    # Print results
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    
    print(f"\nTotal databases: {stats['total_dbs']}")
    print(f"\nPhase 2 Features Found:")
    print(f"  - Bridge table markers (is_bridge_table): {stats['has_bridge_tables']}")
    print(f"  - Complete join paths: {stats['has_complete_join_path']}")
    print(f"  - Common mistakes documented: {stats['has_common_mistakes']}")
    print(f"  - Column disambiguations: {stats['has_disambiguation']}")
    
    # Show examples
    if stats['bridge_table_examples']:
        print(f"\n" + "-" * 70)
        print(f"BRIDGE TABLE EXAMPLES (showing first 3):")
        print("-" * 70)
        for i, example in enumerate(stats['bridge_table_examples'][:3]):
            print(f"\n{i+1}. {example['db']} - {example['table']}")
            rel = example['relationship']
            print(f"   References: {rel.get('references_table')}")
            print(f"   Is bridge: {rel.get('is_bridge_table')}")
            if rel.get('complete_join_path'):
                print(f"   Join path: {rel.get('complete_join_path')}")
            if rel.get('business_meaning'):
                print(f"   Meaning: {rel.get('business_meaning')}")
            if rel.get('common_mistakes'):
                print(f"   Common mistakes: {rel.get('common_mistakes')}")
    
    if stats['disambiguation_examples']:
        print(f"\n" + "-" * 70)
        print(f"COLUMN DISAMBIGUATION EXAMPLES (showing first 3):")
        print("-" * 70)
        for i, example in enumerate(stats['disambiguation_examples'][:3]):
            print(f"\n{i+1}. {example['db']} - {example['table']}.{example['column']}")
            dis = example['disambiguation']
            if dis.get('appears_in_tables'):
                print(f"   Also appears in: {dis.get('appears_in_tables')}")
            if dis.get('this_table_meaning'):
                print(f"   This table meaning: {dis.get('this_table_meaning')}")
            if dis.get('usage_guidance'):
                print(f"   Usage guidance: {dis.get('usage_guidance')}")
    
    # Validation status
    print("\n" + "=" * 70)
    if stats['has_bridge_tables'] > 0 or stats['has_disambiguation'] > 0:
        print("✅ PHASE 2 FEATURES DETECTED")
    else:
        print("⚠️  WARNING: NO PHASE 2 FEATURES FOUND")
        print("This might indicate the Phase 2 prompt was not used.")
    print("=" * 70)
    
    return stats

if __name__ == '__main__':
    validate_phase2_changes()
