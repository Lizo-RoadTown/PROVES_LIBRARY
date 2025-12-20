#!/usr/bin/env python3
"""
GitHub API Documentation Sync Manager
Fetches F´ and PROVES Kit docs directly from GitHub API (no local clones)
"""
import os
import base64
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
from db_connector import get_db


class GitHubDocSync:
    """
    Sync documentation from GitHub repos using GitHub API

    Benefits:
    - No local storage needed
    - Always fetches latest from source
    - Incremental updates via commit SHA tracking
    - Works within GitHub API rate limits

    Rate Limits:
    - Authenticated: 5000 requests/hour
    - Unauthenticated: 60 requests/hour
    - Recommendation: Use personal access token
    """

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub API sync manager

        Args:
            github_token: GitHub personal access token (optional but recommended)
                         Get one at: https://github.com/settings/tokens
        """
        self.db = get_db()
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')

        # Setup headers for API requests
        self.headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'

        # Repo configurations
        self.repos = {
            'fprime': {
                'owner': 'nasa',
                'repo': 'fprime',
                'name': 'F Prime',
                'doc_paths': ['docs/'],  # Paths to fetch
                'branch': 'main'
            },
            'proves_kit': {
                'owner': None,  # To be filled in
                'repo': None,   # To be filled in
                'name': 'PROVES Kit',
                'doc_paths': ['docs/'],
                'branch': 'main'
            }
        }

        self.base_url = 'https://api.github.com'

    # ============================================
    # GITHUB API METHODS
    # ============================================

    def _api_request(self, endpoint: str) -> Dict:
        """
        Make GitHub API request with rate limit handling

        Args:
            endpoint: API endpoint (e.g., '/repos/nasa/fprime/commits/main')

        Returns:
            JSON response
        """
        url = f"{self.base_url}{endpoint}"

        response = requests.get(url, headers=self.headers)

        # Check rate limit
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        if remaining < 100:
            print(f"[WARN] GitHub API rate limit low: {remaining} requests remaining")

        if response.status_code == 403 and 'rate limit' in response.text.lower():
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            wait_seconds = reset_time - int(time.time())
            print(f"[ERROR] Rate limit exceeded. Resets in {wait_seconds} seconds")
            raise Exception(f"GitHub API rate limit exceeded")

        response.raise_for_status()
        return response.json()

    def get_latest_commit_sha(self, repo_key: str) -> str:
        """
        Get latest commit SHA for a repo

        Args:
            repo_key: 'fprime' or 'proves_kit'

        Returns:
            Commit SHA
        """
        config = self.repos[repo_key]
        endpoint = f"/repos/{config['owner']}/{config['repo']}/commits/{config['branch']}"

        commit_data = self._api_request(endpoint)
        return commit_data['sha']

    def get_file_content(self, repo_key: str, file_path: str) -> str:
        """
        Fetch file content from GitHub

        Args:
            repo_key: 'fprime' or 'proves_kit'
            file_path: Path to file in repo (e.g., 'docs/UserGuide.md')

        Returns:
            File content (decoded)
        """
        config = self.repos[repo_key]
        endpoint = f"/repos/{config['owner']}/{config['repo']}/contents/{file_path}"

        params = {'ref': config['branch']}
        url = f"{self.base_url}{endpoint}"

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        data = response.json()

        # Decode base64 content
        content_b64 = data['content']
        content = base64.b64decode(content_b64).decode('utf-8')

        return content

    def list_files_recursive(self, repo_key: str, path: str = '') -> List[Dict]:
        """
        List all files in a directory (recursively)

        Args:
            repo_key: 'fprime' or 'proves_kit'
            path: Directory path (default: root)

        Returns:
            List of file metadata dicts
        """
        config = self.repos[repo_key]
        endpoint = f"/repos/{config['owner']}/{config['repo']}/contents/{path}"

        try:
            items = self._api_request(endpoint)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"[WARN] Path not found: {path}")
                return []
            raise

        files = []

        for item in items:
            if item['type'] == 'file':
                files.append({
                    'path': item['path'],
                    'name': item['name'],
                    'size': item['size'],
                    'sha': item['sha'],
                    'url': item['url']
                })
            elif item['type'] == 'dir':
                # Recursively fetch subdirectory
                subfiles = self.list_files_recursive(repo_key, item['path'])
                files.extend(subfiles)

        return files

    def get_changed_files(
        self,
        repo_key: str,
        old_sha: str,
        new_sha: str
    ) -> List[str]:
        """
        Get list of files changed between two commits

        Args:
            repo_key: 'fprime' or 'proves_kit'
            old_sha: Previous commit SHA
            new_sha: New commit SHA

        Returns:
            List of changed file paths
        """
        config = self.repos[repo_key]
        endpoint = f"/repos/{config['owner']}/{config['repo']}/compare/{old_sha}...{new_sha}"

        data = self._api_request(endpoint)

        changed_files = []
        for file_data in data.get('files', []):
            # Filter to only markdown files in doc paths
            file_path = file_data['filename']
            if file_path.endswith('.md'):
                for doc_path in config['doc_paths']:
                    if file_path.startswith(doc_path):
                        changed_files.append(file_path)
                        break

        return changed_files

    # ============================================
    # SYNC OPERATIONS
    # ============================================

    def initial_sync(self, repo_key: str) -> Dict:
        """
        Initial fetch and index of all documentation

        Args:
            repo_key: 'fprime' or 'proves_kit'

        Returns:
            Statistics dict
        """
        config = self.repos[repo_key]
        print(f"[*] Initial sync: {config['name']}")

        # Get current commit SHA
        commit_sha = self.get_latest_commit_sha(repo_key)
        print(f"[*] Latest commit: {commit_sha[:8]}")

        # Get all markdown files in doc paths
        all_files = []
        for doc_path in config['doc_paths']:
            print(f"[*] Fetching files from {doc_path}...")
            files = self.list_files_recursive(repo_key, doc_path)
            # Filter to markdown
            md_files = [f for f in files if f['name'].endswith('.md')]
            all_files.extend(md_files)

        print(f"[*] Found {len(all_files)} markdown files")

        stats = {
            'total': len(all_files),
            'indexed': 0,
            'errors': 0
        }

        # Process each file
        for file_meta in all_files:
            try:
                print(f"[*] Processing {file_meta['path']}...")

                # Fetch content
                content = self.get_file_content(repo_key, file_meta['path'])

                # TODO: Process and index
                # For now, just count
                stats['indexed'] += 1

                # Sleep to avoid rate limiting
                time.sleep(0.1)  # 10 files/second = well within limits

            except Exception as e:
                print(f"[ERROR] Failed to process {file_meta['path']}: {e}")
                stats['errors'] += 1

        # Store sync metadata
        self._store_sync_metadata(repo_key, commit_sha, stats)

        print(f"[OK] Initial sync complete")
        print(f"     Files indexed: {stats['indexed']}")
        print(f"     Errors: {stats['errors']}")

        return stats

    def check_for_updates(self, repo_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if repo has updates since last sync

        Args:
            repo_key: 'fprime' or 'proves_kit'

        Returns:
            (has_updates, old_sha, new_sha)
        """
        # Get last synced commit from database
        metadata = self.db.fetch_one(
            "SELECT last_commit_sha FROM sync_metadata WHERE repo_key = %s",
            (repo_key,)
        )

        if not metadata:
            print(f"[WARN] No sync metadata for {repo_key}, needs initial sync")
            return False, None, None

        old_sha = metadata['last_commit_sha']

        # Get latest commit from GitHub
        new_sha = self.get_latest_commit_sha(repo_key)

        has_updates = old_sha != new_sha

        if has_updates:
            print(f"[*] Updates available: {old_sha[:8]} -> {new_sha[:8]}")
        else:
            print(f"[OK] Already up-to-date at {old_sha[:8]}")

        return has_updates, old_sha, new_sha

    def incremental_update(self, repo_key: str) -> Dict:
        """
        Fetch and process only changed files

        Args:
            repo_key: 'fprime' or 'proves_kit'

        Returns:
            Statistics dict
        """
        has_updates, old_sha, new_sha = self.check_for_updates(repo_key)

        if not has_updates:
            return {'status': 'up-to-date', 'updated': 0}

        config = self.repos[repo_key]
        print(f"[*] Updating {config['name']}...")

        # Get changed files
        changed_files = self.get_changed_files(repo_key, old_sha, new_sha)

        print(f"[*] Changed markdown files: {len(changed_files)}")

        stats = {
            'status': 'updated',
            'updated': 0,
            'errors': 0,
            'files': changed_files
        }

        # Process each changed file
        for file_path in changed_files:
            try:
                print(f"[*] Updating {file_path}...")

                # Fetch content
                content = self.get_file_content(repo_key, file_path)

                # TODO: Reprocess and update database
                stats['updated'] += 1

                time.sleep(0.1)  # Rate limit friendly

            except Exception as e:
                print(f"[ERROR] Failed to update {file_path}: {e}")
                stats['errors'] += 1

        # Update sync metadata
        self._store_sync_metadata(repo_key, new_sha, stats)

        print(f"[OK] Incremental update complete")
        print(f"     Files updated: {stats['updated']}")

        return stats

    def _store_sync_metadata(self, repo_key: str, commit_sha: str, stats: Dict):
        """Store sync metadata in database"""
        # Create table if not exists
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS sync_metadata (
                repo_key TEXT PRIMARY KEY,
                last_commit_sha TEXT NOT NULL,
                last_sync_at TIMESTAMP DEFAULT NOW(),
                files_indexed INTEGER DEFAULT 0,
                sync_stats JSONB
            )
        """)

        import json

        # Upsert
        self.db.execute("""
            INSERT INTO sync_metadata (repo_key, last_commit_sha, files_indexed, sync_stats)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (repo_key)
            DO UPDATE SET
                last_commit_sha = EXCLUDED.last_commit_sha,
                last_sync_at = NOW(),
                files_indexed = EXCLUDED.files_indexed,
                sync_stats = EXCLUDED.sync_stats
        """, (
            repo_key,
            commit_sha,
            stats.get('indexed', stats.get('updated', 0)),
            json.dumps(stats)
        ))

    # ============================================
    # SCHEDULING
    # ============================================

    def daily_sync(self):
        """Daily sync routine for all configured repos"""
        print(f"[*] Starting daily sync at {datetime.now()}")

        results = {}

        for repo_key, config in self.repos.items():
            if config['owner'] is None or config['repo'] is None:
                print(f"[SKIP] {repo_key} not configured")
                continue

            try:
                # Check if initial sync done
                metadata = self.db.fetch_one(
                    "SELECT last_commit_sha FROM sync_metadata WHERE repo_key = %s",
                    (repo_key,)
                )

                if metadata:
                    # Incremental update
                    results[repo_key] = self.incremental_update(repo_key)
                else:
                    # Initial sync needed
                    results[repo_key] = self.initial_sync(repo_key)

            except Exception as e:
                print(f"[ERROR] Failed to sync {repo_key}: {e}")
                results[repo_key] = {'status': 'error', 'error': str(e)}

        print(f"[OK] Daily sync complete")
        return results


if __name__ == '__main__':
    import sys

    # Check for GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("[WARN] GITHUB_TOKEN not set. Using unauthenticated requests (60/hour limit)")
        print("       Get a token at: https://github.com/settings/tokens")
        print("       Add to .env: GITHUB_TOKEN=ghp_xxxxx")

    sync = GitHubDocSync(github_token)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'init':
            # Initial sync
            repo_key = sys.argv[2] if len(sys.argv) > 2 else 'fprime'
            sync.initial_sync(repo_key)

        elif command == 'update':
            # Incremental update
            repo_key = sys.argv[2] if len(sys.argv) > 2 else 'fprime'
            sync.incremental_update(repo_key)

        elif command == 'daily':
            # Daily sync all repos
            sync.daily_sync()

        elif command == 'check':
            # Check for updates
            repo_key = sys.argv[2] if len(sys.argv) > 2 else 'fprime'
            has_updates, old, new = sync.check_for_updates(repo_key)
            print(f"Updates available: {has_updates}")

        elif command == 'test':
            # Test API connection
            try:
                sha = sync.get_latest_commit_sha('fprime')
                print(f"[OK] GitHub API working. F' latest commit: {sha[:8]}")
            except Exception as e:
                print(f"[ERROR] GitHub API test failed: {e}")

        else:
            print("Unknown command")

    else:
        print("GitHub API Documentation Sync")
        print("=" * 50)
        print()
        print("Usage:")
        print("  python github_doc_sync.py test               # Test API connection")
        print("  python github_doc_sync.py init fprime        # Initial fetch and index")
        print("  python github_doc_sync.py update fprime      # Incremental update")
        print("  python github_doc_sync.py check fprime       # Check for updates")
        print("  python github_doc_sync.py daily              # Daily sync all repos")
        print()
        print("Setup:")
        print("  1. Get GitHub token: https://github.com/settings/tokens")
        print("  2. Add to .env: GITHUB_TOKEN=ghp_xxxxx")
        print("  3. Run: python github_doc_sync.py init fprime")
