-- ============================================================
-- Supabase Migration: Mandi Location Data
-- Run this in Supabase SQL Editor
-- ============================================================

-- Enable trigram extension (needed for ILIKE-optimized indexes)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. States
CREATE TABLE IF NOT EXISTS states (
    state_id   INT PRIMARY KEY,
    state_name TEXT NOT NULL
);

CREATE INDEX idx_states_name ON states USING gin (state_name gin_trgm_ops);

-- 2. Districts (FK -> states)
CREATE TABLE IF NOT EXISTS districts (
    id            INT PRIMARY KEY,
    state_id      INT REFERENCES states(state_id),
    district_name TEXT NOT NULL
);

CREATE INDEX idx_districts_name ON districts USING gin (district_name gin_trgm_ops);
CREATE INDEX idx_districts_state ON districts (state_id);

-- 3. Markets (FK -> states, districts)
CREATE TABLE IF NOT EXISTS markets (
    id          INT PRIMARY KEY,
    mkt_name    TEXT NOT NULL,
    state_id    INT REFERENCES states(state_id),
    district_id INT REFERENCES districts(id)
);

CREATE INDEX idx_markets_name ON markets USING gin (mkt_name gin_trgm_ops);
CREATE INDEX idx_markets_state ON markets (state_id);
CREATE INDEX idx_markets_district ON markets (district_id);

-- 4. Commodity Groups
CREATE TABLE IF NOT EXISTS commodity_groups (
    id            INT PRIMARY KEY,
    cmdt_grp_name TEXT NOT NULL
);

-- 5. Commodities (FK -> commodity_groups)
CREATE TABLE IF NOT EXISTS commodities (
    cmdt_id        INT PRIMARY KEY,
    cmdt_name      TEXT NOT NULL,
    cmdt_group_id  INT REFERENCES commodity_groups(id),
    cmdt_type_flag TEXT
);

-- 6. Varieties
CREATE TABLE IF NOT EXISTS varieties (
    id           INT PRIMARY KEY,
    variety_name TEXT NOT NULL
);

-- 7. Grades
CREATE TABLE IF NOT EXISTS grades (
    id         INT PRIMARY KEY,
    grade_name TEXT NOT NULL
);

-- ============================================================
-- Optimized location search function
-- Priority: market -> district -> state
-- Returns the resolved state_id, district_id, market_id + names
-- ============================================================
CREATE OR REPLACE FUNCTION search_location(query TEXT)
RETURNS TABLE (
    matched_level TEXT,
    state_id      INT,
    state_name    TEXT,
    district_id   INT,
    district_name TEXT,
    market_id     INT,
    market_name   TEXT
) AS $$
BEGIN
    -- 1. Try market match
    RETURN QUERY
    SELECT
        'market'::TEXT AS matched_level,
        m.state_id,
        s.state_name,
        m.district_id,
        d.district_name,
        m.id AS market_id,
        m.mkt_name AS market_name
    FROM markets m
    LEFT JOIN states s ON s.state_id = m.state_id
    LEFT JOIN districts d ON d.id = m.district_id
    WHERE m.id != 100009
      AND m.mkt_name ILIKE '%' || query || '%'
    LIMIT 1;

    IF FOUND THEN RETURN; END IF;

    -- 2. Try district match
    RETURN QUERY
    SELECT
        'district'::TEXT AS matched_level,
        d.state_id,
        s.state_name,
        d.id AS district_id,
        d.district_name,
        100009 AS market_id,
        'All Markets'::TEXT AS market_name
    FROM districts d
    LEFT JOIN states s ON s.state_id = d.state_id
    WHERE d.id != 100007
      AND d.district_name ILIKE '%' || query || '%'
    LIMIT 1;

    IF FOUND THEN RETURN; END IF;

    -- 3. Try state match
    RETURN QUERY
    SELECT
        'state'::TEXT AS matched_level,
        s.state_id,
        s.state_name,
        100007 AS district_id,
        'All Districts'::TEXT AS district_name,
        100009 AS market_id,
        'All Markets'::TEXT AS market_name
    FROM states s
    WHERE s.state_id != 100006
      AND s.state_name ILIKE '%' || query || '%'
    LIMIT 1;

    IF FOUND THEN RETURN; END IF;

    -- 4. No match - return all defaults
    RETURN QUERY
    SELECT
        NULL::TEXT AS matched_level,
        100006 AS state_id,
        'All States'::TEXT AS state_name,
        100007 AS district_id,
        'All Districts'::TEXT AS district_name,
        100009 AS market_id,
        'All Markets'::TEXT AS market_name;
END;
$$ LANGUAGE plpgsql;
