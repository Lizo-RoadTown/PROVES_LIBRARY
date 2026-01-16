# Supabase Local Development Setup (Windows)

**Purpose:** Set up Supabase CLI with Docker for local development on Windows

**Date:** 2026-01-15

**Estimated Time:** 15-20 minutes

---

## Prerequisites

Before starting, you need:

1. **Node.js and npm** - Already installed (used for the project)
2. **Docker Desktop** - Required for Supabase local stack
3. **Git Bash or PowerShell** - For running commands

---

## Step 1: Install Docker Desktop

Supabase CLI uses Docker containers to run the local database, API, and Studio.

### Download and Install

1. Go to https://www.docker.com/products/docker-desktop/
2. Download **Docker Desktop for Windows**
3. Run the installer
4. Follow the setup wizard (accept defaults)
5. **Restart your computer** after installation

### Verify Docker Installation

Open PowerShell and run:

```powershell
docker --version
```

Expected output:
```
Docker version 24.0.x, build xxxxx
```

If you see "command not found", restart your terminal or computer.

---

## Step 2: Install Supabase CLI

The CLI is installed as an npm dev dependency in the project.

### Install via npm

Open PowerShell in the project root (`c:\Users\Liz\PROVES_LIBRARY`) and run:

```powershell
npm install supabase --save-dev
```

Expected output:
```
added 1 package, and audited X packages in Xs
```

### Verify Installation

```powershell
npx supabase --version
```

Expected output:
```
1.x.x
```

---

## Step 3: Initialize Supabase (Already Done)

The `supabase/` folder already exists with configuration, so you can skip `supabase init`.

Verify the configuration exists:

```powershell
cat supabase\config.toml
```

You should see the project configuration with ports 54321-54324.

---

## Step 4: Login to Supabase

Link your local CLI to your Supabase account.

### Login Command

```powershell
npx supabase login
```

This will:
1. Open a browser window
2. Ask you to authorize the CLI
3. Return an access token to the CLI

### Troubleshooting Login

**Error: "Browser didn't open"**

If the browser doesn't open automatically:
1. Copy the URL from the terminal
2. Paste it into your browser manually
3. Complete authorization
4. Copy the token
5. Paste it back into the terminal

---

## Step 5: Link to Your Supabase Project

Connect your local development to the remote Supabase project.

### Link Command

```powershell
npx supabase link --project-ref guigtpwxlqwueylbbcpx
```

You'll be asked for your **database password** (the one you set when creating the Supabase project in Step 1 of DASHBOARD_PLATFORM_SETUP.md).

Expected output:
```
Finished supabase link.
```

### Verify Link

```powershell
npx supabase status
```

This should show your project ID: `guigtpwxlqwueylbbcpx`

---

## Step 6: Start Local Supabase Stack

This command starts Docker containers for the database, API, auth, and Studio.

### Start Command

```powershell
npx supabase start
```

**First time:** This will take 2-5 minutes to download Docker images (~2 GB).

Expected output:
```
Started supabase local development setup.

         API URL: http://localhost:54321
          DB URL: postgresql://postgres:postgres@localhost:54322/postgres
      Studio URL: http://localhost:54323
    Inbucket URL: http://localhost:54324
        anon key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
service_role key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Save these keys!** You'll need them for local development.

### Access Supabase Studio

Open your browser to http://localhost:54323

You should see the Supabase Studio interface with:
- Table Editor
- SQL Editor
- Authentication
- Storage
- etc.

---

## Step 7: Pull Remote Schema (Optional)

If you want to pull the schema from your remote Supabase project to local:

```powershell
npx supabase db pull
```

This creates a new migration file in `supabase/migrations/` with your current remote schema.

**For this project:** We'll create Migration 016 manually instead, since the remote Supabase is empty and we're keeping Neon for production.

---

## Step 8: Create Migration 016 for Teams/Batch Claims

Now that local Supabase is running, create the migration for dashboard tables.

### Create Migration File

```powershell
npx supabase migration new teams_and_batch_claims
```

This creates a file like `supabase/migrations/20260115123456_teams_and_batch_claims.sql`

Edit this file with the SQL for:
- `teams` table
- `team_members` table
- `batch_claims` table
- `team_notifications` table
- Row-level security policies

(We'll create the SQL content next)

### Apply Migration Locally

```powershell
npx supabase db reset
```

This applies all migrations to your local database.

### Verify in Studio

1. Go to http://localhost:54323
2. Click "Table Editor"
3. You should see the new tables: `teams`, `team_members`, `batch_claims`, `team_notifications`

---

## Common Commands

### Start/Stop Local Stack

```powershell
# Start (if stopped)
npx supabase start

# Stop (keeps data)
npx supabase stop

# Stop and delete all data
npx supabase stop --no-backup
```

### Check Status

```powershell
npx supabase status
```

Shows running services and URLs.

### Reset Database

```powershell
# Reset to migrations (deletes all data, reapplies migrations)
npx supabase db reset

# Reset to specific migration
npx supabase db reset --version 20260115123456
```

### View Logs

```powershell
# All services
npx supabase logs

# Specific service
npx supabase logs db
npx supabase logs api
```

---

## Environment Variables for Local Development

When running the dashboard locally, use these environment variables:

```bash
# .env.local (for Next.js dashboard)
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon key from supabase start output>
SUPABASE_SERVICE_ROLE_KEY=<service_role key from supabase start output>

# Database URL for local Supabase
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
```

**For production:** Use the remote Supabase URLs from your `.env` file.

---

## Troubleshooting

### Docker Not Running

**Error:** `Cannot connect to the Docker daemon`

**Fix:**
1. Open Docker Desktop
2. Wait for it to finish starting (whale icon in system tray)
3. Try `npx supabase start` again

### Port Already in Use

**Error:** `port 54321 is already allocated`

**Fix:**
1. Check what's using the port: `netstat -ano | findstr :54321`
2. Stop that process or change Supabase ports in `supabase/config.toml`

### Supabase Won't Start

**Error:** Various Docker errors

**Fix:**
1. Stop Supabase: `npx supabase stop`
2. Restart Docker Desktop
3. Try again: `npx supabase start`

### Migration Fails

**Error:** `migration failed: syntax error at or near...`

**Fix:**
1. Check SQL syntax in migration file
2. Test SQL in Studio SQL Editor first (http://localhost:54323)
3. Fix migration file
4. Run `npx supabase db reset` to reapply

---

## Next Steps

Once Supabase is running locally:

1. **Create Migration 016** - Define teams, batch_claims, team_notifications tables
2. **Apply Migration** - Run `npx supabase db reset` to create tables locally
3. **Test in Studio** - Verify tables and RLS policies work
4. **Push to Remote** - Run `npx supabase db push` to apply to remote Supabase
5. **Build Dashboard** - Create Next.js app using the Figma design

---

## Resources

- **Supabase CLI Docs:** https://supabase.com/docs/guides/cli
- **Local Development:** https://supabase.com/docs/guides/cli/local-development
- **Migrations:** https://supabase.com/docs/guides/cli/managing-environments
- **Docker Desktop:** https://docs.docker.com/desktop/

---

**Status:** Ready to start local development once Docker Desktop is installed
