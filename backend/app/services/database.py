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
        # Hardcoded list of 19 Spider databases loaded into Supabase
        # This avoids IPv6 connection issues with direct PostgreSQL access
        # TODO: Make this dynamic once connection issues are resolved
        return [
            "battle_death",
            "car_1",
            "concert_singer",
            "course_teach",
            "cre_Doc_Template_Mgt",
            "dog_kennels",
            "employee_hire_evaluation",
            "flight_2",
            "museum_visit",
            "network_1",
            "orchestra",
            "pets_1",
            "poker_player",
            "real_estate_properties",
            "singer",
            "student_transcripts_tracking",
            "tvshow",
            "voter_1",
            "world_1"
        ]

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
