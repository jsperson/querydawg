"""
Semantic Layer API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from ..config import get_settings
from ..services.llm.config import LLMConfig
from ..services.semantic_layer_generator import SemanticLayerGenerator
from ..database.metadata_store import MetadataStore, get_metadata_store
from ..dependencies import verify_api_key
from ..services.embedding_service import EmbeddingService


router = APIRouter(prefix="/api/semantic", tags=["semantic"])


# Pydantic models
class GenerateRequest(BaseModel):
    database: str
    custom_instructions: Optional[str] = None
    anonymize: bool = True
    sample_rows: int = 10
    connection_name: str = "Supabase"


class PromptRequest(BaseModel):
    database: str
    custom_instructions: Optional[str] = None
    anonymize: bool = True
    sample_rows: int = 10


class CustomInstructionsRequest(BaseModel):
    instructions: str


class SearchRequest(BaseModel):
    database: str
    query: str
    top_k: int = 5


class SearchResultChunk(BaseModel):
    chunk_type: str
    table_name: Optional[str]
    text: str
    score: float


class SearchResponse(BaseModel):
    database: str
    query: str
    results: List[SearchResultChunk]


class SemanticLayerResponse(BaseModel):
    database: str
    semantic_layer: Dict[str, Any]
    metadata: Dict[str, Any]
    prompt_used: Optional[str] = None


class SemanticLayerListItem(BaseModel):
    id: str
    connection_name: str
    database_name: str
    version: str
    created_at: str
    llm_model: str


# Dependency to get metadata store
def get_metadata_store_instance() -> MetadataStore:
    settings = get_settings()
    return get_metadata_store(
        settings.supabase_url,
        settings.supabase_service_role_key
    )


@router.post("/generate", response_model=SemanticLayerResponse)
async def generate_semantic_layer(
    request: GenerateRequest,
    _: str = Depends(verify_api_key),
    metadata_store: MetadataStore = Depends(get_metadata_store_instance)
):
    """
    Generate a semantic layer for a database.

    Extracts schema and sample data from Supabase,
    uses LLM to generate semantic documentation, and stores back in Supabase.

    Automatically deletes any existing semantic layers for this database before creating new one.
    """
    settings = get_settings()

    try:
        print(f"[GENERATE] Starting generation for database: {request.database}")

        # Initialize LLM provider for semantic layer generation
        print("[GENERATE] Initializing LLM provider...")
        llm = LLMConfig.get_provider_for_task("semantic_layer")
        print(f"[GENERATE] LLM provider initialized: {llm.__class__.__name__}, model: {llm.model}")

        # Get custom instructions (from request or stored)
        custom_instructions = request.custom_instructions
        if not custom_instructions:
            custom_instructions = metadata_store.get_custom_instructions()
        print(f"[GENERATE] Custom instructions: {len(custom_instructions) if custom_instructions else 0} chars")

        # Generate semantic layer (using Supabase PostgreSQL as source)
        print(f"[GENERATE] Creating generator with DATABASE_URL: {settings.database_url[:50]}...")
        generator = SemanticLayerGenerator(
            llm=llm,
            database_url=settings.database_url,  # PostgreSQL connection string
            custom_instructions=custom_instructions,
            sample_rows=request.sample_rows
        )
        print("[GENERATE] Generator created successfully")

        print(f"[GENERATE] Calling generator.generate() for {request.database}...")
        result = generator.generate(
            database_name=request.database,  # Schema name in Supabase
            anonymize=request.anonymize,
            save_prompt=True
        )
        print("[GENERATE] Generation completed successfully")

        # Delete existing semantic layers for this database (only after successful generation)
        print("[GENERATE] Deleting existing semantic layer...")
        metadata_store.delete_semantic_layer(
            database_name=request.database,
            connection_name=request.connection_name
        )

        # Save to Supabase metadata store
        print("[GENERATE] Saving to metadata store...")
        metadata_store.save_semantic_layer(
            database_name=request.database,
            semantic_layer=result["semantic_layer"],
            metadata=result["metadata"],
            prompt_used=result.get("prompt_used"),
            connection_name=request.connection_name
        )
        print("[GENERATE] Saved successfully!")

        return SemanticLayerResponse(
            database=request.database,
            semantic_layer=result["semantic_layer"],
            metadata=result["metadata"],
            prompt_used=result.get("prompt_used")
        )

    except Exception as e:
        print(f"[GENERATE ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating semantic layer: {type(e).__name__}: {str(e)}"
        )


@router.get("/{database}", response_model=SemanticLayerResponse)
async def get_semantic_layer(
    database: str,
    version: Optional[str] = None,
    connection_name: str = "Supabase",
    _: str = Depends(verify_api_key),
    metadata_store: MetadataStore = Depends(get_metadata_store_instance)
):
    """
    Retrieve a semantic layer from Supabase.

    Returns the latest version by default, or a specific version if provided.
    """
    result = metadata_store.get_semantic_layer(
        database,
        version,
        connection_name
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Semantic layer not found for database: {database} (connection: {connection_name})"
        )

    return SemanticLayerResponse(
        database=result["database_name"],
        semantic_layer=result["semantic_layer"],
        metadata=result["metadata"],
        prompt_used=result.get("prompt_used")
    )


@router.get("/", response_model=List[SemanticLayerListItem])
async def list_semantic_layers(
    _: str = Depends(verify_api_key),
    metadata_store: MetadataStore = Depends(get_metadata_store_instance)
):
    """
    List all semantic layers stored in Supabase.

    Returns metadata only (not full semantic layer content).
    """
    layers = metadata_store.list_semantic_layers()

    return [
        SemanticLayerListItem(
            id=layer["id"],
            connection_name=layer.get("connection_name", "Supabase"),
            database_name=layer["database_name"],
            version=layer["version"],
            created_at=layer["created_at"],
            llm_model=layer["metadata"].get("llm_model", "unknown")
        )
        for layer in layers
    ]


@router.post("/prompt", response_model=Dict[str, str])
async def get_generation_prompt(
    request: PromptRequest,
    _: str = Depends(verify_api_key),
    metadata_store: MetadataStore = Depends(get_metadata_store_instance)
):
    """
    Get the prompt that would be used to generate a semantic layer.

    Does NOT actually generate - just shows what would be sent to the LLM.
    Useful for verifying no dataset-specific information is leaked.
    """
    settings = get_settings()

    try:
        # Initialize LLM provider (not used for generation, only for building prompt)
        llm = LLMConfig.get_provider_for_task("semantic_layer")

        # Get custom instructions
        custom_instructions = request.custom_instructions
        if not custom_instructions:
            custom_instructions = metadata_store.get_custom_instructions()

        # Build prompt only (does NOT call LLM)
        generator = SemanticLayerGenerator(
            llm=llm,
            database_url=settings.database_url,  # PostgreSQL connection string
            custom_instructions=custom_instructions,
            sample_rows=request.sample_rows
        )

        result = generator.build_prompt_only(
            database_name=request.database,  # Schema name in Supabase
            anonymize=request.anonymize
        )

        return {
            "database": result["database"],
            "prompt": result["prompt"],
            "prompt_length": str(result["prompt_length"]),
            "anonymized": str(result["anonymized"])
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error building prompt: {str(e)}"
        )


@router.delete("/{database}")
async def delete_semantic_layer(
    database: str,
    connection_name: str = "Supabase",
    _: str = Depends(verify_api_key),
    metadata_store: MetadataStore = Depends(get_metadata_store_instance)
):
    """Delete semantic layer(s) for a database."""
    success = metadata_store.delete_semantic_layer(
        database,
        connection_name
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No semantic layers found for database: {database} (connection: {connection_name})"
        )

    return {"message": f"Deleted semantic layers for {database} ({connection_name})"}


@router.get("/overview/{database}", response_model=Dict[str, Any])
async def get_database_overview(
    database: str,
    connection_name: str = "Supabase",
    _: str = Depends(verify_api_key),
    metadata_store: MetadataStore = Depends(get_metadata_store_instance)
):
    """
    Get overview/summary of a database from its semantic layer.

    Returns domain, purpose, key entities, and typical questions to help
    users understand what the database contains and what questions they can ask.
    """
    result = metadata_store.get_semantic_layer(
        database,
        connection_name=connection_name
    )

    if not result or 'semantic_layer' not in result:
        raise HTTPException(
            status_code=404,
            detail=f"Semantic layer not found for database: {database}"
        )

    semantic_layer = result['semantic_layer']
    overview = semantic_layer.get('overview', {})

    # Return overview with database name
    return {
        "database": database,
        "overview": overview
    }


@router.get("/status", response_model=Dict[str, List[str]])
async def get_databases_with_semantic_layers(
    connection_name: str = "Supabase",
    _: str = Depends(verify_api_key),
    metadata_store: MetadataStore = Depends(get_metadata_store_instance)
):
    """
    Get list of databases that have semantic layers.

    Returns database names with existing semantic layers for status indicators.
    """
    databases = metadata_store.get_databases_with_semantic_layers(connection_name)
    return {"databases": databases}


@router.get("/instructions/get", response_model=Dict[str, str])
async def get_custom_instructions(
    _: str = Depends(verify_api_key),
    metadata_store: MetadataStore = Depends(get_metadata_store_instance)
):
    """Get stored custom instructions for semantic layer generation."""
    instructions = metadata_store.get_custom_instructions()
    return {"instructions": instructions}


@router.post("/instructions/set")
async def set_custom_instructions(
    request: CustomInstructionsRequest,
    _: str = Depends(verify_api_key),
    metadata_store: MetadataStore = Depends(get_metadata_store_instance)
):
    """Set custom instructions for semantic layer generation."""
    metadata_store.save_custom_instructions(request.instructions)
    return {"message": "Custom instructions saved"}


# Dependency to get embedding service
def get_embedding_service_instance() -> EmbeddingService:
    settings = get_settings()
    return EmbeddingService(
        openai_api_key=settings.openai_api_key,
        pinecone_api_key=settings.pinecone_api_key,
        pinecone_environment=settings.pinecone_environment,
        pinecone_index_name=settings.pinecone_index_name
    )


@router.post("/search", response_model=SearchResponse)
async def search_semantic_context(
    request: SearchRequest,
    _: str = Depends(verify_api_key),
    embedding_service: EmbeddingService = Depends(get_embedding_service_instance)
):
    """
    Search for relevant semantic context for a given query.

    Uses vector similarity search in Pinecone to find the most relevant
    semantic layer chunks for the user's question.
    """
    try:
        # Search for relevant chunks
        results = embedding_service.search_semantic_context(
            query=request.query,
            database_name=request.database,
            top_k=request.top_k
        )

        return SearchResponse(
            database=request.database,
            query=request.query,
            results=[
                SearchResultChunk(
                    chunk_type=chunk['chunk_type'],
                    table_name=chunk.get('table_name'),
                    text=chunk['text'],
                    score=chunk['score']
                )
                for chunk in results
            ]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching semantic context: {str(e)}"
        )
