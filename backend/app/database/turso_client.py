"""
Turso (libSQL) Client for QueryDawg

Provides access to Spider benchmark databases hosted on Turso.
Turso is SQLite-compatible, maintaining high fidelity with Spider's native SQLite format.
"""

import os
from typing import List, Dict, Any, Optional
import requests
import json


class TursoClient:
    """Client for querying Turso (libSQL) databases via HTTP API"""

    def __init__(self, db_name: str):
        """
        Initialize Turso client for a specific database

        Args:
            db_name: Name of the Turso database (e.g., 'concert_singer' or 'concert-singer')
                     Underscores will be automatically converted to dashes for Turso compatibility

        Raises:
            ValueError: If Turso configuration is missing
        """
        # Normalize database name: Turso only allows lowercase, numbers, and dashes
        self.db_name = db_name.replace("_", "-").lower()

        # Get configuration from environment
        self.org = os.getenv("TURSO_ORG", "querydawg")
        self.base_url = os.getenv("TURSO_BASE_URL", f"{self.org}.turso.io")

        # Get account-level token (required for creating database tokens)
        self.account_token = os.getenv("TURSO_TOKEN")
        if not self.account_token:
            raise ValueError("TURSO_TOKEN environment variable not set")

        # Try database-specific token from environment first
        db_token_env_var = f"TURSO_TOKEN_{self.db_name.upper().replace('-', '_')}"
        self.token = os.getenv(db_token_env_var)

        # If no database-specific token, create one using the API
        if not self.token:
            self.token = self._create_database_token()
            if not self.token:
                raise ValueError(f"Failed to create database token for {self.db_name}")

        # Build database URL using normalized name
        self.db_url = f"https://{self.db_name}-{self.base_url}"

    def _create_database_token(self) -> Optional[str]:
        """
        Create a database-specific JWT token using Turso API

        Returns:
            Database-specific JWT token or None if creation fails
        """
        url = f"https://api.turso.tech/v1/organizations/{self.org}/databases/{self.db_name}/auth/tokens"
        headers = {
            "Authorization": f"Bearer {self.account_token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json={}, timeout=30)
            if response.status_code in [200, 201]:
                return response.json().get("jwt")
            else:
                print(f"Warning: Failed to create database token for {self.db_name}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Warning: Exception creating database token for {self.db_name}: {e}")
            return None

    def execute(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """
        Execute SQL query against Turso database

        Args:
            sql: SQL query string
            params: Optional query parameters (for prepared statements)

        Returns:
            Dictionary with query results:
            {
                "columns": List[str],  # Column names
                "rows": List[List[Any]],  # Row data
                "rows_affected": int  # For INSERT/UPDATE/DELETE
            }

        Raises:
            RuntimeError: If query execution fails
        """
        # Build request payload (Turso v2 API uses "requests" not "statements")
        # Format params as Turso v2 expects (with type wrapping)
        formatted_args = []
        if params:
            for param in params:
                if param is None:
                    formatted_args.append({"type": "null"})
                elif isinstance(param, bool):
                    formatted_args.append({"type": "integer", "value": str(1 if param else 0)})
                elif isinstance(param, int):
                    formatted_args.append({"type": "integer", "value": str(param)})
                elif isinstance(param, float):
                    formatted_args.append({"type": "float", "value": param})
                elif isinstance(param, bytes):
                    import base64
                    formatted_args.append({"type": "blob", "base64": base64.b64encode(param).decode()})
                else:
                    formatted_args.append({"type": "text", "value": str(param)})

        payload = {
            "requests": [
                {
                    "type": "execute",
                    "stmt": {
                        "sql": sql
                    }
                }
            ]
        }

        # Add formatted params if provided
        if formatted_args:
            payload["requests"][0]["stmt"]["args"] = formatted_args

        # Execute via HTTP API
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                f"{self.db_url}/v2/pipeline",
                headers=headers,
                json=payload,
                timeout=30
            )

            # Check status code and capture error response if failed
            if response.status_code >= 400:
                try:
                    error_json = response.json()
                    error_detail = json.dumps(error_json, indent=2)
                except:
                    error_detail = response.text

                raise RuntimeError(
                    f"HTTP {response.status_code} error from Turso\n"
                    f"URL: {response.url}\n"
                    f"Response: {error_detail}"
                )

            # Parse response
            data = response.json()

            if not data or "results" not in data:
                raise RuntimeError(f"Invalid response from Turso: {data}")

            result = data["results"][0]

            # Check for errors
            if result.get("type") == "error" or "error" in result:
                error_msg = result.get("error", result)
                raise RuntimeError(f"Query error: {error_msg}")

            # Navigate to actual result (Turso v2 API structure)
            if "response" in result and "result" in result["response"]:
                actual_result = result["response"]["result"]

                # Extract column names from "cols" array
                cols = actual_result.get("cols", [])
                columns = [col["name"] for col in cols]

                # Extract and unwrap rows (each value is {"type": "...", "value": "..."})
                raw_rows = actual_result.get("rows", [])
                rows = []
                for row in raw_rows:
                    unwrapped_row = []
                    for cell in row:
                        if isinstance(cell, dict) and "value" in cell:
                            unwrapped_row.append(cell["value"])
                        else:
                            unwrapped_row.append(cell)
                    rows.append(unwrapped_row)

                rows_affected = actual_result.get("affected_row_count", 0)
            else:
                # Fallback for older API format (if any)
                columns = result.get("columns", [])
                rows = result.get("rows", [])
                rows_affected = result.get("rows_affected", 0)

            return {
                "columns": columns,
                "rows": rows,
                "rows_affected": rows_affected
            }

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to execute query on Turso: {e}")

    def execute_batch(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Execute multiple queries in a transaction

        Args:
            queries: List of SQL query strings

        Returns:
            List of result dictionaries (one per query)

        Raises:
            RuntimeError: If batch execution fails
        """
        # Build batch request
        payload = {
            "statements": [{"q": q} for q in queries]
        }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                f"{self.db_url}/v2/pipeline",
                headers=headers,
                json=payload,
                timeout=60
            )

            response.raise_for_status()

            data = response.json()

            if not data or "results" not in data:
                raise RuntimeError(f"Invalid response from Turso: {data}")

            # Parse each result
            results = []
            for result in data["results"]:
                if "error" in result:
                    raise RuntimeError(f"Query error in batch: {result['error']}")

                results.append({
                    "columns": result.get("columns", []),
                    "rows": result.get("rows", []),
                    "rows_affected": result.get("rows_affected", 0)
                })

            return results

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to execute batch on Turso: {e}")

    def get_table_names(self) -> List[str]:
        """
        Get list of all tables in the database

        Returns:
            List of table names
        """
        result = self.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )

        return [row[0] for row in result["rows"]]

    def get_row_count(self, table_name: str) -> int:
        """
        Get row count for a table

        Args:
            table_name: Name of the table

        Returns:
            Number of rows
        """
        result = self.execute(f"SELECT COUNT(*) FROM {table_name}")
        return result["rows"][0][0]

    def sample_table(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Sample rows from a table

        Args:
            table_name: Name of the table
            limit: Maximum number of rows to return

        Returns:
            List of row dictionaries
        """
        result = self.execute(f"SELECT * FROM {table_name} LIMIT {limit}")

        # Convert to list of dicts
        rows = []
        for row in result["rows"]:
            rows.append(dict(zip(result["columns"], row)))

        return rows

    def test_connection(self) -> bool:
        """
        Test connection to Turso database

        Returns:
            True if connection successful

        Raises:
            RuntimeError: If connection fails
        """
        try:
            # Simple query to test connection
            result = self.execute("SELECT 1")
            return result["rows"][0][0] == 1
        except Exception as e:
            raise RuntimeError(f"Connection test failed: {e}")
