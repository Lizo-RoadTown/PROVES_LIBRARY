-- Mark all existing migrations as applied in Supabase migration history
-- Run this in the SQL Editor BEFORE running `npx supabase db push`

-- Create the migration history table if it doesn't exist
CREATE TABLE IF NOT EXISTS supabase_migrations.schema_migrations (
    version TEXT PRIMARY KEY,
    inserted_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Insert all migrations that were applied manually
INSERT INTO supabase_migrations.schema_migrations (version) VALUES
    ('000'),
    ('001'),
    ('002'),
    ('003'),
    ('004'),
    ('005'),
    ('006'),
    ('007'),
    ('008'),
    ('009'),
    ('010'),
    ('011'),
    ('012'),
    ('013'),
    ('014'),
    ('015'),
    ('016'),
    ('017'),
    ('018'),
    ('019'),
    ('020'),
    ('20260115191105')
ON CONFLICT (version) DO NOTHING;

-- Verify
SELECT * FROM supabase_migrations.schema_migrations ORDER BY version;
