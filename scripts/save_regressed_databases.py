#!/usr/bin/env python3
"""
Save car_1 and world_1 semantic layers to files for detailed review.
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

def main():
    # Connect to Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials!")
        return

    supabase = create_client(supabase_url, supabase_key)

    # Databases that regressed
    databases = ["car_1", "world_1"]

    # Create output directory
    output_dir = Path(__file__).parent.parent / "docs/phase2/regressed_databases"
    output_dir.mkdir(parents=True, exist_ok=True)

    for db_name in databases:
        print(f"Fetching {db_name}...")

        # Fetch semantic layer
        result = supabase.table("semantic_layers").select("database_name, updated_at, semantic_layer").eq("database_name", db_name).execute()

        if not result.data:
            print(f"❌ {db_name} not found in Supabase!")
            continue

        layer = result.data[0]

        # Save to file
        output_file = output_dir / f"{db_name}_phase2.json"
        with open(output_file, 'w') as f:
            json.dump(layer['semantic_layer'], f, indent=2)

        print(f"✅ Saved to {output_file}")
        print(f"   Updated: {layer['updated_at']}")

        # Print summary
        tables = layer['semantic_layer'].get('tables', [])
        total_rels = sum(len(t.get('relationships', [])) for t in tables)
        total_cols = sum(len(t.get('columns', [])) for t in tables)

        print(f"   Tables: {len(tables)}, Relationships: {total_rels}, Columns: {total_cols}")

    print(f"\n✅ Files saved to {output_dir}")

if __name__ == "__main__":
    main()
