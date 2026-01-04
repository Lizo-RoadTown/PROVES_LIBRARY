# Fix Notion Teamspace Integration Permissions

## Problem
After moving to a teamspace, the Notion integration cannot see database properties (shows 0 properties).

## Solution - Re-grant Integration Access

### Step 1: Open Notion Integration Settings
1. Go to: https://www.notion.so/profile/integrations
2. Find your integration (PROVES Library integration)

### Step 2: Connect Integration to Teamspace
1. In the integration settings, find **"Select pages"** or **"Connected pages"**
2. Click **"Add pages"**
3. **IMPORTANT**: Switch from "Private pages" to your **TEAMSPACE**
4. Select these databases:
   - Staging Extractions Review
   - Curator Errors Log
   - Curator Reports
   - Improvement Suggestions

### Step 3: Grant Explicit Database Permissions
For each database in Notion:
1. Open the database in Notion
2. Click the **"..."** menu (top right)
3. Select **"Connections"** or **"Add connections"**
4. Find and add your integration
5. Grant these permissions:
   - ✅ Read content
   - ✅ Update content
   - ✅ Insert content

### Step 4: Verify Webhook Connection
1. Go to Notion integration settings
2. Under **"Capabilities"** tab, ensure:
   - ✅ Read content
   - ✅ Update content
   - ✅ Insert content
   - ✅ Read user information (for webhook actor tracking)
3. Under **"Webhooks"** tab (if visible):
   - Verify webhook URL: https://proves-notion.vercel.app/api/notion_webhook
   - Ensure it's subscribed to your teamspace databases

### Step 5: Re-test Integration
Run the test script again:
```bash
python test_notion_teamspace.py
```

You should see:
```
[OK] Found 25+ properties:
   - Candidate Key
   - Extraction ID
   - Accept/Reject
   - Status
   - ...
```

## Alternative: Database ID May Have Changed

If the above doesn't work, the database ID might have changed when moving to teamspace:

1. Open your Extractions database in Notion
2. Copy the URL - it looks like:
   ```
   https://www.notion.so/<workspace>/69f15f92c95245...
                                      ^^^^^^^^^^^ - Database ID
   ```
3. Update `.env` with new ID if different:
   ```bash
   NOTION_EXTRACTIONS_DB_ID=<new-id>
   ```

## What This Fixes

Once permissions are restored:
- ✅ Database → Notion: Local webhook server can push new extractions
- ✅ Notion → Database: Vercel webhook can receive status updates
- ✅ Both sync directions working in teamspace
