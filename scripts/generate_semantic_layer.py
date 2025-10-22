#!/usr/bin/env python3
"""
Script to generate semantic layers for Spider databases.

Usage:
    # Generate for a single database
    python scripts/generate_semantic_layer.py --database world_1

    # Generate for all databases
    python scripts/generate_semantic_layer.py --all

    # View the prompt that will be used
    python scripts/generate_semantic_layer.py --database world_1 --show-prompt-only

    # Use custom instructions
    python scripts/generate_semantic_layer.py --database world_1 --instructions "Focus on e-commerce patterns"
"""

import argparse
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import get_settings
from app.llm.openai_llm import OpenAILLM
from app.services.semantic_layer_generator import SemanticLayerGenerator, load_custom_instructions


def main():
    parser = argparse.ArgumentParser(
        description="Generate semantic layers for databases"
    )
    parser.add_argument(
        "--database",
        type=str,
        help="Database name (e.g., world_1, car_1)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate for all databases in data/spider/database/"
    )
    parser.add_argument(
        "--show-prompt-only",
        action="store_true",
        help="Show the prompt that would be used without generating"
    )
    parser.add_argument(
        "--instructions",
        type=str,
        help="Custom instructions for semantic layer generation"
    )
    parser.add_argument(
        "--instructions-file",
        type=str,
        help="Path to file containing custom instructions"
    )
    parser.add_argument(
        "--no-anonymize",
        action="store_true",
        help="Don't anonymize database name in prompt (use actual name)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/semantic_layers",
        help="Output directory for generated semantic layers"
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=10,
        help="Number of sample rows per table (default: 10)"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.database and not args.all:
        parser.error("Either --database or --all must be specified")

    if args.database and args.all:
        parser.error("Cannot specify both --database and --all")

    # Get database paths
    spider_db_dir = Path("data/spider/database")
    if not spider_db_dir.exists():
        print(f"Error: Spider database directory not found: {spider_db_dir}")
        sys.exit(1)

    if args.all:
        databases = sorted([f.stem for f in spider_db_dir.glob("*.sqlite")])
        if not databases:
            print(f"Error: No .sqlite files found in {spider_db_dir}")
            sys.exit(1)
    else:
        databases = [args.database]

    # Load custom instructions
    custom_instructions = ""
    if args.instructions:
        custom_instructions = args.instructions
    elif args.instructions_file:
        custom_instructions = load_custom_instructions(args.instructions_file)
    else:
        # Try default location
        custom_instructions = load_custom_instructions()

    if custom_instructions:
        print(f"Using custom instructions ({len(custom_instructions)} characters)")

    # Initialize LLM
    settings = get_settings()
    llm = OpenAILLM(
        api_key=settings.openai_api_key,
        model=settings.llm_model
    )

    # Initialize generator
    generator = SemanticLayerGenerator(
        llm=llm,
        custom_instructions=custom_instructions,
        sample_rows=args.sample_rows
    )

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each database
    for db_name in databases:
        db_path = spider_db_dir / f"{db_name}.sqlite"
        if not db_path.exists():
            print(f"Warning: Database not found: {db_path}")
            continue

        print(f"\n{'='*60}")
        print(f"Database: {db_name}")
        print(f"{'='*60}")

        try:
            if args.show_prompt_only:
                # Just show the prompt
                result = generator.generate(
                    database_path=str(db_path),
                    anonymize=not args.no_anonymize,
                    save_prompt=True
                )
                print("\nPROMPT:")
                print("-" * 60)
                print(result["prompt_used"])
                print("-" * 60)
                print(f"\nPrompt length: {len(result['prompt_used'])} characters")
            else:
                # Generate semantic layer
                result = generator.generate(
                    database_path=str(db_path),
                    anonymize=not args.no_anonymize,
                    save_prompt=True
                )

                # Save to file
                output_file = output_dir / f"{db_name}.json"
                with open(output_file, "w") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

                print(f"✓ Generated semantic layer: {output_file}")
                print(f"  Domain: {result['semantic_layer'].get('domain', 'Unknown')}")
                print(f"  Tables: {len(result['semantic_layer'].get('tables', []))}")
                print(f"  LLM: {result['metadata']['llm_model']}")
                print(f"  Prompt saved: Yes")

        except Exception as e:
            print(f"✗ Error generating semantic layer for {db_name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n{'='*60}")
    print(f"Done! Generated {len(databases)} semantic layer(s)")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
