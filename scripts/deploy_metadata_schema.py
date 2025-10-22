#!/usr/bin/env python3
"""
Deploy metadata schema to Supabase.

This script executes the SQL to create metadata tables directly in Supabase.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import get_settings
import psycopg2


def get_schema_sql() -> str:
    """Get the SQL to create metadata schema."""
    return """
-- Semantic Layers Table
CREATE TABLE IF NOT EXISTS semantic_layers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    database_name TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0.0',
    semantic_layer JSONB NOT NULL,
    metadata JSONB NOT NULL,
    prompt_used TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for semantic_layers
CREATE INDEX IF NOT EXISTS idx_semantic_layers_database ON semantic_layers(database_name);
CREATE INDEX IF NOT EXISTS idx_semantic_layers_created_at ON semantic_layers(created_at DESC);

-- Settings Table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Policies (optional, but recommended)
-- Enable RLS
ALTER TABLE semantic_layers ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Enable all access for service role" ON semantic_layers;
DROP POLICY IF EXISTS "Enable all access for settings" ON settings;

-- Allow service role full access (you can customize these policies)
CREATE POLICY "Enable all access for service role" ON semantic_layers
    FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Enable all access for settings" ON settings
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Insert default custom instructions if not exists
INSERT INTO settings (key, value)
VALUES ('custom_instructions', '')
ON CONFLICT (key) DO NOTHING;
"""


def main():
    print("\n" + "=" * 80)
    print("DATAPRISM METADATA SCHEMA DEPLOYMENT")
    print("=" * 80)
    print("\nThis will create tables in Supabase for:")
    print("  - semantic_layers (generated database documentation)")
    print("  - settings (custom instructions, configuration)")
    print("\n" + "=" * 80)

    # Get settings
    settings = get_settings()

    if not settings.database_url:
        print("\nERROR: DATABASE_URL not set in environment")
        print("Please ensure .env file has DATABASE_URL configured")
        sys.exit(1)

    print(f"\nConnecting to Supabase...")
    print(f"Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")

    try:
        # Connect to database
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()

        print("\nExecuting schema SQL...")

        # Get and execute SQL
        sql = get_schema_sql()
        cursor.execute(sql)
        conn.commit()

        print("\n✓ Schema created successfully!")

        # Verify tables exist
        print("\nVerifying tables...")
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name IN ('semantic_layers', 'settings')
            AND table_schema = 'public'
            ORDER BY table_name
        """)

        tables = cursor.fetchall()
        for (table_name,) in tables:
            print(f"  ✓ {table_name}")

        # Check row counts
        print("\nTable status:")
        cursor.execute("SELECT COUNT(*) FROM semantic_layers")
        semantic_count = cursor.fetchone()[0]
        print(f"  semantic_layers: {semantic_count} rows")

        cursor.execute("SELECT COUNT(*) FROM settings")
        settings_count = cursor.fetchone()[0]
        print(f"  settings: {settings_count} rows")

        cursor.close()
        conn.close()

        print("\n" + "=" * 80)
        print("DEPLOYMENT COMPLETE!")
        print("=" * 80)
        print("\nYou can now use the semantic layer generation features.")
        print("Visit: http://localhost:3000/admin/semantic")
        print("\n")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nTroubleshooting:")
        print("  1. Check DATABASE_URL is correct in .env")
        print("  2. Ensure you're using Transaction Pooler URL (pooler.supabase.com)")
        print("  3. Verify Supabase project is running")
        sys.exit(1)


if __name__ == "__main__":
    main()
