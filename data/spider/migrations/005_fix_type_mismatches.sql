-- ============================================================================
-- Migration 005: Fix Type Mismatches from SQLite to PostgreSQL Migration
-- Created: 2025-10-30
-- Purpose: Fix foreign key type mismatches that cause gold SQL to fail
-- ============================================================================

-- Fix concert_singer schema
-- Stadium_ID should be BIGINT to match stadium.Stadium_ID
ALTER TABLE concert_singer.concert
    ALTER COLUMN Stadium_ID TYPE BIGINT USING Stadium_ID::BIGINT;

-- Singer_ID should be BIGINT to match singer.Singer_ID
ALTER TABLE concert_singer.singer_in_concert
    ALTER COLUMN Singer_ID TYPE BIGINT USING Singer_ID::BIGINT;

-- Year should probably stay TEXT as it may contain non-numeric values in Spider
-- But if needed, can convert later

COMMENT ON TABLE concert_singer.concert IS 'Fixed Stadium_ID type from TEXT to BIGINT';
COMMENT ON TABLE concert_singer.singer_in_concert IS 'Fixed Singer_ID type from TEXT to BIGINT';
