"""
Team Collaboration Loaders for PROVES Library

Extraction tools for team knowledge sources:
- Notion: Team documentation, wikis, meeting notes
- Google Drive: Shared documents, spreadsheets, presentations
- Discord: Team discussions, decisions, Q&A

All fetched content is stored in raw_snapshots for auditability.
"""
import os
import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool

# Import shared database functions
from pathlib import Path
version3_folder = Path(__file__).parent
import sys
sys.path.insert(0, str(version3_folder))
from database import get_db_connection


def get_or_create_pipeline_run(conn, run_name: str = "team_extraction") -> str:
    """Get or create a pipeline run for tracking. Returns run_id."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id FROM pipeline_runs
            WHERE run_name = %s AND score_status = 'pending'
            ORDER BY created_at DESC LIMIT 1
        """, (run_name,))
        existing = cur.fetchone()
        if existing:
            return str(existing[0])

        cur.execute("""
            INSERT INTO pipeline_runs (run_name, run_type, triggered_by)
            VALUES (%s, 'extraction', 'team_loader')
            RETURNING id
        """, (run_name,))
        return str(cur.fetchone()[0])


def store_raw_snapshot(source_url: str, source_type: str, ecosystem: str, content: str, content_hash: str, metadata: dict = None) -> str:
    """Store raw content in raw_snapshots table. Returns snapshot_id."""
    try:
        conn = get_db_connection()

        with conn.cursor() as cur:
            # Check if we already have this exact content
            cur.execute("""
                SELECT id FROM raw_snapshots
                WHERE content_hash = %s AND status = 'captured'::snapshot_status
            """, (content_hash,))
            existing = cur.fetchone()

            if existing:
                conn.close()
                return str(existing[0])

            run_id = get_or_create_pipeline_run(conn)

            # Store content as JSONB payload with metadata
            payload_data = {"content": content, "format": "text"}
            if metadata:
                payload_data["metadata"] = metadata
            payload = json.dumps(payload_data)

            cur.execute("""
                INSERT INTO raw_snapshots (
                    source_url, source_type, ecosystem,
                    content_hash, payload, payload_size_bytes,
                    captured_by_run_id, status
                ) VALUES (
                    %s, %s::source_type, %s::ecosystem_type,
                    %s, %s::jsonb, %s,
                    %s::uuid, 'captured'::snapshot_status
                )
                RETURNING id
            """, (
                source_url, source_type, ecosystem,
                content_hash, payload, len(content.encode('utf-8')),
                run_id
            ))
            snapshot_id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        return str(snapshot_id)
    except Exception as e:
        return f"ERROR: {str(e)}"


# ============================================================================
# NOTION LOADER
# ============================================================================

