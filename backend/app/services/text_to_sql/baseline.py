"""
Baseline text-to-SQL generator using schema only
"""
import os
from typing import Dict, Any, Optional
from app.services.schema import SchemaExtractorFactory
from app.services.llm.config import LLMConfig
from app.services.llm.prompts import PromptTemplates


class BaselineSQLGenerator:
    """
    Generate SQL queries from natural language questions using only schema information

    This is the "baseline" approach without RAG, few-shot examples, or query history.
    """

    def __init__(self, database_url: str, database_name: str):
        """
        Initialize baseline SQL generator

        Args:
            database_url: PostgreSQL connection string
            database_name: Schema name in Supabase
        """
        self.database_url = database_url
        self.database_name = database_name
        self._schema_cache: Optional[Dict[str, Any]] = None

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
        """
        # Get schema
        schema = self._get_schema()

        # Get LLM provider for baseline SQL generation
        llm = LLMConfig.get_provider_for_task("baseline_sql")
        config = LLMConfig.get_task_config("baseline_sql")

        # Generate SQL
        system_prompt = PromptTemplates.baseline_sql_system()
        user_prompt = PromptTemplates.baseline_sql_user(question, schema)

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
                "database": self.database_name
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
