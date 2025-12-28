-- Migration 004: Update evidence_type enum for GNN training
-- Replaces format-based types with semantic content types
--
-- Rationale: For Graph Neural Network features and MCP server,
-- semantic meaning (what the evidence says) is more valuable than
-- documentation format (how it's presented).
--
-- Old types (format-based):
--   definition_spec, interface_contract, example, narrative,
--   table_diagram, comment, inferred
--
-- New types (semantic-based):
--   explicit_requirement, safety_constraint, performance_constraint,
--   feature_description, interface_specification, behavioral_contract,
--   example_usage, design_rationale, inferred

BEGIN;

-- Step 1: Create new enum with semantic types
CREATE TYPE evidence_type_new AS ENUM (
    'explicit_requirement',      -- "System shall/must..." statements
    'safety_constraint',          -- Safety-critical requirements, failure modes
    'performance_constraint',     -- Timing, resource, throughput constraints
    'feature_description',        -- Functional descriptions, capabilities
    'interface_specification',    -- Port/API contracts, protocols
    'behavioral_contract',        -- State machines, event sequences, modes
    'example_usage',              -- Code examples, usage patterns
    'design_rationale',           -- Why decisions were made, trade-offs
    'dependency_declaration',     -- Explicit dependency statements
    'configuration_parameter',    -- Settings, modes, configuration
    'inferred'                    -- Derived from context, not explicit
);

-- Step 2: Add temporary column with new type
ALTER TABLE staging_extractions
ADD COLUMN evidence_type_new evidence_type_new;

-- Step 3: Migrate existing data with semantic mapping
-- Map old format types to new semantic types
UPDATE staging_extractions
SET evidence_type_new = CASE
    -- Specs and contracts are usually requirements
    WHEN evidence_type = 'definition_spec' THEN 'explicit_requirement'::evidence_type_new
    WHEN evidence_type = 'interface_contract' THEN 'interface_specification'::evidence_type_new

    -- Examples stay examples
    WHEN evidence_type = 'example' THEN 'example_usage'::evidence_type_new

    -- Narrative could be features or rationale - default to feature
    WHEN evidence_type = 'narrative' THEN 'feature_description'::evidence_type_new

    -- Tables and diagrams often describe behavior
    WHEN evidence_type = 'table_diagram' THEN 'behavioral_contract'::evidence_type_new

    -- Comments could be rationale or features - default to rationale
    WHEN evidence_type = 'comment' THEN 'design_rationale'::evidence_type_new

    -- Inferred stays inferred
    WHEN evidence_type = 'inferred' THEN 'inferred'::evidence_type_new

    -- Fallback (shouldn't happen)
    ELSE 'inferred'::evidence_type_new
END;

-- Step 4: Drop old column and rename new column
ALTER TABLE staging_extractions DROP COLUMN evidence_type;
ALTER TABLE staging_extractions RENAME COLUMN evidence_type_new TO evidence_type;

-- Step 5: Drop old enum type
DROP TYPE evidence_type;

-- Step 6: Rename new type to standard name
ALTER TYPE evidence_type_new RENAME TO evidence_type;

-- Add helpful comment
COMMENT ON TYPE evidence_type IS
'Semantic classification of evidence for GNN training and criticality analysis.
Types capture WHAT the evidence says (content) rather than HOW it appears (format).

Categories:
- explicit_requirement: SHALL/MUST statements, formal requirements
- safety_constraint: Safety-critical requirements, failure modes, inhibit schemes
- performance_constraint: Timing (within Xms), resources, throughput limits
- feature_description: Functional capabilities, what the system does
- interface_specification: Port contracts, APIs, protocols, picolock specs
- behavioral_contract: State machines, event sequences, operational modes
- example_usage: Code examples, usage patterns, how-to guides
- design_rationale: Why decisions made, trade-offs, architectural choices
- dependency_declaration: Explicit "depends on", "requires", "uses" statements
- configuration_parameter: Settings, modes, tunable parameters
- inferred: Derived from context, not explicitly stated';

COMMIT;

-- Verification query (run after migration)
-- SELECT evidence_type, COUNT(*) as count
-- FROM staging_extractions
-- GROUP BY evidence_type
-- ORDER BY count DESC;

DO $$
BEGIN
    RAISE NOTICE 'Migration 004 completed successfully ✓';
    RAISE NOTICE '  - Replaced evidence_type enum with semantic categories';
    RAISE NOTICE '  - Migrated existing data to new types';
    RAISE NOTICE '  - Ready for GNN training and MCP server';
    RAISE NOTICE '';
    RAISE NOTICE 'New evidence types available:';
    RAISE NOTICE '  - explicit_requirement (SHALL/MUST statements)';
    RAISE NOTICE '  - safety_constraint (safety-critical requirements)';
    RAISE NOTICE '  - performance_constraint (timing, resource limits)';
    RAISE NOTICE '  - feature_description (functional capabilities)';
    RAISE NOTICE '  - interface_specification (port/API contracts)';
    RAISE NOTICE '  - behavioral_contract (state machines, sequences)';
    RAISE NOTICE '  - example_usage (code examples, patterns)';
    RAISE NOTICE '  - design_rationale (why decisions made)';
    RAISE NOTICE '  - dependency_declaration (explicit dependencies)';
    RAISE NOTICE '  - configuration_parameter (settings, modes)';
    RAISE NOTICE '  - inferred (derived from context)';
END $$;
