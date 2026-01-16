-- Migration 005b: Fix review_decision constraint to include 'modified'
-- The webhook handler uses 'modified' but the original constraint only allowed 'approve' and 'reject'

BEGIN;

-- Drop the old constraint
ALTER TABLE staging_extractions
DROP CONSTRAINT IF EXISTS staging_extractions_review_decision_check;

-- Add updated constraint
ALTER TABLE staging_extractions
ADD CONSTRAINT staging_extractions_review_decision_check
CHECK (review_decision IN ('approve', 'reject', 'modified'));

COMMIT;
