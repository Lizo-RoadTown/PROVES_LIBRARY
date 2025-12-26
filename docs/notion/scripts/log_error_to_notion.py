"""
Log Agent Errors to Notion Error Log Database

Provides a reusable function for all agents to log errors to Notion for
tracking, pattern analysis, and investigation.

Usage:
    from log_error_to_notion import log_error

    try:
        # Agent work
        result = process_page(url)
    except Exception as e:
        log_error(
            agent="extractor",
            error_type="http_error",
            severity="high",
            message=str(e),
            context=f"Processing {url}",
            source_url=url
        )
        raise  # Re-raise to let LangGraph handle
"""

import os
import traceback
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
import hashlib

# Load environment
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(project_root, '.env'))

def generate_error_id():
    """Generate unique error ID: ERR-YYYY-MM-DD-XXX"""
    timestamp = datetime.now(timezone.utc)
    date_str = timestamp.strftime('%Y-%m-%d')

    # Use timestamp hash for uniqueness
    unique_hash = hashlib.md5(str(timestamp.timestamp()).encode()).hexdigest()[:3].upper()

    return f"ERR-{date_str}-{unique_hash}"

def log_error(
    agent,
    error_type,
    severity,
    message,
    context=None,
    stack_trace=None,
    thread_id=None,
    extraction_id=None,
    source_url=None,
    use_api=True
):
    """
    Log an error to Notion Error Log database.

    Args:
        agent: Agent name (extractor, validator, storage, curator, etc.)
        error_type: Error category (recursive_error, null_values, timeout, etc.)
        severity: Critical, High, Medium, Low
        message: Short error description
        context: What was being processed
        stack_trace: Full traceback (will auto-capture if None)
        thread_id: LangGraph thread ID
        extraction_id: Related extraction_id if applicable
        source_url: Page URL being processed
        use_api: If True, use Notion API (requires NOTION_API_KEY)

    Returns:
        Error ID if successful, None otherwise
    """
    # Auto-capture stack trace if not provided
    if stack_trace is None:
        stack_trace = traceback.format_exc()

    # Generate error ID
    error_id = generate_error_id()
    timestamp = datetime.now(timezone.utc)

    # Truncate long fields for Notion limits
    if len(message) > 2000:
        message = message[:1997] + "..."
    if stack_trace and len(stack_trace) > 2000:
        stack_trace = stack_trace[:1997] + "..."
    if context and len(context) > 2000:
        context = context[:1997] + "..."

    # Build Notion properties
    properties = {
        'Error ID': {
            'title': [{'text': {'content': error_id}}]
        },
        'Timestamp': {
            'date': {'start': timestamp.isoformat()}
        },
        'Agent': {
            'select': {'name': agent}
        },
        'Error Type': {
            'select': {'name': error_type}
        },
        'Severity': {
            'select': {'name': severity}
        },
        'Error Message': {
            'rich_text': [{'text': {'content': message}}]
        },
        'Status': {
            'select': {'name': 'Open'}
        },
        'Occurrence Count': {
            'number': 1
        },
        'First Seen': {
            'date': {'start': timestamp.isoformat()}
        },
        'Last Seen': {
            'date': {'start': timestamp.isoformat()}
        }
    }

    # Add optional fields
    if stack_trace:
        properties['Stack Trace'] = {
            'rich_text': [{'text': {'content': stack_trace}}]
        }

    if context:
        properties['Context'] = {
            'rich_text': [{'text': {'content': context}}]
        }

    if thread_id:
        properties['Thread ID'] = {
            'rich_text': [{'text': {'content': thread_id}}]
        }

    if extraction_id:
        properties['Extraction ID'] = {
            'rich_text': [{'text': {'content': extraction_id}}]
        }

    if source_url:
        properties['Source URL'] = {
            'url': source_url
        }

    # Log to Notion
    if use_api:
        try:
            import requests

            notion_api_key = os.getenv('NOTION_API_KEY')
            error_log_db = os.getenv('NOTION_ERROR_LOG_DB')

            if not notion_api_key or not error_log_db:
                print(f"[WARNING] Notion credentials not configured. Error logged locally only.")
                print(f"Error {error_id}: {agent} - {error_type} - {message}")
                return None

            headers = {
                'Authorization': f'Bearer {notion_api_key}',
                'Content-Type': 'application/json',
                'Notion-Version': '2022-06-28'
            }

            data = {
                'parent': {'database_id': error_log_db},
                'properties': properties
            }

            response = requests.post(
                'https://api.notion.com/v1/pages',
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                print(f"[ERROR LOGGED] {error_id} to Notion")
                return error_id
            else:
                print(f"[WARNING] Failed to log to Notion: {response.status_code}")
                print(f"Error {error_id}: {agent} - {error_type} - {message}")
                return None

        except Exception as e:
            print(f"[WARNING] Exception while logging to Notion: {e}")
            print(f"Error {error_id}: {agent} - {error_type} - {message}")
            return None

    else:
        # Just print to console
        print(f"\n{'='*80}")
        print(f"ERROR LOGGED: {error_id}")
        print(f"{'='*80}")
        print(f"Agent:        {agent}")
        print(f"Type:         {error_type}")
        print(f"Severity:     {severity}")
        print(f"Message:      {message}")
        if context:
            print(f"Context:      {context}")
        if source_url:
            print(f"Source:       {source_url}")
        print(f"{'='*80}\n")
        return error_id

def update_error_occurrence(error_id, use_api=True):
    """
    Update occurrence count for a recurring error.

    Args:
        error_id: The error ID to update
        use_api: If True, use Notion API

    Returns:
        True if successful
    """
    if not use_api:
        print(f"[INFO] Would update occurrence count for {error_id}")
        return False

    try:
        import requests

        notion_api_key = os.getenv('NOTION_API_KEY')
        error_log_db = os.getenv('NOTION_ERROR_LOG_DB')

        if not notion_api_key or not error_log_db:
            return False

        headers = {
            'Authorization': f'Bearer {notion_api_key}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }

        # Query for the error
        query_data = {
            'filter': {
                'property': 'Error ID',
                'title': {
                    'equals': error_id
                }
            }
        }

        response = requests.post(
            f'https://api.notion.com/v1/databases/{error_log_db}/query',
            headers=headers,
            json=query_data
        )

        if response.status_code != 200 or not response.json().get('results'):
            return False

        page_id = response.json()['results'][0]['id']
        current_count = response.json()['results'][0]['properties']['Occurrence Count']['number']

        # Update occurrence count and last seen
        update_data = {
            'properties': {
                'Occurrence Count': {
                    'number': current_count + 1
                },
                'Last Seen': {
                    'date': {'start': datetime.now(timezone.utc).isoformat()}
                },
                'Status': {
                    'select': {'name': 'Recurring'}
                }
            }
        }

        response = requests.patch(
            f'https://api.notion.com/v1/pages/{page_id}',
            headers=headers,
            json=update_data
        )

        return response.status_code == 200

    except Exception as e:
        print(f"[WARNING] Could not update error occurrence: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Test error logging
    print("Testing error logging...\n")

    # Simulate an error
    try:
        raise ValueError("Test error for Notion logging")
    except Exception as e:
        error_id = log_error(
            agent="test_agent",
            error_type="validation_failure",
            severity="Medium",
            message="This is a test error message",
            context="Testing error logging functionality",
            source_url="https://test.example.com",
            use_api=False  # Set to True to actually log to Notion
        )

        print(f"\nGenerated Error ID: {error_id}")
        print("\nTo log to Notion:")
        print("1. Set NOTION_API_KEY in .env")
        print("2. Set NOTION_ERROR_LOG_DB in .env (database ID)")
        print("3. Call log_error() with use_api=True")
