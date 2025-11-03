"""
Schema Extractor Factory

Creates the appropriate schema extractor based on configuration.
Supports both Supabase (PostgreSQL) and Turso (SQLite) sources.
"""

import os
from typing import Optional
from enum import Enum

from .base_client import SchemaExtractor


class DatabaseSource(str, Enum):
    """Supported database sources"""
    SUPABASE = "supabase"
    TURSO = "turso"


class SchemaExtractorFactory:
    """Factory for creating schema extractors"""

    @staticmethod
    def create(
        source: Optional[DatabaseSource] = None,
        database_url: Optional[str] = None,
        database_name: Optional[str] = None
    ) -> SchemaExtractor:
        """
        Create a schema extractor for the specified source

        Args:
            source: Database source (supabase or turso). If None, uses env var SPIDER_DATA_SOURCE
            database_url: Connection URL (for Supabase). If None, uses env var SUPABASE_DB_URL
            database_name: Database/schema name. Required for Turso, optional for Supabase

        Returns:
            SchemaExtractor instance

        Raises:
            ValueError: If source is invalid or required parameters missing
        """
        # Determine source
        if source is None:
            source_str = os.getenv("SPIDER_DATA_SOURCE", "supabase").lower()
            try:
                source = DatabaseSource(source_str)
            except ValueError:
                raise ValueError(
                    f"Invalid SPIDER_DATA_SOURCE: {source_str}. "
                    f"Must be one of: {[s.value for s in DatabaseSource]}"
                )

        # Create appropriate extractor
        if source == DatabaseSource.SUPABASE:
            from .supabase_schema_extractor import SupabaseSchemaExtractor

            if database_url is None:
                database_url = os.getenv("SUPABASE_DB_URL")
                if not database_url:
                    raise ValueError("SUPABASE_DB_URL environment variable not set")

            return SupabaseSchemaExtractor(
                database_url=database_url,
                use_spider_metadata=False  # Always use live schema
            )

        elif source == DatabaseSource.TURSO:
            from .turso_schema_extractor import TursoSchemaExtractor

            if database_name is None:
                raise ValueError("database_name required for Turso source")

            return TursoSchemaExtractor(db_name=database_name)

        else:
            raise ValueError(f"Unsupported database source: {source}")

    @staticmethod
    def get_default_source() -> DatabaseSource:
        """
        Get the default database source from environment

        Returns:
            DatabaseSource enum value
        """
        source_str = os.getenv("SPIDER_DATA_SOURCE", "supabase").lower()
        try:
            return DatabaseSource(source_str)
        except ValueError:
            print(f"Warning: Invalid SPIDER_DATA_SOURCE '{source_str}', using 'supabase'")
            return DatabaseSource.SUPABASE
