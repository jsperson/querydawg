"""
Enhanced text-to-SQL generator using schema + semantic layer
"""
import os
import json
from typing import Dict, Any, Optional
from app.services.schema import SchemaExtractorFactory
from app.services.llm.config import LLMConfig
from app.services.llm.prompts import PromptTemplates
from app.database.metadata_store import get_metadata_store
from app.config import get_settings


class EnhancedSQLGenerator:
    """
    Generate SQL queries from natural language questions using schema + semantic layer

    This is the "enhanced" approach that includes semantic documentation
    to provide better context about table meanings, column descriptions, and business logic.
    """

    def __init__(self, database_url: str, database_name: str, connection_name: str = "Supabase"):
        """
        Initialize enhanced SQL generator

        Args:
            database_url: PostgreSQL connection string
            database_name: Schema name in Supabase
            connection_name: Connection name for semantic layer lookup
        """
        self.database_url = database_url
        self.database_name = database_name
        self.connection_name = connection_name
        self._schema_cache: Optional[Dict[str, Any]] = None
        self._semantic_layer_cache: Optional[Dict[str, Any]] = None

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

    def _get_semantic_layer(self) -> Optional[Dict[str, Any]]:
        """
        Get semantic layer from metadata store (cached)

        Returns:
            Semantic layer dictionary or None if not found
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

        return self._semantic_layer_cache

    def generate_sql(self, question: str) -> Dict[str, Any]:
        """
        Generate SQL query from natural language question

        Args:
            question: Natural language question

        Returns:
            Dictionary with:
                - sql: Generated SQL query
                - explanation: Natural language explanation
                - metadata: Token usage, cost, timing, model info
                - has_semantic_layer: Whether semantic layer was used
        """
        # Get schema
        schema = self._get_schema()

        # Get semantic layer (may be None)
        semantic_layer = self._get_semantic_layer()

        # Get LLM provider for enhanced SQL generation
        llm = LLMConfig.get_provider_for_task("enhanced_sql")
        config = LLMConfig.get_task_config("enhanced_sql")

        # Generate SQL with semantic context
        system_prompt = PromptTemplates.enhanced_sql_system()
        user_prompt = PromptTemplates.enhanced_sql_user(question, schema, semantic_layer)

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
                "has_semantic_layer": semantic_layer is not None
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
