#!/usr/bin/env python3
"""
Test script to verify new semantic layer format works correctly.
Generates a semantic layer for a small database and validates the structure.
"""
import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.semantic_layer_generator import SemanticLayerGenerator
from backend.app.services.llm.openai_provider import OpenAIProvider
from backend.app.services.embedding_service import EmbeddingService

def test_generate_semantic_layer():
    """Test generating a semantic layer with new format."""

    # Initialize
    openai_api_key = os.getenv("OPENAI_API_KEY")
    database_url = os.getenv("SUPABASE_DB_URL")

    if not openai_api_key or not database_url:
        print("ERROR: Missing OPENAI_API_KEY or SUPABASE_DB_URL")
        return False

    # Use GPT-4o-mini for testing
    llm = OpenAIProvider(
        api_key=openai_api_key,
        model="gpt-4o-mini"
    )

    generator = SemanticLayerGenerator(
        llm=llm,
        database_url=database_url,
        sample_rows=5
    )

    # Generate for a small database
    test_database = "network_1"  # Small database with only 3 tables

    print(f"Generating semantic layer for {test_database}...")
    print("-" * 60)

    try:
        result = generator.generate(
            database_name=test_database,
            anonymize=False,
            save_prompt=False
        )

        semantic_layer = result["semantic_layer"]

        # Validate structure
        print("\n✓ Generation successful!")
        print(f"✓ Model: {result['metadata']['llm_model']}")
        print(f"✓ Tokens: {result['metadata']['tokens_used']}")
        print(f"✓ Cost: ${result['metadata']['cost_usd']:.4f}")

        # Check that old fields are NOT present
        errors = []

        for table in semantic_layer.get("tables", []):
            table_name = table.get("name")

            # These fields should NOT exist
            if "row_count" in table:
                errors.append(f"❌ {table_name}: has 'row_count' (should be removed)")
            if "primary_key" in table:
                errors.append(f"❌ {table_name}: has 'primary_key' (should be removed)")

            for col in table.get("columns", []):
                col_name = col.get("name")
                if "type" in col:
                    errors.append(f"❌ {table_name}.{col_name}: has 'type' (should be removed)")
                if "nullable" in col:
                    errors.append(f"❌ {table_name}.{col_name}: has 'nullable' (should be removed)")
                if "sample_values" in col:
                    errors.append(f"❌ {table_name}.{col_name}: has 'sample_values' (should be 'common_values')")

            for rel in table.get("relationships", []):
                if "references_column" in rel:
                    errors.append(f"❌ {table_name}: relationship has 'references_column' (should be removed)")
                if "cardinality" in rel:
                    errors.append(f"❌ {table_name}: relationship has 'cardinality' (should be removed)")
                if "join_pattern" in rel:
                    errors.append(f"❌ {table_name}: relationship has 'join_pattern' (should be removed)")

        # Check that domain_glossary is NOT present
        if "domain_glossary" in semantic_layer:
            errors.append("❌ Semantic layer has 'domain_glossary' (should be removed)")

        # Check that new fields ARE present
        for table in semantic_layer.get("tables", []):
            table_name = table.get("name")

            # These fields SHOULD exist
            if "business_name" not in table:
                errors.append(f"❌ {table_name}: missing 'business_name'")
            if "purpose" not in table:
                errors.append(f"❌ {table_name}: missing 'purpose'")

            for col in table.get("columns", []):
                col_name = col.get("name")
                if "business_name" not in col:
                    errors.append(f"❌ {table_name}.{col_name}: missing 'business_name'")
                if "business_meaning" not in col:
                    errors.append(f"❌ {table_name}.{col_name}: missing 'business_meaning'")

        if errors:
            print("\n" + "\n".join(errors))
            return False

        print("\n✓ Structure validation passed!")
        print("✓ No old schema fields present")
        print("✓ All required business context fields present")

        # Test chunking
        print("\nTesting embedding service chunking...")
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        pinecone_index = os.getenv("PINECONE_INDEX_NAME", "querydawg-semantic")

        if pinecone_api_key:
            embedding_service = EmbeddingService(
                openai_api_key=openai_api_key,
                pinecone_api_key=pinecone_api_key,
                pinecone_environment=pinecone_environment,
                pinecone_index_name=pinecone_index
            )

            chunks = embedding_service.chunk_semantic_layer(semantic_layer, test_database)
            print(f"✓ Created {len(chunks)} chunks")
            print(f"  Chunk types: {[c['metadata']['chunk_type'] for c in chunks]}")

            # Check no glossary chunks
            if any(c['metadata']['chunk_type'] == 'glossary' for c in chunks):
                print("❌ Found glossary chunk (should not exist)")
                return False

            print("✓ No glossary chunks (correct)")

            # Show sample chunk
            table_chunks = [c for c in chunks if c['metadata']['chunk_type'] == 'table']
            if table_chunks:
                print("\nSample table chunk:")
                print("-" * 60)
                print(table_chunks[0]['text'][:500])
                print("-" * 60)

        # Save for inspection
        output_path = Path(__file__).parent.parent / "data" / "semantic_layers_test" / f"{test_database}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(semantic_layer, f, indent=2)

        print(f"\n✓ Saved to: {output_path}")
        print("\n" + "="*60)
        print("SUCCESS! New semantic layer format is working correctly.")
        print("="*60)

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_generate_semantic_layer()
    sys.exit(0 if success else 1)
