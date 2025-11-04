#!/usr/bin/env python3
"""
Regenerate all Spider semantic layers with enriched FK metadata.
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import get_settings
from app.services.llm.openai_provider import OpenAIProvider
from app.services.semantic_layer_generator import SemanticLayerGenerator
from app.database.supabase_schema_extractor import SupabaseSchemaExtractor

# List of all Spider databases
SPIDER_DATABASES = [
    'concert_singer',
    'pets_1',
    'car_1',
    'flight_2',
    'employee_hire_evaluation',
    'cre_doc_template_mgt',
    'course_teach',
    'museum_visit',
    'wta_1',
    'battle_death',
    'student_transcripts_tracking',
    'tvshow',
    'poker_player',
    'voter_1',
    'world_1',
    'orchestra',
    'network_1',
    'dog_kennels',
    'singer',
    'real_estate_properties'
]

def main():
    print('=' * 70)
    print('REGENERATING ALL SPIDER SEMANTIC LAYERS WITH FK METADATA')
    print('=' * 70)

    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print('ERROR: DATABASE_URL not set in environment')
        return False

    # Get OpenAI API key
    settings = get_settings()

    # Initialize LLM
    print('\nInitializing OpenAI LLM...')
    llm = OpenAIProvider(
        api_key=settings.openai_api_key,
        model=settings.llm_model
    )

    # Initialize generator (with Spider metadata enabled by default)
    print('Initializing Semantic Layer Generator...')
    generator = SemanticLayerGenerator(
        llm=llm,
        database_url=db_url,
        sample_rows=10
    )

    # Initialize extractor to verify databases
    extractor = SupabaseSchemaExtractor(db_url, use_spider_metadata=True)
    available_dbs = extractor.list_databases()

    print(f'\nFound {len(available_dbs)} databases in Supabase')

    # Filter to only databases that exist
    databases_to_generate = [db for db in SPIDER_DATABASES if db in available_dbs]
    missing_dbs = [db for db in SPIDER_DATABASES if db not in available_dbs]

    if missing_dbs:
        print(f'\nWarning: {len(missing_dbs)} databases not found in Supabase:')
        for db in missing_dbs:
            print(f'  - {db}')

    print(f'\nWill regenerate {len(databases_to_generate)} semantic layers')

    # Create output directory
    output_dir = Path('data/semantic_layers')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Track results
    results = {
        'success': [],
        'failed': [],
        'total_cost': 0.0,
        'total_tokens': 0
    }

    # Process each database
    for i, db_name in enumerate(databases_to_generate, 1):
        print(f'\n{"=" * 70}')
        print(f'[{i}/{len(databases_to_generate)}] Processing: {db_name}')
        print(f'{"=" * 70}')

        try:
            # Generate semantic layer
            result = generator.generate(
                database_name=db_name,
                anonymize=True,
                save_prompt=True
            )

            # Save to output file
            output_file = output_dir / f'{db_name}.json'
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            # Extract stats
            semantic_layer = result['semantic_layer']
            tables = semantic_layer.get('tables', [])
            total_fks = sum(
                len([r for r in t.get('relationships', []) if r.get('type') == 'foreign_key'])
                for t in tables
            )

            print(f'✅ SUCCESS: {db_name}')
            print(f'   File: {output_file}')
            print(f'   Tables: {len(tables)}')
            print(f'   FK Relationships: {total_fks}')
            print(f'   Tokens: {result["metadata"]["tokens_used"]}')
            print(f'   Cost: ${result["metadata"]["cost_usd"]:.4f}')

            results['success'].append(db_name)
            results['total_cost'] += result['metadata']['cost_usd']
            results['total_tokens'] += result['metadata']['tokens_used']

        except Exception as e:
            print(f'❌ FAILED: {db_name}')
            print(f'   Error: {e}')
            results['failed'].append(db_name)
            import traceback
            traceback.print_exc()

    # Print summary
    print(f'\n{"=" * 70}')
    print('REGENERATION SUMMARY')
    print(f'{"=" * 70}')
    print(f'Successful: {len(results["success"])}/{len(databases_to_generate)}')
    print(f'Failed: {len(results["failed"])}')
    print(f'Total Tokens: {results["total_tokens"]:,}')
    print(f'Total Cost: ${results["total_cost"]:.2f}')
    print(f'Output Directory: {output_dir}')

    if results['failed']:
        print(f'\nFailed databases:')
        for db in results['failed']:
            print(f'  - {db}')

    print(f'\n{"=" * 70}')

    # If regeneration was successful, automatically run embeddings
    if len(results['success']) > 0:
        print(f'\n{"=" * 70}')
        print('STARTING AUTOMATIC EMBEDDING GENERATION')
        print(f'{"=" * 70}')
        print('Regeneration complete. Now generating embeddings for Pinecone...')
        print()

        try:
            # Import and run the embedding script
            from app.services.embedding_service import EmbeddingService
            from app.database.metadata_store import MetadataStore

            # Get environment variables for embedding
            openai_api_key = os.getenv("OPENAI_API_KEY")
            pinecone_api_key = os.getenv("PINECONE_API_KEY")
            pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
            pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "querydawg-semantic")
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

            # Validate environment variables
            if not all([openai_api_key, pinecone_api_key, pinecone_environment, supabase_url, supabase_service_role_key]):
                print("⚠️  Warning: Missing required environment variables for embedding")
                print("Skipping automatic embedding generation.")
                print("You can run embeddings manually with: python scripts/embed_semantic_layers.py")
            else:
                # Initialize embedding services
                print("Initializing embedding services...")
                embedding_service = EmbeddingService(
                    openai_api_key=openai_api_key,
                    pinecone_api_key=pinecone_api_key,
                    pinecone_environment=pinecone_environment,
                    pinecone_index_name=pinecone_index_name
                )

                metadata_store = MetadataStore(supabase_url, supabase_service_role_key)

                # Get semantic layers from Supabase
                print("Fetching semantic layers from Supabase...")
                semantic_layers = metadata_store.list_semantic_layers()
                print(f"Found {len(semantic_layers)} semantic layer(s)")
                print()

                # Process each semantic layer
                total_chunks = 0
                total_vectors = 0
                total_cost = 0.0

                for i, layer_metadata in enumerate(semantic_layers, 1):
                    database_name = layer_metadata['database_name']
                    print(f"[{i}/{len(semantic_layers)}] Embedding {database_name}...")

                    result = embedding_service.embed_semantic_layer(
                        database_name=database_name,
                        semantic_layer=layer_metadata['semantic_layer'],
                        metadata=layer_metadata.get('metadata', {})
                    )

                    total_chunks += result['chunks_created']
                    total_vectors += result['vectors_uploaded']
                    total_cost += result['cost_usd']

                    print(f"   ✅ Chunks: {result['chunks_created']}, "
                          f"Vectors: {result['vectors_uploaded']}, "
                          f"Cost: ${result['cost_usd']:.4f}")

                print()
                print(f'{"=" * 70}')
                print('EMBEDDING SUMMARY')
                print(f'{"=" * 70}')
                print(f"Databases processed: {len(semantic_layers)}")
                print(f"Total chunks: {total_chunks:,}")
                print(f"Total vectors: {total_vectors:,}")
                print(f"Total cost: ${total_cost:.2f}")
                print(f'{"=" * 70}')
                print('✅ REGENERATION AND EMBEDDING COMPLETE')
                print(f'{"=" * 70}')

        except Exception as e:
            print(f'⚠️  Warning: Failed to run automatic embedding: {e}')
            print('You can run embeddings manually with: python scripts/embed_semantic_layers.py')
            import traceback
            traceback.print_exc()
    else:
        print('\n⚠️  No semantic layers were successfully generated.')
        print('Skipping automatic embedding generation.')

    return len(results['failed']) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
