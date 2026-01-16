-- ============================================================================
-- Migration 010: Knowledge Epistemics Sidecar
-- ============================================================================
-- Purpose: Add practical checklist-oriented epistemic metadata that maps
--          directly to the 7-question Knowledge Capture Checklist
-- Reference: canon/KNOWLEDGE_CAPTURE_CHECKLIST.md
-- Date: 2025-12-30
-- ============================================================================

BEGIN;

-- ============================================================================
-- PART 1: ENUM TYPES FOR EPISTEMIC METADATA
-- ============================================================================

-- Question 1: Who knew this, and how close were they?
CREATE TYPE contact_mode AS ENUM ('direct','mediated','effect_only','derived');

CREATE TYPE signal_type AS ENUM (
  'text','code','spec','comment','example','log','telemetry',
  'diagram','model','table','test','conversation','unknown'
);

-- Question 2: Where does the experience live now?
CREATE TYPE pattern_storage AS ENUM ('internalized','externalized','mixed','unknown');

-- Question 6: Who wrote or taught this, and why?
CREATE TYPE author_intent AS ENUM (
  'explain','instruct','justify','explore','comply','persuade','remember','unknown'
);

-- Question 7: Does this only work if someone keeps doing it?
CREATE TYPE transferability AS ENUM ('portable','conditional','local','tacit_like','unknown');

-- Question 3: What has to stay connected for this to work?
CREATE TYPE sequence_role AS ENUM ('precondition','step','outcome','postcondition','none');

-- Loss modes we care about (from checklist flags)
CREATE TYPE loss_mode AS ENUM (
  'embodiment_loss',
  'practice_decay',
  'context_collapse',
  'relational_fragmentation',
  'drift',
  'authorship_loss',
  'pedagogical_distortion',
  'model_overreach',
  'proxy_replacement'
);

COMMENT ON TYPE contact_mode IS 'How the observer touched reality (or didn''t)';
COMMENT ON TYPE signal_type IS 'What kind of signal this is';
COMMENT ON TYPE pattern_storage IS 'Where accumulated historical patterns live (internalized in body/nervous system vs externalized in symbols/records)';
COMMENT ON TYPE author_intent IS 'Why this was written (helps catch pedagogical/authorship issues)';
COMMENT ON TYPE transferability IS 'How transferable knowledge is (risk proxy; NOT recordability)';
COMMENT ON TYPE sequence_role IS 'Role in a sequence (for relational integrity tracking)';
COMMENT ON TYPE loss_mode IS 'Specific knowledge loss failure modes';

-- ============================================================================
-- PART 2: KNOWLEDGE EPISTEMICS SIDECAR TABLE
-- ============================================================================

