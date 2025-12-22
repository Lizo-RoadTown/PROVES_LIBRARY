# GitHub API Sync - Quick Start Guide

## Why GitHub API Instead of Local Clones?

**Problem:** F´ and PROVES Kit repos are large - you don't want to store them locally.

**Solution:** Fetch documentation directly from GitHub API!

**Benefits:**
- ✅ No local disk space needed
- ✅ Always fetch latest from source
- ✅ Incremental updates via commit SHA tracking
- ✅ Well within GitHub rate limits (5000/hour authenticated)

---

## Setup (5 Minutes)

### Step 1: Get GitHub Personal Access Token

1. Go to [https://github.com/settings/tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Name: `PROVES Library Doc Sync`
4. Permissions: Check `public_repo` (read access to public repos)
5. Click "Generate token"
6. **Copy the token** (starts with `ghp_...`)

### Step 2: Add Token to .env

Open [.env](.env) and add:
```bash
GITHUB_TOKEN=ghp_your_token_here
```

### Step 3: Test Connection

```bash
.venv/Scripts/python.exe scripts/github_doc_sync.py test
```

**Expected output:**
```
[OK] GitHub API working. F' latest commit: abc123de
```

---

## Usage

### Initial Sync (One-Time)

```bash
# Fetch all F´ documentation
.venv/Scripts/python.exe scripts/github_doc_sync.py init fprime
```

**What happens:**
- Fetches latest commit SHA
- Lists all `.md` files in `docs/` directory
- Downloads each file via API
- Processes and stores in Neon database
- Tracks commit SHA for future updates

**Time:** ~2-5 minutes (depending on docs size)
**API calls:** ~50-100 (well within 5000/hour limit)

### Check for Updates

```bash
# Check if F´ docs have changed
.venv/Scripts/python.exe scripts/github_doc_sync.py check fprime
```

**Output:**
```
[OK] Already up-to-date at abc123de
```
or
```
[*] Updates available: abc123de -> def456gh
```

### Incremental Update

```bash
# Fetch and process only changed files
.venv/Scripts/python.exe scripts/github_doc_sync.py update fprime
```

**What happens:**
- Compares stored SHA with latest GitHub SHA
- Fetches list of changed files (via commit comparison)
- Downloads only changed `.md` files
- Updates affected entries in database
- Updates stored SHA

**Time:** ~10-30 seconds (usually only 1-5 files changed)
**API calls:** ~5-15

### Daily Sync (All Repos)

```bash
# Sync all configured repos
.venv/Scripts/python.exe scripts/github_doc_sync.py daily
```

**Recommendation:** Schedule this to run daily at 6 AM

---

## Scheduling

### Windows Task Scheduler

```powershell
schtasks /create /tn "PROVES_DocSync" `
  /tr "C:\Users\LizO5\PROVES_LIBRARY\.venv\Scripts\python.exe C:\Users\LizO5\PROVES_LIBRARY\scripts\github_doc_sync.py daily" `
  /sc daily /st 06:00
```

### Linux/Mac Cron

```bash
# Add to crontab (crontab -e)
0 6 * * * cd /path/to/PROVES_LIBRARY && .venv/bin/python scripts/github_doc_sync.py daily >> logs/sync.log 2>&1
```

---

## GitHub Rate Limits

### Unauthenticated
- **Limit:** 60 requests/hour
- **Recommendation:** Don't use unauthenticated

### Authenticated (with token)
- **Limit:** 5000 requests/hour
- **Daily sync usage:** ~50-100 requests
- **Margin:** ~50x headroom

### Check Your Rate Limit

```bash
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit
```

**Output:**
```json
{
  "resources": {
    "core": {
      "limit": 5000,
      "remaining": 4950,
      "reset": 1640995200
    }
  }
}
```

---

## Adding PROVES Kit Repository

Once you have the PROVES Kit GitHub URL, update the script:

**Edit `scripts/github_doc_sync.py`:**
```python
self.repos = {
    'fprime': {
        'owner': 'nasa',
        'repo': 'fprime',
        # ...
    },
    'proves_kit': {
        'owner': 'cal-poly-proves',  # ← Update this
        'repo': 'proves-kit',         # ← Update this
        'name': 'PROVES Kit',
        'doc_paths': ['docs/'],
        'branch': 'main'
    }
}
```

Then sync:
```bash
.venv/Scripts/python.exe scripts/github_doc_sync.py init proves_kit
```

---

## How It Works

### 1. Fetch Latest Commit SHA
```
GET /repos/nasa/fprime/commits/main
→ Returns: { "sha": "abc123..." }
```

### 2. List Files in docs/
```
GET /repos/nasa/fprime/contents/docs
→ Returns: [{ "name": "UserGuide.md", "path": "docs/UserGuide.md", ... }, ...]
```

### 3. Download File Content
```
GET /repos/nasa/fprime/contents/docs/UserGuide.md
→ Returns: { "content": "base64_encoded_content" }
```

### 4. Decode and Process
```python
content = base64.b64decode(data['content']).decode('utf-8')
# Extract metadata, create library entry, build graph
```

### 5. Store in Database
```sql
INSERT INTO library_entries (
    title, source_repo, source_file_path, source_commit_sha, content
) VALUES (...);
```

### 6. Track SHA
```sql
INSERT INTO sync_metadata (repo_key, last_commit_sha)
VALUES ('fprime', 'abc123...');
```

---

## Incremental Updates (Next Day)

### 1. Check for New Commits
```
Database: last_commit_sha = 'abc123'
GitHub:   current_sha = 'def456'
→ Updates detected!
```

### 2. Get Changed Files
```
GET /repos/nasa/fprime/compare/abc123...def456
→ Returns: { "files": [
    { "filename": "docs/Architecture.md", "status": "modified" },
    { "filename": "docs/NewGuide.md", "status": "added" }
]}
```

### 3. Fetch Only Changed Files
```
GET /repos/nasa/fprime/contents/docs/Architecture.md
GET /repos/nasa/fprime/contents/docs/NewGuide.md
```

### 4. Update Database
```sql
UPDATE library_entries
SET content = ..., updated_at = NOW()
WHERE source_repo = 'fprime'
AND source_file_path = 'docs/Architecture.md';
```

### 5. Update SHA
```sql
UPDATE sync_metadata
SET last_commit_sha = 'def456'
WHERE repo_key = 'fprime';
```

---

## Troubleshooting

### Error: "Rate limit exceeded"
**Cause:** Too many requests in 1 hour
**Fix:** Wait for reset time, or use authenticated requests

### Error: "Bad credentials"
**Cause:** Invalid GITHUB_TOKEN
**Fix:** Regenerate token at github.com/settings/tokens

### Error: "404 Not Found"
**Cause:** Repo/path doesn't exist
**Fix:** Check owner/repo names in script

### Warning: "Rate limit low: 50 requests remaining"
**Cause:** Many syncs in short time
**Action:** Script will continue but log warning

---

## Comparison: GitHub API vs Local Clone

| Aspect | GitHub API | Local Clone |
|--------|------------|-------------|
| **Disk space** | ✅ None | ❌ 100+ MB per repo |
| **Speed** | ⚠️ Slower (network) | ✅ Fast (local Git) |
| **Freshness** | ✅ Always latest | ⚠️ Need to pull |
| **Rate limits** | ⚠️ 5000/hour | ✅ Unlimited |
| **Setup** | ✅ Simple (just token) | ⚠️ Need Git installed |
| **Best for** | ✅ **Your use case** | Large teams, frequent access |

---

## Next Steps

1. ✅ Get GitHub token
2. ✅ Add to `.env`
3. ✅ Test connection
4. ✅ Run initial sync for F´
5. ⏸️ Wait for PROVES Kit URL
6. ⏸️ Schedule daily sync
7. ⏸️ Monitor first few syncs

**Ready to sync F´ docs now?**
```bash
.venv/Scripts/python.exe scripts/github_doc_sync.py init fprime
```
