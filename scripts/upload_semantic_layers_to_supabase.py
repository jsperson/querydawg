#!/usr/bin/env python3
"""
Upload Semantic Layers to Supabase

Uploads all semantic layers from data/semantic_layers/ to Supabase.
This should be run after regenerating semantic layers with Spider FK metadata.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database.metadata_store import MetadataStore


def main():
    """Upload all semantic layers to Supabase."""
    # Load environment variables
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not all([supabase_url, supabase_service_role_key]):
        print("❌ Error: Missing Supabase credentials")
        print("Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)

    print("=" * 70)
    print("UPLOADING SEMANTIC LAYERS TO SUPABASE")
    print("=" * 70)

    # Initialize metadata store
    print("\nInitializing Supabase connection...")
    metadata_store = MetadataStore(supabase_url, supabase_service_role_key)

    # Get all semantic layer files
    semantic_layers_dir = Path("data/semantic_layers")
    if not semantic_layers_dir.exists():
        print(f"❌ Error: Directory not found: {semantic_layers_dir}")
        sys.exit(1)

    layer_files = sorted(semantic_layers_dir.glob("*.json"))
    if not layer_files:
        print(f"❌ Error: No .json files found in {semantic_layers_dir}")
        sys.exit(1)

    print(f"Found {len(layer_files)} semantic layer file(s)")

    # Ask for confirmation
    print("\nThis will:")
    print(f"  - Upload {len(layer_files)} semantic layers to Supabase")
    print("  - Replace existing layers with the same database names")
    print("\nStarting upload...")
    print()

    # Track results
    results = {
        'success': [],
        'failed': [],
        'skipped': []
    }

    # Process each file
    for i, layer_file in enumerate(layer_files, 1):
        database_name = layer_file.stem
        print(f"[{i}/{len(layer_files)}] Processing: {database_name}")
        print("-" * 70)

        try:
            # Load semantic layer from file
            with open(layer_file, 'r') as f:
                data = json.load(f)

            # Validate structure
            if 'semantic_layer' not in data:
                print(f"⚠️  Skipping {database_name}: missing 'semantic_layer' key")
                results['skipped'].append(database_name)
                print()
                continue

            if 'metadata' not in data:
                print(f"⚠️  Skipping {database_name}: missing 'metadata' key")
                results['skipped'].append(database_name)
                print()
                continue

            semantic_layer = data['semantic_layer']
            metadata = data['metadata']
            prompt_used = data.get('prompt_used')

            # Delete existing layer if it exists
            try:
                existing = metadata_store.get_semantic_layer(
                    database_name,
                    connection_name="Supabase"
                )
                if existing:
                    print(f"   Deleting existing layer for {database_name}...")
                    metadata_store.delete_semantic_layer(
                        database_name,
                        connection_name="Supabase"
                    )
            except Exception as e:
                # Layer doesn't exist, that's fine
                pass

            # Save new semantic layer
            layer_id = metadata_store.save_semantic_layer(
                database_name=database_name,
                semantic_layer=semantic_layer,
                metadata=metadata,
                prompt_used=prompt_used,
                connection_name="Supabase"
            )

            # Count FK relationships
            tables = semantic_layer.get('tables', [])
            total_fks = sum(
                len([r for r in t.get('relationships', []) if r.get('type') == 'foreign_key'])
                for t in tables
            )

            print(f"✅ SUCCESS: {database_name}")
            print(f"   ID: {layer_id}")
            print(f"   Tables: {len(tables)}")
            print(f"   FK Relationships: {total_fks}")
            print(f"   LLM: {metadata.get('llm_model', 'unknown')}")
            print()

            results['success'].append(database_name)

        except Exception as e:
            print(f"❌ FAILED: {database_name}")
            print(f"   Error: {e}")
            results['failed'].append(database_name)
            import traceback
            traceback.print_exc()
            print()

    # Print summary
    print("=" * 70)
    print("UPLOAD SUMMARY")
    print("=" * 70)
    print(f"Successful: {len(results['success'])}/{len(layer_files)}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Skipped: {len(results['skipped'])}")

    if results['failed']:
        print(f"\nFailed uploads:")
        for db in results['failed']:
            print(f"  - {db}")

    if results['skipped']:
        print(f"\nSkipped files:")
        for db in results['skipped']:
            print(f"  - {db}")

    print()
    print("=" * 70)

    return len(results['failed']) == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
