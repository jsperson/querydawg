"""
Base Database Client Interface

Defines the common interface for database clients (Supabase, Turso, etc.)
This allows flexible switching between database sources.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional


class DatabaseClient(ABC):
    """Abstract base class for database clients"""

    @abstractmethod
    def execute(self, sql: str, params: Optional[List[Any]] = None) -> Tuple[Any, Optional[str]]:
        """
        Execute SQL query

        Args:
            sql: SQL query string
            params: Optional query parameters

        Returns:
            Tuple of (results, error_message)
            - results: Query results (format depends on implementation)
            - error_message: None if successful, error string if failed
        """
        pass

    @abstractmethod
    def get_table_names(self, schema: Optional[str] = None) -> List[str]:
        """
        Get list of all tables in the database

        Args:
            schema: Optional schema name (for PostgreSQL)

        Returns:
            List of table names
        """
        pass

    @abstractmethod
    def get_row_count(self, table_name: str, schema: Optional[str] = None) -> int:
        """
        Get row count for a table

        Args:
            table_name: Name of the table
            schema: Optional schema name (for PostgreSQL)

        Returns:
            Number of rows
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to database

        Returns:
            True if connection successful

        Raises:
            RuntimeError: If connection fails
        """
        pass


class SchemaExtractor(ABC):
    """Abstract base class for schema extractors"""

    @abstractmethod
    def extract_schema(self, database_name: str) -> Dict[str, Any]:
        """
        Extract complete schema information

        Args:
            database_name: Name of the database/schema

        Returns:
            Dictionary containing schema information
        """
        pass

    @abstractmethod
    def sample_all_tables(self, database_name: str, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        Sample data from all tables

        Args:
            database_name: Name of the database/schema
            limit: Maximum rows per table

        Returns:
            Dictionary mapping table names to sample rows
        """
        pass

    @abstractmethod
    def sample_table(self, database_name: str, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Sample data from a specific table

        Args:
            database_name: Name of the database/schema
            table_name: Name of the table
            limit: Maximum rows to return

        Returns:
            List of row dictionaries
        """
        pass
