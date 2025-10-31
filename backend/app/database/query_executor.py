"""
Query execution interface for benchmark queries.

Separates query execution (against various databases) from metadata storage (Supabase).
Allows pluggable database support (PostgreSQL, MySQL, SQLite, etc.) for running benchmarks.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import psycopg2
from psycopg2 import pool, sql
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class QueryExecutor(ABC):
    """
    Abstract interface for executing SQL queries against benchmark databases.

    Subclasses implement this for specific database types (PostgreSQL, MySQL, SQLite, etc.)
    """

    @abstractmethod
    def execute_query(
        self,
        query: str,
        database: str
    ) -> Tuple[List[Tuple], Optional[str]]:
        """
        Execute a SQL query against the specified database.

        Args:
            query: SQL query to execute
            database: Database/schema name

        Returns:
            Tuple of (results, error_message)
            - results: List of tuples (sorted for deterministic comparison)
            - error_message: None if success, error string if failure
        """
        pass

    @abstractmethod
    def close(self):
        """Clean up database connections and resources"""
        pass


class PostgreSQLExecutor(QueryExecutor):
    """
    PostgreSQL query executor with connection pooling and retry logic.

    Used for executing benchmark queries against PostgreSQL databases.
    """

    def __init__(self, connection_string: str):
        """
        Initialize PostgreSQL executor with connection pooling.

        Args:
            connection_string: PostgreSQL connection string (DSN)
        """
        self.connection_string = connection_string

        # Create connection pool (2-10 connections)
        self.db_pool = pool.SimpleConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=connection_string
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        retry=retry_if_exception_type(psycopg2.OperationalError)
    )
    def execute_query(
        self,
        query: str,
        database: str
    ) -> Tuple[List[Tuple], Optional[str]]:
        """
        Execute SQL query in read-only transaction with timeout.

        Automatically retries on transient OperationalError (up to 3 attempts).

        Args:
            query: SQL query to execute
            database: Database/schema name (used for search_path)

        Returns:
            Tuple of (results, error_message)
            - results: List of tuples, sorted for deterministic comparison
            - error_message: None if success, error string if failure
        """
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                # Set read-only and timeout
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute("SET statement_timeout = '5s'")

                # Safely set search_path using sql.Identifier to prevent SQL injection
                search_path_query = sql.SQL("SET search_path TO {}").format(
                    sql.Identifier(database)
                )
                cur.execute(search_path_query)

                # Execute query
                cur.execute(query)
                results = cur.fetchall()

                # Sort results for deterministic comparison
                sorted_results = sorted(results, key=lambda x: str(x))
                return sorted_results, None

        except Exception as e:
            return [], str(e)

        finally:
            # Always rollback (read-only) and return connection
            conn.rollback()
            self.db_pool.putconn(conn)

    def close(self):
        """Close all connections in the pool"""
        if hasattr(self, 'db_pool') and self.db_pool:
            self.db_pool.closeall()

    def __del__(self):
        """Cleanup on garbage collection"""
        self.close()
