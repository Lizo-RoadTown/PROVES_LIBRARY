#!/usr/bin/env python3
"""Check recent crawl jobs and source configs."""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

# Get recent jobs
result = supabase.from_("crawl_jobs").select("id, source_id, status, error_message, created_at").order("created_at", desc=True).limit(5).execute()
print("Recent crawl jobs:")
for job in result.data:
    print(f"  {job['id'][:8]}... status={job['status']} error={job.get('error_message', 'none')}")

# Get source config for the jobs
if result.data:
    source_id = result.data[0]["source_id"]
    source = supabase.from_("team_sources").select("name, source_type, source_config").eq("id", source_id).single().execute()
    print(f"\nSource: {source.data['name']} ({source.data['source_type']})")
    print(f"Config: {source.data['source_config']}")
