-- Migration 027: Seed Test Graph Data
--
-- Creates realistic test entities and equivalences to demonstrate 3D graph
-- These represent a CubeSat system with interconnected components

BEGIN;

-- Get PROVES Lab ID and create a pipeline run for the seed data
DO $$
DECLARE
    v_proves_lab_id UUID;
    v_run_id UUID;
BEGIN
    SELECT id INTO v_proves_lab_id FROM organizations WHERE slug = 'proves-lab';

    -- Create a pipeline run for this seed data
    INSERT INTO pipeline_runs (run_name, run_type, started_at, completed_at)
    VALUES ('seed_cubesat_demo', 'manual', NOW(), NOW())
    RETURNING id INTO v_run_id;

    -- ==========================================================================
    -- ARCHITECTURE: Core satellite components
    -- ==========================================================================

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('flight_computer', 'Flight Computer', 'flight_computer', 'component',
            '{"domain": "software", "description": "Main onboard computer running flight software", "tags": ["avionics", "processing"]}'::jsonb,
            v_proves_lab_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('eps', 'Electrical Power System', 'eps', 'component',
            '{"domain": "hardware", "description": "Power generation, storage, and distribution", "tags": ["power", "batteries", "solar"]}'::jsonb,
            v_proves_lab_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('adcs', 'Attitude Determination and Control', 'adcs', 'component',
            '{"domain": "hardware", "description": "Spacecraft orientation sensing and control", "tags": ["attitude", "sensors", "actuators"]}'::jsonb,
            v_proves_lab_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('comm_system', 'Communications System', 'comm_system', 'component',
            '{"domain": "hardware", "description": "UHF/VHF radio for ground communication", "tags": ["radio", "telemetry", "command"]}'::jsonb,
            v_proves_lab_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('payload_camera', 'Imaging Payload', 'payload_camera', 'component',
            '{"domain": "hardware", "description": "Earth observation camera payload", "tags": ["camera", "imaging", "science"]}'::jsonb,
            v_proves_lab_id, v_run_id);

    -- ==========================================================================
    -- INTERFACES: Communication protocols and data interfaces
    -- ==========================================================================

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('i2c_bus', 'I2C Bus', 'i2c_bus', 'interface',
            '{"domain": "software", "description": "Inter-IC communication bus for subsystem data", "tags": ["bus", "serial", "data"]}'::jsonb,
            v_proves_lab_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('spi_bus', 'SPI Bus', 'spi_bus', 'interface',
            '{"domain": "software", "description": "High-speed serial interface for sensors", "tags": ["bus", "serial", "sensors"]}'::jsonb,
            v_proves_lab_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('uart_telemetry', 'UART Telemetry', 'uart_telemetry', 'interface',
            '{"domain": "software", "description": "Serial telemetry output to radio", "tags": ["serial", "telemetry"]}'::jsonb,
            v_proves_lab_id, v_run_id);

    -- ==========================================================================
    -- PROCEDURES: Operations runbooks
    -- ==========================================================================

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('deployment_sequence', 'Deployment Sequence', 'deployment_sequence', 'procedure',
            '{"domain": "ops", "description": "Post-separation antenna and solar panel deployment", "tags": ["deployment", "sequence", "critical"]}'::jsonb,
            v_proves_lab_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('safe_mode_procedure', 'Safe Mode Procedure', 'safe_mode_procedure', 'procedure',
            '{"domain": "ops", "description": "Autonomous fault response and recovery", "tags": ["safety", "fault", "recovery"]}'::jsonb,
            v_proves_lab_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('pass_operations', 'Ground Pass Operations', 'pass_operations', 'procedure',
            '{"domain": "ops", "description": "Standard ground station contact procedure", "tags": ["groundstation", "contact", "operations"]}'::jsonb,
            v_proves_lab_id, v_run_id);

    -- ==========================================================================
    -- DECISIONS: Architecture decisions
    -- ==========================================================================

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('adr_processor', 'ADR: STM32 Processor Selection', 'adr_processor', 'constraint',
            '{"domain": "software", "description": "Selected STM32F4 for flight computer due to radiation tolerance", "tags": ["adr", "processor", "radiation"], "category": "decision"}'::jsonb,
            v_proves_lab_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('adr_os', 'ADR: FreeRTOS Selection', 'adr_os', 'constraint',
            '{"domain": "software", "description": "Selected FreeRTOS for deterministic real-time behavior", "tags": ["adr", "rtos", "software"], "category": "decision"}'::jsonb,
            v_proves_lab_id, v_run_id);

    -- ==========================================================================
    -- LESSONS: Post-mission insights (using failure_mode type)
    -- ==========================================================================

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('lesson_thermal', 'Lesson: Battery Thermal Management', 'lesson_thermal', 'failure_mode',
            '{"domain": "hardware", "description": "Battery heaters essential during eclipse - nearly lost mission", "tags": ["thermal", "battery", "eclipse", "critical"], "category": "lesson"}'::jsonb,
            v_proves_lab_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('lesson_testing', 'Lesson: End-to-End Testing', 'lesson_testing', 'failure_mode',
            '{"domain": "process", "description": "Day-in-the-life testing caught critical timing bug", "tags": ["testing", "integration", "timing"], "category": "lesson"}'::jsonb,
            v_proves_lab_id, v_run_id);

    -- ==========================================================================
    -- CREATE EDGES (core_equivalences)
    -- ==========================================================================

    -- Flight Computer connects to everything via I2C
    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'flight_computer' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'i2c_bus' ORDER BY created_at DESC LIMIT 1),
        0.95, 'Flight computer is I2C master for all subsystems', true, NOW(), v_run_id;

    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'i2c_bus' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'eps' ORDER BY created_at DESC LIMIT 1),
        0.90, 'EPS telemetry and commands via I2C', true, NOW(), v_run_id;

    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'i2c_bus' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'adcs' ORDER BY created_at DESC LIMIT 1),
        0.90, 'ADCS sensor data and commands via I2C', true, NOW(), v_run_id;

    -- SPI for high-speed sensor data
    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'flight_computer' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'spi_bus' ORDER BY created_at DESC LIMIT 1),
        0.92, 'SPI master for camera and high-rate sensors', true, NOW(), v_run_id;

    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'spi_bus' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'payload_camera' ORDER BY created_at DESC LIMIT 1),
        0.88, 'Camera data transfer via SPI', true, NOW(), v_run_id;

    -- UART to radio
    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'flight_computer' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'uart_telemetry' ORDER BY created_at DESC LIMIT 1),
        0.95, 'Telemetry frames sent via UART', true, NOW(), v_run_id;

    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'uart_telemetry' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'comm_system' ORDER BY created_at DESC LIMIT 1),
        0.93, 'Radio receives telemetry via UART', true, NOW(), v_run_id;

    -- Power relationships
    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'eps' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'flight_computer' ORDER BY created_at DESC LIMIT 1),
        0.98, 'EPS provides regulated power to flight computer', true, NOW(), v_run_id;

    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'eps' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'comm_system' ORDER BY created_at DESC LIMIT 1),
        0.95, 'EPS provides power to radio system', true, NOW(), v_run_id;

    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'eps' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'payload_camera' ORDER BY created_at DESC LIMIT 1),
        0.90, 'Payload powered via switched EPS channel', true, NOW(), v_run_id;

    -- Procedure relationships
    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'deployment_sequence' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'eps' ORDER BY created_at DESC LIMIT 1),
        0.85, 'Deployment requires EPS health check first', true, NOW(), v_run_id;

    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'safe_mode_procedure' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'flight_computer' ORDER BY created_at DESC LIMIT 1),
        0.92, 'Safe mode triggered by flight computer watchdog', true, NOW(), v_run_id;

    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'pass_operations' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'comm_system' ORDER BY created_at DESC LIMIT 1),
        0.95, 'Pass ops procedure governs radio operations', true, NOW(), v_run_id;

    -- Decision relationships
    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'adr_processor' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'flight_computer' ORDER BY created_at DESC LIMIT 1),
        0.90, 'STM32F4 selected for flight computer', true, NOW(), v_run_id;

    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'adr_os' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'flight_computer' ORDER BY created_at DESC LIMIT 1),
        0.88, 'FreeRTOS runs on flight computer', true, NOW(), v_run_id;

    -- Lesson relationships
    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'lesson_thermal' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'eps' ORDER BY created_at DESC LIMIT 1),
        0.85, 'Thermal lesson relates to EPS battery management', true, NOW(), v_run_id;

    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'lesson_testing' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'flight_computer' ORDER BY created_at DESC LIMIT 1),
        0.80, 'Testing lesson found flight software timing bug', true, NOW(), v_run_id;

    -- Cross-category connections
    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'adcs' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'payload_camera' ORDER BY created_at DESC LIMIT 1),
        0.85, 'ADCS points camera for imaging', true, NOW(), v_run_id;

    RAISE NOTICE '=========================================';
    RAISE NOTICE 'Migration 027: Seed Test Graph Data';
    RAISE NOTICE '=========================================';
    RAISE NOTICE '  - Created 16 test entities';
    RAISE NOTICE '  - Created 19 test equivalences (edges)';
    RAISE NOTICE '  - Representing a CubeSat system architecture';
END $$;

COMMIT;
