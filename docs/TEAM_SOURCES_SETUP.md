# Team Collaboration Sources Setup

This guide covers setting up extraction from team collaboration tools: **Notion**, **Google Drive**, and **Discord**.

## Quick Start

1. Set up credentials (see sections below)
2. Add credentials to your `.env` file
3. Run extraction with the new tools

---

## Notion Setup

Notion stores team wikis, documentation, and meeting notes.

### Step 1: Create a Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Fill in:
   - Name: `PROVES Library Extractor`
   - Associated workspace: Select your team workspace
   - Capabilities: Check **Read content**
4. Click **Submit**
5. Copy the **Internal Integration Token** (starts with `secret_`)

### Step 2: Share Pages with Your Integration

For each page or database you want to extract from:

1. Open the page in Notion
2. Click **Share** (top right)
3. Click **"Invite"**
4. Search for your integration name (`PROVES Library Extractor`)
5. Click **Invite**

### Step 3: Add to Environment

```env
NOTION_API_KEY=secret_your_integration_token_here
```

### Step 4: Get Page/Database IDs

**From a page URL:**
```
https://notion.so/My-Page-Title-abc123def456ghi789
                                ^^^^^^^^^^^^^^^^
                                This is the page ID
```

**From a database URL:**
```
https://notion.so/abc123def456?v=...
                 ^^^^^^^^^^^^
                 This is the database ID
```

### Usage Examples

```python
# Fetch a Notion page
fetch_notion_page("abc123def456ghi789")

# Query a Notion database
fetch_notion_database("abc123def456")

# With filter
fetch_notion_database("abc123def456", '{"property": "Status", "select": {"equals": "Active"}}')
```

---

## Google Drive Setup

Google Drive stores shared documents, spreadsheets, and team files.

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Note your **Project ID**

### Step 2: Enable APIs

In your project, enable these APIs:
- [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)
- [Google Docs API](https://console.cloud.google.com/apis/library/docs.googleapis.com)
- [Google Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com)

### Step 3: Create Service Account

1. Go to [IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click **"+ Create Service Account"**
3. Fill in:
   - Name: `proves-library-extractor`
   - Description: `Extracts team docs for PROVES Library`
4. Click **Create and Continue**
5. Skip roles (we'll use file sharing instead)
6. Click **Done**

### Step 4: Create Service Account Key

1. Click on your new service account
2. Go to **Keys** tab
3. Click **Add Key > Create new key**
4. Select **JSON**
5. Click **Create**
6. Save the downloaded file to `credentials/google-service-account.json`

### Step 5: Share Files with Service Account

For each file/folder you want to access:

1. Open the file in Google Drive
2. Click **Share**
3. Add your service account email (looks like `proves-library-extractor@your-project.iam.gserviceaccount.com`)
4. Set permission to **Viewer**
5. Click **Send**

### Step 6: Add to Environment

```env
# Option A: Path to credentials file
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google-service-account.json

# Option B: JSON string (for deployment)
# GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}
```

### Step 7: Get Document IDs

**From a Google Doc URL:**
```
https://docs.google.com/document/d/1ABC123xyz_abcdefg/edit
                                   ^^^^^^^^^^^^^^^^^
                                   This is the document ID
```

**From a Google Sheet URL:**
```
https://docs.google.com/spreadsheets/d/1ABC123xyz_abcdefg/edit
                                       ^^^^^^^^^^^^^^^^^
                                       This is the spreadsheet ID
```

**From a folder URL:**
```
https://drive.google.com/drive/folders/1ABC123xyz_abcdefg
                                        ^^^^^^^^^^^^^^^^^
                                        This is the folder ID
```

### Usage Examples

```python
# Fetch a Google Doc
fetch_google_doc("1ABC123xyz_abcdefg")

# Fetch a Google Sheet (first sheet)
fetch_google_sheet("1ABC123xyz_abcdefg")

# Fetch specific sheet by name
fetch_google_sheet("1ABC123xyz_abcdefg", "Components List")

# List files in a folder
list_google_drive_folder("1ABC123xyz_abcdefg")
```

---

## Discord Setup

Discord captures team discussions, decisions, and Q&A.

### Step 1: Create a Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Name: `PROVES Library Bot`
4. Click **Create**

### Step 2: Create a Bot

1. Go to **Bot** tab (left sidebar)
2. Click **"Add Bot"**
3. Under **Privileged Gateway Intents**, enable:
   - **Message Content Intent** (required to read message content)
4. Click **Reset Token** and copy the token

### Step 3: Invite Bot to Your Server

1. Go to **OAuth2 > URL Generator**
2. Select scopes:
   - `bot`
3. Select bot permissions:
   - `Read Message History`
   - `View Channels`
4. Copy the generated URL
5. Open URL in browser and select your server
6. Click **Authorize**

### Step 4: Add to Environment

```env
DISCORD_BOT_TOKEN=your_bot_token_here
```

### Step 5: Get Channel/Server IDs

Enable Developer Mode in Discord:
1. User Settings > App Settings > Advanced
2. Enable **Developer Mode**

Now you can right-click channels/servers and select **"Copy ID"**

### Usage Examples

```python
# Fetch messages from a channel (last 100)
fetch_discord_channel("1234567890123456789")

# Fetch with custom limit
fetch_discord_channel("1234567890123456789", limit=50)

# Fetch from a thread
fetch_discord_thread("1234567890123456789")

# Search messages in a server
search_discord_messages("9876543210987654321", "I2C address conflict")
```

---

## Folder Structure

Create a `credentials/` folder in your project root:

```
PROVES_LIBRARY/
├── credentials/
│   ├── .gitignore              # Ignore all credentials
│   ├── google-service-account.json
│   └── README.md               # Setup instructions
├── .env                        # Contains API keys
└── ...
```

The `credentials/.gitignore` should contain:
```
# Ignore all credential files
*.json
*.key
*.pem
!README.md
```

---

## Testing Your Setup

### Test Notion

```python
from production.Version3.team_loaders import fetch_notion_page

# Test with a page ID
result = fetch_notion_page.invoke({"page_id": "your-page-id"})
print(result)
```

### Test Google Drive

```python
from production.Version3.team_loaders import fetch_google_doc

# Test with a document ID
result = fetch_google_doc.invoke({"document_id": "your-doc-id"})
print(result)
```

### Test Discord

```python
from production.Version3.team_loaders import fetch_discord_channel

# Test with a channel ID
result = fetch_discord_channel.invoke({"channel_id": "your-channel-id"})
print(result)
```

---

## Extraction Workflow

Once configured, you can extract team knowledge using the curator agent:

```python
# Example: Extract from a Notion meeting notes page
from production.Version3.agent_v3 import run_curator

result = run_curator(
    task="Extract architecture knowledge from this Notion page",
    source_url="notion://page/abc123def456"
)
```

The extractor will:
1. Fetch content using the appropriate loader
2. Store raw content in `raw_snapshots`
3. Extract architecture using FRAMES methodology
4. Stage extractions for human review

---

## Troubleshooting

### Notion: "Page not found"
- Make sure you shared the page with your integration
- Check the page ID is correct (32 hex characters)

### Google: "Invalid credentials"
- Verify the service account JSON file path
- Check the file hasn't been corrupted
- Ensure the APIs are enabled

### Discord: "Access denied"
- Verify the bot is in the server
- Check the bot has "Read Message History" permission
- Ensure Message Content Intent is enabled

### General: "API key not set"
- Check your `.env` file has the correct variable names
- Restart your Python environment after adding keys
- Verify the `.env` file is in the project root