@tool
def fetch_notion_page(page_id: str) -> str:
    """
    Fetch content from a Notion page.

    Use this to read team documentation, meeting notes, and wikis from Notion.
    Content is stored in raw_snapshots for auditability.

    Args:
        page_id: Notion page ID (the UUID part of the page URL)
                 Example: from https://notion.so/My-Page-abc123def456
                 Use: abc123def456 (or full UUID with dashes)

    Returns:
        Page content with title, blocks, and metadata for extraction.

    Requires: NOTION_API_KEY environment variable
    """
    try:
        import httpx

        notion_token = os.environ.get("NOTION_API_KEY")
        if not notion_token:
            return "Error: NOTION_API_KEY environment variable not set. Get your token from https://www.notion.so/my-integrations"

        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        # Clean up page ID (remove dashes if present, then format correctly)
        clean_id = page_id.replace("-", "")
        if len(clean_id) == 32:
            formatted_id = f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"
        else:
            formatted_id = page_id

        with httpx.Client(timeout=30.0) as client:
            # Get page metadata
            page_response = client.get(
                f"https://api.notion.com/v1/pages/{formatted_id}",
                headers=headers
            )
            page_response.raise_for_status()
            page_data = page_response.json()

            # Get page content (blocks)
            blocks_response = client.get(
                f"https://api.notion.com/v1/blocks/{formatted_id}/children?page_size=100",
                headers=headers
            )
            blocks_response.raise_for_status()
            blocks_data = blocks_response.json()

        # Extract title
        title = "Untitled"
        if "properties" in page_data:
            for prop_name, prop_value in page_data["properties"].items():
                if prop_value.get("type") == "title":
                    title_content = prop_value.get("title", [])
                    if title_content:
                        title = "".join([t.get("plain_text", "") for t in title_content])
                    break

        # Extract text content from blocks
        content_lines = [f"# {title}\n"]

        def extract_rich_text(rich_text_list):
            return "".join([rt.get("plain_text", "") for rt in rich_text_list])

        for block in blocks_data.get("results", []):
            block_type = block.get("type", "")
            block_content = block.get(block_type, {})

            if block_type == "paragraph":
                text = extract_rich_text(block_content.get("rich_text", []))
                if text:
                    content_lines.append(text)

            elif block_type in ["heading_1", "heading_2", "heading_3"]:
                text = extract_rich_text(block_content.get("rich_text", []))
                level = int(block_type[-1])
                if text:
                    content_lines.append(f"{'#' * level} {text}")

            elif block_type == "bulleted_list_item":
                text = extract_rich_text(block_content.get("rich_text", []))
                if text:
                    content_lines.append(f"• {text}")

            elif block_type == "numbered_list_item":
                text = extract_rich_text(block_content.get("rich_text", []))
                if text:
                    content_lines.append(f"1. {text}")

            elif block_type == "code":
                text = extract_rich_text(block_content.get("rich_text", []))
                language = block_content.get("language", "")
                if text:
                    content_lines.append(f"```{language}\n{text}\n```")

            elif block_type == "quote":
                text = extract_rich_text(block_content.get("rich_text", []))
                if text:
                    content_lines.append(f"> {text}")

            elif block_type == "callout":
                text = extract_rich_text(block_content.get("rich_text", []))
                if text:
                    content_lines.append(f"[!] {text}")

            elif block_type == "to_do":
                text = extract_rich_text(block_content.get("rich_text", []))
                checked = block_content.get("checked", False)
                checkbox = "[x]" if checked else "[ ]"
                if text:
                    content_lines.append(f"{checkbox} {text}")

        content = "\n\n".join(content_lines)

        # Store in raw_snapshots
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        source_url = f"notion://page/{formatted_id}"

        metadata = {
            "title": title,
            "page_id": formatted_id,
            "created_time": page_data.get("created_time"),
            "last_edited_time": page_data.get("last_edited_time"),
            "block_count": len(blocks_data.get("results", []))
        }

        snapshot_id = store_raw_snapshot(
            source_url=source_url,
            source_type="notion_page",
            ecosystem="generic",
            content=content,
            content_hash=content_hash,
            metadata=metadata
        )

        return f"Source: Notion Page\nPage ID: {formatted_id}\nTitle: {title}\nSnapshot ID: {snapshot_id}\nBlocks: {len(blocks_data.get('results', []))}\n\nContent:\n{content}"

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Page not found: {page_id}. Make sure the page is shared with your integration."
        elif e.response.status_code == 401:
            return "Unauthorized. Check your NOTION_API_KEY and make sure the page is shared with your integration."
        return f"HTTP error fetching Notion page: {e.response.status_code}"
    except Exception as e:
        return f"Error fetching Notion page: {str(e)}"


