"""
Error Logger - Utility for agents to log errors to their tables

Each agent uses this to log errors to its own table without disrupting workflow.
Errors are stored in JSONB format and can be synced to Notion later.
"""

import os
import json
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
import psycopg
from dotenv import load_dotenv

load_dotenv()

class ErrorLogger:
    """Helper class for logging errors to database tables"""

    def __init__(self):
        self.db_url = os.getenv('NEON_DATABASE_URL')

    def log_to_extraction(
        self,
        extraction_id: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log an error to the staging_extractions table

        Args:
            extraction_id: UUID of the extraction record
            error_type: Category of error (e.g., 'extraction_failed', 'validation_error', 'api_timeout')
            error_message: Human-readable error message
            stack_trace: Optional stack trace
            context: Optional additional context (dict)

        Returns:
            True if logged successfully, False otherwise
        """
        error_entry = {
            'error_type': error_type,
            'message': error_message,
            'logged_at': datetime.now().isoformat(),
            'context': context or {}
        }

        if stack_trace:
            error_entry['stack_trace'] = stack_trace

        try:
            conn = psycopg.connect(self.db_url)
            with conn.cursor() as cur:
                # Append error to error_log array and increment counter
                cur.execute("""
                    UPDATE staging_extractions
                    SET
                        error_log = error_log || %s::jsonb,
                        error_count = error_count + 1,
                        last_error_at = NOW()
                    WHERE extraction_id = %s::uuid
                    RETURNING extraction_id
                """, (json.dumps(error_entry), extraction_id))

                result = cur.fetchone()
                conn.commit()
            conn.close()

            if result:
                print(f"✓ Logged error for extraction {extraction_id}: {error_type}")
                return True
            else:
                print(f"⚠ Extraction {extraction_id} not found, could not log error")
                return False

        except Exception as e:
            print(f"❌ Failed to log error to database: {e}")
            return False

    def log_to_suggestion(
        self,
        suggestion_id: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log an error to the improvement_suggestions table

        Args:
            suggestion_id: UUID of the suggestion record
            error_type: Category of error
            error_message: Human-readable error message
            stack_trace: Optional stack trace
            context: Optional additional context

        Returns:
            True if logged successfully, False otherwise
        """
        error_entry = {
            'error_type': error_type,
            'message': error_message,
            'logged_at': datetime.now().isoformat(),
            'context': context or {}
        }

        if stack_trace:
            error_entry['stack_trace'] = stack_trace

        try:
            conn = psycopg.connect(self.db_url)
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE improvement_suggestions
                    SET
                        error_log = error_log || %s::jsonb,
                        error_count = error_count + 1,
                        last_error_at = NOW()
                    WHERE suggestion_id = %s::uuid
                    RETURNING suggestion_id
                """, (json.dumps(error_entry), suggestion_id))

                result = cur.fetchone()
                conn.commit()
            conn.close()

            if result:
                print(f"✓ Logged error for suggestion {suggestion_id}: {error_type}")
                return True
            else:
                print(f"⚠ Suggestion {suggestion_id} not found, could not log error")
                return False

        except Exception as e:
            print(f"❌ Failed to log error to database: {e}")
            return False

    @staticmethod
    def capture_exception(error: Exception) -> tuple[str, str]:
        """
        Capture exception message and stack trace

        Returns:
            Tuple of (error_message, stack_trace)
        """
        error_message = str(error)
        stack_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        return error_message, stack_trace

    def get_recent_errors(self, table: str = 'all', limit: int = 10) -> list:
        """
        Retrieve recent errors from tables

        Args:
            table: 'staging_extractions', 'improvement_suggestions', or 'all'
            limit: Maximum number of errors to return

        Returns:
            List of error records
        """
        try:
            conn = psycopg.connect(self.db_url)
            with conn.cursor() as cur:
                if table == 'all':
                    cur.execute("""
                        SELECT * FROM all_errors
                        ORDER BY last_error_at DESC
                        LIMIT %s
                    """, (limit,))
                elif table == 'staging_extractions':
                    cur.execute("""
                        SELECT
                            extraction_id::text,
                            candidate_key,
                            error_log,
                            error_count,
                            last_error_at
                        FROM staging_extractions
                        WHERE error_count > 0
                        ORDER BY last_error_at DESC
                        LIMIT %s
                    """, (limit,))
                elif table == 'improvement_suggestions':
                    cur.execute("""
                        SELECT
                            suggestion_id::text,
                            title,
                            error_log,
                            error_count,
                            last_error_at
                        FROM improvement_suggestions
                        WHERE error_count > 0
                        ORDER BY last_error_at DESC
                        LIMIT %s
                    """, (limit,))
                else:
                    raise ValueError(f"Unknown table: {table}")

                rows = cur.fetchall()
            conn.close()

            return rows

        except Exception as e:
            print(f"❌ Failed to retrieve errors: {e}")
            return []


# Example usage for agents:
"""
from src.curator.error_logger import ErrorLogger

logger = ErrorLogger()

# In your agent code:
try:
    # ... do something that might fail ...
    extract_data()
except Exception as e:
    error_msg, stack_trace = ErrorLogger.capture_exception(e)
    logger.log_to_extraction(
        extraction_id=extraction_id,
        error_type='extraction_failed',
        error_message=error_msg,
        stack_trace=stack_trace,
        context={'url': document_url, 'ecosystem': 'fprime'}
    )
"""
