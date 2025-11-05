"""
Schema extractor for Turso databases.

Extracts schema information directly from Turso databases,
preserving the original case of table and column names.
"""

from typing import Dict, List, Any
from .turso_client import TursoClient


class TursoSchemaExtractor:
    """Extract schema and sample data from Turso databases."""

    def __init__(self):
        """Initialize the Turso schema extractor."""
        pass

    def extract_schema(self, database_name: str) -> Dict[str, Any]:
        """
        Extract schema information for a database from Turso.

        Args:
            database_name: Name of the database (e.g., 'network_1', 'world_1')

        Returns:
            Dictionary with tables, columns, foreign keys, row counts
        """
        client = TursoClient(database_name)

        # Get all tables
        table_names = client.get_table_names()

        tables = []
        for table_name in table_names:
            table_info = self._extract_table_info(client, table_name)
            tables.append(table_info)

        return {
            "database": database_name,
            "tables": tables
        }

    def _extract_table_info(self, client: TursoClient, table_name: str) -> Dict[str, Any]:
        """Extract detailed information for a single table."""

        # Get table info using PRAGMA
        pragma_result = client.execute(f"PRAGMA table_info(`{table_name}`)")

        columns = []
        pk_columns = set()

        for row in pragma_result["rows"]:
            cid, name, type_, notnull, default, pk = row

            columns.append({
                "name": name,  # Preserves original case!
                "type": type_,
                "nullable": notnull == 0,
                "default": default,
                "primary_key": pk > 0
            })
            if pk > 0:
                pk_columns.add(name)

        # Get foreign keys using PRAGMA
        fk_result = client.execute(f"PRAGMA foreign_key_list(`{table_name}`)")

        foreign_keys = []
        for row in fk_result["rows"]:
            id_, seq, referenced_table, from_column, to_column = row[:5]

            foreign_keys.append({
                "column": from_column,  # Preserves original case!
                "referenced_table": referenced_table,
                "referenced_column": to_column,
                "source": "turso_schema"
            })

        # Get row count
        row_count = client.get_row_count(f"`{table_name}`")

        return {
            "name": table_name,  # Preserves original case!
            "columns": columns,
            "foreign_keys": foreign_keys,
            "row_count": row_count
        }

    def sample_all_tables(
        self,
        database_name: str,
        limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Sample data from all tables in a database.

        Args:
            database_name: Name of the database
            limit: Maximum number of rows to sample per table

        Returns:
            Dictionary mapping table names to lists of row dictionaries
        """
        client = TursoClient(database_name)

        # Get all tables
        table_names = client.get_table_names()

        samples = {}
        for table_name in table_names:
            # Sample rows
            rows = client.sample_table(f"`{table_name}`", limit=limit)
            samples[table_name] = rows

        return samples