CREATE TABLE knowledge_epistemics (
  extraction_id UUID PRIMARY KEY REFERENCES staging_extractions(extraction_id) ON DELETE CASCADE,

  -- ========================================================================
  -- Identity / Quick Handle
  -- ========================================================================
  domain TEXT NOT NULL,                     -- 'fprime', 'proveskit', etc (or finer: subsystem)
  claim_summary TEXT,                       -- Optional: short paraphrase for UX/search

  -- ========================================================================
  -- QUESTION 1: Who knew this & how close were they?
  -- ========================================================================
  observer_id TEXT,                         -- 'agent:parser_v1', 'doc:...', 'human:technician_x'
  observer_type TEXT,                       -- 'ai','human','instrument','process' (keep TEXT for flexibility)
  contact_mode contact_mode NOT NULL DEFAULT 'derived',
  contact_strength NUMERIC(3,2) NOT NULL DEFAULT 0.30 CHECK (
    contact_strength >= 0.00 AND contact_strength <= 1.00
  ),  -- Continuous 0.00..1.00
  signal_type signal_type NOT NULL DEFAULT 'text',
  evidence_ref JSONB,                       -- Pointer(s): file path, url, checksum, offsets

  -- ========================================================================
  -- QUESTION 2: Where does the experience live now?
  -- ========================================================================
  pattern_storage pattern_storage NOT NULL DEFAULT 'externalized',
  representation_media TEXT[] NOT NULL DEFAULT ARRAY['text'], -- e.g., {'text','code','diagram'}

  -- ========================================================================
  -- QUESTION 3: What must stay connected for this to work?
  -- ========================================================================
  episode_id UUID REFERENCES episodic_entities(episode_id) ON DELETE SET NULL,
  sequence_role sequence_role NOT NULL DEFAULT 'none',
  dependencies JSONB,                       -- List of entity keys or extraction_ids that must remain bound
  relational_notes TEXT,                    -- Freeform description of relational dependencies

  -- ========================================================================
  -- QUESTION 4: Under what conditions was this true?
  -- ========================================================================
  validity_conditions JSONB,                -- Key-values: { "fprime_version": "...", "config": "...", ... }
  assumptions TEXT[],                       -- Lightweight list of assumptions
  scope TEXT,                               -- 'local'|'subsystem'|'system'|'general' (TEXT keeps it simple)

  -- ========================================================================
  -- QUESTION 5: When does this stop being reliable?
  -- ========================================================================
  observed_at TIMESTAMPTZ,                  -- When the source snapshot was taken (or doc commit time)
  valid_from TIMESTAMPTZ,
  valid_to TIMESTAMPTZ,
  refresh_trigger TEXT,                     -- 'new_rev','recalibration','periodic','after_incident', etc
  staleness_risk NUMERIC(3,2) NOT NULL DEFAULT 0.20 CHECK (
    staleness_risk >= 0.00 AND staleness_risk <= 1.00
  ),

  -- ========================================================================
  -- QUESTION 6: Who wrote/taught this, and why?
  -- ========================================================================
  author_id TEXT,                           -- Author identifier
  intent author_intent NOT NULL DEFAULT 'unknown',
  confidence NUMERIC(3,2) CHECK (           -- Separate from extraction confidence_score; this is epistemic confidence
    confidence IS NULL OR (confidence >= 0 AND confidence <= 1)
  ),
  uncertainty_notes TEXT,                   -- What uncertainty was present but not recorded?

  -- ========================================================================
  -- QUESTION 7: Does this only work if someone keeps doing it?
  -- ========================================================================
  reenactment_required BOOLEAN NOT NULL DEFAULT FALSE,
  practice_interval TEXT,                   -- 'per-run','weekly','per-release', etc
  skill_transferability transferability NOT NULL DEFAULT 'portable',

  -- ========================================================================
  -- Loss Mode Tracking
  -- ========================================================================
  identified_loss_modes loss_mode[],        -- Array of detected loss modes

  -- ========================================================================
  -- Housekeeping
  -- ========================================================================
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE knowledge_epistemics IS
  'Epistemic metadata sidecar for staging_extractions, mapping to the 7-question Knowledge Capture Checklist';

COMMENT ON COLUMN knowledge_epistemics.observer_id IS
  'Who observed this knowledge (agent ID, human ID, instrument ID)';

COMMENT ON COLUMN knowledge_epistemics.contact_strength IS
  'Continuous measure (0.0-1.0) of observer coupling to phenomenon';

COMMENT ON COLUMN knowledge_epistemics.pattern_storage IS
  'Where accumulated historical patterns live: internalized (body/nervous system) vs externalized (symbols/records)';

COMMENT ON COLUMN knowledge_epistemics.dependencies IS
  'JSONB array of entity keys or extraction_ids that must remain connected for this knowledge to work';

COMMENT ON COLUMN knowledge_epistemics.validity_conditions IS
  'JSONB object describing conditions under which this knowledge holds (versions, configs, environmental constraints)';

COMMENT ON COLUMN knowledge_epistemics.staleness_risk IS
  'Risk (0.0-1.0) that this knowledge has become stale or invalid due to system changes';

COMMENT ON COLUMN knowledge_epistemics.intent IS
  'Why this was written - helps detect pedagogical distortion, false authority, compliance theater';

COMMENT ON COLUMN knowledge_epistemics.reenactment_required IS
  'TRUE if this knowledge requires ongoing practice/reenactment to maintain (embodied skills that degrade without use)';

COMMENT ON COLUMN knowledge_epistemics.identified_loss_modes IS
  'Array of specific loss modes detected for this knowledge (e.g., embodiment_loss, practice_decay, context_collapse)';

-- ============================================================================
-- PART 3: INDEXES FOR EFFICIENT QUERIES
-- ============================================================================

CREATE INDEX idx_epistemics_domain ON knowledge_epistemics(domain);
CREATE INDEX idx_epistemics_contact_mode ON knowledge_epistemics(contact_mode);
CREATE INDEX idx_epistemics_pattern_storage ON knowledge_epistemics(pattern_storage);
CREATE INDEX idx_epistemics_reenactment ON knowledge_epistemics(reenactment_required) WHERE reenactment_required = TRUE;
CREATE INDEX idx_epistemics_episode ON knowledge_epistemics(episode_id) WHERE episode_id IS NOT NULL;
CREATE INDEX idx_epistemics_intent ON knowledge_epistemics(intent);
CREATE INDEX idx_epistemics_staleness ON knowledge_epistemics(staleness_risk) WHERE staleness_risk > 0.5;

-- JSONB indexes for complex queries
CREATE INDEX idx_epistemics_validity_conditions ON knowledge_epistemics USING GIN (validity_conditions);
CREATE INDEX idx_epistemics_dependencies ON knowledge_epistemics USING GIN (dependencies);
CREATE INDEX idx_epistemics_loss_modes ON knowledge_epistemics USING GIN (identified_loss_modes);

-- ============================================================================
-- PART 4: TRIGGER FOR AUTOMATIC LOSS MODE DETECTION
-- ============================================================================

CREATE OR REPLACE FUNCTION detect_loss_modes()
RETURNS TRIGGER AS $$
DECLARE
  detected_modes loss_mode[] := ARRAY[]::loss_mode[];
BEGIN
  -- Detect embodiment_loss: internalized pattern storage + no reenactment mechanism
  IF NEW.pattern_storage = 'internalized'
     AND NEW.reenactment_required = FALSE
     AND NEW.skill_transferability IN ('tacit_like', 'local') THEN
    detected_modes := array_append(detected_modes, 'embodiment_loss'::loss_mode);
  END IF;

  -- Detect practice_decay: reenactment required but no practice interval specified
  IF NEW.reenactment_required = TRUE AND NEW.practice_interval IS NULL THEN
    detected_modes := array_append(detected_modes, 'practice_decay'::loss_mode);
  END IF;

  -- Detect context_collapse: validity conditions missing for conditional knowledge
  IF NEW.skill_transferability = 'conditional'
     AND (NEW.validity_conditions IS NULL OR NEW.validity_conditions = '{}'::jsonb) THEN
    detected_modes := array_append(detected_modes, 'context_collapse'::loss_mode);
  END IF;

  -- Detect relational_fragmentation: dependencies exist but not linked to episode
  IF NEW.dependencies IS NOT NULL
     AND jsonb_array_length(NEW.dependencies) > 0
     AND NEW.episode_id IS NULL
     AND NEW.sequence_role != 'none' THEN
    detected_modes := array_append(detected_modes, 'relational_fragmentation'::loss_mode);
  END IF;

  -- Detect drift: high staleness risk without refresh trigger
  IF NEW.staleness_risk > 0.6 AND NEW.refresh_trigger IS NULL THEN
    detected_modes := array_append(detected_modes, 'drift'::loss_mode);
  END IF;

  -- Detect pedagogical_distortion: instructional intent but low contact strength
  IF NEW.intent IN ('instruct', 'explain') AND NEW.contact_strength < 0.4 THEN
    detected_modes := array_append(detected_modes, 'pedagogical_distortion'::loss_mode);
  END IF;

  -- Detect model_overreach: derived contact mode but missing validity conditions
  IF NEW.contact_mode = 'derived'
     AND (NEW.validity_conditions IS NULL OR NEW.validity_conditions = '{}'::jsonb) THEN
    detected_modes := array_append(detected_modes, 'model_overreach'::loss_mode);
  END IF;

  -- Detect proxy_replacement: effect_only contact but treated as direct observation
  IF NEW.contact_mode = 'effect_only' AND NEW.contact_strength > 0.7 THEN
    detected_modes := array_append(detected_modes, 'proxy_replacement'::loss_mode);
  END IF;

  -- Set detected loss modes
  NEW.identified_loss_modes := detected_modes;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_detect_loss_modes
  BEFORE INSERT OR UPDATE ON knowledge_epistemics
  FOR EACH ROW
  EXECUTE FUNCTION detect_loss_modes();

COMMENT ON FUNCTION detect_loss_modes IS
  'Automatically detects epistemic loss modes based on checklist patterns';

-- ============================================================================
-- PART 5: COMBINED VIEW FOR COMPLETE EPISTEMIC PROFILE
-- ============================================================================

CREATE OR REPLACE VIEW complete_epistemic_profile AS
SELECT
  -- Extraction basics
  se.extraction_id,
  se.candidate_key,
  se.candidate_type,
  se.ecosystem,
  se.status,
  se.confidence_score AS extraction_confidence,

  -- Original dimensional metadata (from migration 008)
  se.knowledge_form,
  se.knowledge_form_confidence,
  se.contact_level,
  se.contact_confidence,
  se.directionality,
  se.temporality,
  se.formalizability,
  se.carrier,
  se.dimensional_completeness,

  -- Checklist-oriented epistemics (from migration 010)
  ke.domain,
  ke.claim_summary,
  ke.observer_id,
  ke.observer_type,
  ke.contact_mode,
  ke.contact_strength,
  ke.signal_type,
  ke.pattern_storage,
  ke.representation_media,
  ke.episode_id,
  ke.sequence_role,
  ke.dependencies,
  ke.validity_conditions,
  ke.assumptions,
  ke.scope,
  ke.observed_at,
  ke.valid_from,
  ke.valid_to,
  ke.refresh_trigger,
  ke.staleness_risk,
  ke.author_id,
  ke.intent AS author_intent,
  ke.confidence AS epistemic_confidence,
  ke.uncertainty_notes,
  ke.reenactment_required,
  ke.practice_interval,
  ke.skill_transferability,
  ke.identified_loss_modes,

  -- Lineage
  se.snapshot_id,
  se.created_at,
  se.updated_at

FROM staging_extractions se
LEFT JOIN knowledge_epistemics ke ON se.extraction_id = ke.extraction_id;

COMMENT ON VIEW complete_epistemic_profile IS
  'Complete epistemic metadata combining original dimensions (migration 008) with checklist-oriented fields (migration 010)';

-- ============================================================================
-- PART 6: ANALYSIS VIEWS FOR CHECKLIST QUESTIONS
-- ============================================================================

-- View: High-risk knowledge requiring intervention
CREATE OR REPLACE VIEW knowledge_at_risk AS
SELECT
  ep.extraction_id,
  ep.candidate_key,
  ep.domain,
  ep.pattern_storage,
  ep.contact_mode,
  ep.reenactment_required,
  ep.skill_transferability,
  ep.identified_loss_modes,
  ep.staleness_risk,

  -- Risk score (0-1)
  (
    CASE WHEN ep.pattern_storage = 'internalized' THEN 0.3 ELSE 0.0 END +
    CASE WHEN ep.reenactment_required AND ep.practice_interval IS NULL THEN 0.3 ELSE 0.0 END +
    CASE WHEN ep.skill_transferability IN ('tacit_like', 'local') THEN 0.2 ELSE 0.0 END +
    CASE WHEN ep.staleness_risk > 0.6 THEN 0.2 ELSE 0.0 END +
    CASE WHEN array_length(ep.identified_loss_modes, 1) > 2 THEN 0.2 ELSE 0.0 END
  ) AS composite_risk_score,

  -- Recommended interventions
  CASE
    WHEN 'embodiment_loss' = ANY(ep.identified_loss_modes) THEN 'Pair with experienced technician, capture video walkthroughs'
    WHEN 'practice_decay' = ANY(ep.identified_loss_modes) THEN 'Establish practice schedule, create simulation environment'
    WHEN 'context_collapse' = ANY(ep.identified_loss_modes) THEN 'Document validity conditions, add scope constraints'
    WHEN 'drift' = ANY(ep.identified_loss_modes) THEN 'Set refresh trigger, establish recalibration procedure'
    ELSE 'Monitor for loss modes'
  END AS recommended_intervention,

  ep.created_at

FROM complete_epistemic_profile ep
WHERE ep.identified_loss_modes IS NOT NULL
  AND array_length(ep.identified_loss_modes, 1) > 0
ORDER BY composite_risk_score DESC, ep.created_at DESC;

COMMENT ON VIEW knowledge_at_risk IS
  'Knowledge with identified loss modes and recommended interventions';

-- View: Pattern storage distribution (Question 2)
CREATE OR REPLACE VIEW pattern_storage_distribution AS
SELECT
  pattern_storage,
  COUNT(*) as count,
  AVG(contact_strength) as avg_contact_strength,
  AVG(staleness_risk) as avg_staleness_risk,
  COUNT(*) FILTER (WHERE reenactment_required = TRUE) as reenactment_count,
  COUNT(*) FILTER (WHERE skill_transferability IN ('tacit_like', 'local')) as transfer_risk_count
FROM knowledge_epistemics
GROUP BY pattern_storage
ORDER BY count DESC;

COMMENT ON VIEW pattern_storage_distribution IS
  'Distribution of knowledge by pattern storage location (internalized vs externalized)';

-- View: Authorship intent analysis (Question 6)
CREATE OR REPLACE VIEW authorship_intent_analysis AS
SELECT
  intent,
  COUNT(*) as count,
  AVG(contact_strength) as avg_contact_strength,
  COUNT(*) FILTER (WHERE 'pedagogical_distortion' = ANY(identified_loss_modes)) as pedagogical_distortion_count,
  COUNT(*) FILTER (WHERE uncertainty_notes IS NOT NULL) as has_uncertainty_notes
FROM knowledge_epistemics
GROUP BY intent
ORDER BY count DESC;

COMMENT ON VIEW authorship_intent_analysis IS
  'Distribution of knowledge by authorship intent, flagging pedagogical distortion risks';

-- View: Temporal validity tracking (Question 5)
CREATE OR REPLACE VIEW temporal_validity_status AS
SELECT
  ke.extraction_id,
  se.candidate_key,
  ke.domain,
  ke.observed_at,
  ke.valid_from,
  ke.valid_to,
  ke.refresh_trigger,
  ke.staleness_risk,

  -- Status flags
  CASE
    WHEN ke.valid_to IS NOT NULL AND ke.valid_to < NOW() THEN 'expired'
    WHEN ke.staleness_risk > 0.7 THEN 'high_staleness_risk'
    WHEN ke.refresh_trigger IS NOT NULL AND ke.staleness_risk > 0.4 THEN 'needs_refresh'
    ELSE 'valid'
  END AS validity_status,

  -- Days until expiration (if applicable)
  CASE
    WHEN ke.valid_to IS NOT NULL THEN EXTRACT(DAY FROM ke.valid_to - NOW())
    ELSE NULL
  END AS days_until_expiration,

  ke.created_at

FROM knowledge_epistemics ke
JOIN staging_extractions se ON ke.extraction_id = se.extraction_id
ORDER BY ke.staleness_risk DESC, days_until_expiration ASC NULLS LAST;

COMMENT ON VIEW temporal_validity_status IS
  'Tracks when knowledge stops being reliable (Question 5)';

-- ============================================================================
-- PART 7: HELPER FUNCTIONS
-- ============================================================================

-- Function: Calculate composite risk score
CREATE OR REPLACE FUNCTION calculate_epistemic_risk(
  p_extraction_id UUID
) RETURNS NUMERIC AS $$
DECLARE
  v_risk NUMERIC := 0.0;
  v_record RECORD;
BEGIN
  SELECT * INTO v_record
  FROM knowledge_epistemics
  WHERE extraction_id = p_extraction_id;

  IF NOT FOUND THEN
    RETURN 0.0;
  END IF;

  -- Pattern storage risk
  IF v_record.pattern_storage = 'internalized' THEN
    v_risk := v_risk + 0.3;
  END IF;

  -- Reenactment risk
  IF v_record.reenactment_required AND v_record.practice_interval IS NULL THEN
    v_risk := v_risk + 0.3;
  END IF;

  -- Transferability risk
  IF v_record.skill_transferability IN ('tacit_like', 'local') THEN
    v_risk := v_risk + 0.2;
  END IF;

  -- Staleness risk
  IF v_record.staleness_risk > 0.6 THEN
    v_risk := v_risk + 0.2;
  END IF;

  -- Loss mode count
  IF array_length(v_record.identified_loss_modes, 1) > 2 THEN
    v_risk := v_risk + 0.2;
  END IF;

  RETURN LEAST(v_risk, 1.0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_epistemic_risk IS
  'Calculates composite epistemic risk score (0.0-1.0) for an extraction';

-- ============================================================================
-- PART 8: DATA VALIDATION
-- ============================================================================

DO $$
DECLARE
  table_exists BOOLEAN;
BEGIN
  -- Check knowledge_epistemics table exists
  SELECT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = 'knowledge_epistemics'
  ) INTO table_exists;

  IF NOT table_exists THEN
    RAISE EXCEPTION 'Table knowledge_epistemics was not created';
  END IF;

  -- Check ENUMs exist
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'contact_mode') THEN
    RAISE EXCEPTION 'ENUM contact_mode was not created';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'pattern_storage') THEN
    RAISE EXCEPTION 'ENUM pattern_storage was not created';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'loss_mode') THEN
    RAISE EXCEPTION 'ENUM loss_mode was not created';
  END IF;

  -- Check views exist
  IF NOT EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'complete_epistemic_profile') THEN
    RAISE EXCEPTION 'View complete_epistemic_profile was not created';
  END IF;

  RAISE NOTICE 'Knowledge epistemics sidecar migration completed successfully ✓';
  RAISE NOTICE 'Created: knowledge_epistemics table, 7 ENUMs, 5 views, 2 functions, 1 trigger';
