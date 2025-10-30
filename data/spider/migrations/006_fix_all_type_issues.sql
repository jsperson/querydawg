-- ============================================================================
-- Migration 006: Fix All Type Issues Identified in Benchmark Run
-- Created: 2025-10-30
-- Purpose: Fix numeric columns stored as TEXT and FK type mismatches
-- ============================================================================

-- ============================================================================
-- Part 1: Fix Numeric Columns Stored as TEXT
-- ============================================================================

-- car_1: MPG and Horsepower should be NUMERIC, not TEXT
-- This prevents AVG(), SUM() and other aggregate functions from working
ALTER TABLE car_1.cars_data
    ALTER COLUMN MPG TYPE NUMERIC USING CASE
        WHEN MPG = '' OR MPG IS NULL OR LOWER(MPG) = 'null' OR MPG = 'NA' THEN NULL
        ELSE MPG::NUMERIC
    END;

ALTER TABLE car_1.cars_data
    ALTER COLUMN Horsepower TYPE NUMERIC USING CASE
        WHEN Horsepower = '' OR Horsepower IS NULL OR LOWER(Horsepower) = 'null' OR Horsepower = 'NA' THEN NULL
        ELSE Horsepower::NUMERIC
    END;

COMMENT ON COLUMN car_1.cars_data.MPG IS 'Fixed from TEXT to NUMERIC for aggregate functions';
COMMENT ON COLUMN car_1.cars_data.Horsepower IS 'Fixed from TEXT to NUMERIC for aggregate functions';

-- ============================================================================
-- Part 2: Fix Foreign Key Type Mismatches and Other Type Issues
-- ============================================================================

-- employee_hire_evaluation: Employee_ID type mismatch between tables
-- evaluation.Employee_ID should be BIGINT to match employee.Employee_ID
ALTER TABLE employee_hire_evaluation.evaluation
    ALTER COLUMN Employee_ID TYPE BIGINT USING Employee_ID::BIGINT;

COMMENT ON TABLE employee_hire_evaluation.evaluation IS 'Fixed Employee_ID from TEXT to BIGINT';

-- museum_visit: open_year should be INTEGER for numeric comparisons
ALTER TABLE museum_visit.museum
    ALTER COLUMN open_year TYPE INTEGER USING CASE
        WHEN open_year = '' OR open_year IS NULL OR LOWER(open_year) = 'null' THEN NULL
        ELSE open_year::INTEGER
    END;

COMMENT ON TABLE museum_visit.museum IS 'Fixed open_year from TEXT to INTEGER';

-- ============================================================================
-- Summary
-- ============================================================================

COMMENT ON SCHEMA car_1 IS 'Fixed numeric column types for MPG and Horsepower';
COMMENT ON SCHEMA employee_hire_evaluation IS 'Fixed Employee_ID FK type mismatch';
COMMENT ON SCHEMA museum_visit IS 'Fixed open_year type for numeric comparisons';
