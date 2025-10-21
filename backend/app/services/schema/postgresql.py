"""
PostgreSQL schema extractor implementation
"""
import psycopg2
from typing import List, Dict, Any
from .base import SchemaExtractor


class PostgreSQLSchemaExtractor(SchemaExtractor):
    """Extract schema from PostgreSQL databases"""

    def __init__(self, connection_string: str, schema_name: str):
        """
        Initialize PostgreSQL schema extractor

        Args:
            connection_string: PostgreSQL connection string
            schema_name: Name of the schema to extract
        """
        super().__init__(connection_string, schema_name)
        self.conn = psycopg2.connect(connection_string)

    def __del__(self):
        """Close connection on cleanup"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def get_tables(self) -> List[Dict[str, Any]]:
        """Get all tables in the schema"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (self.schema_name,))

        tables = [{'name': row[0]} for row in cursor.fetchall()]
        cursor.close()
        return tables

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all columns for a table"""
        cursor = self.conn.cursor()

        # Get column information
        cursor.execute("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
            ORDER BY ordinal_position
        """, (self.schema_name, table_name))

        columns = []
        for row in cursor.fetchall():
            col_name = row[0]
            data_type = row[1]
            is_nullable = row[2] == 'YES'
            column_default = row[3]
            char_max_length = row[4]
            numeric_precision = row[5]
            numeric_scale = row[6]

            # Format type with length/precision
            if char_max_length:
                formatted_type = f"{data_type}({char_max_length})"
            elif numeric_precision and numeric_scale:
                formatted_type = f"{data_type}({numeric_precision},{numeric_scale})"
            elif numeric_precision:
                formatted_type = f"{data_type}({numeric_precision})"
            else:
                formatted_type = data_type

            columns.append({
                'name': col_name,
                'type': formatted_type,
                'nullable': is_nullable,
                'primary_key': False,  # Will be updated below
                'default': column_default
            })

        # Get primary key information
        cursor.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_schema = %s
              AND tc.table_name = %s
        """, (self.schema_name, table_name))

        pk_columns = {row[0] for row in cursor.fetchall()}

        # Update primary_key flag
        for col in columns:
            if col['name'] in pk_columns:
                col['primary_key'] = True

        cursor.close()
        return columns

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all foreign keys for a table"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = %s
              AND tc.table_name = %s
            ORDER BY kcu.ordinal_position
        """, (self.schema_name, table_name))

        foreign_keys = []
        for row in cursor.fetchall():
            foreign_keys.append({
                'column': row[0],
                'referenced_table': row[1],
                'referenced_column': row[2]
            })

        cursor.close()
        return foreign_keys

    def get_row_count(self, table_name: str) -> int:
        """Get row count for a table"""
        cursor = self.conn.cursor()

        # Use COUNT(*) for accurate count
        # For very large tables, could use pg_class.reltuples for estimate
        cursor.execute(f"""
            SELECT COUNT(*) FROM {self.schema_name}."{table_name}"
        """)

        count = cursor.fetchone()[0]
        cursor.close()
        return count
