"""
Schema extractor for Supabase PostgreSQL databases.

Extracts schema information and sample data from Spider databases stored in Supabase.
Each Spider database is stored as a separate schema in the same Supabase PostgreSQL instance.
"""

import psycopg2
from typing import Dict, List, Any, Optional


class SupabaseSchemaExtractor:
    """Extract schema and sample data from Supabase PostgreSQL databases."""

    def __init__(self, database_url: str):
        """
        Initialize with Supabase database connection.

        Args:
            database_url: PostgreSQL connection string (use Transaction Pooler)
        """
        self.database_url = database_url

    def extract_schema(self, schema_name: str) -> Dict[str, Any]:
        """
        Extract schema information for a database (schema).

        Args:
            schema_name: Name of the schema (e.g., 'world_1', 'car_1')

        Returns:
            Dictionary with tables, columns, foreign keys, row counts
        """
        conn = psycopg2.connect(self.database_url)
        cursor = conn.cursor()

        try:
            # Get all tables in the schema
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (schema_name,))

            tables = []
            for (table_name,) in cursor.fetchall():
                table_info = self._extract_table_info(cursor, schema_name, table_name)
                tables.append(table_info)

            return {
                "database": schema_name,
                "tables": tables
            }

        finally:
            cursor.close()
            conn.close()

    def _extract_table_info(
        self,
        cursor,
        schema_name: str,
        table_name: str
    ) -> Dict[str, Any]:
        """Extract detailed information for a single table."""

        # Get columns
        cursor.execute("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s
            AND table_name = %s
            ORDER BY ordinal_position
        """, (schema_name, table_name))

        columns = []
        for col_name, data_type, is_nullable, default in cursor.fetchall():
            columns.append({
                "name": col_name,
                "type": data_type,
                "nullable": is_nullable == "YES",
                "default": default,
                "primary_key": False  # Will update below
            })

        # Get primary keys
        cursor.execute("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid
                AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = (%s || '.' || %s)::regclass
            AND i.indisprimary
        """, (schema_name, table_name))

        pk_columns = {row[0] for row in cursor.fetchall()}
        for col in columns:
            if col["name"] in pk_columns:
                col["primary_key"] = True

        # Get foreign keys
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
        """, (schema_name, table_name))

        foreign_keys = []
        for col_name, ref_table, ref_col in cursor.fetchall():
            foreign_keys.append({
                "column": col_name,
                "referenced_table": ref_table,
                "referenced_column": ref_col
            })

        # Get row count
        cursor.execute(
            f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}"'
        )
        row_count = cursor.fetchone()[0]

        return {
            "name": table_name,
            "columns": columns,
            "foreign_keys": foreign_keys,
            "row_count": row_count
        }

    def sample_data(
        self,
        schema_name: str,
        table_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Sample data from a table.

        Args:
            schema_name: Schema name (database)
            table_name: Table name
            limit: Number of rows to sample

        Returns:
            List of row dictionaries
        """
        conn = psycopg2.connect(self.database_url)
        cursor = conn.cursor()

        try:
            # Get column names
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s
                AND table_name = %s
                ORDER BY ordinal_position
            """, (schema_name, table_name))

            columns = [row[0] for row in cursor.fetchall()]

            # Sample data
            cursor.execute(
                f'SELECT * FROM "{schema_name}"."{table_name}" LIMIT %s',
                (limit,)
            )

            rows = []
            for row in cursor.fetchall():
                rows.append(dict(zip(columns, row)))

            return rows

        finally:
            cursor.close()
            conn.close()

    def sample_all_tables(
        self,
        schema_name: str,
        limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Sample data from all tables in a schema.

        Args:
            schema_name: Schema name (database)
            limit: Number of rows per table

        Returns:
            Dictionary mapping table names to sample rows
        """
        conn = psycopg2.connect(self.database_url)
        cursor = conn.cursor()

        try:
            # Get all tables
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                AND table_type = 'BASE TABLE'
            """, (schema_name,))

            samples = {}
            for (table_name,) in cursor.fetchall():
                samples[table_name] = self.sample_data(schema_name, table_name, limit)

            return samples

        finally:
            cursor.close()
            conn.close()

    def list_databases(self) -> List[str]:
        """
        List all available Spider database schemas.

        Returns:
            List of schema names
        """
        conn = psycopg2.connect(self.database_url)
        cursor = conn.cursor()

        try:
            # Get all schemas except system schemas
            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'public')
                AND schema_name NOT LIKE 'pg_%'
                ORDER BY schema_name
            """)

            return [row[0] for row in cursor.fetchall()]

        finally:
            cursor.close()
            conn.close()
