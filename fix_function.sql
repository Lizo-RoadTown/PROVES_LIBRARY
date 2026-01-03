CREATE OR REPLACE FUNCTION public.record_human_decision(
    p_extraction_id uuid,
    p_action_type text,
    p_actor_id text DEFAULT 'unknown'::text,
    p_reason text DEFAULT NULL::text,
    p_before_payload jsonb DEFAULT NULL::jsonb,
    p_after_payload jsonb DEFAULT NULL::jsonb,
    p_webhook_source text DEFAULT NULL::text
)
RETURNS uuid
LANGUAGE plpgsql
AS $function$
DECLARE
    v_decision_id UUID;
BEGIN
    INSERT INTO validation_decisions (
        extraction_id,
        decided_by,
        decider_type,
        decision,
        decision_reason,
        before_payload,
        after_payload,
        source,
        decided_at
    ) VALUES (
        p_extraction_id,
        p_actor_id,
        'human'::decider_type,
        p_action_type::validation_decision_type,
        COALESCE(p_reason, 'No reason provided'),
        p_before_payload,
        p_after_payload,
        p_webhook_source,
        NOW()
    )
    RETURNING decision_id INTO v_decision_id;

    UPDATE staging_extractions
    SET latest_decision_id = v_decision_id
    WHERE extraction_id = p_extraction_id;

    RETURN v_decision_id;
END;
$function$;
