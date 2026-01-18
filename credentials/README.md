# Credentials Folder

This folder stores API credentials for team collaboration tools. **All credential files are git-ignored for security.**

## Required Credentials

### Google Drive/Docs/Sheets
- **File**: `google-service-account.json`
- **Setup**: See [Team Sources Setup Guide](../docs/TEAM_SOURCES_SETUP.md#google-drive-setup)

### Notion & Discord
These use API tokens stored in `.env` (not files in this folder):
- `NOTION_API_KEY` - Notion integration token
- `DISCORD_BOT_TOKEN` - Discord bot token

## Security Notes

- Never commit credential files to git
- The `.gitignore` in this folder prevents accidental commits
- For deployment, use environment variables instead of files
- Rotate credentials if accidentally exposed
