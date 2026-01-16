-- ============================================================================
-- Migration 000: Initial Base Schema
-- ============================================================================
-- Purpose: Create foundational tables that all other migrations depend on
-- Date: 2026-01-15
-- Note: This recreates the bootstrap schema that existed in Neon
-- ============================================================================

BEGIN;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- ENUMS
-- ============================================================================

DO $$
BEGIN
  -- Create ecosystem_type enum
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ecosystem_type') THEN
    CREATE TYPE ecosystem_type AS ENUM ('fprime', 'proveskit', 'generic');
  END IF;

  -- Create entity_type enum
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'entity_type') THEN
    CREATE TYPE entity_type AS ENUM ('component', 'interface', 'subsystem');
  END IF;

  -- Create candidate_status enum
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'candidate_status') THEN
    CREATE TYPE candidate_status AS ENUM ('pending', 'accepted', 'rejected', 'needs_context', 'merged');
  END IF;

  -- Create validation_decision_type enum
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'validation_decision_type') THEN
    CREATE TYPE validation_decision_type AS ENUM ('accept', 'reject', 'needs_more_evidence', 'defer', 'merge');
  END IF;

  -- Create decider_type enum
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'decider_type') THEN
    CREATE TYPE decider_type AS ENUM ('human', 'agent');
  END IF;
END $$;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Pipeline runs tracking
CREATE TABLE IF NOT EXISTS pipeline_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_type TEXT NOT NULL,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  ended_at TIMESTAMPTZ,
  status TEXT DEFAULT 'running',
  metadata JSONB
);

-- Raw source snapshots
CREATE TABLE IF NOT EXISTS raw_snapshots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_url TEXT NOT NULL,
  payload JSONB NOT NULL,
  snapshot_at TIMESTAMPTZ DEFAULT NOW(),
  pipeline_run_id UUID REFERENCES pipeline_runs(id)
);

CREATE INDEX idx_snapshots_url ON raw_snapshots(source_url);
CREATE INDEX idx_snapshots_pipeline ON raw_snapshots(pipeline_run_id);

-- Staging extractions (inbox)
CREATE TABLE IF NOT EXISTS staging_extractions (
  extraction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Entity identification
  candidate_key TEXT NOT NULL,
  candidate_type TEXT NOT NULL,
  candidate_payload JSONB NOT NULL,

  -- Source tracking
  snapshot_id UUID REFERENCES raw_snapshots(id),
  pipeline_run_id UUID REFERENCES pipeline_runs(id),

  -- Confidence and status
  confidence_score NUMERIC(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
  status candidate_status DEFAULT 'pending',

  -- Evidence
  evidence JSONB,

  -- Ecosystem
  ecosystem ecosystem_type,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Review tracking (added by later migrations)
  reviewed_by TEXT,
  reviewed_at TIMESTAMPTZ
);

CREATE INDEX idx_extractions_status ON staging_extractions(status);
CREATE INDEX idx_extractions_key ON staging_extractions(candidate_key);
CREATE INDEX idx_extractions_type ON staging_extractions(candidate_type);
CREATE INDEX idx_extractions_snapshot ON staging_extractions(snapshot_id);
CREATE INDEX idx_extractions_created ON staging_extractions(created_at DESC);

-- Validation decisions (audit trail)
CREATE TABLE IF NOT EXISTS validation_decisions (
  decision_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  extraction_id UUID NOT NULL REFERENCES staging_extractions(extraction_id),

  -- Decision details
  decision validation_decision_type NOT NULL,
  decided_by TEXT NOT NULL,
  decider_type decider_type DEFAULT 'human',
  decision_reason TEXT,

  -- Timestamp
  decided_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_decisions_extraction ON validation_decisions(extraction_id);
CREATE INDEX idx_decisions_decided_at ON validation_decisions(decided_at DESC);

-- Core entities (verified knowledge)
CREATE TABLE IF NOT EXISTS core_entities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Entity identification
  entity_type entity_type NOT NULL,
  canonical_key TEXT NOT NULL,
  name TEXT NOT NULL,
  display_name TEXT,

  -- Attributes
  attributes JSONB,
  ecosystem ecosystem_type,

  -- Source tracking
  source_snapshot_id UUID REFERENCES raw_snapshots(id),

  -- Versioning
  is_current BOOLEAN DEFAULT TRUE,
  superseded_by UUID REFERENCES core_entities(id),
  version INTEGER DEFAULT 1,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_core_entities_key ON core_entities(canonical_key);
CREATE INDEX idx_core_entities_type ON core_entities(entity_type);
CREATE INDEX idx_core_entities_current ON core_entities(is_current) WHERE is_current = TRUE;
CREATE INDEX idx_core_entities_ecosystem ON core_entities(ecosystem);

COMMIT;

-- ============================================================================
-- VALIDATION
-- ============================================================================

DO $$
BEGIN
  -- Verify tables exist
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pipeline_runs') THEN
    RAISE EXCEPTION 'Table pipeline_runs was not created';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'raw_snapshots') THEN
    RAISE EXCEPTION 'Table raw_snapshots was not created';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'staging_extractions') THEN
    RAISE EXCEPTION 'Table staging_extractions was not created';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'validation_decisions') THEN
    RAISE EXCEPTION 'Table validation_decisions was not created';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'core_entities') THEN
    RAISE EXCEPTION 'Table core_entities was not created';
  END IF;

  RAISE NOTICE 'Migration 000 completed successfully ✓';
  RAISE NOTICE '  - Created 5 base tables: pipeline_runs, raw_snapshots, staging_extractions, validation_decisions, core_entities';
  RAISE NOTICE '  - Created 5 enums: ecosystem_type, entity_type, candidate_status, validation_decision_type, decider_type';
END $$;
