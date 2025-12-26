## Notion Integration Setup

Export extraction statistics and reports to Notion for easy sharing and visualization.

---

## Setup Steps

### 1. Create Notion Integration

1. Go to: https://www.notion.so/my-integrations
2. Click **"+ New integration"**
3. Name: `PROVES Library Curator`
4. Associated workspace: Select your workspace
5. Click **"Submit"**
6. Copy the **"Internal Integration Token"** (starts with `secret_`)

### 2. Add Integration Token to .env

Add to your `.env` file:

```bash
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Create Target Page in Notion

1. Open Notion
2. Create a new page: **"PROVES Library Extraction"**
3. Share this page with your integration:
   - Click **"Share"** (top right)
   - Click **"Invite"**
   - Search for **"PROVES Library Curator"** (your integration name)
   - Click **"Invite"**

### 4. Get Page ID

1. Open your **"PROVES Library Extraction"** page in Notion
2. Look at the URL in your browser:
   ```
   https://www.notion.so/YOUR_PAGE_ID?...
   ```
3. Copy the `YOUR_PAGE_ID` part (the long string of letters/numbers)

### 5. Add Page ID to .env

Add to your `.env` file:

```bash
NOTION_PAGE_ID=your_page_id_here
```

### 6. Install Notion Client

```bash
pip install notion-client
```

---

## Test Connection

```bash
python export_to_notion.py --test
```

**Expected output:**
```
✅ Connected to Notion (found X users)
```

---

## Usage

### Export After Each Page

Automatically exports daily report to Notion after each successful extraction:

```bash
python daily_extraction.py
```

### Export Final Summary

```bash
python generate_final_report.py --notion
```

### Manual Export

```bash
python export_to_notion.py
```

---

## What Gets Exported

### Daily Stats Page (created after each extraction)

- **Overview**
  - Progress: X/Y pages (Z%)
  - Total Extractions: N
  - Verified Entities: M

- **Progress Breakdown**
  - Completed: X ✅
  - Skipped: Y ⏭️
  - Failed: Z ❌

- **Confidence Scores**
  - Average: 0.XX
  - Min/Max range

- **By Ecosystem**
  - fprime: X
  - proveskit: Y
  - hardware: Z

- **Recent Pages**
  - List of last 10 completed pages

---

## Troubleshooting

### ❌ "NOTION_API_KEY not set"

**Solution:**
1. Check `.env` file exists in project root
2. Verify `NOTION_API_KEY=secret_...` is set
3. Restart terminal/Python to reload environment

---

### ❌ "NOTION_PAGE_ID not set"

**Solution:**
1. Open target Notion page
2. Copy page ID from URL
3. Add to `.env`: `NOTION_PAGE_ID=your_id_here`

---

### ❌ "Could not find page"

**Solution:**
Page is not shared with integration:
1. Open page in Notion
2. Click **"Share"** → **"Invite"**
3. Search for your integration name
4. Click **"Invite"**

---

### ❌ "notion-client not installed"

**Solution:**
```bash
pip install notion-client
```

---

## Advanced: Custom Page Layout

You can customize what gets exported by editing `export_to_notion.py`:

```python
def create_extraction_stats_page(client, page_id, progress, db_stats):
    # Add custom blocks here
    # See: https://developers.notion.com/reference/block
```

**Block types available:**
- Heading (h1, h2, h3)
- Paragraph
- Bulleted/numbered list
- Callout (with emoji)
- Quote
- Code block
- Table
- Toggle

---

## Example Notion Page Structure

```
📊 PROVES Kit Extraction Stats - 2025-12-23

Overview
┌─────────────────────────────────────────┐
│ Progress: 10/60 pages (16.7%)           │
│ Total Extractions: 85                   │
│ Verified Entities: 72                   │
└─────────────────────────────────────────┘

Progress
✅ Completed: 10
⏭️ Skipped: 2
❌ Failed: 0

Confidence Scores
Average: 0.82
Min: 0.65
Max: 0.95

By Ecosystem
fprime: 25
proveskit: 30
hardware: 17

Recent Pages
• Hardware Overview (8 extractions)
• PROVES Prime (12 extractions)
• Flight Control Board (9 extractions)
...
```

---

## Next Steps

After setup:
1. Run test: `python export_to_notion.py --test`
2. Run extraction: `python daily_extraction.py`
3. Check Notion page for stats!

---

*For API reference: https://developers.notion.com/reference/intro*
