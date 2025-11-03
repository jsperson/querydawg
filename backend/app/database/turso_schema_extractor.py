"""
Turso Schema Extractor for QueryDawg

Extracts schema information from Turso (SQLite) databases for semantic layer generation.
Maintains high fidelity with Spider's native SQLite format.
"""

from typing import Dict, Any, List
from .turso_client import TursoClient


class TursoSchemaExtractor:
    """Extract schema information from Turso (SQLite) databases"""

    def __init__(self, db_name: str):
        """
        Initialize schema extractor for a Turso database

        Args:
            db_name: Name of the Turso database
        """
        self.db_name = db_name
        self.client = TursoClient(db_name)

    def extract_schema(self) -> Dict[str, Any]:
        """
        Extract complete schema information

        Returns:
            Dictionary containing schema information:
            {
                "database": str,
                "tables": [
                    {
                        "name": str,
                        "row_count": int,
                        "columns": [
                            {
                                "name": str,
                                "type": str,
                                "nullable": bool,
                                "default": Any,
                                "primary_key": bool
                            }
                        ],
                        "foreign_keys": [
                            {
                                "column": str,
                                "referenced_table": str,
                                "referenced_column": str
                            }
                        ]
                    }
                ]
            }
        """
        # Get all tables
        tables_result = self.client.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )

        tables = []

        for row in tables_result["rows"]:
            table_name = row[0]
            tables.append(self._extract_table_schema(table_name))

        return {
            "database": self.db_name,
            "tables": tables
        }

    def _extract_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Extract schema for a single table

        Args:
            table_name: Name of the table

        Returns:
            Table schema dictionary
        """
        # Get table info using PRAGMA
        table_info = self.client.execute(f"PRAGMA table_info({table_name})")

        # Get foreign keys
        fk_info = self.client.execute(f"PRAGMA foreign_key_list({table_name})")

        # Get row count
        count_result = self.client.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = count_result["rows"][0][0]

        # Build column schema
        columns = []
        for col in table_info["rows"]:
            # PRAGMA table_info returns:
            # [cid, name, type, notnull, dflt_value, pk]
            columns.append({
                "name": col[1],  # column name
                "type": col[2] or "TEXT",  # data type (default to TEXT if empty)
                "nullable": not col[3],  # notnull flag (inverted)
                "default": col[4],  # default value
                "primary_key": bool(col[5])  # pk flag
            })

        # Build foreign key schema
        foreign_keys = []
        for fk in fk_info["rows"]:
            # PRAGMA foreign_key_list returns:
            # [id, seq, table, from, to, on_update, on_delete, match]
            foreign_keys.append({
                "column": fk[3],  # from column
                "referenced_table": fk[2],  # to table
                "referenced_column": fk[4],  # to column
                "source": "database"  # Indicate this came from actual DB constraints
            })

        return {
            "name": table_name,
            "row_count": row_count,
            "columns": columns,
            "foreign_keys": foreign_keys
        }

    def sample_all_tables(self, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        Sample data from all tables

        Args:
            limit: Maximum rows per table

        Returns:
            Dictionary mapping table names to sample rows:
            {
                "table_name": [
                    {"col1": val1, "col2": val2, ...},
                    ...
                ]
            }
        """
        tables_result = self.client.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )

        samples = {}

        for row in tables_result["rows"]:
            table_name = row[0]
            samples[table_name] = self.client.sample_table(table_name, limit)

        return samples

    def sample_table(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Sample data from a specific table

        Args:
            table_name: Name of the table
            limit: Maximum rows to return

        Returns:
            List of row dictionaries
        """
        return self.client.sample_table(table_name, limit)

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific table

        Args:
            table_name: Name of the table

        Returns:
            Table information dictionary
        """
        return self._extract_table_schema(table_name)

    def test_connection(self) -> bool:
        """
        Test connection to Turso database

        Returns:
            True if connection successful

        Raises:
            RuntimeError: If connection fails
        """
        return self.client.test_connection()
