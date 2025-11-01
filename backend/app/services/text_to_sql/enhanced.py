"""
Enhanced text-to-SQL generator using schema + semantic layer
"""
import os
import json
from typing import Dict, Any, Optional, List
from app.services.schema import SchemaExtractorFactory
from app.services.llm.config import LLMConfig
from app.services.llm.prompts import PromptTemplates
from app.database.metadata_store import get_metadata_store
from app.services.embedding_service import EmbeddingService
from app.config import get_settings


class EnhancedSQLGenerator:
    """
    Generate SQL queries from natural language questions using schema + semantic layer

    This is the "enhanced" approach that includes semantic documentation
    to provide better context about table meanings, column descriptions, and business logic.
    """

    def __init__(
        self,
        database_url: str,
        database_name: str,
        connection_name: str = "Supabase",
        use_vector_search: bool = True,
        top_k_chunks: int = 5
    ):
        """
        Initialize enhanced SQL generator

        Args:
            database_url: PostgreSQL connection string
            database_name: Schema name in Supabase
            connection_name: Connection name for semantic layer lookup
            use_vector_search: If True, use vector search for semantic context retrieval
            top_k_chunks: Number of semantic chunks to retrieve (if using vector search)
        """
        self.database_url = database_url
        self.database_name = database_name
        self.connection_name = connection_name
        self.use_vector_search = use_vector_search
        self.top_k_chunks = top_k_chunks
        self._schema_cache: Optional[Dict[str, Any]] = None
        self._semantic_layer_cache: Optional[Dict[str, Any]] = None
        self._embedding_service: Optional[EmbeddingService] = None

        # Tracking for last retrieval
        self._last_retrieval_method: Optional[str] = None
        self._last_chunks_retrieved: int = 0

    def _get_schema(self) -> Dict[str, Any]:
        """
        Get database schema (cached)

        Returns:
            Schema dictionary from SchemaExtractor
        """
        if self._schema_cache is None:
            extractor = SchemaExtractorFactory.create(
                db_type='postgresql',
                connection_string=self.database_url,
                schema_name=self.database_name
            )
            self._schema_cache = extractor.extract_full_schema()

        return self._schema_cache

    def _get_embedding_service(self) -> EmbeddingService:
        """
        Get embedding service instance (lazy initialization)

        Returns:
            EmbeddingService instance
        """
        if self._embedding_service is None:
            settings = get_settings()
            self._embedding_service = EmbeddingService(
                openai_api_key=settings.openai_api_key,
                pinecone_api_key=settings.pinecone_api_key,
                pinecone_environment=settings.pinecone_environment,
                pinecone_index_name=settings.pinecone_index_name
            )
        return self._embedding_service

    def _get_semantic_context(self, question: str) -> Optional[str]:
        """
        Get relevant semantic context for the question.

        If use_vector_search is True, retrieves relevant chunks via vector search.
        Otherwise, loads the full semantic layer from metadata store.

        Tracks retrieval method for analysis:
        - "vector_search_success": Successfully retrieved chunks from Pinecone
        - "vector_search_empty_fallback": Pinecone returned 0 results, used full layer
        - "vector_search_error_fallback": Pinecone error, used full layer
        - "full_layer_direct": Configured to use full layer (no vector search)
        - "none": No semantic layer available

        Args:
            question: Natural language question

        Returns:
            Formatted semantic context string or None if not available
        """
        if self.use_vector_search:
            # Use vector search to get relevant chunks
            try:
                embedding_service = self._get_embedding_service()
                chunks = embedding_service.search_semantic_context(
                    query=question,
                    database_name=self.database_name,
                    top_k=self.top_k_chunks
                )

                if not chunks:
                    # No chunks found in Pinecone - fall back to full semantic layer
                    print(f"Warning: Vector search returned 0 chunks for {self.database_name}, falling back to full semantic layer")
                    self._last_retrieval_method = "vector_search_empty_fallback"
                    self._last_chunks_retrieved = 0
                    return self._get_full_semantic_layer_text()

                # Successfully retrieved chunks
                self._last_retrieval_method = "vector_search_success"
                self._last_chunks_retrieved = len(chunks)

                # Format chunks into a readable context
                context_parts = [f"Relevant semantic information for {self.database_name}:\n"]

                for i, chunk in enumerate(chunks, 1):
                    context_parts.append(f"\n[Context {i}] ({chunk['chunk_type']}, relevance: {chunk['score']:.3f})")
                    if chunk.get('table_name'):
                        context_parts.append(f"Table: {chunk['table_name']}")
                    context_parts.append(chunk['text'])

                return "\n".join(context_parts)

            except Exception as e:
                print(f"Warning: Vector search failed with error: {e}")
                print(f"Falling back to full semantic layer for {self.database_name}")
                # Fall back to full semantic layer on error
                self._last_retrieval_method = "vector_search_error_fallback"
                self._last_chunks_retrieved = 0
                return self._get_full_semantic_layer_text()

        else:
            # Configured to use full semantic layer directly
            self._last_retrieval_method = "full_layer_direct"
            self._last_chunks_retrieved = 0
            return self._get_full_semantic_layer_text()

    def _get_full_semantic_layer_text(self) -> Optional[str]:
        """
        Get full semantic layer from metadata store and format as text.

        Returns:
            Formatted semantic layer string or None if not found
        """
        if self._semantic_layer_cache is None:
            settings = get_settings()
            metadata_store = get_metadata_store(
                settings.supabase_url,
                settings.supabase_service_role_key
            )

            result = metadata_store.get_semantic_layer(
                self.database_name,
                connection_name=self.connection_name
            )

            if result:
                self._semantic_layer_cache = result.get("semantic_layer")

        if not self._semantic_layer_cache:
            # Track when no semantic layer is available
            if self._last_retrieval_method is None:
                self._last_retrieval_method = "none"
            return None

        # Convert semantic layer to formatted text
        return json.dumps(self._semantic_layer_cache, indent=2)

    def generate_sql(self, question: str) -> Dict[str, Any]:
        """
        Generate SQL query from natural language question

        Args:
            question: Natural language question

        Returns:
            Dictionary with:
                - sql: Generated SQL query
                - explanation: Natural language explanation
                - metadata: Token usage, cost, timing, model info, retrieval tracking
        """
        # Get schema
        schema = self._get_schema()

        # Get semantic context (may be None)
        # This also sets self._last_retrieval_method and self._last_chunks_retrieved
        semantic_context = self._get_semantic_context(question)

        # Track if no semantic layer was available
        if semantic_context is None and self._last_retrieval_method is None:
            self._last_retrieval_method = "none"
            self._last_chunks_retrieved = 0

        # Get LLM provider for enhanced SQL generation
        llm = LLMConfig.get_provider_for_task("enhanced_sql")
        config = LLMConfig.get_task_config("enhanced_sql")

        # Generate SQL with semantic context
        system_prompt = PromptTemplates.enhanced_sql_system()
        user_prompt = PromptTemplates.enhanced_sql_user_with_context(
            question, schema, semantic_context
        )

        response = llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=config["temperature"],
            max_tokens=config.get("max_tokens")
        )

        # Generate explanation
        explanation = self._generate_explanation(question, response.content)

        return {
            "sql": response.content,
            "explanation": explanation,
            "metadata": {
                "tokens_used": response.tokens_used,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "cost_usd": response.cost_usd,
                "generation_time_ms": response.generation_time_ms,
                "model": response.model,
                "provider": response.provider,
                "database": self.database_name,
                "has_semantic_context": semantic_context is not None,
                "used_vector_search": self.use_vector_search,
                # New tracking fields
                "semantic_retrieval_method": self._last_retrieval_method,
                "semantic_chunks_retrieved": self._last_chunks_retrieved
            }
        }

    def _generate_explanation(self, question: str, sql: str) -> str:
        """
        Generate natural language explanation of the SQL query

        Args:
            question: Original question
            sql: Generated SQL query

        Returns:
            Natural language explanation
        """
        try:
            llm = LLMConfig.get_provider_for_task("sql_explanation")
            config = LLMConfig.get_task_config("sql_explanation")

            system_prompt = PromptTemplates.sql_explanation_system()
            user_prompt = PromptTemplates.sql_explanation_user(sql, question)

            response = llm.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=config["temperature"],
                max_tokens=config.get("max_tokens")
            )

            return response.content

        except Exception as e:
            # If explanation fails, return a simple fallback
            return f"This query answers: {question}"
