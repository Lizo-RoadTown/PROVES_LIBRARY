# Curation Dashboard Platform Setup Guide

**Purpose:** Step-by-step guide to sign up for platform services and configure environment variables

**Date:** 2026-01-15

**Estimated Time:** 30-45 minutes

---

## Overview

You need to sign up for 3 services to run the curation dashboard:

1. **Supabase** - Database + Auth + Real-time (FREE tier available)
2. **Vercel** - Next.js hosting (FREE tier available)
3. **Resend** - Email notifications (FREE tier available)

**Total Cost:** $0 for development, $45-65/month for production with 8+ teams

---

## Step 1: Sign Up for Supabase

**What:** Database, authentication, and real-time subscriptions in one platform

**Link:** https://supabase.com

### Sign Up Steps

1. Go to https://supabase.com
2. Click **"Start your project"**
3. Sign up with **GitHub** (recommended) or email
4. Click **"New Project"**

### Create Project

1. **Organization:** Create new organization (e.g., "PROVES Library")
2. **Project Name:** `proves-curation-dashboard`
3. **Database Password:** Generate strong password (save this!)
4. **Region:** Choose closest to your users (e.g., `us-east-1`)
5. **Pricing Plan:** Free (for now)
6. Click **"Create new project"**

⏱️ Wait 2-3 minutes for database to provision

### Get Your API Keys

Once project is ready:

1. Click **"Project Settings"** (gear icon in sidebar)
2. Click **"API"** in sidebar
3. You'll see:

   **Project URL:**
   ```
   https://abcdefghijklmnop.supabase.co
   ```
   Copy this → Use for `NEXT_PUBLIC_SUPABASE_URL`

   **anon public key:**
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBh...
   ```
   Copy this → Use for `NEXT_PUBLIC_SUPABASE_ANON_KEY`

   **service_role key:** (Click "Reveal" first)
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBh...
   ```
   ⚠️ **KEEP THIS SECRET!** → Use for `SUPABASE_SERVICE_ROLE_KEY`

### Get Database Connection String

1. Click **"Database"** in Project Settings sidebar
2. Scroll to **"Connection string"**
3. Select **"URI"** tab
4. Copy the connection string:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghijklmnop.supabase.co:5432/postgres
   ```
5. Replace `[YOUR-PASSWORD]` with your database password from earlier
6. Use for `SUPABASE_DATABASE_URL` (if using Supabase instead of Neon)

### Enable Email Authentication

1. Click **"Authentication"** in sidebar
2. Click **"Providers"**
3. **Email** should be enabled by default
4. Configure email settings:
   - **Enable Email Confirmations:** ON (for production)
   - **Enable Email Confirmations:** OFF (for development/testing)

---

## Step 2: Sign Up for Vercel

**What:** Hosting platform for Next.js dashboard (auto-deploys from GitHub)

**Link:** https://vercel.com

### Sign Up Steps

1. Go to https://vercel.com
2. Click **"Start Deploying"** or **"Sign Up"**
3. Choose **"Continue with GitHub"**
4. Authorize Vercel to access your GitHub account

### Don't Deploy Yet!

We'll deploy after we create the Next.js dashboard repo. For now, just having an account is enough.

**Pricing:** Free tier includes:
- Unlimited deployments
- 100 GB bandwidth/month
- Serverless functions
- Automatic HTTPS

---

## Step 3: Sign Up for Resend

**What:** Email API for sending notifications (claim expiry, new extractions, etc.)

**Link:** https://resend.com

### Sign Up Steps

1. Go to https://resend.com
2. Click **"Start Building"** or **"Sign Up"**
3. Sign up with email or GitHub
4. Verify your email address

### Get Your API Key

1. After sign-up, you'll land on the dashboard
2. Click **"API Keys"** in sidebar
3. Click **"Create API Key"**
4. **Name:** `PROVES Dashboard`
5. **Permission:** Full Access
6. Click **"Create"**
7. Copy the key (starts with `re_`):
   ```
   re_ABC123def456GHI789jkl012MNO345pqr678
   ```
   ⚠️ **Save this immediately!** You can't see it again.
8. Use for `RESEND_API_KEY`

### Configure Email Domain (Optional for Production)

For development, you can use Resend's test domain (`onboarding@resend.dev`).

For production (when you want to send real emails):

1. Click **"Domains"** in sidebar
2. Click **"Add Domain"**
3. Enter your domain (e.g., `yourdomain.com`)
4. Add DNS records to your domain provider (Resend provides exact records)
5. Wait for verification (usually 5-10 minutes)
6. Use `noreply@yourdomain.com` for `EMAIL_FROM`

**For now (development):** Use `onboarding@resend.dev`

**Pricing:** Free tier includes:
- 3,000 emails/month
- 100 emails/day
- API access

---

## Step 4: Update Your `.env` File

Now that you have all the keys, update your `.env` file:

```bash
# Copy the example file
cp .env.example .env
```

Then edit `.env` and add your keys:

```bash
# ============================================
# CURATION DASHBOARD PLATFORM
# ============================================

