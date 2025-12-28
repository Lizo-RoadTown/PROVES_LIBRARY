"""
Setup Notion Integration for Curator Agent

This script creates the three required Notion databases and updates your .env file.

Usage:
    python setup_notion.py

Follow the prompts to provide your Notion parent page ID.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('\\', 1)[0])

from src.curator.notion_sync import setup_notion_databases

if __name__ == "__main__":
    print("\n" + "="*80)
    print("CURATOR AGENT - NOTION INTEGRATION SETUP")
    print("="*80)
    print("\nThis script will create three Notion databases:")
    print("  1. Curator Errors Log")
    print("  2. Staging Extractions Review")
    print("  3. Curator Run Reports")
    print("\nYou'll need a Notion page ID where these databases will be created.")
    print("\nTo get your Notion page ID:")
    print("  1. Open Notion and create/open a page for the curator databases")
    print("  2. Click 'Share' → 'Copy link'")
    print("  3. Extract the ID from the URL")
    print("     Example URL: https://notion.so/Curator-Databases-1234567890abcdef...")
    print("     Page ID: 1234567890abcdef (the hex string after the page name)")
    print("\n" + "="*80)
    print()

    # Get parent page ID from user
    parent_page_id = input("Enter your Notion parent page ID: ").strip()

    if not parent_page_id:
        print("\nError: Page ID is required!")
        sys.exit(1)

    # Run setup
    try:
        setup_notion_databases(parent_page_id)

        print("\n" + "="*80)
        print("SUCCESS! Notion integration is ready.")
        print("="*80)
        print("\nNext steps:")
        print("\n1. Grant database access to your integration:")
        print("   - Visit https://www.notion.so/profile/integrations")
        print("   - Find your integration")
        print("   - Click 'Capabilities' and ensure 'Read content', 'Update content', and 'Insert content' are enabled")
        print()
        print("2. Test the integration:")
        print("   - Run: python -c \"from src.curator.notion_sync import NotionSync; s=NotionSync(); print('✓ Connected!')\"")
        print()
        print("3. Start the webhook server:")
        print("   - Run: python notion_webhook_server.py")
        print("   - In another terminal: ngrok http 8000")
        print("   - Copy the ngrok HTTPS URL")
        print()
        print("4. Configure Notion webhook:")
        print("   - Visit https://www.notion.so/profile/integrations")
        print("   - Select your integration → 'Webhooks' tab")
        print("   - Create subscription with your ngrok URL: https://YOUR_URL.ngrok.io/webhook/notion")
        print("   - Copy the verification token from webhook server logs")
        print("   - Verify the webhook subscription")
        print()
        print("5. Run the curator:")
        print("   - python production/process_extractions.py --limit 5")
        print("   - Check Notion - extractions should appear automatically!")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
