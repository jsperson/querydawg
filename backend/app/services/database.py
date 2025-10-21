"""
Database service for Supabase PostgreSQL operations
"""
import os
from typing import List
import psycopg2
from psycopg2.extras import RealDictCursor


class DatabaseService:
    """Service for database operations"""

    def __init__(self):
        """Initialize database connection"""
        self.connection_string = os.getenv("DATABASE_URL")
        if not self.connection_string:
            raise ValueError("DATABASE_URL environment variable not set")

    def get_connection(self):
        """Get a database connection"""
        return psycopg2.connect(self.connection_string)

    def get_databases(self) -> List[str]:
        """
        Get list of Spider databases (schemas) in Supabase

        Returns:
            List of database/schema names (excluding system schemas)
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Query for all schemas, excluding system and Supabase-specific schemas
            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'public', 'auth', 'storage', 'extensions')
                  AND schema_name NOT LIKE 'pg_temp_%'
                  AND schema_name NOT LIKE 'pg_toast%'
                  AND schema_name NOT IN ('pgbouncer', 'vault', 'realtime', 'graphql', 'graphql_public')
                ORDER BY schema_name
            """)

            databases = [row[0] for row in cursor.fetchall()]
            cursor.close()

            return databases
        finally:
            conn.close()

    def database_exists(self, database_name: str) -> bool:
        """
        Check if a database (schema) exists

        Args:
            database_name: Name of the database/schema

        Returns:
            True if database exists, False otherwise
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s",
                (database_name,)
            )
            exists = cursor.fetchone() is not None
            cursor.close()
            return exists
        finally:
            conn.close()


# Singleton instance
_db_service = None


def get_db_service() -> DatabaseService:
    """Get or create database service singleton"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
