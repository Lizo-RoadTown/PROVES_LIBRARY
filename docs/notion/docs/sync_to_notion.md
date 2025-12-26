# Sync Reports to Notion (via Claude Desktop)

Since the Notion MCP server runs in Claude Desktop, you can sync reports by asking Claude to help.

## Setup

1. **Create Notion Pages:**
   - Create a page: "PROVES Extraction - Daily Reports"
   - Create a page: "PROVES Extraction - Error Log"

2. **Get Page IDs:**
   - Open each page in Notion
   - Copy the page ID from the URL: `https://www.notion.so/PAGE_ID`
   - Save them for reference

## Sync Daily Report

After each extraction, a report is saved to: `reports/daily_report_YYYY-MM-DD.md`

**To sync to Notion:**

1. Open Claude Desktop (which has Notion MCP access)
2. Say:

```
Read the file curator-agent/reports/daily_report_2025-12-23.md and append it to my Notion page "PROVES Extraction - Daily Reports" (page ID: YOUR_PAGE_ID)
```

Claude will use the MCP tools to append the report content.

## Sync Error Log

When errors occur, they're logged in the progress tracker and daily reports.

**To log to Notion:**

1. Open Claude Desktop
2. Say:

```
Check curator-agent/extraction_progress.json for failed pages and append them to my Notion page "PROVES Extraction - Error Log" (page ID: YOUR_PAGE_ID) with error details
```

## Automated Sync (Optional)

You can automate this by:

1. Create a simple script that outputs the report path
2. Use Claude Desktop's API (if available) to trigger sync

**Or simpler:** Just manually sync at end of day (takes 30 seconds).

---

## Example Claude Desktop Commands

### Sync Today's Report
```
Read curator-agent/reports/daily_report_2025-12-23.md and create a new section in my Notion page (ID: abc123) with today's date as heading and the report content below
```

### Sync All Failed Pages
```
Read curator-agent/extraction_progress.json, find all entries in the "failed" array, and append them to my Notion error log page (ID: def456) as a bulleted list with error messages
```

### Create Weekly Summary
```
Read all daily reports from curator-agent/reports/ from this week and create a weekly summary in my Notion page (ID: ghi789) showing:
- Total pages completed
- Total extractions
- Any errors or issues
```

---

The reports are already formatted as clean markdown, so Claude Desktop can directly copy them to Notion without modification.
