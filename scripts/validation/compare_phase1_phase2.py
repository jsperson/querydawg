#!/usr/bin/env python3
"""
Compare Phase 1 and Phase 2 semantic layers to show improvements.
"""
import json
from pathlib import Path

def compare_phases():
    """Compare Phase 1 and Phase 2 semantic layers"""
    
    phase1_dir = Path('data/semantic_layers_phase1')
    phase2_dir = Path('data/semantic_layers')
    
    phase1_files = {f.stem: f for f in phase1_dir.glob('*.json') if not f.name.startswith('_')}
    phase2_files = {f.stem: f for f in phase2_dir.glob('*.json') if not f.name.startswith('_')}
    
    print("=" * 70)
    print("PHASE 1 vs PHASE 2 COMPARISON")
    print("=" * 70)
    
    # Pick a few interesting databases to compare
    examples = ['concert_singer', 'network_1', 'student_transcripts_tracking']
    
    for db_name in examples:
        if db_name not in phase1_files or db_name not in phase2_files:
            continue
            
        print(f"\n{'=' * 70}")
        print(f"DATABASE: {db_name}")
        print('=' * 70)
        
        with open(phase1_files[db_name]) as f:
            phase1_data = json.load(f)
        
        with open(phase2_files[db_name]) as f:
            phase2_data = json.load(f)
        
        # Compare relationships
        for table in phase2_data.get('tables', []):
            table_name = table.get('name', '')
            relationships = table.get('relationships', [])
            
            # Find bridge tables
            bridge_rels = [r for r in relationships if r.get('is_bridge_table')]
            if bridge_rels:
                print(f"\n📊 Table: {table_name}")
                print("-" * 70)
                for rel in bridge_rels:
                    print(f"   ✨ BRIDGE TABLE DETECTED")
                    print(f"      References: {rel.get('references_table')}")
                    print(f"      Join path: {rel.get('complete_join_path')}")
                    print(f"      Business meaning: {rel.get('business_meaning')}")
                    if rel.get('common_mistakes'):
                        print(f"      ⚠️  Common mistakes:")
                        for mistake in rel.get('common_mistakes', []):
                            print(f"         - {mistake}")
            
            # Find disambiguated columns
            columns = table.get('columns', [])
            disambiguated = [c for c in columns if c.get('disambiguation')]
            if disambiguated and len(disambiguated) <= 2:  # Show a couple examples
                for col in disambiguated[:2]:
                    dis = col.get('disambiguation', {})
                    print(f"\n   🔍 Column: {col.get('name')}")
                    print(f"      Disambiguation:")
                    if dis.get('appears_in_tables'):
                        print(f"         Also in: {dis.get('appears_in_tables')}")
                    if dis.get('this_table_meaning'):
                        print(f"         Meaning here: {dis.get('this_table_meaning')}")
    
    print("\n" + "=" * 70)
    print("SUMMARY OF PHASE 2 IMPROVEMENTS")
    print("=" * 70)
    print("""
Phase 2 adds critical metadata for text-to-SQL generation:

1. BRIDGE TABLE DOCUMENTATION
   - Identifies many-to-many relationship tables
   - Documents complete join paths
   - Warns about common mistakes (skipping bridge tables)
   
2. COLUMN DISAMBIGUATION  
   - Identifies columns with same name across tables
   - Clarifies semantic differences
   - Provides usage guidance for ambiguous references

3. ENHANCED RELATIONSHIPS
   - Richer business meaning explanations
   - Common query patterns
   - Typical errors to avoid

These improvements should help the LLM:
- Avoid skipping bridge tables in joins
- Use correct table qualifications for ambiguous columns
- Better understand relationship semantics
""")

if __name__ == '__main__':
    compare_phases()
