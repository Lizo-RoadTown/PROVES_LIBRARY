-- Migration 018: Add peer reflection analyzer views
-- Read-only views for computing agent drift metrics
-- These views power the Peer Reflection dashboard

BEGIN;

-- =============================================================================
-- VIEW: v_confidence_calibration
-- Purpose: Compare claimed confidence vs actual acceptance rate
-- Shows if agents are over-confident or under-confident
-- =============================================================================

CREATE OR REPLACE VIEW v_confidence_calibration AS
SELECT
    ecosystem,
    DATE_TRUNC('week', created_at)::DATE as week,
    COUNT(*) as extraction_count,
    AVG(confidence_score) as avg_claimed_confidence,
    AVG(CASE WHEN status = 'accepted' THEN 1.0 ELSE 0.0 END) as actual_acceptance_rate,
    AVG(confidence_score) - AVG(CASE WHEN status = 'accepted' THEN 1.0 ELSE 0.0 END) as calibration_error,
    STDDEV(confidence_score) as confidence_stddev
FROM staging_extractions
WHERE
    status IN ('accepted', 'rejected')
    AND confidence_score IS NOT NULL
GROUP BY ecosystem, DATE_TRUNC('week', created_at)
ORDER BY week DESC;

COMMENT ON VIEW v_confidence_calibration IS
'Weekly confidence calibration metrics. Positive calibration_error means over-confident.';

-- =============================================================================
-- VIEW: v_rejection_trend
-- Purpose: Track rejection patterns over time by reason and type
-- Helps identify systematic extraction issues
-- =============================================================================

CREATE OR REPLACE VIEW v_rejection_trend AS
SELECT
    ecosystem,
    candidate_type,
    DATE_TRUNC('week', se.created_at)::DATE as week,
    COUNT(*) FILTER (WHERE se.status = 'rejected') as rejection_count,
    COUNT(*) as total_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE se.status = 'rejected') / NULLIF(COUNT(*), 0),
        1
    ) as rejection_rate,
    -- Most common rejection reason (from validation_decisions)
    MODE() WITHIN GROUP (ORDER BY vd.decision_reason) FILTER (WHERE se.status = 'rejected') as top_rejection_reason
FROM staging_extractions se
LEFT JOIN validation_decisions vd ON se.extraction_id = vd.extraction_id
    AND vd.decision = 'reject'
WHERE se.status IN ('accepted', 'rejected')
GROUP BY ecosystem, candidate_type, DATE_TRUNC('week', se.created_at)
HAVING COUNT(*) >= 3  -- Only show if we have enough samples
ORDER BY week DESC, rejection_count DESC;

COMMENT ON VIEW v_rejection_trend IS
'Weekly rejection rates by ecosystem and entity type with top rejection reasons.';

-- =============================================================================
-- VIEW: v_lineage_failures
-- Purpose: Track lineage verification failures
-- Identifies evidence that couldn't be verified in source documents
-- =============================================================================

CREATE OR REPLACE VIEW v_lineage_failures AS
SELECT
    se.extraction_id,
    se.candidate_key,
    se.candidate_type,
    se.ecosystem,
    se.confidence_score,
    se.created_at,
    se.status,
    -- Use direct columns from staging_extractions (they have lineage info)
    se.lineage_verified,
    se.lineage_confidence,
    se.evidence->>'raw_evidence' as raw_evidence,
    -- Snapshot info if available
    se.snapshot_id,
    rs.source_url,
    rs.captured_at as fetch_timestamp
FROM staging_extractions se
LEFT JOIN raw_snapshots rs ON se.snapshot_id = rs.id
WHERE
    -- Include entries where lineage failed or was low confidence
    (
        se.lineage_verified = FALSE
        OR se.lineage_confidence < 0.5
    )
ORDER BY se.created_at DESC;

COMMENT ON VIEW v_lineage_failures IS
'Extractions with failed or low-confidence lineage verification.';

-- =============================================================================
-- VIEW: v_extraction_volume
-- Purpose: Track extraction volume over time by ecosystem
-- =============================================================================

CREATE OR REPLACE VIEW v_extraction_volume AS
SELECT
    ecosystem,
    DATE_TRUNC('day', created_at)::DATE as day,
    COUNT(*) as total_extractions,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
    COUNT(*) FILTER (WHERE status = 'accepted') as accepted_count,
    COUNT(*) FILTER (WHERE status = 'rejected') as rejected_count,
    AVG(confidence_score) as avg_confidence
FROM staging_extractions
GROUP BY ecosystem, DATE_TRUNC('day', created_at)
ORDER BY day DESC;

