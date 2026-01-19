"""Check OAuth provider configuration in Supabase."""
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

SUPABASE_URL = os.environ.get('VITE_SUPABASE_URL') or 'https://guigtpwxlqwueylbbcpx.supabase.co'

print("=" * 60)
print("OAUTH CONFIGURATION CHECK")
print("=" * 60)

# Check Supabase auth settings endpoint
auth_settings_url = f"{SUPABASE_URL}/auth/v1/settings"
try:
    response = requests.get(auth_settings_url)
    if response.ok:
        settings = response.json()
        print(f"\n✓ Supabase Auth API responding")
        print(f"\nExternal providers configured:")

        external = settings.get('external', {})
        for provider in ['google', 'github', 'email']:
            enabled = external.get(provider, False)
            status = "✓ Enabled" if enabled else "✗ Disabled"
            print(f"  {provider}: {status}")

        print(f"\nOther settings:")
        print(f"  Site URL: {settings.get('site_url', 'Not set')}")
        print(f"  URI Allow List: {settings.get('uri_allow_list', [])}")
    else:
        print(f"✗ Failed to get auth settings: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
except Exception as e:
    print(f"✗ Error connecting to Supabase: {e}")

# Check redirect URL configuration
print("\n" + "=" * 60)
print("REDIRECT URL CHECK")
print("=" * 60)

expected_urls = [
    'http://localhost:5173',
    'http://localhost:5173/',
    'https://proves-curation-dashboard.vercel.app',
]

print(f"\nExpected redirect URLs (configure in Supabase Dashboard):")
for url in expected_urls:
    print(f"  - {url}")

print(f"\nTo configure:")
print(f"  1. Go to: https://supabase.com/dashboard/project/guigtpwxlqwueylbbcpx/auth/url-configuration")
print(f"  2. Add your redirect URLs to the 'Redirect URLs' list")
print(f"  3. For Google: https://supabase.com/dashboard/project/guigtpwxlqwueylbbcpx/auth/providers")
print(f"  4. For GitHub: Same providers page")
