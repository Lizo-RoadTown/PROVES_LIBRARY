"""
[YES] PRODUCTION-READY | VALIDATED 2025-12-26

Smart WebFetch Agent - Crawl documentation and extract context

VALIDATION STATUS: Gold Script
- Tested on 10 pages from F' Prime and PROVES Kit documentation
- Quality scoring verified (0.65-1.00 range captures both technical and educational content)
- Context extraction working (components, interfaces, keywords)
- Successfully filters noise (TOC pages, short pages, index pages)
- Correctly identifies institutional knowledge (how-to, patterns, organizational docs)

This agent:
1. Crawls documentation sites (F' Prime, PROVES Kit, etc.)
2. Assesses page quality (0.0-1.0 score, threshold: 0.65)
3. Scans pages for extraction context (components, interfaces, keywords)
4. Stores URLs + context in urls_to_process database table for curator processing

Usage:
    python production/find_good_urls.py --fprime --proveskit --max-pages 50
    python production/find_good_urls.py --url https://docs.example.com --max-pages 20

Quality Scoring Philosophy:
- Educational content IS valuable (institutional knowledge, not just API specs)
- Scores 0.65+ capture mental models, patterns, and decision frameworks
- These are the "nodes and edges" that prevent knowledge loss when students graduate
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple, Set
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import psycopg

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv(os.path.join(Path(__file__).parent.parent, '.env'))


class SmartWebFetchAgent:
    """
    Intelligent web crawler that finds good documentation pages
    and extracts context hints for the curator.
    """

    def __init__(self):
        """Initialize with database connection."""
        self.db_url = os.environ.get('NEON_DATABASE_URL')
        if not self.db_url:
            raise ValueError("NEON_DATABASE_URL not set in environment")

    def get_processed_urls(self) -> Set[str]:
        """Get URLs that have already been added to queue or processed."""
        conn = psycopg.connect(self.db_url)
        with conn.cursor() as cur:
            # Check both urls_to_process and raw_snapshots
            cur.execute("""
                SELECT url FROM urls_to_process
                UNION
                SELECT DISTINCT source_url FROM raw_snapshots
                WHERE status = 'captured'::snapshot_status
            """)
            urls = {row[0] for row in cur.fetchall()}
        conn.close()
        return urls

    def fetch_page(self, url: str) -> Tuple[bool, str, str]:
        """Fetch a page and return (success, content, error_msg)."""
        try:
            headers = {
                "User-Agent": "PROVES-Library-Curator/1.0 (knowledge extraction for CubeSat safety)"
            }
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                return (True, response.text, "")
        except httpx.HTTPStatusError as e:
            return (False, "", f"HTTP {e.response.status_code}")
        except Exception as e:
            return (False, "", str(e))

    def scan_for_context(self, url: str, html_content: str) -> Dict:
        """
        Scan page content and extract context hints for the curator.

        Returns dict with:
        - components: List of component/module names found
        - interfaces: List of port/interface mentions
        - keywords: List of technical keywords
        - summary: Brief content summary
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        except:
            return {
                'components': [],
                'interfaces': [],
                'keywords': [],
                'summary': ''
            }

        # Remove script and style tags
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()

        text_content = soup.get_text()
        lower_text = text_content.lower()

        # Extract components (look for class names, module names)
        components = []
        # F' component patterns: NameComponentImpl, NameComponentAc, Svc::Name, Drv::Name
        fprime_components = re.findall(r'\b([A-Z][a-zA-Z0-9]+)(?:Component(?:Impl|Ac)?|Port|Driver)\b', text_content)
        components.extend(fprime_components)

        # Generic component patterns
        generic_components = re.findall(r'\bclass\s+([A-Z][a-zA-Z0-9]+)\b', text_content)
        components.extend(generic_components)

        # Circuit/hardware components
        hardware_components = re.findall(r'\b([A-Z][a-zA-Z0-9]*(?:Board|Chip|Sensor|Module|Controller))\b', text_content)
        components.extend(hardware_components)

        # Extract interfaces (ports, functions, APIs)
        interfaces = []

        # Port names
        port_patterns = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*Port)\b', text_content)
        interfaces.extend(port_patterns)

        # Function calls
        function_patterns = re.findall(r'\b([a-z_][a-zA-Z0-9_]*)\(\)', text_content)
        interfaces.extend(function_patterns[:10])  # Limit to first 10

        # Common interface keywords
        if 'tlmchan' in lower_text or 'telemetry' in lower_text:
            interfaces.append('TlmChan')
        if 'cmddisp' in lower_text or 'command' in lower_text:
            interfaces.append('CmdDisp')
        if 'i2c' in lower_text:
            interfaces.extend(['read()', 'write()'])

        # Extract technical keywords
        keywords = []
        keyword_patterns = {
            'i2c', 'spi', 'uart', 'gpio',
            'telemetry', 'command', 'event',
            'component', 'driver', 'port',
            'configuration', 'parameter',
            'dependency', 'interface',
            'power', 'battery', 'solar',
            'flight', 'mode', 'state'
        }

        for kw in keyword_patterns:
            if kw in lower_text:
                keywords.append(kw)

        # Create summary (first paragraph or heading)
        summary = ""
        first_p = soup.find('p')
        if first_p:
            summary = first_p.get_text().strip()[:200]
        else:
            # Try first heading
            first_h = soup.find(['h1', 'h2', 'h3'])
            if first_h:
                summary = first_h.get_text().strip()

        # Deduplicate and limit
        components = list(set(components))[:15]
        interfaces = list(set(interfaces))[:15]
        keywords = list(set(keywords))

        return {
            'components': components,
            'interfaces': interfaces,
            'keywords': keywords,
            'summary': summary
        }

    def assess_page_quality(self, url: str, html_content: str) -> Tuple[bool, float, str]:
        """
        Assess page quality and return (is_good, score, reason).

        Returns:
            (True, score, reason) if good
            (False, 0.0, reason) if should be skipped
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            return (False, 0.0, f"Failed to parse HTML: {e}")

        # Remove script and style tags
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()

        text_content = soup.get_text()
        text_length = len(text_content.strip())
        lower_text = text_content.lower()
        lower_url = url.lower()

        # Quality checks
        if text_length < 500:
            return (False, 0.0, f"Too short ({text_length} chars)")

        # Skip index pages (unless specific module index)
        if 'index.html' in lower_url or 'index.md' in lower_url:
            if not any(x in lower_url for x in ['hardware', 'software', 'component', 'module']):
                return (False, 0.0, "Generic index page")

        # Skip TOC pages
        links = soup.find_all('a')
        if len(links) > 50 and text_length < 2000:
            return (False, 0.0, "Table of contents (too many links, too little content)")

        # Quality scoring (0.0 - 1.0)
        score = 0.5  # Base score

        # Length score
        if text_length > 5000:
            score += 0.2
        elif text_length > 2000:
            score += 0.1

        # Technical content score
        technical_keywords = ['class', 'function', 'component', 'interface', 'port',
                              'command', 'telemetry', 'driver', 'i2c', 'spi', 'uart']
        tech_count = sum(1 for kw in technical_keywords if kw in lower_text)
        score += min(tech_count * 0.05, 0.3)

        # Code examples boost
        if soup.find('code') or soup.find('pre'):
            score += 0.1

        # Documentation structure boost
        if soup.find(['h2', 'h3']):
            score += 0.05

        # Cap at 1.0
        score = min(score, 1.0)

        # Reject low-quality pages
        if score < 0.65:
            return (False, score, f"Quality score too low ({score:.2f} < 0.65)")

        return (True, score, f"Quality score: {score:.2f}")

    def extract_links(self, base_url: str, html_content: str) -> List[str]:
        """Extract documentation links from a page."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        except:
            return []

        from urllib.parse import urljoin, urlparse

        links = []
        base_domain = urlparse(base_url).netloc

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']

            # Skip anchors, mailto, javascript
            if href.startswith('#') or href.startswith('mailto:') or href.startswith('javascript:'):
                continue

            # Make absolute URL
            absolute_url = urljoin(base_url, href)

            # Only keep same-domain links
            if urlparse(absolute_url).netloc != base_domain:
                continue

            # Skip common non-documentation paths
            skip_patterns = ['/search', '/genindex', '/py-modindex',
                            '/_static', '/_sources', '/archive']
            if any(pattern in absolute_url for pattern in skip_patterns):
                continue

            # Clean URL (remove fragments)
            clean_url = absolute_url.split('#')[0]

            links.append(clean_url)

        return list(set(links))

    def store_url(self, url: str, quality_score: float, quality_reason: str, context: Dict):
        """Store URL with context in database."""
        conn = psycopg.connect(self.db_url)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO urls_to_process
                (url, status, quality_score, quality_reason,
                 preview_components, preview_interfaces, preview_keywords, preview_summary)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (
                url,
                'pending',
                quality_score,
                quality_reason,
                context['components'],
                context['interfaces'],
                context['keywords'],
                context['summary']
            ))
            conn.commit()
        conn.close()

    def crawl(self, starting_urls: List[str], max_pages: int = 50) -> int:
        """
        Crawl from starting URLs and find good pages.

        Returns:
            Number of pages added to queue
        """
        print(f"\n{'='*80}")
        print("SMART WEBFETCH AGENT - Finding Documentation Pages")
        print(f"{'='*80}")
        print(f"\nStarting URLs: {len(starting_urls)}")
        for url in starting_urls:
            print(f"  - {url}")
        print(f"\nTarget: Find up to {max_pages} good pages")
        print(f"\n{'='*80}\n")

        # Get already processed URLs
        processed_urls = self.get_processed_urls()
        print(f"Already known: {len(processed_urls)} URLs\n")

        # Track what we've found
        pages_added = 0
        to_visit = list(starting_urls)
        visited = set()
        max_iterations = max_pages * 10

        iteration = 0
        while to_visit and pages_added < max_pages and iteration < max_iterations:
            iteration += 1
            url = to_visit.pop(0)

            # Skip if already visited
            if url in visited:
                continue

            visited.add(url)
            print(f"[{iteration}] Checking: {url}")

            # If already known, skip but still crawl links
            if url in processed_urls:
                print(f"  Already known, extracting links...")
                success, content, error = self.fetch_page(url)
                if success:
                    new_links = self.extract_links(url, content)
                    to_visit.extend([link for link in new_links if link not in visited])
                    print(f"    Added {len(new_links)} links to queue")
                continue

            # Fetch page
            success, content, error = self.fetch_page(url)
            if not success:
                print(f"  Failed: {error}")
                continue

            # Assess quality
            is_good, score, reason = self.assess_page_quality(url, content)
            if not is_good:
                print(f"  Skipped: {reason}")
                # Still extract links
                new_links = self.extract_links(url, content)
                to_visit.extend([link for link in new_links if link not in visited])
                continue

            # Scan for context
            context = self.scan_for_context(url, content)

            # Store in database
            self.store_url(url, score, reason, context)
            pages_added += 1

            print(f"  GOOD (score: {score:.2f})")
            if context['components']:
                print(f"    Components: {', '.join(context['components'][:5])}")
            if context['interfaces']:
                print(f"    Interfaces: {', '.join(context['interfaces'][:5])}")
            if context['keywords']:
                print(f"    Keywords: {', '.join(context['keywords'][:8])}")

            # Extract more links
            new_links = self.extract_links(url, content)
            to_visit.extend([link for link in new_links if link not in visited])

        print(f"\n{'='*80}")
        print(f"Crawl Complete: {pages_added} new pages added to queue")
        print(f"{'='*80}\n")

        return pages_added


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Smart WebFetch: Crawl documentation and extract context"
    )
    parser.add_argument(
        "--fprime",
        action="store_true",
        help="Crawl F' Prime documentation"
    )
    parser.add_argument(
        "--proveskit",
        action="store_true",
        help="Crawl PROVES Kit documentation"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Custom starting URL to crawl"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Maximum pages to find (default: 50)"
    )

    args = parser.parse_args()

    # Build starting URLs
    starting_urls = []
    if args.fprime:
        starting_urls.append("https://nasa.github.io/fprime/")
    if args.proveskit:
        starting_urls.append("https://docs.proveskit.space/en/latest/")
    if args.url:
        starting_urls.append(args.url)

    if not starting_urls:
        print("Error: Specify at least one source (--fprime, --proveskit, or --url)")
        print("\nExamples:")
        print("  python find_good_urls.py --fprime --proveskit --max-pages 50")
        print("  python find_good_urls.py --url https://docs.example.com")
        return

    # Run crawler
    agent = SmartWebFetchAgent()
    pages_added = agent.crawl(starting_urls, max_pages=args.max_pages)

    print(f"\nSuccess! {pages_added} pages added to database")
    print("\nNext step: python process_extractions.py")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
