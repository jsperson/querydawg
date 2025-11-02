#!/usr/bin/env python3
"""
Apply prompt logging migration to Supabase.

This adds columns to benchmark_results table for storing prompts used during benchmark runs.
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

def main():
    print("=" * 80)
    print("PROMPT LOGGING MIGRATION")
    print("=" * 80)
    print("\nThis migration adds prompt logging columns to benchmark_results table:")
    print("  - baseline_system_prompt")
    print("  - baseline_user_prompt")
    print("  - enhanced_system_prompt")
    print("  - enhanced_user_prompt")
    print("  - enhanced_semantic_chunks")
    print("\nBenefits:")
    print("  ✓ Debug failed queries by examining exact prompts")
    print("  ✓ Compare baseline vs enhanced prompt differences")
    print("  ✓ Analyze semantic layer retrieval quality")
    print("  ✓ Identify prompt engineering issues")
    print("\n" + "=" * 80)
    print("\nMigration SQL:")
    print("=" * 80)
    print()

    # Read and display migration SQL
    migration_file = Path(__file__).parent.parent / "migrations" / "002_add_prompt_logging.sql"
    with open(migration_file, 'r') as f:
        sql = f.read()
        print(sql)

    print("\n" + "=" * 80)
    print("INSTRUCTIONS:")
    print("=" * 80)
    print("\n1. Copy the SQL above")
    print("2. Go to Supabase SQL Editor")
    print("3. Paste and run the SQL")
    print("4. Verify migration success message")
    print("\n" + "=" * 80)
    print()


if __name__ == "__main__":
    main()
