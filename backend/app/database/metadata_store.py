"""
Metadata Store - Supabase connection for storing semantic layers and other metadata.

Separate from source databases to allow flexibility in data sources.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from .supabase_client import SupabaseClient


class MetadataStore(SupabaseClient):
    """
    Store and retrieve semantic layers and metadata in Supabase.

    Inherits automatic retry logic from SupabaseClient for all database operations.
    """

    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize metadata store connection with retry logic.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key (for write access)
        """
        super().__init__(supabase_url, supabase_key)

    def save_semantic_layer(
        self,
        database_name: str,
        semantic_layer: Dict[str, Any],
        metadata: Dict[str, Any],
        prompt_used: Optional[str] = None,
        connection_name: str = "Supabase"
    ) -> str:
        """
        Save a semantic layer to Supabase.

        Args:
            database_name: Name of the database this semantic layer describes
            semantic_layer: The semantic layer JSON object
            metadata: Generation metadata (LLM model, timestamp, etc.)
            prompt_used: Optional prompt that was used for generation
            connection_name: Name of the connection (e.g., "Supabase", "PostgreSQL")

        Returns:
            ID of the saved semantic layer
        """
        data = {
            "connection_name": connection_name,
            "database_name": database_name,
            "semantic_layer": semantic_layer,
            "metadata": metadata,
            "prompt_used": prompt_used,
            "created_at": datetime.utcnow().isoformat(),
            "version": semantic_layer.get("version", "1.0.0")
        }

        result = self.client.table("semantic_layers").insert(data).execute()
        return result.data[0]["id"]

    def get_semantic_layer(
        self,
        database_name: str,
        version: Optional[str] = None,
        connection_name: str = "Supabase"
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a semantic layer from Supabase.

        Args:
            database_name: Name of the database
            version: Optional specific version. If None, returns latest.
            connection_name: Name of the connection (e.g., "Supabase", "PostgreSQL")

        Returns:
            Semantic layer data or None if not found
        """
        query = (
            self.client.table("semantic_layers")
            .select("*")
            .eq("connection_name", connection_name)
            .eq("database_name", database_name)
        )

        if version:
            query = query.eq("version", version)

        query = query.order("created_at", desc=True).limit(1)

        result = query.execute()

        if result.data:
            return result.data[0]
        return None

    def list_semantic_layers(self) -> List[Dict[str, Any]]:
        """
        List all semantic layers.

        Returns:
            List of semantic layer metadata (without full content)
        """
        result = (
            self.client.table("semantic_layers")
            .select("id, connection_name, database_name, version, created_at, metadata")
            .order("connection_name, database_name")
            .execute()
        )
        return result.data

    def delete_semantic_layer(
        self,
        database_name: str,
        connection_name: str = "Supabase"
    ) -> bool:
        """
        Delete semantic layer(s) for a database.

        Args:
            database_name: Name of the database
            connection_name: Name of the connection (e.g., "Supabase", "PostgreSQL")

        Returns:
            True if deleted, False if not found
        """
        result = (
            self.client.table("semantic_layers")
            .delete()
            .eq("connection_name", connection_name)
            .eq("database_name", database_name)
            .execute()
        )
        return len(result.data) > 0

    def get_custom_instructions(self) -> str:
        """
        Get custom instructions from metadata store.

        Returns:
            Custom instructions string, or empty string if not set
        """
        result = (
            self.client.table("settings")
            .select("value")
            .eq("key", "semantic_layer_instructions")
            .execute()
        )

        if result.data:
            return result.data[0]["value"]
        return ""

    def save_custom_instructions(self, instructions: str) -> None:
        """
        Save custom instructions to metadata store.

        Args:
            instructions: Custom instructions text
        """
        data = {
            "key": "semantic_layer_instructions",
            "value": instructions,
            "updated_at": datetime.utcnow().isoformat()
        }

        # Upsert (insert or update)
        self.client.table("settings").upsert(data, on_conflict="key").execute()

    def get_databases_with_semantic_layers(
        self,
        connection_name: str = "Supabase"
    ) -> List[str]:
        """
        Get list of database names that have semantic layers.

        Args:
            connection_name: Name of the connection to filter by

        Returns:
            List of database names with semantic layers
        """
        result = (
            self.client.table("semantic_layers")
            .select("database_name")
            .eq("connection_name", connection_name)
            .execute()
        )

        # Return unique database names
        return list(set(row["database_name"] for row in result.data))

    def initialize_schema(self) -> None:
        """
        Initialize the Supabase schema for metadata storage.

        Note: This requires Supabase SQL access. Run the SQL manually in Supabase dashboard.
        This method just provides the SQL for reference.
        """
        sql = """
        -- Semantic Layers table
        CREATE TABLE IF NOT EXISTS semantic_layers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            connection_name TEXT NOT NULL DEFAULT 'Supabase',
            database_name TEXT NOT NULL,
            version TEXT NOT NULL DEFAULT '1.0.0',
            semantic_layer JSONB NOT NULL,
            metadata JSONB NOT NULL,
            prompt_used TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

            -- Constraints (connection_name + database_name + version must be unique)
            UNIQUE(connection_name, database_name, version)
        );

        -- Index for faster lookups
        CREATE INDEX IF NOT EXISTS idx_semantic_layers_connection_database
            ON semantic_layers(connection_name, database_name);
        CREATE INDEX IF NOT EXISTS idx_semantic_layers_created
            ON semantic_layers(created_at DESC);

        -- Settings table (for custom instructions and other config)
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Enable Row Level Security (optional, for multi-user access)
        ALTER TABLE semantic_layers ENABLE ROW LEVEL SECURITY;
        ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

        -- Allow service role full access
        CREATE POLICY IF NOT EXISTS "Service role has full access to semantic_layers"
            ON semantic_layers FOR ALL
            USING (true);

        CREATE POLICY IF NOT EXISTS "Service role has full access to settings"
            ON settings FOR ALL
            USING (true);

        -- Optional: Allow authenticated users read access
        CREATE POLICY IF NOT EXISTS "Authenticated users can read semantic_layers"
            ON semantic_layers FOR SELECT
            USING (auth.role() = 'authenticated');
        """

        print("Run this SQL in Supabase SQL Editor:")
        print("=" * 60)
        print(sql)
        print("=" * 60)


def get_metadata_store(supabase_url: str, supabase_key: str) -> MetadataStore:
    """
    Factory function to create metadata store instance.

    Args:
        supabase_url: Supabase project URL
        supabase_key: Supabase service role key

    Returns:
        MetadataStore instance
    """
    return MetadataStore(supabase_url, supabase_key)
