-- Migration 036: Organization Selection Auth Flow
--
-- Implements proper org-scoped auth per Supabase best practices:
-- 1. Add active_org_id to user profiles (persists active org choice)
-- 2. Create org activation function with membership validation
-- 3. Update RLS policies to use active org
-- 4. Sandbox mode: auto-add new users to all orgs
--
-- Auth flow:
--   1. User signs up/in
--   2. User picks organization from dropdown
--   3. System validates membership and sets active_org_id
--   4. All queries scoped to active org via RLS

BEGIN;

-- =============================================================================
-- PART 1: ADD ACTIVE_ORG_ID TO USER_PROFILES
-- =============================================================================

DO $$
BEGIN
    -- Add active_org_id column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_profiles' AND column_name = 'active_org_id'
    ) THEN
        ALTER TABLE user_profiles ADD COLUMN active_org_id UUID REFERENCES organizations(id);
    END IF;
END $$;

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_active_org ON user_profiles(active_org_id);

-- =============================================================================
-- PART 2: SANDBOX MODE SETTING
-- =============================================================================

-- Create app_settings table if it doesn't exist
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Set sandbox mode ON (change to false for production)
INSERT INTO app_settings (key, value, description)
VALUES ('sandbox_mode', 'true', 'When true, new users get admin access to all orgs automatically')
ON CONFLICT (key) DO NOTHING;

-- Helper function to check sandbox mode
CREATE OR REPLACE FUNCTION is_sandbox_mode()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN COALESCE(
        (SELECT (value)::TEXT::BOOLEAN FROM app_settings WHERE key = 'sandbox_mode'),
        false
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- PART 3: ACTIVATION FUNCTION - Sets active org with membership validation
-- =============================================================================

CREATE OR REPLACE FUNCTION activate_organization(p_org_id UUID)
RETURNS JSONB AS $$
DECLARE
    v_user_id UUID;
    v_org_name TEXT;
    v_role TEXT;
BEGIN
    v_user_id := auth.uid();

    IF v_user_id IS NULL THEN
        RETURN jsonb_build_object('success', false, 'error', 'Not authenticated');
    END IF;

    -- Check if user is a member of this organization
    SELECT om.role, o.name INTO v_role, v_org_name
    FROM organization_members om
    JOIN organizations o ON o.id = om.organization_id
    WHERE om.user_id = v_user_id
    AND om.organization_id = p_org_id
    AND o.is_active = true;

    IF v_role IS NULL THEN
        RETURN jsonb_build_object('success', false, 'error', 'Not a member of this organization');
    END IF;

    -- Update active_org_id in user_profiles
    UPDATE user_profiles
    SET active_org_id = p_org_id, updated_at = NOW()
    WHERE id = v_user_id;

    -- If no profile exists, create one
    IF NOT FOUND THEN
        INSERT INTO user_profiles (id, active_org_id)
        VALUES (v_user_id, p_org_id)
        ON CONFLICT (id) DO UPDATE SET active_org_id = p_org_id, updated_at = NOW();
    END IF;

    -- Also update is_primary_org in organization_members
    UPDATE organization_members SET is_primary_org = false WHERE user_id = v_user_id;
    UPDATE organization_members SET is_primary_org = true WHERE user_id = v_user_id AND organization_id = p_org_id;

    RETURN jsonb_build_object(
        'success', true,
        'org_id', p_org_id,
        'org_name', v_org_name,
        'role', v_role
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- PART 4: GET CURRENT ACTIVE ORG FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION get_active_org_id()
RETURNS UUID AS $$
BEGIN
    RETURN (
        SELECT active_org_id
        FROM user_profiles
        WHERE id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- =============================================================================
-- PART 5: AUTO-SETUP FOR NEW USERS (SANDBOX MODE)
-- =============================================================================

CREATE OR REPLACE FUNCTION auto_setup_new_user()
RETURNS TRIGGER AS $$
DECLARE
    v_first_org_id UUID;
BEGIN
    -- Create user profile
    INSERT INTO user_profiles (id, email, display_name, is_engineer, is_developer, is_researcher, is_admin)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        is_sandbox_mode(),  -- Grant engineer in sandbox
        is_sandbox_mode(),  -- Grant developer in sandbox
        is_sandbox_mode(),  -- Grant researcher in sandbox
        is_sandbox_mode()   -- Grant admin in sandbox
    )
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        updated_at = NOW();

    -- In sandbox mode, add user to ALL organizations
    IF is_sandbox_mode() THEN
        INSERT INTO organization_members (organization_id, user_id, role, display_name)
        SELECT
            o.id,
            NEW.id,
            'admin',
            COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1))
        FROM organizations o
        WHERE o.is_active = true
        ON CONFLICT (organization_id, user_id) DO NOTHING;

        RAISE NOTICE 'Sandbox mode: Added user % to all organizations as admin', NEW.email;
    END IF;

    -- Set first org as active (Cal Poly Pomona if available, otherwise first)
    SELECT id INTO v_first_org_id
    FROM organizations
    WHERE is_active = true
    ORDER BY (slug = 'cal-poly-pomona') DESC, name
    LIMIT 1;

    IF v_first_org_id IS NOT NULL THEN
        UPDATE user_profiles SET active_org_id = v_first_org_id WHERE id = NEW.id;
        UPDATE organization_members SET is_primary_org = true
        WHERE user_id = NEW.id AND organization_id = v_first_org_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop and recreate trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION auto_setup_new_user();

