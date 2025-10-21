"""
Factory for creating schema extractors based on database type
"""
from .base import SchemaExtractor
from .postgresql import PostgreSQLSchemaExtractor


class SchemaExtractorFactory:
    """Factory to create appropriate schema extractor for database type"""

    @staticmethod
    def create(db_type: str, connection_string: str, schema_name: str = None) -> SchemaExtractor:
        """
        Create a schema extractor for the specified database type

        Args:
            db_type: Database type ('postgresql', 'sqlite', 'mysql', etc.)
            connection_string: Connection string or file path
            schema_name: Schema name (required for PostgreSQL, None for SQLite)

        Returns:
            SchemaExtractor instance

        Raises:
            ValueError: If database type is not supported
        """
        if db_type == 'postgresql':
            if not schema_name:
                raise ValueError("schema_name is required for PostgreSQL")
            return PostgreSQLSchemaExtractor(connection_string, schema_name)

        # Future database types can be added here:
        # elif db_type == 'sqlite':
        #     return SQLiteSchemaExtractor(connection_string)
        # elif db_type == 'mysql':
        #     return MySQLSchemaExtractor(connection_string, schema_name)

        raise ValueError(f"Unsupported database type: {db_type}")
