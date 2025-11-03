"""
Turso (SQLite) schema extractor for SQL generators

Extracts schema information from Turso-hosted SQLite databases.
"""
from typing import List, Dict, Any
from .base import SchemaExtractor
from ...database.turso_client import TursoClient


class TursoSchemaExtractor(SchemaExtractor):
    """Extract schema from Turso (libSQL/SQLite) databases"""

    def __init__(self, db_name: str):
        """
        Initialize with Turso database name

        Args:
            db_name: Name of the Turso database (e.g., 'concert_singer')
        """
        super().__init__(connection_info=db_name, schema_name=db_name)
        self.db_name = db_name
        self.client = TursoClient(db_name=db_name)

    def get_tables(self) -> List[Dict[str, Any]]:
        """
        Get list of all tables in the database

        Returns:
            List of dicts with 'name' key
        """
        result = self.client.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )

        return [{'name': row[0]} for row in result['rows']]

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all columns for a specific table

        Args:
            table_name: Name of the table

        Returns:
            List of dicts with keys: name, type, nullable, primary_key
        """
        # Get column info using PRAGMA
        table_info = self.client.execute(f"PRAGMA table_info({table_name})")

        columns = []
        for col in table_info['rows']:
            # PRAGMA table_info returns: [cid, name, type, notnull, dflt_value, pk]
            columns.append({
                'name': col[1],  # column name
                'type': col[2] or 'TEXT',  # data type (default to TEXT if empty)
                'nullable': not col[3],  # notnull flag (inverted)
                'primary_key': bool(col[5]),  # pk flag
                'default': col[4]  # default value (not in base interface but useful)
            })

        return columns

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all foreign keys for a specific table

        Args:
            table_name: Name of the table

        Returns:
            List of dicts with keys: column, referenced_table, referenced_column
        """
        # Get foreign key info using PRAGMA
        fk_info = self.client.execute(f"PRAGMA foreign_key_list({table_name})")

        foreign_keys = []
        for fk in fk_info['rows']:
            # PRAGMA foreign_key_list returns:
            # [id, seq, table, from, to, on_update, on_delete, match]
            foreign_keys.append({
                'column': fk[3],  # from column
                'referenced_table': fk[2],  # to table
                'referenced_column': fk[4]  # to column
            })

        return foreign_keys

    def get_row_count(self, table_name: str) -> int:
        """
        Get row count for a specific table

        Args:
            table_name: Name of the table

        Returns:
            Number of rows in the table
        """
        result = self.client.execute(f"SELECT COUNT(*) FROM {table_name}")
        return result['rows'][0][0]
