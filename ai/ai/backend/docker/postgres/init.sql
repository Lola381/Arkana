-- Arkana — PostgreSQL Initialization Script
-- Run automatically on first container startup via docker-entrypoint-initdb.d

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Heritage Sites (Master Table) ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS heritage_sites (
    site_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wikidata_qid VARCHAR(20) UNIQUE,
    wikipedia_title TEXT,
    osm_id TEXT,
    asi_id TEXT,
    unesco_id TEXT,

    name TEXT NOT NULL,
    alternate_names TEXT[],
    description TEXT,
    short_summary TEXT,
    description_quality VARCHAR(20) DEFAULT 'missing'
        CHECK (description_quality IN ('full', 'stub', 'missing')),

    -- Location
    state VARCHAR(100),
    district VARCHAR(100),
    address TEXT,

    -- Coordinates (PostGIS)
    coordinates GEOGRAPHY(POINT, 4326),
    coord_source VARCHAR(30),
    coord_conflict BOOLEAN DEFAULT FALSE,
    geohash VARCHAR(12),

    -- Classification
    category VARCHAR(50),
    category_tags TEXT[],

    -- Heritage Status
    is_unesco_whs BOOLEAN DEFAULT FALSE,
    is_asi_protected BOOLEAN DEFAULT FALSE,
    heritage_designations TEXT[],

    -- Historical Period
    historical_era VARCHAR(100),
    historical_start_year INT,
    historical_end_year INT,
    historical_certainty VARCHAR(20) DEFAULT 'unknown'
        CHECK (historical_certainty IN ('exact', 'approximate', 'unknown')),
    commissioned_by TEXT,

    -- Sources
    source_wikipedia TEXT,
    source_wikidata TEXT,
    source_unesco TEXT,
    source_osm TEXT,
    source_official_website TEXT,
    citations TEXT[],

    -- Related Entities (JSON)
    related_entities JSONB DEFAULT '{}',

    -- Ingestion Metadata
    data_sources TEXT[],
    data_quality_score FLOAT DEFAULT 0.0,
    ingestion_version VARCHAR(10) DEFAULT '1.0',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Site Images ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS site_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id UUID NOT NULL REFERENCES heritage_sites(site_id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    license VARCHAR(100),
    author TEXT,
    source VARCHAR(50),
    commons_filename TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── RAG Chunks ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rag_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id UUID NOT NULL REFERENCES heritage_sites(site_id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    parent_section TEXT,
    chunk_text TEXT NOT NULL,
    token_count INT,
    source_url TEXT,
    embedding_model VARCHAR(100),
    vector_db_id TEXT,          -- ID assigned by ChromaDB/Qdrant
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Ingestion Log ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ingestion_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id UUID REFERENCES heritage_sites(site_id),
    wikidata_qid VARCHAR(20),
    source_name VARCHAR(50),
    status VARCHAR(20) CHECK (status IN ('success', 'error', 'skipped', 'duplicate')),
    error_message TEXT,
    raw_record_id TEXT,
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes ────────────────────────────────────────────────────────────────

-- Spatial index for geo queries (CRITICAL for map features)
CREATE INDEX IF NOT EXISTS idx_heritage_sites_coords
    ON heritage_sites USING GIST (coordinates);

-- Filter indexes
CREATE INDEX IF NOT EXISTS idx_heritage_sites_state ON heritage_sites (state);
CREATE INDEX IF NOT EXISTS idx_heritage_sites_category ON heritage_sites (category);
CREATE INDEX IF NOT EXISTS idx_heritage_sites_is_unesco ON heritage_sites (is_unesco_whs);
CREATE INDEX IF NOT EXISTS idx_heritage_sites_era ON heritage_sites (historical_era);
CREATE INDEX IF NOT EXISTS idx_heritage_sites_quality ON heritage_sites (data_quality_score DESC);

-- Full-text search index on name + description
CREATE INDEX IF NOT EXISTS idx_heritage_sites_fts
    ON heritage_sites
    USING GIN (to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, '')));

-- Chunk lookup
CREATE INDEX IF NOT EXISTS idx_rag_chunks_site_id ON rag_chunks (site_id);
CREATE INDEX IF NOT EXISTS idx_images_site_id ON site_images (site_id);

-- ── Update Timestamp Trigger ──────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_heritage_sites_updated_at
    BEFORE UPDATE ON heritage_sites
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
