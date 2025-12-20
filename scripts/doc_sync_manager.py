#!/usr/bin/env python3
"""
Documentation Sync Manager for PROVES Library
Handles incremental updates from F´ and PROVES Kit GitHub repos
"""
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from db_connector import get_db
from library_indexer import LibraryIndexer


class DocSyncManager:
    """
    Manages documentation synchronization from GitHub repos

    Features:
    - Initial clone and full index
    - Incremental updates via Git diff
    - Change tracking (commit SHAs)
    - File-to-node mapping
    - Orphaned relationship cleanup
    """

    def __init__(self, cache_dir: Path = None):
        """
        Initialize the sync manager

        Args:
            cache_dir: Directory to clone repos into (default: .cache/repos/)
        """
        self.db = get_db()
        self.indexer = LibraryIndexer()

        # Cache directory for cloned repos
        if cache_dir is None:
            self.cache_dir = Path(__file__).parent.parent / '.cache' / 'repos'
        else:
            self.cache_dir = cache_dir

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Repos to sync
        self.repos = {
            'fprime': {
                'url': 'https://github.com/nasa/fprime.git',
                'name': 'F Prime',
                'doc_paths': ['docs/', 'README.md'],  # Where docs live
                'local_path': self.cache_dir / 'fprime'
            },
            'proves_kit': {
                'url': None,  # To be filled in by user
                'name': 'PROVES Kit',
                'doc_paths': ['docs/', 'README.md'],
                'local_path': self.cache_dir / 'proves_kit'
            }
        }

    # ============================================
    # INITIAL SETUP
    # ============================================

    def initial_sync(self, repo_key: str) -> Dict:
        """
        Initial clone and full indexing of a repository

        Args:
            repo_key: 'fprime' or 'proves_kit'

        Returns:
            Stats dict
        """
        repo_config = self.repos[repo_key]
        local_path = repo_config['local_path']

        print(f"[*] Initial sync: {repo_config['name']}")

        # Clone if doesn't exist
        if not local_path.exists():
            print(f"[*] Cloning {repo_config['url']}...")
            subprocess.run(
                ['git', 'clone', '--depth', '1', repo_config['url'], str(local_path)],
                check=True
            )
            print(f"[OK] Cloned to {local_path}")
        else:
            print(f"[*] Repo already cloned at {local_path}")

        # Get current commit SHA
        commit_sha = self._get_current_commit(local_path)
        print(f"[*] Current commit: {commit_sha[:8]}")

        # Process all documentation
        stats = self._process_repo_docs(repo_key, repo_config, is_initial=True)

        # Store sync metadata
        self._store_sync_metadata(repo_key, commit_sha, stats)

        print(f"[OK] Initial sync complete")
        print(f"     Files indexed: {stats['indexed']}")
        print(f"     Nodes created: {stats.get('nodes_created', 0)}")

        return stats

    def _get_current_commit(self, repo_path: Path) -> str:
        """Get current HEAD commit SHA"""
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    def _process_repo_docs(
        self,
        repo_key: str,
        repo_config: Dict,
        is_initial: bool = False
    ) -> Dict:
        """
        Process documentation files from a repo

        Args:
            repo_key: Repo identifier
            repo_config: Repo configuration
            is_initial: True for initial sync, False for incremental

        Returns:
            Statistics dict
        """
        local_path = repo_config['local_path']
        doc_paths = repo_config['doc_paths']

        stats = {
            'total': 0,
            'indexed': 0,
            'errors': 0,
            'nodes_created': 0
        }

        # Find all markdown files in doc paths
        md_files = []
        for doc_path in doc_paths:
            full_path = local_path / doc_path
            if full_path.is_dir():
                md_files.extend(full_path.rglob('*.md'))
            elif full_path.is_file():
                md_files.append(full_path)

        stats['total'] = len(md_files)

        print(f"[*] Found {len(md_files)} markdown files")

        # TODO: Process each file
        # For now, just count them
        # In full implementation:
        # - Extract metadata
        # - Create library entries
        # - Build knowledge graph nodes
        # - Create relationships

        return stats

    def _store_sync_metadata(self, repo_key: str, commit_sha: str, stats: Dict):
        """
        Store sync metadata in database for change tracking

        Creates a sync_metadata table to track:
        - Last synced commit SHA
        - Last sync timestamp
        - Files processed
        - Statistics
        """
        # Check if sync_metadata table exists, create if not
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS sync_metadata (
                repo_key TEXT PRIMARY KEY,
                last_commit_sha TEXT NOT NULL,
                last_sync_at TIMESTAMP DEFAULT NOW(),
                files_indexed INTEGER DEFAULT 0,
                nodes_created INTEGER DEFAULT 0,
                sync_stats JSONB
            )
        """)

        # Upsert sync metadata
        self.db.execute("""
            INSERT INTO sync_metadata (repo_key, last_commit_sha, files_indexed, nodes_created, sync_stats)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (repo_key)
            DO UPDATE SET
                last_commit_sha = EXCLUDED.last_commit_sha,
                last_sync_at = NOW(),
                files_indexed = EXCLUDED.files_indexed,
                nodes_created = EXCLUDED.nodes_created,
                sync_stats = EXCLUDED.sync_stats
        """, (
            repo_key,
            commit_sha,
            stats.get('indexed', 0),
            stats.get('nodes_created', 0),
            json.dumps(stats)
        ))

    # ============================================
    # INCREMENTAL UPDATES
    # ============================================

    def check_for_updates(self, repo_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if repo has updates since last sync

        Args:
            repo_key: 'fprime' or 'proves_kit'

        Returns:
            (has_updates, old_sha, new_sha)
        """
        repo_config = self.repos[repo_key]
        local_path = repo_config['local_path']

        if not local_path.exists():
            print(f"[WARN] Repo not cloned yet: {repo_key}")
            return False, None, None

        # Get last synced commit from database
        metadata = self.db.fetch_one(
            "SELECT last_commit_sha FROM sync_metadata WHERE repo_key = %s",
            (repo_key,)
        )

        if not metadata:
            print(f"[WARN] No sync metadata for {repo_key}, needs initial sync")
            return False, None, None

        old_sha = metadata['last_commit_sha']

        # Fetch latest from remote
        print(f"[*] Fetching updates for {repo_config['name']}...")
        subprocess.run(
            ['git', 'fetch', 'origin'],
            cwd=local_path,
            check=True,
            capture_output=True
        )

        # Get remote HEAD
        result = subprocess.run(
            ['git', 'rev-parse', 'origin/main'],
            cwd=local_path,
            capture_output=True,
            text=True
        )

        # Fallback to master if main doesn't exist
        if result.returncode != 0:
            result = subprocess.run(
                ['git', 'rev-parse', 'origin/master'],
                cwd=local_path,
                capture_output=True,
                text=True,
                check=True
            )

        new_sha = result.stdout.strip()

        has_updates = old_sha != new_sha

        if has_updates:
            print(f"[*] Updates available: {old_sha[:8]} -> {new_sha[:8]}")
        else:
            print(f"[OK] Already up-to-date at {old_sha[:8]}")

        return has_updates, old_sha, new_sha

    def incremental_update(self, repo_key: str) -> Dict:
        """
        Perform incremental update (only changed files)

        Args:
            repo_key: 'fprime' or 'proves_kit'

        Returns:
            Stats dict
        """
        has_updates, old_sha, new_sha = self.check_for_updates(repo_key)

        if not has_updates:
            return {'status': 'up-to-date', 'updated': 0}

        repo_config = self.repos[repo_key]
        local_path = repo_config['local_path']

        print(f"[*] Updating {repo_config['name']}...")

        # Pull changes
        subprocess.run(
            ['git', 'pull', 'origin'],
            cwd=local_path,
            check=True,
            capture_output=True
        )

        # Get list of changed files
        changed_files = self._get_changed_files(local_path, old_sha, new_sha)

        print(f"[*] Changed files: {len(changed_files)}")

        # Filter to only markdown files in doc paths
        doc_paths = repo_config['doc_paths']
        md_changes = [
            f for f in changed_files
            if f.endswith('.md') and any(f.startswith(dp) for dp in doc_paths)
        ]

        print(f"[*] Markdown changes: {len(md_changes)}")

        stats = {
            'status': 'updated',
            'updated': len(md_changes),
            'files': md_changes
        }

        # TODO: Reprocess changed files
        # For each changed file:
        # - Re-extract metadata
        # - Update library entry
        # - Update graph nodes
        # - Update relationships

        # Update sync metadata
        self._store_sync_metadata(repo_key, new_sha, stats)

        print(f"[OK] Incremental update complete")

        return stats

    def _get_changed_files(self, repo_path: Path, old_sha: str, new_sha: str) -> List[str]:
        """Get list of files that changed between commits"""
        result = subprocess.run(
            ['git', 'diff', '--name-only', old_sha, new_sha],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        files = result.stdout.strip().split('\n')
        return [f for f in files if f]  # Filter empty strings

    # ============================================
    # SCHEDULING
    # ============================================

    def daily_sync(self):
        """
        Daily sync routine (call this from cron/scheduler)

        Checks all configured repos for updates and processes incrementally
        """
        print(f"[*] Starting daily sync at {datetime.now()}")

        results = {}

        for repo_key in self.repos.keys():
            if self.repos[repo_key]['url'] is None:
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

    sync_manager = DocSyncManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'init':
            # Initial sync
            repo_key = sys.argv[2] if len(sys.argv) > 2 else 'fprime'
            sync_manager.initial_sync(repo_key)

        elif command == 'update':
            # Incremental update
            repo_key = sys.argv[2] if len(sys.argv) > 2 else 'fprime'
            sync_manager.incremental_update(repo_key)

        elif command == 'daily':
            # Daily sync (both repos)
            sync_manager.daily_sync()

        elif command == 'check':
            # Just check for updates
            repo_key = sys.argv[2] if len(sys.argv) > 2 else 'fprime'
            has_updates, old, new = sync_manager.check_for_updates(repo_key)
            print(f"Updates available: {has_updates}")

        else:
            print("Unknown command. Usage:")
            print("  python doc_sync_manager.py init [repo_key]")
            print("  python doc_sync_manager.py update [repo_key]")
            print("  python doc_sync_manager.py daily")
            print("  python doc_sync_manager.py check [repo_key]")
    else:
        print("Usage:")
        print("  python doc_sync_manager.py init fprime       # Initial clone and index")
        print("  python doc_sync_manager.py update fprime     # Incremental update")
        print("  python doc_sync_manager.py daily             # Daily sync all repos")
        print("  python doc_sync_manager.py check fprime      # Check for updates")
