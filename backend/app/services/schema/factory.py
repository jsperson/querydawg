"""
Factory for creating schema extractors based on database type
"""
import os
from .base import SchemaExtractor
from .postgresql import PostgreSQLSchemaExtractor
from .turso import TursoSchemaExtractor


class SchemaExtractorFactory:
    """Factory to create appropriate schema extractor for database type"""

    @staticmethod
    def create(db_type: str = None, connection_string: str = None, schema_name: str = None) -> SchemaExtractor:
        """
        Create a schema extractor for the specified database type

        Args:
            db_type: Database type ('postgresql', 'sqlite', 'turso', 'mysql', etc.)
                    If None, uses SPIDER_DATA_SOURCE env var (defaults to 'postgresql')
            connection_string: Connection string (required for PostgreSQL)
                             For Turso, this parameter is ignored (uses db_name from schema_name)
            schema_name: Schema/database name
                        - For PostgreSQL: schema name (required)
                        - For Turso: database name (required, e.g., 'concert_singer')

        Returns:
            SchemaExtractor instance

        Raises:
            ValueError: If database type is not supported or required parameters missing
        """
        # Determine database type from env if not provided
        if db_type is None:
            source = os.getenv("SPIDER_DATA_SOURCE", "postgresql").lower()
            # Map source names to db_type
            if source in ["supabase", "postgresql"]:
                db_type = "postgresql"
            elif source in ["turso", "sqlite"]:
                db_type = "turso"
            else:
                db_type = source

        db_type = db_type.lower()

        if db_type == 'postgresql':
            if not schema_name:
                raise ValueError("schema_name is required for PostgreSQL")
            if not connection_string:
                # Try to get from env
                connection_string = os.getenv("DATABASE_URL")
                if not connection_string:
                    raise ValueError("connection_string or DATABASE_URL env var is required for PostgreSQL")
            return PostgreSQLSchemaExtractor(connection_string, schema_name)

        elif db_type in ['sqlite', 'turso']:
            if not schema_name:
                raise ValueError("schema_name (database name) is required for Turso")
            return TursoSchemaExtractor(db_name=schema_name)

        # Future database types can be added here:
        # elif db_type == 'mysql':
        #     return MySQLSchemaExtractor(connection_string, schema_name)

        raise ValueError(f"Unsupported database type: {db_type}")
