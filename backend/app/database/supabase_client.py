"""
Base class for Supabase operations with automatic retry logic.

This handles metadata/status storage (benchmark runs, semantic layers, etc.)
and is separate from query execution against benchmark databases.
"""
from typing import Dict, Any, Optional
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx


class SupabaseClient:
    """
    Base class for Supabase metadata operations with automatic retry logic.

    Provides connection handling and retry logic for all Supabase operations.
    Subclasses (BenchmarkStore, MetadataStore) inherit this behavior.

    This is ONLY for metadata/status storage in Supabase, NOT for executing
    benchmark SQL queries (which may target different databases).
    """

    def __init__(self, supabase_url: str, api_key: str):
        """
        Initialize Supabase client for metadata operations.

        Args:
            supabase_url: Supabase project URL
            api_key: Supabase API key (service_role for writes)
        """
        self.client: Client = create_client(supabase_url, api_key)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((
            httpx.RemoteProtocolError,
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.ReadError
        ))
    )
    def _execute_with_retry(self, operation):
        """
        Execute any Supabase operation with automatic retry.

        Retries up to 5 times with exponential backoff for transient network errors.

        Args:
            operation: Supabase query builder (not yet executed)

        Returns:
            Query execution result
        """
        return operation.execute()

    # Convenience methods that wrap _execute_with_retry
    # These provide cleaner API for common operations

    def insert(self, table: str, data: dict):
        """Insert data with automatic retry"""
        return self._execute_with_retry(
            self.client.table(table).insert(data)
        )

    def update(self, table: str, data: dict, **filters):
        """Update data with automatic retry"""
        query = self.client.table(table).update(data)
        for key, value in filters.items():
            query = query.eq(key, value)
        return self._execute_with_retry(query)

    def select(self, table: str, columns: str = "*", **filters):
        """Select data with automatic retry"""
        query = self.client.table(table).select(columns)
        for key, value in filters.items():
            query = query.eq(key, value)
        return self._execute_with_retry(query)

    def delete(self, table: str, **filters):
        """Delete data with automatic retry"""
        query = self.client.table(table).delete()
        for key, value in filters.items():
            query = query.eq(key, value)
        return self._execute_with_retry(query)

    def upsert(self, table: str, data: dict, on_conflict: Optional[str] = None):
        """Upsert data with automatic retry"""
        if on_conflict:
            return self._execute_with_retry(
                self.client.table(table).upsert(data, on_conflict=on_conflict)
            )
        else:
            return self._execute_with_retry(
                self.client.table(table).upsert(data)
            )