@tool
def fetch_notion_database(database_id: str, filter_json: str = None) -> str:
    """
    Query a Notion database and fetch its entries.

    Use this to read structured team data like task lists, component registries,
    or meeting logs stored in Notion databases.

    Args:
        database_id: Notion database ID (from the database URL)
        filter_json: Optional JSON filter string (Notion filter format)
                     Example: '{"property": "Status", "select": {"equals": "Done"}}'

    Returns:
        Database entries with properties for extraction.

    Requires: NOTION_API_KEY environment variable
    """
    try:
        import httpx

        notion_token = os.environ.get("NOTION_API_KEY")
        if not notion_token:
            return "Error: NOTION_API_KEY environment variable not set."

        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        # Clean up database ID
        clean_id = database_id.replace("-", "")
        if len(clean_id) == 32:
            formatted_id = f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"
        else:
            formatted_id = database_id

        # Build query body
        body = {"page_size": 100}
        if filter_json:
            body["filter"] = json.loads(filter_json)

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"https://api.notion.com/v1/databases/{formatted_id}/query",
                headers=headers,
                json=body
            )
            response.raise_for_status()
            data = response.json()

        results = data.get("results", [])
        content_lines = [f"# Notion Database Query Results\n\nDatabase ID: {formatted_id}\nEntries: {len(results)}\n"]

        for i, page in enumerate(results, 1):
            content_lines.append(f"\n## Entry {i}")
            props = page.get("properties", {})

            for prop_name, prop_value in props.items():
                prop_type = prop_value.get("type", "")
                value = ""

                if prop_type == "title":
                    value = "".join([t.get("plain_text", "") for t in prop_value.get("title", [])])
                elif prop_type == "rich_text":
                    value = "".join([t.get("plain_text", "") for t in prop_value.get("rich_text", [])])
                elif prop_type == "select":
                    select = prop_value.get("select")
                    value = select.get("name", "") if select else ""
                elif prop_type == "multi_select":
                    value = ", ".join([s.get("name", "") for s in prop_value.get("multi_select", [])])
                elif prop_type == "date":
                    date = prop_value.get("date")
                    value = date.get("start", "") if date else ""
                elif prop_type == "checkbox":
                    value = "Yes" if prop_value.get("checkbox") else "No"
                elif prop_type == "number":
                    value = str(prop_value.get("number", ""))
                elif prop_type == "url":
                    value = prop_value.get("url", "")

                if value:
                    content_lines.append(f"- **{prop_name}**: {value}")

        content = "\n".join(content_lines)

        # Store in raw_snapshots
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        source_url = f"notion://database/{formatted_id}"

        snapshot_id = store_raw_snapshot(
            source_url=source_url,
            source_type="notion_database",
            ecosystem="generic",
            content=content,
            content_hash=content_hash,
            metadata={"database_id": formatted_id, "entry_count": len(results)}
        )

        return f"Source: Notion Database\nDatabase ID: {formatted_id}\nSnapshot ID: {snapshot_id}\nEntries: {len(results)}\n\nContent:\n{content}"

    except Exception as e:
        return f"Error querying Notion database: {str(e)}"


# ============================================================================
# GOOGLE DRIVE LOADER
# ============================================================================

