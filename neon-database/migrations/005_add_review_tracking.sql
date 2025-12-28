-- Migration 005: Add review tracking columns
-- Tracks who approved/rejected extractions and when

BEGIN;

-- Add review tracking columns to staging_extractions
ALTER TABLE staging_extractions
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS review_decision TEXT CHECK (review_decision IN ('approve', 'reject')),
ADD COLUMN IF NOT EXISTS review_notes TEXT;

-- Create index for querying reviewed items
CREATE INDEX IF NOT EXISTS idx_staging_extractions_reviewed
ON staging_extractions(reviewed_at)
WHERE reviewed_at IS NOT NULL;

-- Create index for review decisions
CREATE INDEX IF NOT EXISTS idx_staging_extractions_review_decision
ON staging_extractions(review_decision)
WHERE review_decision IS NOT NULL;

COMMIT;
