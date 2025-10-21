"""
Base schema extractor - abstract class for database schema extraction
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class SchemaExtractor(ABC):
    """
    Abstract base class for extracting database schemas.

    Supports multiple database types (PostgreSQL, SQLite, MySQL, etc.)
    """

    def __init__(self, connection_info: str, schema_name: Optional[str] = None):
        """
        Initialize schema extractor

        Args:
            connection_info: Connection string (PostgreSQL) or file path (SQLite)
            schema_name: Schema name (PostgreSQL) or None (SQLite)
        """
        self.connection_info = connection_info
        self.schema_name = schema_name

    @abstractmethod
    def get_tables(self) -> List[Dict[str, Any]]:
        """
        Get list of all tables in the database/schema

        Returns:
            List of dicts with 'name' key
        """
        pass

    @abstractmethod
    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all columns for a specific table

        Args:
            table_name: Name of the table

        Returns:
            List of dicts with keys: name, type, nullable, primary_key
        """
        pass

    @abstractmethod
    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all foreign keys for a specific table

        Args:
            table_name: Name of the table

        Returns:
            List of dicts with keys: column, referenced_table, referenced_column
        """
        pass

    @abstractmethod
    def get_row_count(self, table_name: str) -> int:
        """
        Get row count for a specific table

        Args:
            table_name: Name of the table

        Returns:
            Number of rows in the table
        """
        pass

    def extract_full_schema(self) -> Dict[str, Any]:
        """
        Extract complete schema including all tables, columns, and relationships

        Returns:
            Dict with 'database' and 'tables' keys
        """
        tables = []

        for table_info in self.get_tables():
            table_name = table_info['name']

            tables.append({
                'name': table_name,
                'columns': self.get_columns(table_name),
                'foreign_keys': self.get_foreign_keys(table_name),
                'row_count': self.get_row_count(table_name)
            })

        return {
            'database': self.schema_name or 'main',
            'tables': tables
        }