COMMENT ON VIEW v_extraction_volume IS
'Daily extraction counts by ecosystem and status.';

-- =============================================================================
-- VIEW: v_reviewer_patterns
-- Purpose: Analyze human reviewer behavior for calibrating agent trust
-- =============================================================================

CREATE OR REPLACE VIEW v_reviewer_patterns AS
SELECT
    vd.decided_by as reviewer_id,
    DATE_TRUNC('week', vd.decided_at)::DATE as week,
    COUNT(*) as decisions_made,
    COUNT(*) FILTER (WHERE vd.decision = 'accept') as approvals,
    COUNT(*) FILTER (WHERE vd.decision = 'reject') as rejections,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE vd.decision = 'accept') / NULLIF(COUNT(*), 0),
        1
    ) as approval_rate,
    AVG(se.confidence_score) FILTER (WHERE vd.decision = 'accept') as avg_approved_confidence,
    AVG(se.confidence_score) FILTER (WHERE vd.decision = 'reject') as avg_rejected_confidence
FROM validation_decisions vd
JOIN staging_extractions se ON vd.extraction_id = se.extraction_id
WHERE vd.decider_type = 'human'
GROUP BY vd.decided_by, DATE_TRUNC('week', vd.decided_at)
ORDER BY week DESC, decisions_made DESC;

COMMENT ON VIEW v_reviewer_patterns IS
'Human reviewer behavior patterns for trust calibration baseline.';

-- =============================================================================
-- VIEW: v_entity_type_performance
-- Purpose: Track extraction quality by entity type
-- =============================================================================

CREATE OR REPLACE VIEW v_entity_type_performance AS
SELECT
    candidate_type,
    ecosystem,
    COUNT(*) as total_extractions,
    COUNT(*) FILTER (WHERE status = 'accepted') as accepted_count,
    COUNT(*) FILTER (WHERE status = 'rejected') as rejected_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'accepted') /
        NULLIF(COUNT(*) FILTER (WHERE status IN ('accepted', 'rejected')), 0),
        1
    ) as acceptance_rate,
    AVG(confidence_score) as avg_confidence,
    AVG(confidence_score) FILTER (WHERE status = 'accepted') as avg_accepted_confidence,
    AVG(confidence_score) FILTER (WHERE status = 'rejected') as avg_rejected_confidence
FROM staging_extractions
WHERE status IN ('accepted', 'rejected', 'pending')
GROUP BY candidate_type, ecosystem
ORDER BY total_extractions DESC;

COMMENT ON VIEW v_entity_type_performance IS
'Extraction performance metrics broken down by entity type and ecosystem.';

-- =============================================================================
-- VIEW: v_calibration_drift_alert
-- Purpose: Identify weeks where calibration error exceeds threshold
-- For alerting on agent drift
-- =============================================================================

CREATE OR REPLACE VIEW v_calibration_drift_alert AS
SELECT
    *,
    CASE
        WHEN ABS(calibration_error) > 0.2 THEN 'critical'
        WHEN ABS(calibration_error) > 0.1 THEN 'warning'
        ELSE 'ok'
    END as alert_level,
    CASE
        WHEN calibration_error > 0.1 THEN 'over_confident'
        WHEN calibration_error < -0.1 THEN 'under_confident'
        ELSE 'well_calibrated'
    END as drift_direction
FROM v_confidence_calibration
WHERE extraction_count >= 5;  -- Only alert if we have enough samples

COMMENT ON VIEW v_calibration_drift_alert IS
'Alerts for weeks where confidence calibration drifted beyond thresholds.';

-- =============================================================================
-- GRANT READ ACCESS
-- These views are read-only by design
-- =============================================================================

-- Grant select on all views to authenticated users
GRANT SELECT ON v_confidence_calibration TO authenticated;
GRANT SELECT ON v_rejection_trend TO authenticated;
GRANT SELECT ON v_lineage_failures TO authenticated;
GRANT SELECT ON v_extraction_volume TO authenticated;
GRANT SELECT ON v_reviewer_patterns TO authenticated;
GRANT SELECT ON v_entity_type_performance TO authenticated;
GRANT SELECT ON v_calibration_drift_alert TO authenticated;

-- Grant to service role as well
GRANT SELECT ON v_confidence_calibration TO service_role;
GRANT SELECT ON v_rejection_trend TO service_role;
GRANT SELECT ON v_lineage_failures TO service_role;
GRANT SELECT ON v_extraction_volume TO service_role;
GRANT SELECT ON v_reviewer_patterns TO service_role;
GRANT SELECT ON v_entity_type_performance TO service_role;
GRANT SELECT ON v_calibration_drift_alert TO service_role;

COMMIT;
