-- Patch for Migration 003: Add missing triggers
-- This adds the triggers that weren't created when migration 003 partially failed

BEGIN;

-- 4.1: Trigger on new extraction
DROP TRIGGER IF EXISTS trigger_notify_new_extraction ON staging_extractions;
CREATE TRIGGER trigger_notify_new_extraction
    AFTER INSERT ON staging_extractions
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_extraction();

-- 4.2: Trigger on new error
DROP TRIGGER IF EXISTS trigger_notify_new_error ON curator_errors;
CREATE TRIGGER trigger_notify_new_error
    AFTER INSERT ON curator_errors
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_error();

-- 4.3: Trigger on new report
DROP TRIGGER IF EXISTS trigger_notify_new_report ON curator_reports;
CREATE TRIGGER trigger_notify_new_report
    AFTER INSERT ON curator_reports
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_report();

-- 4.4: Trigger to check queue status
DROP TRIGGER IF EXISTS trigger_check_url_queue ON urls_to_process;
CREATE TRIGGER trigger_check_url_queue
    AFTER UPDATE OF status ON urls_to_process
    FOR EACH ROW
    EXECUTE FUNCTION check_url_queue_empty();

COMMIT;

DO $$
BEGIN
    RAISE NOTICE 'Migration 003b completed successfully ✓';
    RAISE NOTICE '  - Created trigger_notify_new_extraction';
    RAISE NOTICE '  - Created trigger_notify_new_error';
    RAISE NOTICE '  - Created trigger_notify_new_report';
    RAISE NOTICE '  - Created trigger_check_url_queue';
END $$;
