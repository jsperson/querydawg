#!/usr/bin/env python3
"""
Embed Semantic Layers Script

Generates embeddings for all semantic layers and uploads them to Pinecone.
Run this after semantic layers have been generated.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.embedding_service import EmbeddingService
from app.database.metadata_store import MetadataStore


def main():
    """Main function to embed all semantic layers."""
    # Load environment variables
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    # Get required environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "querydawg-semantic")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # Validate environment variables
    if not all([openai_api_key, pinecone_api_key, pinecone_environment, supabase_url, supabase_service_role_key]):
        print("❌ Error: Missing required environment variables")
        print("Required: OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_ENVIRONMENT, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)

    print("=" * 80)
    print("QueryDawg Semantic Layer Embedding Generator")
    print("=" * 80)
    print()

    # Initialize services
    print("Initializing services...")
    embedding_service = EmbeddingService(
        openai_api_key=openai_api_key,
        pinecone_api_key=pinecone_api_key,
        pinecone_environment=pinecone_environment,
        pinecone_index_name=pinecone_index_name
    )

    metadata_store = MetadataStore(supabase_url, supabase_service_role_key)

    # Get Pinecone index stats
    print("\nPinecone Index Status:")
    stats = embedding_service.get_index_stats()
    print(f"  Total vectors: {stats['total_vectors']:,}")
    print(f"  Dimensions: {stats['dimension']}")
    print(f"  Index fullness: {stats['index_fullness']:.2%}")
    print()

    # Get all semantic layers
    print("Fetching semantic layers from Supabase...")
    semantic_layers = metadata_store.list_semantic_layers()

    if not semantic_layers:
        print("⚠️  No semantic layers found in database.")
        print("   Please generate semantic layers first using the admin interface.")
        sys.exit(0)

    print(f"Found {len(semantic_layers)} semantic layer(s)")
    print()

    # Show what will be done
    print("This will:")
    print(f"  - Generate embeddings for {len(semantic_layers)} database(s)")
    print("  - Upload vectors to Pinecone")
    print("  - Estimated cost: ~$0.10-0.50 (depending on semantic layer sizes)")
    print()
    print("Starting embedding generation...")

    print()
    print("=" * 80)
    print("Starting Embedding Generation")
    print("=" * 80)
    print()

    # Process each semantic layer
    total_chunks = 0
    total_vectors = 0
    total_cost = 0.0

    for i, layer_metadata in enumerate(semantic_layers, 1):
        database_name = layer_metadata['database_name']
        connection_name = layer_metadata.get('connection_name', 'Supabase')

        print(f"[{i}/{len(semantic_layers)}] Processing: {database_name}")
        print("-" * 80)

        try:
            # Fetch full semantic layer (list_semantic_layers only returns metadata)
            full_layer = metadata_store.get_semantic_layer(database_name, connection_name=connection_name)

            if not full_layer or 'semantic_layer' not in full_layer:
                print(f"⚠️  Skipping {database_name}: semantic layer data not found")
                print()
                continue

            semantic_layer = full_layer['semantic_layer']

            # Embed and upload
            result = embedding_service.embed_semantic_layer(
                semantic_layer=semantic_layer,
                database_name=database_name
            )

            print(f"✅ Success!")
            print(f"   Chunks created: {result['chunks_created']}")
            print(f"   Vectors uploaded: {result['vectors_uploaded']}")
            print(f"   Estimated tokens: {result['estimated_tokens']:,}")
            print(f"   Estimated cost: ${result['estimated_cost_usd']:.4f}")
            print(f"   Chunk types: {', '.join(set(result['chunk_types']))}")
            print()

            total_chunks += result['chunks_created']
            total_vectors += result['vectors_uploaded']
            total_cost += result['estimated_cost_usd']

        except Exception as e:
            print(f"❌ Error processing {database_name}: {e}")
            print()
            continue

    # Final summary
    print("=" * 80)
    print("Embedding Generation Complete!")
    print("=" * 80)
    print(f"Databases processed: {len(semantic_layers)}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Total vectors uploaded: {total_vectors}")
    print(f"Total estimated cost: ${total_cost:.4f}")
    print()

    # Final Pinecone stats
    print("Final Pinecone Index Status:")
    stats = embedding_service.get_index_stats()
    print(f"  Total vectors: {stats['total_vectors']:,}")
    print(f"  Index fullness: {stats['index_fullness']:.2%}")
    print()

    print("✅ All done! Vectors are ready for semantic search.")
    print()


if __name__ == "__main__":
    main()
