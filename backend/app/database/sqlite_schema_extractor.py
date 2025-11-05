"""
Schema extractor for local Spider SQLite databases.

Extracts schema information and sample data from Spider SQLite databases,
preserving the original case of table and column names.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional


class SQLiteSchemaExtractor:
    """Extract schema and sample data from local SQLite databases."""

    def __init__(self, spider_data_path: str = "data/spider/database"):
        """
        Initialize with path to Spider database directory.

        Args:
            spider_data_path: Path to directory containing Spider database folders
        """
        self.spider_data_path = Path(spider_data_path)

    def extract_schema(self, database_name: str) -> Dict[str, Any]:
        """
        Extract schema information for a database.

        Args:
            database_name: Name of the database (e.g., 'network_1', 'world_1')

        Returns:
            Dictionary with tables, columns, foreign keys, row counts
        """
        # Find the SQLite database file
        db_path = self.spider_data_path / database_name / f"{database_name}.sqlite"

        if not db_path.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        try:
            # Get all tables
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)

            tables = []
            for (table_name,) in cursor.fetchall():
                table_info = self._extract_table_info(cursor, table_name)
                tables.append(table_info)

            return {
                "database": database_name,
                "tables": tables
            }

        finally:
            cursor.close()
            conn.close()

    def _extract_table_info(self, cursor, table_name: str) -> Dict[str, Any]:
        """Extract detailed information for a single table."""

        # Get table info using PRAGMA
        cursor.execute(f"PRAGMA table_info({table_name})")
        pragma_columns = cursor.fetchall()

        columns = []
        pk_columns = set()

        for cid, name, type_, notnull, default, pk in pragma_columns:
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
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fk_rows = cursor.fetchall()

        foreign_keys = []
        for (id_, seq, referenced_table, from_column, to_column, *_) in fk_rows:
            foreign_keys.append({
                "column": from_column,  # Preserves original case!
                "referenced_table": referenced_table,
                "referenced_column": to_column,
                "source": "sqlite_schema"
            })

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        row_count = cursor.fetchone()[0]

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
        db_path = self.spider_data_path / database_name / f"{database_name}.sqlite"

        if not db_path.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()

        try:
            # Get all tables
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)

            tables = [row[0] for row in cursor.fetchall()]
            samples = {}

            for table_name in tables:
                # Sample rows (use backticks to handle any special chars in table names)
                cursor.execute(f"SELECT * FROM `{table_name}` LIMIT {limit}")
                rows = cursor.fetchall()

                # Convert Row objects to dictionaries
                samples[table_name] = [dict(row) for row in rows]

            return samples

        finally:
            cursor.close()
            conn.close()
