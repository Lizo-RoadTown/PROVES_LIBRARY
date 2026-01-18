-- Migration 031: User Profiles with Stackable Capabilities
--
-- Capabilities are flags that STACK, not hierarchical levels:
--   - is_engineer:   Can review/approve extractions for their lab
--   - is_developer:  Can modify code/schema/deploy
--   - is_researcher: Cross-lab visibility, analytics, manage sources
--   - is_admin:      Full system access (separate from capabilities)
--
-- A person can have multiple capabilities. Example:
--   Liz = researcher + developer + engineer (all three!)
--   Site builder = developer only
--   Lab member = engineer only
--
-- ┌─────────────────┬──────────┬───────────┬────────────┬───────┐
-- │ Capability      │ engineer │ developer │ researcher │ admin │
-- ├─────────────────┼──────────┼───────────┼────────────┼───────┤
-- │ Query library   │ ✓        │ ✓         │ ✓          │ ✓     │
-- │ Review/approve  │ ✓        │ -         │ ✓          │ ✓     │
-- │ View ALL labs   │ -        │ -         │ ✓          │ ✓     │
-- │ Analytics       │ -        │ -         │ ✓          │ ✓     │
-- │ Manage sources  │ -        │ -         │ ✓          │ ✓     │
-- │ Edit schema/DB  │ -        │ ✓         │ -          │ ✓     │
-- │ Deploy code     │ -        │ ✓         │ -          │ ✓     │
-- │ Manage users    │ -        │ -         │ -          │ ✓     │
-- └─────────────────┴──────────┴───────────┴────────────┴───────┘

BEGIN;

-- =============================================================================
-- PART 1: USER PROFILES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Identity
    email TEXT,
    display_name TEXT,
    avatar_url TEXT,

    -- Stackable capability flags (can have multiple)
    is_engineer BOOLEAN DEFAULT false,     -- Can review/approve extractions
    is_developer BOOLEAN DEFAULT false,    -- Can modify code/schema
    is_researcher BOOLEAN DEFAULT false,   -- Cross-lab visibility, analytics

    -- Admin flag (separate from capabilities)
    is_admin BOOLEAN DEFAULT false,        -- Full system access

    -- Preferences
    preferences JSONB DEFAULT '{}',

    -- Last activity
    last_seen_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_researcher ON user_profiles(is_researcher) WHERE is_researcher = true;
CREATE INDEX IF NOT EXISTS idx_user_profiles_admin ON user_profiles(is_admin) WHERE is_admin = true;

-- =============================================================================
-- PART 2: AUTO-CREATE PROFILE ON SIGNUP
-- =============================================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, display_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1))
    )
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Create trigger
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- =============================================================================
-- PART 3: RLS POLICIES FOR USER_PROFILES
-- =============================================================================

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (for idempotent migration)
DROP POLICY IF EXISTS "Users can view own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON user_profiles;
DROP POLICY IF EXISTS "Admins can view all profiles" ON user_profiles;
DROP POLICY IF EXISTS "Admins can manage profiles" ON user_profiles;

-- Users can view their own profile
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

-- Users can update their own profile (but not capability flags)
CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id)
    WITH CHECK (
        auth.uid() = id
        -- Prevent users from changing their own capability flags
        AND (
            (is_engineer = (SELECT is_engineer FROM user_profiles WHERE id = auth.uid()))
            AND (is_developer = (SELECT is_developer FROM user_profiles WHERE id = auth.uid()))
            AND (is_researcher = (SELECT is_researcher FROM user_profiles WHERE id = auth.uid()))
            AND (is_admin = (SELECT is_admin FROM user_profiles WHERE id = auth.uid()))
            -- Unless they're an admin
            OR (SELECT is_admin FROM user_profiles WHERE id = auth.uid()) = true
        )
    );

-- Admins can view all profiles
CREATE POLICY "Admins can view all profiles" ON user_profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid()
            AND is_admin = true
        )
    );

