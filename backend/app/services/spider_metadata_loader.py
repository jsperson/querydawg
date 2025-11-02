"""
Spider Metadata Loader

Loads foreign key relationships and other metadata from Spider's tables.json
to enhance semantic layer generation with accurate relationship information.
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class SpiderMetadataLoader:
    """Load and parse Spider benchmark metadata."""

    def __init__(self, tables_json_path: str = "data/spider/tables.json"):
        """
        Initialize loader with path to Spider's tables.json.

        Args:
            tables_json_path: Path to Spider's tables.json file
        """
        self.tables_json_path = Path(tables_json_path)
        self._metadata_cache: Optional[Dict] = None

    def _load_metadata(self) -> List[Dict]:
        """Load Spider tables.json if not already cached."""
        if self._metadata_cache is None:
            with open(self.tables_json_path) as f:
                self._metadata_cache = json.load(f)
        return self._metadata_cache

    def get_foreign_keys(self, database_name: str) -> List[Dict[str, str]]:
        """
        Get foreign key relationships for a database.

        Args:
            database_name: Name of the database (e.g., 'car_1')

        Returns:
            List of foreign key relationships with structure:
            [
                {
                    "from_table": "table_name",
                    "from_column": "column_name",
                    "to_table": "referenced_table",
                    "to_column": "referenced_column"
                },
                ...
            ]
        """
        metadata = self._load_metadata()

        # Find the database
        db_info = None
        for db in metadata:
            if db['db_id'] == database_name:
                db_info = db
                break

        if not db_info:
            return []

        # Parse foreign keys
        foreign_keys = []
        for fk in db_info.get('foreign_keys', []):
            from_col_idx, to_col_idx = fk

            # Get column information
            from_table_id, from_col_name = db_info['column_names_original'][from_col_idx]
            to_table_id, to_col_name = db_info['column_names_original'][to_col_idx]

            # Get table names
            from_table = db_info['table_names_original'][from_table_id]
            to_table = db_info['table_names_original'][to_table_id]

            foreign_keys.append({
                "from_table": from_table.lower(),  # Normalize to lowercase for PostgreSQL
                "from_column": from_col_name.lower(),
                "to_table": to_table.lower(),
                "to_column": to_col_name.lower()
            })

        return foreign_keys

    def get_primary_keys(self, database_name: str) -> Dict[str, str]:
        """
        Get primary key columns for each table in database.

        Args:
            database_name: Name of the database

        Returns:
            Dictionary mapping table_name -> primary_key_column
        """
        metadata = self._load_metadata()

        # Find the database
        db_info = None
        for db in metadata:
            if db['db_id'] == database_name:
                db_info = db
                break

        if not db_info:
            return {}

        # Parse primary keys
        primary_keys = {}
        for pk_idx in db_info.get('primary_keys', []):
            table_id, col_name = db_info['column_names_original'][pk_idx]
            table_name = db_info['table_names_original'][table_id]
            primary_keys[table_name.lower()] = col_name.lower()

        return primary_keys

    def get_all_tables(self, database_name: str) -> List[str]:
        """
        Get list of all table names in database.

        Args:
            database_name: Name of the database

        Returns:
            List of table names
        """
        metadata = self._load_metadata()

        for db in metadata:
            if db['db_id'] == database_name:
                return [t.lower() for t in db['table_names_original']]

        return []

    def database_exists(self, database_name: str) -> bool:
        """
        Check if database exists in Spider metadata.

        Args:
            database_name: Name of the database

        Returns:
            True if database exists
        """
        metadata = self._load_metadata()
        return any(db['db_id'] == database_name for db in metadata)


# Singleton instance
_spider_loader: Optional[SpiderMetadataLoader] = None


def get_spider_metadata_loader(tables_json_path: str = "data/spider/tables.json") -> SpiderMetadataLoader:
    """
    Get or create singleton Spider metadata loader.

    Args:
        tables_json_path: Path to Spider's tables.json file

    Returns:
        SpiderMetadataLoader instance
    """
    global _spider_loader
    if _spider_loader is None:
        _spider_loader = SpiderMetadataLoader(tables_json_path)
    return _spider_loader
