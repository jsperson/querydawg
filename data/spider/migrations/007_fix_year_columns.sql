-- ============================================================================
-- Migration 007: Fix Year Columns for Numeric Comparisons
-- Created: 2025-10-30
-- Purpose: Convert Year columns from TEXT to INTEGER for numeric comparisons
-- ============================================================================

-- concert_singer: Year should be INTEGER for numeric comparisons
-- Gold SQL uses: WHERE T1.Year = 2014 (integer without quotes)
ALTER TABLE concert_singer.concert
    ALTER COLUMN Year TYPE INTEGER USING CASE
        WHEN Year = '' OR Year IS NULL OR LOWER(Year) = 'null' OR Year = 'NA' THEN NULL
        ELSE Year::INTEGER
    END;

COMMENT ON COLUMN concert_singer.concert.Year IS 'Fixed from TEXT to INTEGER for numeric comparisons';

-- ============================================================================
-- Summary
-- ============================================================================

COMMENT ON SCHEMA concert_singer IS 'Fixed Year column type for numeric comparisons with gold SQL';
