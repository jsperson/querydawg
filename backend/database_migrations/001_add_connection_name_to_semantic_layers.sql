-- Migration: Add connection_name column to semantic_layers table
-- Date: 2025-10-22
-- Description: Adds connection_name column to support multiple database connections

-- Add connection_name column with default value
ALTER TABLE semantic_layers
ADD COLUMN IF NOT EXISTS connection_name TEXT NOT NULL DEFAULT 'Supabase';

-- Drop old unique constraint (database_name, version)
ALTER TABLE semantic_layers
DROP CONSTRAINT IF EXISTS semantic_layers_database_name_version_key;

-- Create new unique constraint (connection_name, database_name, version)
ALTER TABLE semantic_layers
ADD CONSTRAINT semantic_layers_connection_database_version_key
UNIQUE (connection_name, database_name, version);

-- Drop old index and create new one
DROP INDEX IF EXISTS idx_semantic_layers_database;
CREATE INDEX IF NOT EXISTS idx_semantic_layers_connection_database
ON semantic_layers(connection_name, database_name);

-- Update existing rows to have connection_name = 'Supabase' (already done by DEFAULT)
-- This is idempotent and safe to run multiple times
