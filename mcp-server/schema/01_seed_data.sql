-- PROVES Library - Seed Data
-- Initial risk patterns and example knowledge graph nodes

-- ============================================
-- RISK PATTERNS (from risk-scanner/README.md)
-- ============================================

-- I2C Address Conflict Pattern
INSERT INTO risk_patterns (name, pattern_type, severity, detection_method, pattern_definition, fix_summary, related_cascade_domain)
VALUES (
    'I2C Address Conflict',
    'i2c_conflict',
    'critical',
    'graph_query',
    '{
        "description": "Multiple I2C devices sharing the same address on the same bus",
        "detection": "Query KG for nodes with matching i2c_address property connected to same bus",
        "indicators": ["i2c_address", "bus_id", "device_type"]
    }'::jsonb,
    'Use I2C multiplexer (TCA9548A) to isolate devices with conflicting addresses',
    'data'
);

-- Memory Leak Pattern
INSERT INTO risk_patterns (name, pattern_type, severity, detection_method, pattern_definition, fix_summary)
VALUES (
    'F´ Port Memory Leak',
    'memory_leak',
    'high',
    'ast',
    '{
        "description": "Memory allocation without corresponding deallocation in port handlers",
        "ast_patterns": [
            "malloc/new without free/delete in same scope",
            "Fw::Buffer allocation without release",
            "Missing destructor for port with buffers"
        ],
        "indicators": ["malloc", "new", "Fw::Buffer", "no_free", "no_delete"]
    }'::jsonb,
    'Add explicit buffer deallocation in port handler or use RAII patterns'
);

-- Power Budget Violation
INSERT INTO risk_patterns (name, pattern_type, severity, detection_method, pattern_definition, fix_summary, related_cascade_domain)
VALUES (
    'Power Budget Violation',
    'power_budget',
    'critical',
    'graph_query',
    '{
        "description": "Total component power draw exceeds power supply capacity",
        "detection": "Sum power_draw_mw properties of all connected components, compare to supply_capacity_mw",
        "indicators": ["power_draw_mw", "supply_capacity_mw", "power_rail"]
    }'::jsonb,
    'Reduce component count, add power management, or upgrade power supply',
    'power'
);

-- Missing Component Dependencies
INSERT INTO risk_patterns (name, pattern_type, severity, detection_method, pattern_definition, fix_summary)
VALUES (
    'Missing F´ Component Dependencies',
    'missing_dependency',
    'high',
    'ast',
    '{
        "description": "Component uses ports/types from modules not listed in CMakeLists.txt",
        "ast_patterns": [
            "Include directive for FPP component not in target_link_libraries",
            "Port type reference without corresponding module dependency"
        ],
        "indicators": ["include", "port", "CMakeLists.txt", "target_link_libraries"]
    }'::jsonb,
    'Add missing module to CMakeLists.txt target_link_libraries'
);

-- Buffer Overflow Risk
INSERT INTO risk_patterns (name, pattern_type, severity, detection_method, pattern_definition, fix_summary)
VALUES (
    'Unchecked Buffer Size',
    'buffer_overflow',
    'critical',
    'ast',
    '{
        "description": "Buffer writes without size validation",
        "ast_patterns": [
            "memcpy without size check",
            "strcpy instead of strncpy",
            "Array indexing without bounds check"
        ],
        "indicators": ["memcpy", "strcpy", "buffer", "array_access", "no_bounds_check"]
    }'::jsonb,
    'Add size validation before buffer operations, use safe string functions'
);

-- ============================================
-- EXAMPLE KNOWLEDGE GRAPH NODES
-- ============================================

-- Hardware Components
INSERT INTO kg_nodes (name, node_type, description, properties)
VALUES (
    'MPU-6050 IMU',
    'hardware',
    'InvenSense 6-axis IMU with I2C interface',
    '{
        "i2c_address": "0x68",
        "alt_address": "0x69",
        "power_draw_mw": 3.5,
        "voltage": "2.375V-3.46V",
        "interface": "I2C",
        "datasheet": "https://invensense.tdk.com/products/motion-tracking/6-axis/mpu-6050/"
    }'::jsonb
);

INSERT INTO kg_nodes (name, node_type, description, properties)
VALUES (
    'BNO055 IMU',
    'hardware',
    'Bosch 9-axis absolute orientation sensor',
    '{
        "i2c_address": "0x28",
        "alt_address": "0x29",
        "power_draw_mw": 12.3,
        "voltage": "2.4V-3.6V",
        "interface": "I2C",
        "datasheet": "https://www.bosch-sensortec.com/products/smart-sensors/bno055/"
    }'::jsonb
);

INSERT INTO kg_nodes (name, node_type, description, properties)
VALUES (
    'TCA9548A I2C Multiplexer',
    'hardware',
    'Low-voltage 8-channel I2C switch',
    '{
        "i2c_address": "0x70",
        "channels": 8,
        "power_draw_mw": 0.5,
        "voltage": "1.65V-5.5V",
        "interface": "I2C",
        "datasheet": "https://www.ti.com/product/TCA9548A"
    }'::jsonb
);

-- F´ Components
INSERT INTO kg_nodes (name, node_type, description, properties)
VALUES (
    'Imu Driver Component',
    'component',
    'F´ driver component for MPU-6050 IMU',
    '{
        "component_type": "active",
        "language": "C++",
        "ports": ["dataOut", "i2cBus", "cmdIn"],
        "threads": 1,
        "stack_size_kb": 8,
        "priority": "medium"
    }'::jsonb
);

INSERT INTO kg_nodes (name, node_type, description, properties)
VALUES (
    'I2C Bus Driver',
    'component',
    'F´ I2C bus driver with device management',
    '{
        "component_type": "active",
        "language": "C++",
        "max_devices": 8,
        "ports": ["read", "write", "deviceManager"],
        "threads": 1
    }'::jsonb
);

