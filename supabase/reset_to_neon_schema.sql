-- ============================================================================
-- RESET SUPABASE TO MATCH NEON SCHEMA
-- ============================================================================
-- WARNING: This will DROP existing tables and recreate them to match Neon
-- Run this in Supabase SQL Editor before importing CSV files
-- ============================================================================

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS human_decisions CASCADE;
DROP TABLE IF EXISTS validation_decisions CASCADE;
DROP TABLE IF EXISTS staging_extractions CASCADE;
DROP TABLE IF EXISTS raw_snapshots CASCADE;
DROP TABLE IF EXISTS pipeline_runs CASCADE;
DROP TABLE IF EXISTS core_entities CASCADE;

-- Drop enums
DROP TYPE IF EXISTS ecosystem_type CASCADE;
DROP TYPE IF EXISTS entity_type CASCADE;
DROP TYPE IF EXISTS candidate_status CASCADE;
DROP TYPE IF EXISTS validation_decision_type CASCADE;
DROP TYPE IF EXISTS decider_type CASCADE;

-- ============================================================================
-- RECREATE TABLES TO MATCH NEON
-- ============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Pipeline runs (from Neon)
CREATE TABLE pipeline_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_type TEXT NOT NULL,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  ended_at TIMESTAMPTZ,
  status TEXT DEFAULT 'running',
  metadata JSONB
);

-- Raw snapshots (EXACT Neon schema)
CREATE TABLE raw_snapshots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_url TEXT NOT NULL,
  source_type TEXT,
  ecosystem TEXT,
  content_hash TEXT,
  payload JSONB NOT NULL,
  payload_size_bytes INTEGER,
  captured_at TIMESTAMPTZ,
  captured_by_run_id UUID REFERENCES pipeline_runs(id),
  source_commit_sha TEXT,
  source_etag TEXT,
  source_last_modified TIMESTAMPTZ,
  status TEXT DEFAULT 'captured',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  fetched_by_thread_id TEXT
);

CREATE INDEX idx_snapshots_url ON raw_snapshots(source_url);
CREATE INDEX idx_snapshots_content_hash ON raw_snapshots(content_hash);

-- Staging extractions (EXACT Neon schema)
CREATE TABLE staging_extractions (
  extraction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  pipeline_run_id UUID REFERENCES pipeline_runs(id),
  snapshot_id UUID REFERENCES raw_snapshots(id),
  agent_id TEXT,
  agent_version TEXT,
  candidate_type TEXT NOT NULL,
  candidate_key TEXT NOT NULL,
  candidate_payload JSONB NOT NULL,
  ecosystem TEXT,
  confidence_score NUMERIC(3,2),
  confidence_reason TEXT,
  evidence JSONB,
  status TEXT DEFAULT 'pending',
  promoted_to_id UUID,
  promoted_at TIMESTAMPTZ,
  merged_into_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  evidence_checksum TEXT,
  evidence_byte_offset INTEGER,
  evidence_byte_length INTEGER,
  lineage_verified BOOLEAN DEFAULT FALSE,
  lineage_verified_at TIMESTAMPTZ,
  lineage_confidence NUMERIC(3,2),
  lineage_verification_details JSONB,
  extraction_attempt INTEGER DEFAULT 1,
  is_reextraction BOOLEAN DEFAULT FALSE,
  reextraction_reason TEXT,
  original_extraction_id UUID,
  requires_mandatory_review BOOLEAN DEFAULT FALSE,
  mandatory_review_reason TEXT,
  extracted_by_thread_id TEXT,
  notion_page_id UUID,
  notion_synced_at TIMESTAMPTZ,
  notion_last_sync_attempt TIMESTAMPTZ,
  notion_sync_error TEXT,
  evidence_type TEXT,
  reviewed_at TIMESTAMPTZ,
  review_decision TEXT,
  review_notes TEXT,
  error_log JSONB DEFAULT '[]'::jsonb,
  error_count INTEGER DEFAULT 0,
  last_error_at TIMESTAMPTZ,
  current_revision INTEGER DEFAULT 1,
  latest_decision_id UUID,
  assigned_to TEXT,
  promoted_to_entity_id UUID,
  promotion_action TEXT,
  promotion_error TEXT
);

CREATE INDEX idx_extractions_status ON staging_extractions(status);
CREATE INDEX idx_extractions_key ON staging_extractions(candidate_key);
CREATE INDEX idx_extractions_type ON staging_extractions(candidate_type);
CREATE INDEX idx_extractions_snapshot ON staging_extractions(snapshot_id);
CREATE INDEX idx_extractions_created ON staging_extractions(created_at DESC);

-- ============================================================================
-- DONE! Now import CSVs in this order:
-- 1. pipeline_runs.csv
-- 2. raw_snapshots.csv
-- 3. staging_extractions.csv
-- ============================================================================
