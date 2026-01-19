-- CURRENT AUTH TRIGGERS AND FUNCTIONS (from live database)
-- Generated for review

-- Function: is_sandbox_mode()
CREATE OR REPLACE FUNCTION public.is_sandbox_mode()
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
BEGIN
    RETURN COALESCE(
        (SELECT (value)::BOOLEAN FROM app_settings WHERE key = 'sandbox_mode'),
        false
    );
END;
$function$


-- Function: auto_setup_new_user()
CREATE OR REPLACE FUNCTION public.auto_setup_new_user()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
DECLARE
    v_first_org_id UUID;
BEGIN
    -- Create user profile
    INSERT INTO user_profiles (id, email, display_name, is_engineer, is_developer, is_researcher, is_admin)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        is_sandbox_mode(),
        is_sandbox_mode(),
        is_sandbox_mode(),
        is_sandbox_mode()
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
    END IF;

    -- Set first org as active
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
$function$


-- Trigger: on_auth_user_created
CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION auto_setup_new_user()