-- Admins can update any profile
CREATE POLICY "Admins can manage profiles" ON user_profiles
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid()
            AND is_admin = true
        )
    );

-- =============================================================================
-- PART 4: HELPER FUNCTIONS
-- =============================================================================

-- Check if user can view all labs (researchers or admins)
CREATE OR REPLACE FUNCTION can_view_all_labs(p_user_id UUID DEFAULT NULL)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = COALESCE(p_user_id, auth.uid())
        AND (is_researcher = true OR is_admin = true)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Alias for backwards compat
CREATE OR REPLACE FUNCTION is_executive_or_admin(p_user_id UUID DEFAULT NULL)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN can_view_all_labs(p_user_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Check if user is admin
CREATE OR REPLACE FUNCTION is_system_admin(p_user_id UUID DEFAULT NULL)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = COALESCE(p_user_id, auth.uid())
        AND is_admin = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Check if user is a developer (can modify schema/code)
CREATE OR REPLACE FUNCTION is_developer(p_user_id UUID DEFAULT NULL)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = COALESCE(p_user_id, auth.uid())
        AND (is_developer = true OR is_admin = true)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Check if user is an engineer (can review/approve extractions)
CREATE OR REPLACE FUNCTION is_engineer(p_user_id UUID DEFAULT NULL)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = COALESCE(p_user_id, auth.uid())
        AND (is_engineer = true OR is_admin = true)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Check if user is a researcher (cross-lab visibility)
CREATE OR REPLACE FUNCTION is_researcher(p_user_id UUID DEFAULT NULL)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = COALESCE(p_user_id, auth.uid())
        AND (is_researcher = true OR is_admin = true)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Get user's full profile with org memberships and capabilities
CREATE OR REPLACE FUNCTION get_user_profile_with_orgs(p_user_id UUID DEFAULT NULL)
RETURNS TABLE (
    user_id UUID,
    email TEXT,
    display_name TEXT,
    avatar_url TEXT,
    is_engineer BOOLEAN,
    is_developer BOOLEAN,
    is_researcher BOOLEAN,
    is_admin BOOLEAN,
    organizations JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        up.id,
        up.email,
        up.display_name,
        up.avatar_url,
        up.is_engineer,
        up.is_developer,
        up.is_researcher,
        up.is_admin,
        COALESCE(
            (
                SELECT jsonb_agg(jsonb_build_object(
                    'org_id', o.id,
                    'org_name', o.name,
                    'org_slug', o.slug,
                    'org_color', o.primary_color,
                    'role', om.role,
                    'is_primary', om.is_primary_org
                ) ORDER BY om.is_primary_org DESC, o.name)
                FROM organization_members om
                JOIN organizations o ON o.id = om.organization_id
                WHERE om.user_id = up.id AND o.is_active = true
            ),
            '[]'::jsonb
        )
    FROM user_profiles up
    WHERE up.id = COALESCE(p_user_id, auth.uid());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Grant capabilities to a user (admin only, or bootstrap)
CREATE OR REPLACE FUNCTION grant_capabilities(
    p_user_email TEXT,
    p_is_engineer BOOLEAN DEFAULT false,
    p_is_developer BOOLEAN DEFAULT false,
    p_is_researcher BOOLEAN DEFAULT false,
    p_is_admin BOOLEAN DEFAULT false
)
RETURNS BOOLEAN AS $$
DECLARE
    v_user_id UUID;
    v_admin_count INT;
BEGIN
    -- Check if this is the first admin (bootstrap case)
    SELECT COUNT(*) INTO v_admin_count FROM user_profiles WHERE is_admin = true;

    -- Only admins can grant capabilities (unless bootstrapping)
    IF v_admin_count > 0 AND NOT is_system_admin() THEN
        RAISE EXCEPTION 'Only admins can grant capabilities';
    END IF;

    -- Find user by email
    SELECT id INTO v_user_id FROM auth.users WHERE email = p_user_email;

    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'User not found with email: %', p_user_email;
    END IF;

    -- Update or insert profile
    INSERT INTO user_profiles (id, email, is_engineer, is_developer, is_researcher, is_admin)
    VALUES (v_user_id, p_user_email, p_is_engineer, p_is_developer, p_is_researcher, p_is_admin)
    ON CONFLICT (id) DO UPDATE SET
        is_engineer = p_is_engineer,
        is_developer = p_is_developer,
        is_researcher = p_is_researcher,
        is_admin = p_is_admin,
        updated_at = NOW();

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Convenience function: make someone an admin
CREATE OR REPLACE FUNCTION make_admin(p_user_email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN grant_capabilities(p_user_email, true, true, true, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Convenience function: make someone a researcher (cross-lab access)
CREATE OR REPLACE FUNCTION make_researcher(p_user_email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN grant_capabilities(p_user_email, false, false, true, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Convenience function: make someone an engineer (can review/approve)
CREATE OR REPLACE FUNCTION make_engineer(p_user_email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN grant_capabilities(p_user_email, true, false, false, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Convenience function: make someone a developer (can modify code/schema)
CREATE OR REPLACE FUNCTION make_developer(p_user_email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN grant_capabilities(p_user_email, false, true, false, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- =============================================================================
-- PART 5: UPDATE EXISTING RLS POLICIES FOR EXECUTIVE ACCESS
-- =============================================================================

-- Add executive access to organizations view
DROP POLICY IF EXISTS organizations_select ON organizations;
CREATE POLICY organizations_select ON organizations
    FOR SELECT TO authenticated
    USING (
        is_active = true
        OR is_executive_or_admin()
    );

-- Add executive access to organization_members view
DROP POLICY IF EXISTS org_members_select ON organization_members;
CREATE POLICY org_members_select ON organization_members
    FOR SELECT TO authenticated
    USING (
        user_id = auth.uid()
        OR organization_id IN (
            SELECT organization_id FROM organization_members WHERE user_id = auth.uid()
        )
        OR is_executive_or_admin()
    );

-- =============================================================================
-- PART 6: CROSS-ORG ACCESS FOR CORE_ENTITIES
-- =============================================================================

-- Executives can see all core entities regardless of org
DROP POLICY IF EXISTS "Executive cross-org access" ON core_entities;
CREATE POLICY "Executive cross-org access" ON core_entities
    FOR SELECT USING (is_executive_or_admin());

-- =============================================================================
-- PART 7: CROSS-ORG ACCESS FOR STAGING_EXTRACTIONS
-- =============================================================================

-- Executives can view all extractions (read-only)
DROP POLICY IF EXISTS "Executive view all extractions" ON staging_extractions;
CREATE POLICY "Executive view all extractions" ON staging_extractions
    FOR SELECT USING (is_executive_or_admin());

-- =============================================================================
-- PART 8: TIMESTAMP TRIGGER
-- =============================================================================

CREATE OR REPLACE FUNCTION update_user_profiles_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public;

DROP TRIGGER IF EXISTS user_profiles_updated_at ON user_profiles;
CREATE TRIGGER user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_user_profiles_timestamp();

-- =============================================================================
-- PART 9: BACKFILL EXISTING USERS
-- =============================================================================

-- Create profiles for any existing users that don't have one
INSERT INTO user_profiles (id, email, display_name)
SELECT
    u.id,
    u.email,
    COALESCE(u.raw_user_meta_data->>'full_name', u.raw_user_meta_data->>'name', split_part(u.email, '@', 1))
FROM auth.users u
WHERE NOT EXISTS (SELECT 1 FROM user_profiles WHERE id = u.id)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- PART 10: COMMENTS
-- =============================================================================

COMMENT ON TABLE user_profiles IS
'User profiles with stackable capability flags for cross-org access and permissions';

COMMENT ON COLUMN user_profiles.is_engineer IS
'Engineer capability: can review/approve extractions for their lab';

COMMENT ON COLUMN user_profiles.is_developer IS
'Developer capability: can modify code/schema/deploy';

COMMENT ON COLUMN user_profiles.is_researcher IS
'Researcher capability: cross-lab visibility, analytics, manage sources';

COMMENT ON COLUMN user_profiles.is_admin IS
'Admin flag: full system access (separate from stackable capabilities)';

COMMENT ON FUNCTION can_view_all_labs IS
'Check if user has researcher or admin capability for cross-lab access';

-- =============================================================================
-- PART 11: BOOTSTRAP - SET UP INITIAL CAPABILITIES
-- =============================================================================

-- IMPORTANT: After running this migration, run these in SQL editor:
--
-- For Liz (researcher + developer + engineer, but admin for full access):
--   SELECT grant_capabilities('eosborn@cpp.edu', true, true, true, true);
--   -- Or simply: SELECT make_admin('eosborn@cpp.edu');
--
-- For Michael (same):
--   SELECT grant_capabilities('mpham@cpp.edu', true, true, true, true);
--
-- For site developers (developer capability only):
--   SELECT make_developer('developer@email.com');
--
-- For lab engineers (review/approve only):
--   SELECT make_engineer('engineer@email.com');
--
-- For researchers (cross-lab visibility):
--   SELECT make_researcher('researcher@email.com');
--
-- Or combine capabilities:
--   SELECT grant_capabilities('someone@email.com',
--       true,   -- is_engineer: can review/approve
--       true,   -- is_developer: can modify code/schema
--       true,   -- is_researcher: cross-lab visibility
--       false   -- is_admin: NOT full admin
--   );

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
DECLARE
    v_profile_count INT;
BEGIN
    SELECT COUNT(*) INTO v_profile_count FROM user_profiles;

    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Migration 031: User Profiles & Stackable Capabilities';
    RAISE NOTICE '===========================================';
    RAISE NOTICE '  - user_profiles table created';
    RAISE NOTICE '  - Auto-create profile trigger added';
    RAISE NOTICE '  - Stackable capability flags: is_engineer, is_developer, is_researcher, is_admin';
    RAISE NOTICE '  - Helper functions:';
    RAISE NOTICE '      - is_engineer()      - can review/approve extractions';
    RAISE NOTICE '      - is_developer()     - can modify code/schema';
    RAISE NOTICE '      - is_researcher()    - cross-lab visibility';
    RAISE NOTICE '      - is_system_admin()  - full system access';
    RAISE NOTICE '      - can_view_all_labs() - researcher or admin';
    RAISE NOTICE '      - get_user_profile_with_orgs()';
    RAISE NOTICE '      - grant_capabilities(email, engineer, developer, researcher, admin)';
    RAISE NOTICE '      - make_admin/make_researcher/make_engineer/make_developer';
    RAISE NOTICE '  - RLS policies updated for cross-lab access';
    RAISE NOTICE '  - Profiles backfilled: %', v_profile_count;
    RAISE NOTICE '';
    RAISE NOTICE 'NEXT STEPS:';
    RAISE NOTICE '  1. Run: SELECT make_admin(''eosborn@cpp.edu'');';
    RAISE NOTICE '  2. For developers: SELECT make_developer(''dev@email'');';
    RAISE NOTICE '  3. Or combine: SELECT grant_capabilities(email, true, true, true, false);';
    RAISE NOTICE '';
    RAISE NOTICE 'CAPABILITIES (stackable):';
    RAISE NOTICE '  - engineer:   Can review/approve extractions for their lab';
    RAISE NOTICE '  - developer:  Can modify code/schema/deploy';
    RAISE NOTICE '  - researcher: Cross-lab visibility, analytics, manage sources';
    RAISE NOTICE '  - admin:      Full system access';
    RAISE NOTICE '';
    RAISE NOTICE 'Example: Liz = researcher + developer + engineer (all three!)';
END $$;

COMMIT;
