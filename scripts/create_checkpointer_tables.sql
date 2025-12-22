-- LangGraph PostgresSaver Checkpointer Tables
-- Run this manually against your Neon database to create the required tables
-- This avoids the CREATE INDEX CONCURRENTLY issue that occurs during setup()

-- Migration 0: Migrations tracking table
CREATE TABLE IF NOT EXISTS checkpoint_migrations (
    v INTEGER PRIMARY KEY
);

-- Migration 1: Checkpoints table
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- Migration 2: Checkpoint blobs table
CREATE TABLE IF NOT EXISTS checkpoint_blobs (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    channel TEXT NOT NULL,
    version TEXT NOT NULL,
    type TEXT NOT NULL,
    blob BYTEA,
    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
);

-- Migration 3: Checkpoint writes table
CREATE TABLE IF NOT EXISTS checkpoint_writes (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    type TEXT,
    blob BYTEA NOT NULL,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);

-- Migration 4: Allow null blobs
ALTER TABLE checkpoint_blobs ALTER COLUMN blob DROP NOT NULL;

-- Migration 5: No-op (placeholder)
SELECT 1;

-- Migration 6, 7, 8: Indexes (created separately to avoid CONCURRENTLY issue)
-- Using regular CREATE INDEX (not CONCURRENTLY) since this is one-time setup
CREATE INDEX IF NOT EXISTS checkpoints_thread_id_idx ON checkpoints(thread_id);
CREATE INDEX IF NOT EXISTS checkpoint_blobs_thread_id_idx ON checkpoint_blobs(thread_id);
CREATE INDEX IF NOT EXISTS checkpoint_writes_thread_id_idx ON checkpoint_writes(thread_id);

-- Migration 9: Add task_path column
ALTER TABLE checkpoint_writes ADD COLUMN IF NOT EXISTS task_path TEXT NOT NULL DEFAULT '';

-- Record all migrations as complete (migrations 0-9)
INSERT INTO checkpoint_migrations (v) VALUES (0) ON CONFLICT (v) DO NOTHING;
INSERT INTO checkpoint_migrations (v) VALUES (1) ON CONFLICT (v) DO NOTHING;
INSERT INTO checkpoint_migrations (v) VALUES (2) ON CONFLICT (v) DO NOTHING;
INSERT INTO checkpoint_migrations (v) VALUES (3) ON CONFLICT (v) DO NOTHING;
INSERT INTO checkpoint_migrations (v) VALUES (4) ON CONFLICT (v) DO NOTHING;
INSERT INTO checkpoint_migrations (v) VALUES (5) ON CONFLICT (v) DO NOTHING;
INSERT INTO checkpoint_migrations (v) VALUES (6) ON CONFLICT (v) DO NOTHING;
INSERT INTO checkpoint_migrations (v) VALUES (7) ON CONFLICT (v) DO NOTHING;
INSERT INTO checkpoint_migrations (v) VALUES (8) ON CONFLICT (v) DO NOTHING;
INSERT INTO checkpoint_migrations (v) VALUES (9) ON CONFLICT (v) DO NOTHING;

-- Verify tables created
SELECT 'checkpoint_migrations' as table_name, COUNT(*) as row_count FROM checkpoint_migrations
UNION ALL
SELECT 'checkpoints', COUNT(*) FROM checkpoints
UNION ALL
SELECT 'checkpoint_blobs', COUNT(*) FROM checkpoint_blobs
UNION ALL
SELECT 'checkpoint_writes', COUNT(*) FROM checkpoint_writes;