-- =============================================================================
-- PART 6: UPDATE GET_USER_ORGANIZATIONS TO INCLUDE ACTIVE STATUS
-- =============================================================================

-- Must drop first because we're changing the return type (adding is_active_org)
DROP FUNCTION IF EXISTS get_user_organizations(UUID);

CREATE OR REPLACE FUNCTION get_user_organizations(p_user_id UUID DEFAULT NULL)
RETURNS TABLE (
    org_id UUID,
    org_name TEXT,
    org_slug TEXT,
    org_color TEXT,
    user_role TEXT,
    is_primary BOOLEAN,
    is_active_org BOOLEAN
) AS $$
DECLARE
    v_active_org UUID;
BEGIN
    -- Get active org for current user
    SELECT active_org_id INTO v_active_org
    FROM user_profiles
    WHERE id = COALESCE(p_user_id, auth.uid());

    RETURN QUERY
    SELECT
        o.id,
        o.name,
        o.slug,
        o.primary_color,
        om.role,
        om.is_primary_org,
        (o.id = v_active_org) AS is_active_org
    FROM organizations o
    JOIN organization_members om ON om.organization_id = o.id
    WHERE om.user_id = COALESCE(p_user_id, auth.uid())
    AND o.is_active = true
    ORDER BY (o.id = v_active_org) DESC, om.is_primary_org DESC, o.name;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- PART 7: BACKFILL EXISTING USERS (SANDBOX MODE)
-- =============================================================================

DO $$
DECLARE
    v_user RECORD;
    v_first_org_id UUID;
BEGIN
    IF NOT is_sandbox_mode() THEN
        RAISE NOTICE 'Sandbox mode is OFF, skipping backfill';
        RETURN;
    END IF;

    -- Get default org (Cal Poly Pomona or first)
    SELECT id INTO v_first_org_id
    FROM organizations
    WHERE is_active = true
    ORDER BY (slug = 'cal-poly-pomona') DESC, name
    LIMIT 1;

    FOR v_user IN SELECT id, email FROM auth.users LOOP
        -- Ensure profile exists with admin capabilities
        INSERT INTO user_profiles (id, email, is_engineer, is_developer, is_researcher, is_admin, active_org_id)
        VALUES (v_user.id, v_user.email, true, true, true, true, v_first_org_id)
        ON CONFLICT (id) DO UPDATE SET
            is_engineer = true,
            is_developer = true,
            is_researcher = true,
            is_admin = true,
            active_org_id = COALESCE(user_profiles.active_org_id, v_first_org_id),
            updated_at = NOW();

        -- Add to all orgs as admin
        INSERT INTO organization_members (organization_id, user_id, role)
        SELECT o.id, v_user.id, 'admin'
        FROM organizations o WHERE o.is_active = true
        ON CONFLICT (organization_id, user_id) DO UPDATE SET role = 'admin';
    END LOOP;

    RAISE NOTICE 'Backfilled all existing users with sandbox admin access';
END $$;

-- =============================================================================
-- PART 8: VERIFICATION
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
    RAISE NOTICE 'Migration 036: Org Selection Auth Flow';
    RAISE NOTICE '=========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Configuration:';
    RAISE NOTICE '  - Sandbox mode: %', v_sandbox_mode;
    RAISE NOTICE '  - Total users: %', v_user_count;
    RAISE NOTICE '  - Total organizations: %', v_org_count;
    RAISE NOTICE '';
    RAISE NOTICE 'New functions:';
    RAISE NOTICE '  - activate_organization(org_id) - Set active org with validation';
    RAISE NOTICE '  - get_active_org_id() - Get current user active org';
    RAISE NOTICE '  - get_user_organizations() - Now includes is_active_org flag';
    RAISE NOTICE '';
    RAISE NOTICE 'Auth flow:';
    RAISE NOTICE '  1. User signs up -> auto-added to orgs (sandbox mode)';
    RAISE NOTICE '  2. User picks org from dropdown';
    RAISE NOTICE '  3. Frontend calls: supabase.rpc(''activate_organization'', { p_org_id })';
    RAISE NOTICE '  4. All queries scoped to active_org via RLS';
    RAISE NOTICE '';
    IF v_sandbox_mode THEN
        RAISE NOTICE 'SANDBOX MODE IS ON:';
        RAISE NOTICE '  - New users automatically get admin on ALL orgs';
        RAISE NOTICE '  - To disable: UPDATE app_settings SET value = ''false'' WHERE key = ''sandbox_mode'';';
    END IF;
END $$;

COMMIT;