# Supabase (Database + Auth + Real-time)
NEXT_PUBLIC_SUPABASE_URL=https://abcdefghijklmnop.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3M...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3M...

# Supabase Database Connection (if using Supabase instead of Neon)
SUPABASE_DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.abcdefghijklmnop.supabase.co:5432/postgres

# Resend (Email Notifications)
RESEND_API_KEY=re_ABC123def456GHI789jkl012MNO345pqr678

# Email Configuration
EMAIL_FROM=onboarding@resend.dev  # For development
# EMAIL_FROM=noreply@yourdomain.com  # For production (after domain verification)

# Dashboard Configuration
NEXT_PUBLIC_DASHBOARD_URL=http://localhost:3000
```

---

## Step 5: Migrate Your Database to Supabase (Optional)

If you want to use Supabase instead of Neon, migrate your data:

### Export from Neon

```bash
# Set your Neon connection string
export NEON_DATABASE_URL="postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/proves"

# Export database
pg_dump $NEON_DATABASE_URL > proves_backup.sql
```

### Import to Supabase

```bash
# Set your Supabase connection string (use the one from Step 1)
export SUPABASE_DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@db.abcdefghijklmnop.supabase.co:5432/postgres"

# Import database
psql $SUPABASE_DATABASE_URL < proves_backup.sql
```

### Verify Migration

1. Go to Supabase dashboard
2. Click **"Table Editor"** in sidebar
3. You should see all your tables:
   - `core_entities`
   - `staging_extractions`
   - `raw_snapshots`
   - `validation_decisions`
   - etc.

---

## Step 6: Test Your Configuration

Create a simple test script to verify everything works:

**`test_platform.py`**
```python
import os
from dotenv import load_dotenv
import requests

load_dotenv()

# Test Supabase connection
supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

print("Testing Supabase connection...")
response = requests.get(
    f"{supabase_url}/rest/v1/",
    headers={"apikey": supabase_key}
)
print(f"✓ Supabase: {response.status_code == 200}")

# Test Resend
resend_key = os.getenv("RESEND_API_KEY")
print("\nTesting Resend API key...")
response = requests.get(
    "https://api.resend.com/emails",
    headers={"Authorization": f"Bearer {resend_key}"}
)
print(f"✓ Resend: {response.status_code in [200, 403]}")  # 403 is OK (no permission to list)

print("\n✓ All platform services configured!")
```

Run it:
```bash
python test_platform.py
```

---

## Troubleshooting

### Supabase Connection Fails

**Error:** "Could not connect to database"

**Fix:**
1. Check database password is correct
2. Verify connection string format
3. Make sure database is fully provisioned (wait 2-3 minutes after creation)

### Resend API Key Invalid

**Error:** "Invalid API key"

**Fix:**
1. Make sure you copied the full key (starts with `re_`)
2. Check for extra spaces or line breaks
3. Regenerate key in Resend dashboard if needed

### Email Sending Fails

**Error:** "Email address not verified"

**Fix:**
1. Use `onboarding@resend.dev` for development (no verification needed)
2. For production, verify your domain in Resend dashboard
3. Wait 5-10 minutes after adding DNS records

---

## Next Steps

Once you have all keys configured:

1. **Create Next.js Dashboard** - Convert Figma design to Next.js
2. **Set Up Database Schema** - Run Migration 016 (teams, batch_claims)
3. **Connect Supabase Auth** - Add login/signup pages
4. **Deploy to Vercel** - Push to GitHub, auto-deploy

See: `docs/CURATION_DASHBOARD_REQUIREMENTS.md` for full feature list

---

## Security Best Practices

⚠️ **NEVER commit `.env` to Git!**

Your `.gitignore` should include:
```
.env
.env.local
.env.*.local
```

✅ **DO commit `.env.example`** (with placeholder values)

For production secrets:
1. Add environment variables in Vercel dashboard
2. Use Vercel's secure environment variable storage
3. Never hardcode API keys in code

---

## Cost Summary

### Development (Free Tier)
- Supabase: **$0** (Free tier)
- Vercel: **$0** (Hobby plan)
- Resend: **$0** (3,000 emails/month)
- **Total: $0/month**

### Production (8 Teams, Moderate Usage)
- Supabase Pro: **$25/month** (includes DB + Auth + Real-time)
- Vercel Pro: **$20/month** (custom domains, advanced features)
- Resend: **$0-20/month** (depends on email volume)
- **Total: $45-65/month**

### Production (50 Teams, Heavy Usage)
- Supabase Pro: **$25/month** (same, scales well)
- Vercel Pro: **$20/month** (same)
- Resend Pro: **$20/month** (higher email volume)
- **Total: $65/month** (scales without infrastructure changes)

---

## Support Resources

- **Supabase Docs:** https://supabase.com/docs
- **Vercel Docs:** https://vercel.com/docs
- **Resend Docs:** https://resend.com/docs
- **Next.js Docs:** https://nextjs.org/docs

---

**Status:** Platform services ready, credentials configured, ready to build dashboard