END $$;

COMMIT;

-- ============================================================================
-- POST-MIGRATION VERIFICATION QUERIES
-- ============================================================================

-- 1. Check table structure
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'knowledge_epistemics'
-- ORDER BY ordinal_position;

-- 2. Check ENUMs
-- SELECT typname, enumlabel
-- FROM pg_type t
-- JOIN pg_enum e ON t.oid = e.enumtypid
-- WHERE typname IN ('contact_mode', 'pattern_storage', 'author_intent', 'loss_mode')
-- ORDER BY typname, e.enumsortorder;

-- 3. Test loss mode detection
-- INSERT INTO staging_extractions (candidate_key, candidate_type) VALUES ('TestEntity', 'component');
-- INSERT INTO knowledge_epistemics (extraction_id, domain, pattern_storage, reenactment_required, contact_mode)
-- VALUES (
--   (SELECT extraction_id FROM staging_extractions WHERE candidate_key = 'TestEntity'),
--   'test',
--   'internalized',
--   FALSE,
--   'direct'
-- );
-- SELECT identified_loss_modes FROM knowledge_epistemics
-- WHERE extraction_id = (SELECT extraction_id FROM staging_extractions WHERE candidate_key = 'TestEntity');

-- 4. Check views
-- SELECT * FROM pattern_storage_distribution;
-- SELECT * FROM authorship_intent_analysis;
-- SELECT * FROM knowledge_at_risk LIMIT 5;
