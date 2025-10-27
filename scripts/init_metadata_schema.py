#!/usr/bin/env python3
"""
Initialize Supabase schema for metadata storage.

This script prints the SQL needed to create the metadata tables in Supabase.
Copy and paste the SQL into the Supabase SQL Editor and run it.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.database.metadata_store import MetadataStore


def main():
    print("\n" + "=" * 80)
    print("QUERYDAWG METADATA SCHEMA INITIALIZATION")
    print("=" * 80)
    print("\nThis schema creates tables for storing:")
    print("  - Semantic layers (generated database documentation)")
    print("  - Settings (custom instructions, configuration)")
    print("\nInstructions:")
    print("  1. Copy the SQL below")
    print("  2. Go to your Supabase project")
    print("  3. Navigate to SQL Editor")
    print("  4. Paste and run the SQL")
    print("\n" + "=" * 80)
    print("\n")

    # Get the SQL from the metadata store
    store = MetadataStore("", "")  # Dummy instance just to get SQL
    store.initialize_schema()

    print("\n" + "=" * 80)
    print("After running the SQL, you can verify by checking the Tables section")
    print("in Supabase. You should see:")
    print("  - semantic_layers table")
    print("  - settings table")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
