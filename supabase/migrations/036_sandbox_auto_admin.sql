-- Migration 036: Sandbox Mode - Auto-Admin for New Users
--
-- During sandbox/development, automatically:
-- 1. Grant all capabilities to new users (is_engineer, is_developer, is_researcher, is_admin)
-- 2. Add them to ALL organizations as admin
--
-- IMPORTANT: Remove or disable this in production!
-- Set SANDBOX_MODE = false when going to production.

BEGIN;

-- =============================================================================
-- SANDBOX MODE SETTING
-- =============================================================================

-- Create a settings table if it doesn't exist
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Set sandbox mode ON (change to false for production)
INSERT INTO app_settings (key, value, description)
VALUES ('sandbox_mode', 'true', 'When true, new users get admin access to all orgs')
ON CONFLICT (key) DO UPDATE SET value = 'true', updated_at = NOW();

-- =============================================================================
-- HELPER FUNCTION: Check if sandbox mode is enabled
-- =============================================================================

CREATE OR REPLACE FUNCTION is_sandbox_mode()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN COALESCE(
        (SELECT (value)::BOOLEAN FROM app_settings WHERE key = 'sandbox_mode'),
        false
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- AUTO-GRANT FUNCTION: Make new user admin of all orgs
-- =============================================================================

CREATE OR REPLACE FUNCTION auto_grant_sandbox_access()
RETURNS TRIGGER AS $$
BEGIN
    -- Only run in sandbox mode
    IF NOT is_sandbox_mode() THEN
        RETURN NEW;
    END IF;

    RAISE NOTICE 'Sandbox mode: Auto-granting admin access to new user %', NEW.email;

    -- 1. Create user profile with all capabilities
    INSERT INTO user_profiles (id, email, display_name, is_engineer, is_developer, is_researcher, is_admin)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        true,  -- is_engineer
        true,  -- is_developer
        true,  -- is_researcher
        true   -- is_admin
    )
    ON CONFLICT (id) DO UPDATE SET
        is_engineer = true,
        is_developer = true,
        is_researcher = true,
        is_admin = true,
        updated_at = NOW();

    -- 2. Add user to ALL active organizations as admin
    INSERT INTO organization_members (organization_id, user_id, role, display_name)
    SELECT
        o.id,
        NEW.id,
        'admin',
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1))
    FROM organizations o
    WHERE o.is_active = true
    ON CONFLICT (organization_id, user_id) DO NOTHING;

    RAISE NOTICE 'Added user to % organizations', (SELECT COUNT(*) FROM organizations WHERE is_active = true);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- TRIGGER: Run after user signup
-- =============================================================================

-- Drop existing trigger if it exists (from migration 031)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Create new trigger that includes sandbox auto-grant
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION auto_grant_sandbox_access();

-- =============================================================================
-- HELPER: Manually add existing users to all orgs (run once for current users)
-- =============================================================================

-- Add all existing users to all organizations
DO $$
DECLARE
    v_user RECORD;
    v_added INT := 0;
BEGIN
    IF NOT is_sandbox_mode() THEN
        RAISE NOTICE 'Sandbox mode is OFF, skipping backfill';
        RETURN;
    END IF;

    FOR v_user IN SELECT id, email FROM auth.users LOOP
        -- Grant capabilities
        INSERT INTO user_profiles (id, email, is_engineer, is_developer, is_researcher, is_admin)
        VALUES (v_user.id, v_user.email, true, true, true, true)
        ON CONFLICT (id) DO UPDATE SET
            is_engineer = true,
            is_developer = true,
            is_researcher = true,
            is_admin = true,
            updated_at = NOW();

        -- Add to all orgs
        INSERT INTO organization_members (organization_id, user_id, role)
        SELECT o.id, v_user.id, 'admin'
        FROM organizations o WHERE o.is_active = true
        ON CONFLICT (organization_id, user_id) DO UPDATE SET role = 'admin';

        v_added := v_added + 1;
    END LOOP;

    RAISE NOTICE 'Backfilled % existing users with admin access to all organizations', v_added;
END $$;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
DECLARE
    v_sandbox_mode BOOLEAN;
    v_user_count INT;
    v_org_count INT;
BEGIN
    SELECT is_sandbox_mode() INTO v_sandbox_mode;
    SELECT COUNT(*) INTO v_user_count FROM auth.users;
    SELECT COUNT(*) INTO v_org_count FROM organizations WHERE is_active = true;

    RAISE NOTICE '=========================================';
    RAISE NOTICE 'Migration 036: Sandbox Auto-Admin Mode';
    RAISE NOTICE '=========================================';
    RAISE NOTICE '  - Sandbox mode: %', v_sandbox_mode;
    RAISE NOTICE '  - Total users: %', v_user_count;
    RAISE NOTICE '  - Total organizations: %', v_org_count;
    RAISE NOTICE '';
    RAISE NOTICE 'NEW USERS WILL AUTOMATICALLY GET:';
    RAISE NOTICE '  ✓ Admin capabilities (engineer, developer, researcher, admin)';
    RAISE NOTICE '  ✓ Membership in ALL organizations as admin';
    RAISE NOTICE '';
    RAISE NOTICE 'TO DISABLE FOR PRODUCTION:';
    RAISE NOTICE '  UPDATE app_settings SET value = ''false'' WHERE key = ''sandbox_mode'';';
END $$;

COMMIT;
