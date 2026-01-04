-- Migration 014: Add Missing Entity Types to core_entities
-- Date: 2026-01-03
-- Purpose: Add entity types that exist in candidate_status but not in entity_type

BEGIN;

-- Add missing entity types to the enum
-- These are used in staging_extractions but weren't in core_entities schema

DO $$
BEGIN
    -- Add dependency
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'dependency'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'dependency';
        RAISE NOTICE 'Added entity_type: dependency';
    END IF;

    -- Add connection
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'connection'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'connection';
        RAISE NOTICE 'Added entity_type: connection';
    END IF;

    -- Add port
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'port'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'port';
        RAISE NOTICE 'Added entity_type: port';
    END IF;

    -- Add event
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'event'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'event';
        RAISE NOTICE 'Added entity_type: event';
    END IF;

    -- Add telemetry
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'telemetry'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'telemetry';
        RAISE NOTICE 'Added entity_type: telemetry';
    END IF;

    -- Add data_type
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'data_type'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'data_type';
        RAISE NOTICE 'Added entity_type: data_type';
    END IF;

    -- Add parameter
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'parameter'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'parameter';
        RAISE NOTICE 'Added entity_type: parameter';
    END IF;

    -- Add command
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'command'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'command';
        RAISE NOTICE 'Added entity_type: command';
    END IF;
END $$;

COMMIT;

-- Verification
DO $$
DECLARE
    missing_types TEXT[];
BEGIN
    -- Check that all required types exist
    SELECT ARRAY_AGG(type_name)
    INTO missing_types
    FROM (VALUES
        ('dependency'),
        ('connection'),
        ('port'),
        ('event'),
        ('telemetry'),
        ('data_type'),
        ('parameter'),
        ('command')
    ) AS required(type_name)
    WHERE NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = required.type_name
        AND enumtypid = 'entity_type'::regtype
    );

    IF array_length(missing_types, 1) > 0 THEN
        RAISE EXCEPTION 'Missing entity types: %', array_to_string(missing_types, ', ');
    END IF;

    RAISE NOTICE 'Migration 014 completed successfully ✓';
    RAISE NOTICE '  - Added 8 missing entity types to core_entities enum';
END $$;
