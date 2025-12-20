#!/usr/bin/env python3
"""
Library Indexer for PROVES Library
Parses markdown files from library/ and indexes them into the database
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml
from db_connector import get_db
from graph_manager import GraphManager


class LibraryIndexer:
    """Indexes markdown library entries into the database"""

    def __init__(self):
        self.db = get_db()
        self.gm = GraphManager()
        self.library_root = Path(__file__).parent.parent / 'library'

    def parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """
        Extract YAML frontmatter from markdown

        Returns:
            (frontmatter_dict, markdown_content)
        """
        # Check for frontmatter delimiters
        if not content.startswith('---'):
            return {}, content

        # Split on frontmatter delimiters
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content

        # Parse YAML
        try:
            frontmatter = yaml.safe_load(parts[1])
            markdown = parts[2].strip()
            return frontmatter or {}, markdown
        except yaml.YAMLError as e:
            print(f"Warning: Failed to parse frontmatter: {e}")
            return {}, content

    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract all metadata from a markdown file

        Returns:
            Dict with title, slug, frontmatter, content, etc.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        frontmatter, markdown = self.parse_frontmatter(raw_content)

        # Extract title (from frontmatter or first H1)
        title = frontmatter.get('title')
        if not title:
            h1_match = re.search(r'^#\s+(.+)$', markdown, re.MULTILINE)
            if h1_match:
                title = h1_match.group(1).strip()
            else:
                title = file_path.stem.replace('-', ' ').title()

        # Generate slug from filename
        slug = file_path.stem

        # Relative path from library/
        rel_path = file_path.relative_to(self.library_root)

        # Determine domain from directory structure
        domain_map = {
            'software': 'software',
            'build': 'build',
            'ops': 'ops',
            'systems': 'systems',
            'testing': 'testing'
        }
        domain = 'software'  # default
        for dir_name, domain_name in domain_map.items():
            if dir_name in str(rel_path):
                domain = domain_name
                break

        # Entry type (from frontmatter or infer from content)
        entry_type = frontmatter.get('type', 'pattern')

        # Generate summary (first paragraph or from frontmatter)
        summary = frontmatter.get('summary')
        if not summary:
            # Extract first paragraph
            paragraphs = [p.strip() for p in markdown.split('\n\n') if p.strip() and not p.strip().startswith('#')]
            if paragraphs:
                summary = paragraphs[0][:500]  # Limit to 500 chars

        return {
            'title': title,
            'slug': slug,
            'file_path': str(rel_path),
            'entry_type': entry_type,
            'domain': domain,
            'content': markdown,
            'summary': summary,
            'tags': frontmatter.get('tags', []),
            'sources': frontmatter.get('sources', []),
            'authors': frontmatter.get('authors', []),
            'date_captured': frontmatter.get('date_captured'),
            'artifact_repos': frontmatter.get('artifacts', {}).get('repos', []) if isinstance(frontmatter.get('artifacts'), dict) else [],
            'artifact_components': frontmatter.get('artifacts', {}).get('components', []) if isinstance(frontmatter.get('artifacts'), dict) else [],
            'artifact_tests': frontmatter.get('artifacts', {}).get('tests', []) if isinstance(frontmatter.get('artifacts'), dict) else [],
            'artifact_docs': frontmatter.get('artifacts', {}).get('docs', []) if isinstance(frontmatter.get('artifacts'), dict) else [],
        }

    def index_entry(self, file_path: Path, verbose: bool = True) -> Optional[str]:
        """
        Index a single markdown file into the database

        Returns:
            Entry UUID if successful, None otherwise
        """
        try:
            metadata = self.extract_metadata(file_path)

            if verbose:
                print(f"📄 Indexing: {metadata['title']} ({metadata['slug']})")

            # Check if already exists
            existing = self.db.fetch_one(
                "SELECT id FROM library_entries WHERE slug = %s",
                (metadata['slug'],)
            )

            if existing:
                if verbose:
                    print(f"  [WARN]  Entry already exists, skipping")
                return existing['id']

            # Insert into database
            query = """
                INSERT INTO library_entries (
                    title, slug, file_path, entry_type, domain,
                    content, summary, tags, sources, authors, date_captured,
                    artifact_repos, artifact_components, artifact_tests, artifact_docs
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """

            result = self.db.fetch_one(query, (
                metadata['title'],
                metadata['slug'],
                metadata['file_path'],
                metadata['entry_type'],
                metadata['domain'],
                metadata['content'],
                metadata['summary'],
                metadata['tags'],
                metadata['sources'],
                metadata['authors'],
                metadata['date_captured'],
                metadata['artifact_repos'],
                metadata['artifact_components'],
                metadata['artifact_tests'],
                metadata['artifact_docs']
            ))

            entry_id = result['id']

            if verbose:
                print(f"  [OK] Indexed successfully (ID: {entry_id})")

            return entry_id

        except Exception as e:
            print(f"  [ERROR] Error indexing {file_path}: {e}")
            return None

    def index_all(self, verbose: bool = True) -> Dict[str, Any]:
        """
        Index all markdown files in library/

        Returns:
            Statistics dict
        """
        if verbose:
            print(f"\n🔍 Scanning library directory: {self.library_root}")

        # Find all markdown files
        md_files = list(self.library_root.rglob('*.md'))

        if not md_files:
            print(f"[WARN]  No markdown files found in {self.library_root}")
            return {'total': 0, 'indexed': 0, 'skipped': 0, 'errors': 0}

        if verbose:
            print(f"Found {len(md_files)} markdown files\n")

        stats = {
            'total': len(md_files),
            'indexed': 0,
            'skipped': 0,
            'errors': 0
        }

        for file_path in md_files:
            entry_id = self.index_entry(file_path, verbose=verbose)
            if entry_id:
                stats['indexed'] += 1
            else:
                stats['errors'] += 1

        if verbose:
            print(f"\n📊 Indexing Summary:")
            print(f"  Total files: {stats['total']}")
            print(f"  Indexed: {stats['indexed']}")
            print(f"  Errors: {stats['errors']}")

        return stats

    def reindex_entry(self, slug: str, verbose: bool = True) -> bool:
        """
        Re-index a single entry (update existing)

        Args:
            slug: Entry slug to reindex

        Returns:
            True if successful
        """
        # Find file by slug
        md_files = list(self.library_root.rglob(f'{slug}.md'))

        if not md_files:
            print(f"[ERROR] File not found for slug: {slug}")
            return False

        file_path = md_files[0]

        try:
            metadata = self.extract_metadata(file_path)

            if verbose:
                print(f"📄 Re-indexing: {metadata['title']} ({metadata['slug']})")

            # Update existing entry
            query = """
                UPDATE library_entries
                SET title = %s,
                    file_path = %s,
                    entry_type = %s,
                    domain = %s,
                    content = %s,
                    summary = %s,
                    tags = %s,
                    sources = %s,
                    authors = %s,
                    date_captured = %s,
                    artifact_repos = %s,
                    artifact_components = %s,
                    artifact_tests = %s,
                    artifact_docs = %s,
                    updated_at = NOW()
                WHERE slug = %s
            """

            self.db.execute(query, (
                metadata['title'],
                metadata['file_path'],
                metadata['entry_type'],
                metadata['domain'],
                metadata['content'],
                metadata['summary'],
                metadata['tags'],
                metadata['sources'],
                metadata['authors'],
                metadata['date_captured'],
                metadata['artifact_repos'],
                metadata['artifact_components'],
                metadata['artifact_tests'],
                metadata['artifact_docs'],
                slug
            ))

            if verbose:
                print(f"  [OK] Re-indexed successfully")

            return True

        except Exception as e:
            print(f"  [ERROR] Error re-indexing: {e}")
            return False


if __name__ == '__main__':
    import sys

    indexer = LibraryIndexer()

    # Check command line args
    if len(sys.argv) > 1:
        if sys.argv[1] == '--reindex':
            # Reindex specific entry
            if len(sys.argv) < 3:
                print("Usage: python library_indexer.py --reindex <slug>")
                sys.exit(1)
            slug = sys.argv[2]
            indexer.reindex_entry(slug)
        else:
            print("Unknown command. Usage:")
            print("  python library_indexer.py          # Index all")
            print("  python library_indexer.py --reindex <slug>  # Reindex one")
    else:
        # Index all files
        indexer.index_all()
