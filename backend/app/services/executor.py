"""
SQL execution service with query validation and safety checks
"""
import time
import re
import psycopg2
from typing import List, Dict, Any, Optional
from psycopg2.extras import RealDictCursor


class SQLExecutionError(Exception):
    """Custom exception for SQL execution errors"""
    pass


class SQLValidator:
    """Validate SQL queries for safety"""

    # Dangerous keywords that should be blocked
    BLOCKED_KEYWORDS = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'TRUNCATE', 'REPLACE', 'MERGE', 'GRANT', 'REVOKE',
        'EXECUTE', 'EXEC', 'CALL'
    ]

    # Pattern to detect dangerous operations
    BLOCKED_PATTERNS = [
        r'\bINSERT\s+INTO\b',
        r'\bUPDATE\s+\w+\s+SET\b',
        r'\bDELETE\s+FROM\b',
        r'\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX)\b',
        r'\bCREATE\s+(TABLE|DATABASE|SCHEMA|INDEX)\b',
        r'\bALTER\s+(TABLE|DATABASE|SCHEMA)\b',
        r'\bTRUNCATE\s+TABLE\b',
        r'\bGRANT\s+',
        r'\bREVOKE\s+',
    ]

    @classmethod
    def validate_query(cls, sql: str) -> None:
        """
        Validate that SQL query is safe to execute (read-only)

        Args:
            sql: SQL query to validate

        Raises:
            SQLExecutionError: If query contains dangerous operations
        """
        sql_upper = sql.upper()

        # Check for blocked keywords
        for keyword in cls.BLOCKED_KEYWORDS:
            if keyword in sql_upper:
                raise SQLExecutionError(
                    f"Query blocked: '{keyword}' operations are not allowed. "
                    f"Only SELECT queries are permitted."
                )

        # Check for blocked patterns (case-insensitive)
        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                raise SQLExecutionError(
                    f"Query blocked: Detected dangerous operation. "
                    f"Only SELECT queries are permitted."
                )

        # Must start with SELECT or WITH (for CTEs)
        stripped = sql.strip().upper()
        if not (stripped.startswith('SELECT') or stripped.startswith('WITH')):
            raise SQLExecutionError(
                "Query blocked: Only SELECT queries (or CTEs with SELECT) are allowed."
            )


class SQLExecutor:
    """Execute SQL queries safely with validation and limits"""

    # Default limits
    DEFAULT_MAX_ROWS = 1000
    DEFAULT_TIMEOUT_SECONDS = 30

    def __init__(
        self,
        database_url: str,
        schema_name: str,
        max_rows: int = DEFAULT_MAX_ROWS,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    ):
        """
        Initialize SQL executor

        Args:
            database_url: PostgreSQL connection string
            schema_name: Schema name to query
            max_rows: Maximum rows to return
            timeout_seconds: Query timeout in seconds
        """
        self.database_url = database_url
        self.schema_name = schema_name
        self.max_rows = max_rows
        self.timeout_seconds = timeout_seconds

    def execute(self, sql: str) -> Dict[str, Any]:
        """
        Execute SQL query and return results

        Args:
            sql: SQL query to execute

        Returns:
            Dictionary with:
                - results: List of row dictionaries
                - columns: List of column names
                - row_count: Number of rows returned
                - execution_time_ms: Query execution time
                - truncated: Whether results were truncated due to max_rows limit

        Raises:
            SQLExecutionError: If query is invalid or execution fails
        """
        # Validate query first
        SQLValidator.validate_query(sql)

        conn = None
        try:
            # Connect to database
            conn = psycopg2.connect(self.database_url)

            # Set search path to the target schema
            with conn.cursor() as cur:
                cur.execute(f"SET search_path TO {self.schema_name}, public")

            # Set statement timeout
            with conn.cursor() as cur:
                cur.execute(f"SET statement_timeout = '{self.timeout_seconds}s'")

            # Execute query with timing
            start_time = time.time()

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql)

                # Fetch results (up to max_rows + 1 to detect truncation)
                rows = cur.fetchmany(self.max_rows + 1)

                # Check if results were truncated
                truncated = len(rows) > self.max_rows
                if truncated:
                    rows = rows[:self.max_rows]

                # Get column names
                columns = [desc[0] for desc in cur.description] if cur.description else []

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Convert RealDictRow to regular dict
            results = [dict(row) for row in rows]

            return {
                'results': results,
                'columns': columns,
                'row_count': len(results),
                'execution_time_ms': execution_time_ms,
                'truncated': truncated
            }

        except psycopg2.Error as e:
            # PostgreSQL errors
            error_msg = str(e).strip()
            raise SQLExecutionError(f"SQL execution failed: {error_msg}")

        except Exception as e:
            # Other errors
            raise SQLExecutionError(f"Unexpected error: {str(e)}")

        finally:
            if conn:
                conn.close()