-- Patterns
INSERT INTO kg_nodes (name, node_type, description, properties)
VALUES (
    'I2C Address Conflict Resolution',
    'pattern',
    'Pattern for handling I2C devices with identical addresses',
    '{
        "problem": "Multiple devices with same I2C address",
        "solution": "Use I2C multiplexer to create separate buses",
        "trade_offs": ["Added complexity", "Slight latency increase", "One more component"],
        "verified": true
    }'::jsonb
);

-- ============================================
-- EXAMPLE RELATIONSHIPS (ERV)
-- ============================================

-- Hardware dependencies
INSERT INTO kg_relationships (source_node_id, target_node_id, relationship_type, strength, description, cascade_domain)
SELECT
    (SELECT id FROM kg_nodes WHERE name = 'Imu Driver Component'),
    (SELECT id FROM kg_nodes WHERE name = 'I2C Bus Driver'),
    'depends_on',
    0.95,
    'IMU driver requires I2C bus driver to communicate with hardware',
    'data'
WHERE EXISTS (SELECT 1 FROM kg_nodes WHERE name = 'Imu Driver Component')
  AND EXISTS (SELECT 1 FROM kg_nodes WHERE name = 'I2C Bus Driver');

-- Hardware conflicts (example - these would normally conflict)
INSERT INTO kg_relationships (source_node_id, target_node_id, relationship_type, strength, description, cascade_domain, is_critical)
SELECT
    (SELECT id FROM kg_nodes WHERE name = 'MPU-6050 IMU'),
    (SELECT id FROM kg_nodes WHERE name = 'BNO055 IMU'),
    'conflicts_with',
    0.80,
    'Both IMUs use address 0x68 by default - would conflict on same bus',
    'data',
    true
WHERE EXISTS (SELECT 1 FROM kg_nodes WHERE name = 'MPU-6050 IMU')
  AND EXISTS (SELECT 1 FROM kg_nodes WHERE name = 'BNO055 IMU');

-- Mitigation relationship
INSERT INTO kg_relationships (source_node_id, target_node_id, relationship_type, strength, description)
SELECT
    (SELECT id FROM kg_nodes WHERE name = 'TCA9548A I2C Multiplexer'),
    (SELECT id FROM kg_nodes WHERE name = 'I2C Address Conflict Resolution'),
    'enables',
    0.90,
    'I2C multiplexer enables the address conflict resolution pattern'
WHERE EXISTS (SELECT 1 FROM kg_nodes WHERE name = 'TCA9548A I2C Multiplexer')
  AND EXISTS (SELECT 1 FROM kg_nodes WHERE name = 'I2C Address Conflict Resolution');

-- ============================================
-- EXAMPLE LIBRARY ENTRY REFERENCES
-- ============================================

-- Note: This will be populated by the library indexer script
-- For now, we'll create a placeholder reference that links to our example

INSERT INTO library_entries (
    title,
    slug,
    file_path,
    entry_type,
    domain,
    content,
    summary,
    tags,
    sources,
    quality_tier,
    citation_count,
    has_verification
) VALUES (
    'I2C Address Conflict Resolution with TCA9548A',
    'example-i2c-conflict',
    'library/software/example-i2c-conflict.md',
    'pattern',
    'software',
    '# Problem: I2C Address Conflicts

When using multiple I2C devices with identical addresses on the same bus...

[Content would be loaded from actual markdown file by indexer]',
    'Describes how to resolve I2C address conflicts using the TCA9548A multiplexer in F´ systems',
    ARRAY['i2c', 'hardware', 'multiplexer', 'fprime'],
    ARRAY['https://www.ti.com/product/TCA9548A'],
    'high',
    3,
    true
);

-- Link the example entry to the pattern node
UPDATE kg_nodes
SET related_entries = ARRAY[(SELECT id FROM library_entries WHERE slug = 'example-i2c-conflict')]
WHERE name = 'I2C Address Conflict Resolution';

-- Link the relationship to the evidence entry
UPDATE kg_relationships
SET evidence_entry_id = (SELECT id FROM library_entries WHERE slug = 'example-i2c-conflict')
WHERE description LIKE '%Both IMUs use address 0x68%';

-- ============================================
-- EXAMPLE CURATOR JOB
-- ============================================

-- Simulate a raw capture that the curator would process
INSERT INTO curator_jobs (raw_capture_text, source_url, status, stage)
VALUES (
    'We had a major issue during integration testing. Two IMUs (MPU-6050 and BNO055) both defaulted to address 0x68 on the I2C bus. System hung during initialization. After research, we added a TCA9548A multiplexer. This allowed us to put each IMU on a separate channel. Problem solved. Testing showed no performance impact. See commit abc123 and issue #456.',
    'https://github.com/example/cubesat/issues/456',
    'pending',
    'citation_extraction'
);

-- ============================================
-- STATISTICS VIEW
-- ============================================

-- Create a view to show current database statistics
CREATE OR REPLACE VIEW database_statistics AS
SELECT
    'library_entries' AS table_name,
    COUNT(*) AS row_count
FROM library_entries
UNION ALL
SELECT 'kg_nodes', COUNT(*) FROM kg_nodes
UNION ALL
SELECT 'kg_relationships', COUNT(*) FROM kg_relationships
UNION ALL
SELECT 'risk_patterns', COUNT(*) FROM risk_patterns
UNION ALL
SELECT 'curator_jobs', COUNT(*) FROM curator_jobs
UNION ALL
SELECT 'builder_jobs', COUNT(*) FROM builder_jobs;

-- Query this view to see initial state
-- SELECT * FROM database_statistics ORDER BY table_name;