@tool
def fetch_google_doc(document_id: str) -> str:
    """
    Fetch content from a Google Doc.

    Use this to read team documents, specs, and meeting notes from Google Drive.
    Content is stored in raw_snapshots for auditability.

    Args:
        document_id: Google Doc ID (from the document URL)
                     Example: from https://docs.google.com/document/d/1ABC123xyz/edit
                     Use: 1ABC123xyz

    Returns:
        Document content with formatting preserved as markdown.

    Requires: GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_CREDENTIALS_JSON environment variable
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        # Get credentials
        creds_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")

        if creds_file and os.path.exists(creds_file):
            credentials = service_account.Credentials.from_service_account_file(
                creds_file,
                scopes=['https://www.googleapis.com/auth/documents.readonly',
                       'https://www.googleapis.com/auth/drive.readonly']
            )
        elif creds_json:
            import json
            creds_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/documents.readonly',
                       'https://www.googleapis.com/auth/drive.readonly']
            )
        else:
            return "Error: Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_CREDENTIALS_JSON environment variable. See https://cloud.google.com/iam/docs/service-accounts"

        # Build Docs API client
        docs_service = build('docs', 'v1', credentials=credentials)

        # Get document
        document = docs_service.documents().get(documentId=document_id).execute()

        title = document.get('title', 'Untitled')
        content_lines = [f"# {title}\n"]

        # Extract text content from document body
        def extract_text_from_element(element):
            text_run = element.get('textRun')
            if text_run:
                content = text_run.get('content', '')
                style = text_run.get('textStyle', {})

                # Apply basic formatting
                if style.get('bold'):
                    content = f"**{content.strip()}**"
                if style.get('italic'):
                    content = f"*{content.strip()}*"

                return content
            return ''

        body = document.get('body', {})
        for element in body.get('content', []):
            paragraph = element.get('paragraph')
            if paragraph:
                para_style = paragraph.get('paragraphStyle', {})
                named_style = para_style.get('namedStyleType', '')

                para_text = ''
                for elem in paragraph.get('elements', []):
                    para_text += extract_text_from_element(elem)

                # Apply heading styles
                if named_style == 'HEADING_1':
                    para_text = f"# {para_text.strip()}"
                elif named_style == 'HEADING_2':
                    para_text = f"## {para_text.strip()}"
                elif named_style == 'HEADING_3':
                    para_text = f"### {para_text.strip()}"

                if para_text.strip():
                    content_lines.append(para_text)

            # Handle tables
            table = element.get('table')
            if table:
                content_lines.append("\n[TABLE]")
                for row in table.get('tableRows', []):
                    row_text = []
                    for cell in row.get('tableCells', []):
                        cell_text = ''
                        for cell_elem in cell.get('content', []):
                            cell_para = cell_elem.get('paragraph')
                            if cell_para:
                                for elem in cell_para.get('elements', []):
                                    cell_text += extract_text_from_element(elem)
                        row_text.append(cell_text.strip())
                    content_lines.append(" | ".join(row_text))
                content_lines.append("[/TABLE]\n")

        content = "\n".join(content_lines)

        # Store in raw_snapshots
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        source_url = f"https://docs.google.com/document/d/{document_id}"

        snapshot_id = store_raw_snapshot(
            source_url=source_url,
            source_type="google_doc",
            ecosystem="generic",
            content=content,
            content_hash=content_hash,
            metadata={
                "document_id": document_id,
                "title": title,
                "revision_id": document.get('revisionId')
            }
        )

        return f"Source: Google Doc\nDocument ID: {document_id}\nTitle: {title}\nSnapshot ID: {snapshot_id}\n\nContent:\n{content}"

    except Exception as e:
        return f"Error fetching Google Doc: {str(e)}"


@tool
def fetch_google_sheet(spreadsheet_id: str, sheet_name: str = None) -> str:
    """
    Fetch content from a Google Sheet.

    Use this to read structured team data like component lists, schedules,
    or configuration tables from Google Sheets.

    Args:
        spreadsheet_id: Google Sheet ID (from the spreadsheet URL)
        sheet_name: Optional specific sheet name (defaults to first sheet)

    Returns:
        Sheet content as markdown table format.

    Requires: GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_CREDENTIALS_JSON environment variable
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")

        if creds_file and os.path.exists(creds_file):
            credentials = service_account.Credentials.from_service_account_file(
                creds_file,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
        elif creds_json:
            creds_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
        else:
            return "Error: Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_CREDENTIALS_JSON environment variable."

        sheets_service = build('sheets', 'v4', credentials=credentials)

        # Get spreadsheet metadata
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        title = spreadsheet.get('properties', {}).get('title', 'Untitled')

        # Determine range
        if sheet_name:
            range_name = f"'{sheet_name}'"
        else:
            # Use first sheet
            first_sheet = spreadsheet.get('sheets', [{}])[0]
            sheet_name = first_sheet.get('properties', {}).get('title', 'Sheet1')
            range_name = f"'{sheet_name}'"

        # Get values
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        values = result.get('values', [])

        content_lines = [f"# {title}\n\nSheet: {sheet_name}\nRows: {len(values)}\n"]

        if values:
            # Create markdown table
            header = values[0] if values else []
            content_lines.append("| " + " | ".join(str(h) for h in header) + " |")
            content_lines.append("| " + " | ".join(["---"] * len(header)) + " |")

            for row in values[1:]:
                # Pad row if needed
                padded_row = row + [''] * (len(header) - len(row))
                content_lines.append("| " + " | ".join(str(cell) for cell in padded_row[:len(header)]) + " |")

        content = "\n".join(content_lines)

        # Store in raw_snapshots
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        source_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

        snapshot_id = store_raw_snapshot(
            source_url=source_url,
            source_type="google_sheet",
            ecosystem="generic",
            content=content,
            content_hash=content_hash,
            metadata={
                "spreadsheet_id": spreadsheet_id,
                "sheet_name": sheet_name,
                "title": title,
                "row_count": len(values)
            }
        )

        return f"Source: Google Sheet\nSpreadsheet ID: {spreadsheet_id}\nSheet: {sheet_name}\nTitle: {title}\nSnapshot ID: {snapshot_id}\nRows: {len(values)}\n\nContent:\n{content}"

    except Exception as e:
        return f"Error fetching Google Sheet: {str(e)}"


@tool
def list_google_drive_folder(folder_id: str) -> str:
    """
    List files in a Google Drive folder.

    Use this to explore team folders before fetching specific documents.

    Args:
        folder_id: Google Drive folder ID (from the folder URL)
                   Use 'root' for the root folder

    Returns:
        List of files with IDs for fetching.

    Requires: GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_CREDENTIALS_JSON environment variable
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")

        if creds_file and os.path.exists(creds_file):
            credentials = service_account.Credentials.from_service_account_file(
                creds_file,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
        elif creds_json:
            creds_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
        else:
            return "Error: Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_CREDENTIALS_JSON environment variable."

        drive_service = build('drive', 'v3', credentials=credentials)

        # List files in folder
        query = f"'{folder_id}' in parents and trashed = false"
        results = drive_service.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, mimeType, modifiedTime, size)"
        ).execute()

        files = results.get('files', [])

        content_lines = [f"# Google Drive Folder Contents\n\nFolder ID: {folder_id}\nFiles: {len(files)}\n"]

        # Group by type
        folders = []
        docs = []
        sheets = []
        other = []

        for f in files:
            mime = f.get('mimeType', '')
            if mime == 'application/vnd.google-apps.folder':
                folders.append(f)
            elif mime == 'application/vnd.google-apps.document':
                docs.append(f)
            elif mime == 'application/vnd.google-apps.spreadsheet':
                sheets.append(f)
            else:
                other.append(f)

        if folders:
            content_lines.append("\n## Folders")
            for f in folders:
                content_lines.append(f"- 📁 {f['name']} (ID: {f['id']})")

        if docs:
            content_lines.append("\n## Google Docs")
            for f in docs:
                content_lines.append(f"- 📄 {f['name']} (ID: {f['id']})")

        if sheets:
            content_lines.append("\n## Google Sheets")
            for f in sheets:
                content_lines.append(f"- 📊 {f['name']} (ID: {f['id']})")

        if other:
            content_lines.append("\n## Other Files")
            for f in other:
                size = f.get('size', 'N/A')
                content_lines.append(f"- 📎 {f['name']} ({f.get('mimeType', 'unknown')}, {size} bytes, ID: {f['id']})")

        return "\n".join(content_lines)

    except Exception as e:
        return f"Error listing Google Drive folder: {str(e)}"


# ============================================================================
# DISCORD LOADER
# ============================================================================

@tool
def fetch_discord_channel(channel_id: str, limit: int = 100) -> str:
    """
    Fetch messages from a Discord channel.

    Use this to capture team discussions, decisions, and Q&A from Discord.
    Content is stored in raw_snapshots for auditability.

    Args:
        channel_id: Discord channel ID (enable Developer Mode to copy IDs)
        limit: Maximum messages to fetch (default 100, max 100)

    Returns:
        Channel messages with authors and timestamps for extraction.

    Requires: DISCORD_BOT_TOKEN environment variable
    """
    try:
        import httpx

        discord_token = os.environ.get("DISCORD_BOT_TOKEN")
        if not discord_token:
            return "Error: DISCORD_BOT_TOKEN environment variable not set. Create a bot at https://discord.com/developers/applications"

        headers = {
            "Authorization": f"Bot {discord_token}",
            "Content-Type": "application/json"
        }

        limit = min(limit, 100)  # Discord API limit

        with httpx.Client(timeout=30.0) as client:
            # Get channel info
            channel_response = client.get(
                f"https://discord.com/api/v10/channels/{channel_id}",
                headers=headers
            )
            channel_response.raise_for_status()
            channel_data = channel_response.json()

            # Get messages
            messages_response = client.get(
                f"https://discord.com/api/v10/channels/{channel_id}/messages?limit={limit}",
                headers=headers
            )
            messages_response.raise_for_status()
            messages = messages_response.json()

        channel_name = channel_data.get('name', 'unknown')
        guild_id = channel_data.get('guild_id', 'DM')

        content_lines = [
            f"# Discord Channel: #{channel_name}\n",
            f"Channel ID: {channel_id}",
            f"Server ID: {guild_id}",
            f"Messages: {len(messages)}\n",
            "---\n"
        ]

        # Messages come in reverse chronological order, reverse them
        for msg in reversed(messages):
            author = msg.get('author', {})
            username = author.get('username', 'Unknown')
            timestamp = msg.get('timestamp', '')[:19].replace('T', ' ')
            content = msg.get('content', '')

            # Handle embeds
            embeds = msg.get('embeds', [])
            embed_text = ""
            if embeds:
                for embed in embeds:
                    if embed.get('title'):
                        embed_text += f"\n  [Embed: {embed.get('title')}]"
                    if embed.get('description'):
                        embed_text += f"\n  {embed.get('description')[:200]}"

            # Handle attachments
            attachments = msg.get('attachments', [])
            attach_text = ""
            if attachments:
                for att in attachments:
                    attach_text += f"\n  [Attachment: {att.get('filename', 'file')}]"

            # Handle replies
            reply_text = ""
            if msg.get('referenced_message'):
                ref = msg['referenced_message']
                ref_author = ref.get('author', {}).get('username', 'Unknown')
                ref_content = ref.get('content', '')[:50]
                reply_text = f"\n  ↳ Replying to @{ref_author}: {ref_content}..."

            content_lines.append(f"**{username}** [{timestamp}]{reply_text}")
            if content:
                content_lines.append(content)
            if embed_text:
                content_lines.append(embed_text)
            if attach_text:
                content_lines.append(attach_text)
            content_lines.append("")  # Blank line between messages

        content = "\n".join(content_lines)

        # Store in raw_snapshots
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        source_url = f"discord://channel/{guild_id}/{channel_id}"

        snapshot_id = store_raw_snapshot(
            source_url=source_url,
            source_type="discord_channel",
            ecosystem="generic",
            content=content,
            content_hash=content_hash,
            metadata={
                "channel_id": channel_id,
                "channel_name": channel_name,
                "guild_id": guild_id,
                "message_count": len(messages)
            }
        )

        return f"Source: Discord Channel\nChannel: #{channel_name}\nChannel ID: {channel_id}\nSnapshot ID: {snapshot_id}\nMessages: {len(messages)}\n\nContent:\n{content}"

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            return f"Access denied to channel {channel_id}. Make sure your bot has access to this channel."
        elif e.response.status_code == 404:
            return f"Channel not found: {channel_id}"
        return f"HTTP error fetching Discord channel: {e.response.status_code}"
    except Exception as e:
        return f"Error fetching Discord channel: {str(e)}"


@tool
def fetch_discord_thread(thread_id: str, limit: int = 100) -> str:
    """
    Fetch messages from a Discord thread.

    Use this to capture focused discussions in Discord threads.

    Args:
        thread_id: Discord thread ID
        limit: Maximum messages to fetch (default 100)

    Returns:
        Thread messages with context for extraction.

    Requires: DISCORD_BOT_TOKEN environment variable
    """
    # Threads use the same API as channels
    return fetch_discord_channel.invoke({"channel_id": thread_id, "limit": limit})


@tool
def search_discord_messages(guild_id: str, query: str, limit: int = 25) -> str:
    """
    Search Discord messages across a server.

    Use this to find specific discussions or decisions in Discord.

    Args:
        guild_id: Discord server (guild) ID
        query: Search query string
        limit: Maximum results (default 25, max 25)

    Returns:
        Matching messages with context.

    Requires: DISCORD_BOT_TOKEN environment variable
    Note: Requires MESSAGE_CONTENT intent and search permissions
    """
    try:
        import httpx

        discord_token = os.environ.get("DISCORD_BOT_TOKEN")
        if not discord_token:
            return "Error: DISCORD_BOT_TOKEN environment variable not set."

        headers = {
            "Authorization": f"Bot {discord_token}",
            "Content-Type": "application/json"
        }

        limit = min(limit, 25)

        # Note: Message search requires specific bot permissions
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"https://discord.com/api/v10/guilds/{guild_id}/messages/search",
                headers=headers,
                params={"content": query, "limit": limit}
            )

            if response.status_code == 403:
                return f"Bot doesn't have permission to search messages in this server. Grant the bot 'Read Message History' permission."

            response.raise_for_status()
            data = response.json()

        messages = data.get('messages', [])
        total = data.get('total_results', 0)

        content_lines = [
            f"# Discord Search Results\n",
            f"Server ID: {guild_id}",
            f"Query: {query}",
            f"Results: {len(messages)} of {total}\n",
            "---\n"
        ]

        for msg_group in messages:
            for msg in msg_group:
                author = msg.get('author', {})
                username = author.get('username', 'Unknown')
                timestamp = msg.get('timestamp', '')[:19].replace('T', ' ')
                content = msg.get('content', '')
                channel_id = msg.get('channel_id', '')

                content_lines.append(f"**{username}** in <#{channel_id}> [{timestamp}]")
                content_lines.append(content)
                content_lines.append("")

        return "\n".join(content_lines)

    except Exception as e:
        return f"Error searching Discord: {str(e)}"


# ============================================================================
# EXPORT ALL TOOLS
# ============================================================================

# List of all team loader tools for import into extractor
TEAM_LOADER_TOOLS = [
    # Notion
    fetch_notion_page,
    fetch_notion_database,
    # Google Drive
    fetch_google_doc,
    fetch_google_sheet,
    list_google_drive_folder,
    # Discord
    fetch_discord_channel,
    fetch_discord_thread,
    search_discord_messages,
]
