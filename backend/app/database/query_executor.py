"""
Query execution interface for benchmark queries.

Separates query execution (against various databases) from metadata storage (Supabase).
Allows pluggable database support (PostgreSQL, MySQL, SQLite, etc.) for running benchmarks.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import os
import psycopg2
from psycopg2 import pool, sql
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .turso_client import TursoClient


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


class TursoExecutor(QueryExecutor):
    """
    Turso (libSQL/SQLite) query executor for native Spider benchmark execution.

    Used for executing benchmark queries against Turso-hosted SQLite databases
    without SQLite→PostgreSQL conversion issues.
    """

    def __init__(self, org: Optional[str] = None, token: Optional[str] = None):
        """
        Initialize Turso executor.

        Args:
            org: Turso organization name (defaults to TURSO_ORG env var or 'querydawg')
            token: Turso auth token (defaults to TURSO_TOKEN env var)
        """
        self.org = org or os.getenv("TURSO_ORG", "querydawg")
        self.token = token or os.getenv("TURSO_TOKEN")

        if not self.token:
            raise ValueError("TURSO_TOKEN environment variable not set")

        # Cache of TursoClient instances per database
        self._clients = {}

    def _get_client(self, database: str) -> TursoClient:
        """Get or create TursoClient for a database"""
        if database not in self._clients:
            self._clients[database] = TursoClient(db_name=database)
        return self._clients[database]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8)
    )
    def execute_query(
        self,
        query: str,
        database: str
    ) -> Tuple[List[Tuple], Optional[str]]:
        """
        Execute SQL query against Turso database.

        Args:
            query: SQL query to execute (SQLite syntax)
            database: Database name (e.g., 'concert_singer')

        Returns:
            Tuple of (results, error_message)
            - results: List of tuples, sorted for deterministic comparison
            - error_message: None if success, error string if failure
        """
        try:
            client = self._get_client(database)

            # Execute via Turso HTTP API
            result = client.execute(query)

            # Convert results to list of tuples
            if result and 'rows' in result:
                rows = [tuple(row) for row in result['rows']]
                # Sort for deterministic comparison
                sorted_rows = sorted(rows, key=lambda x: str(x))
                return sorted_rows, None

            return [], None

        except Exception as e:
            return [], str(e)

    def close(self):
        """Close all Turso client connections"""
        self._clients.clear()

    def __del__(self):
        """Cleanup on garbage collection"""
        self.close()


class QueryExecutorFactory:
    """
    Factory for creating appropriate QueryExecutor based on configuration.

    Supports switching between Supabase (PostgreSQL) and Turso (SQLite) via
    environment variable or explicit parameter.
    """

    @staticmethod
    def create(
        source: Optional[str] = None,
        connection_string: Optional[str] = None
    ) -> QueryExecutor:
        """
        Create appropriate QueryExecutor based on source.

        Args:
            source: Database source ("supabase" or "turso").
                   If None, uses SPIDER_DATA_SOURCE env var (default: "supabase")
            connection_string: Connection string (required for PostgreSQL)

        Returns:
            QueryExecutor instance (PostgreSQLExecutor or TursoExecutor)

        Raises:
            ValueError: If source is invalid or required config missing
        """
        # Determine source
        if source is None:
            source = os.getenv("SPIDER_DATA_SOURCE", "supabase").lower()

        source = source.lower()

        if source == "supabase" or source == "postgresql":
            if not connection_string:
                connection_string = os.getenv("SUPABASE_DB_URL")
                if not connection_string:
                    raise ValueError("SUPABASE_DB_URL environment variable not set")

            return PostgreSQLExecutor(connection_string=connection_string)

        elif source == "turso" or source == "sqlite":
            return TursoExecutor()

        else:
            raise ValueError(
                f"Invalid SPIDER_DATA_SOURCE: {source}. "
                f"Must be 'supabase' or 'turso'"
            )
