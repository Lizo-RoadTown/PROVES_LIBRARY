"""
Web Processor - Extracts architecture from documentation websites.

Uses the extractor's fetch_webpage tool which:
1. Fetches the page content
2. Stores a snapshot in raw_snapshots table
3. Returns snapshot_id for lineage tracking

Context hints can come from:
- find_good_urls.py pre-scan (quality_score, preview_components, etc.)
- Manual context provided in source_config
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from bs4 import BeautifulSoup
import httpx

from .base import BaseProcessor, FetchResult


class WebProcessor(BaseProcessor):
    """
    Processor for web documentation pages.

    Handles:
    - F' Prime docs (nasa.github.io/fprime/)
    - PROVES Kit docs (docs.proveskit.space)
    - Any documentation website
    """

    @property
    def source_type(self) -> str:
        return "web"

    def fetch(
        self,
        source_config: Dict[str, Any],
        **kwargs
    ) -> FetchResult:
        """
        Fetch a web page and extract context hints.

        Args:
            source_config: Must contain "url" key
            **kwargs: Optional "skip_context_scan" to skip HTML analysis

        Returns:
            FetchResult with content and context hints
        """
        url = source_config.get("url")
        if not url:
            return FetchResult(
                snapshot_id="",
                raw_content="",
                context={},
                source_url="",
                success=False,
                error_message="No URL provided in source_config",
            )

        # Check if context was pre-computed (from urls_to_process table)
        pre_computed_context = source_config.get("context", {})

        # Fetch the page
        try:
            headers = {
                "User-Agent": "PROVES-Library-Curator/1.0 "
                              "(knowledge extraction for CubeSat safety)"
            }
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                html_content = response.text
        except httpx.HTTPStatusError as e:
            return FetchResult(
                snapshot_id="",
                raw_content="",
                context={},
                source_url=url,
                success=False,
                error_message=f"HTTP {e.response.status_code}",
            )
        except Exception as e:
            return FetchResult(
                snapshot_id="",
                raw_content="",
                context={},
                source_url=url,
                success=False,
                error_message=str(e),
            )

        # Generate a snapshot_id (the actual storage happens in fetch_webpage tool)
        # For now we generate a temporary one - the extractor will create the real one
        import uuid
        temp_snapshot_id = f"web-{uuid.uuid4().hex[:12]}"

        # Extract context if not pre-computed
        if pre_computed_context:
            context = pre_computed_context
        elif not kwargs.get("skip_context_scan", False):
            context = self._scan_for_context(url, html_content)
        else:
            context = {}

        return FetchResult(
            snapshot_id=temp_snapshot_id,
            raw_content=html_content,
            context=context,
            source_url=url,
            success=True,
        )

    def _scan_for_context(self, url: str, html_content: str) -> Dict[str, Any]:
        """
        Scan page content and extract context hints for the curator.

        This mirrors the logic from find_good_urls.py but is used for
        on-demand context extraction when not pre-scanned.

        Returns dict with:
        - components: List of component/module names found
        - interfaces: List of port/interface mentions
        - keywords: List of technical keywords
        - summary: Brief content summary
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
        except Exception:
            return {
                "components": [],
                "interfaces": [],
                "keywords": [],
                "summary": "",
            }

        # Remove script and style tags
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        text_content = soup.get_text()
        lower_text = text_content.lower()

        # Extract components (look for class names, module names)
        components = []

        # F' component patterns
        fprime_components = re.findall(
            r'\b([A-Z][a-zA-Z0-9]+)(?:Component(?:Impl|Ac)?|Port|Driver)\b',
            text_content
        )
        components.extend(fprime_components)

        # Generic component patterns
        generic_components = re.findall(
            r'\bclass\s+([A-Z][a-zA-Z0-9]+)\b',
            text_content
        )
        components.extend(generic_components)

        # Hardware components
        hardware_components = re.findall(
            r'\b([A-Z][a-zA-Z0-9]*'
            r'(?:Board|Chip|Sensor|Module|Controller))\b',
            text_content
        )
        components.extend(hardware_components)

        # Extract interfaces (ports, functions, APIs)
        interfaces = []

        # Port names
        port_patterns = re.findall(
            r'\b([a-zA-Z_][a-zA-Z0-9_]*Port)\b',
            text_content
        )
        interfaces.extend(port_patterns)

        # Function calls
        function_patterns = re.findall(
            r'\b([a-z_][a-zA-Z0-9_]*)\(\)',
            text_content
        )
        interfaces.extend(function_patterns[:10])

        # Common interface keywords
        if "tlmchan" in lower_text or "telemetry" in lower_text:
            interfaces.append("TlmChan")
        if "cmddisp" in lower_text or "command" in lower_text:
            interfaces.append("CmdDisp")
        if "i2c" in lower_text:
            interfaces.extend(["read()", "write()"])

        # Extract technical keywords
        keywords = []
        keyword_patterns = {
            "i2c", "spi", "uart", "gpio",
            "telemetry", "command", "event",
            "component", "driver", "port",
            "configuration", "parameter",
            "dependency", "interface",
            "power", "battery", "solar",
            "flight", "mode", "state",
        }

        for kw in keyword_patterns:
            if kw in lower_text:
                keywords.append(kw)

        # Create summary (first paragraph or heading)
        summary = ""
        first_p = soup.find("p")
        if first_p:
            summary = first_p.get_text().strip()[:200]
        else:
            first_h = soup.find(["h1", "h2", "h3"])
            if first_h:
                summary = first_h.get_text().strip()

        # Deduplicate and limit
        components = list(set(components))[:15]
        interfaces = list(set(interfaces))[:15]
        keywords = list(set(keywords))

        return {
            "components": components,
            "interfaces": interfaces,
            "keywords": keywords,
            "summary": summary,
        }

    def assess_quality(self, url: str, html_content: str) -> tuple:
        """
        Assess page quality (mirrors find_good_urls.py logic).

        Returns:
            (is_good, score, reason)
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
        except Exception as e:
            return (False, 0.0, f"Failed to parse HTML: {e}")

        # Remove non-content tags
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        text_content = soup.get_text()
        text_length = len(text_content.strip())
        lower_text = text_content.lower()
        lower_url = url.lower()

        # Quality checks
        if text_length < 500:
            return (False, 0.0, f"Too short ({text_length} chars)")

        # Skip index pages
        if "index.html" in lower_url or "index.md" in lower_url:
            if not any(x in lower_url for x in [
                "hardware", "software", "component", "module"
            ]):
                return (False, 0.0, "Generic index page")

        # Skip TOC pages
        links = soup.find_all("a")
        if len(links) > 50 and text_length < 2000:
            return (False, 0.0, "Table of contents")

        # Quality scoring (0.0 - 1.0)
        score = 0.5

        # Length score
        if text_length > 5000:
            score += 0.2
        elif text_length > 2000:
            score += 0.1

        # Technical content score
        technical_keywords = [
            "class", "function", "component", "interface", "port",
            "command", "telemetry", "driver", "i2c", "spi", "uart"
        ]
        tech_count = sum(1 for kw in technical_keywords if kw in lower_text)
        score += min(tech_count * 0.05, 0.3)

        # Code examples boost
        if soup.find("code") or soup.find("pre"):
            score += 0.1

        # Documentation structure boost
        if soup.find(["h2", "h3"]):
            score += 0.05

        score = min(score, 1.0)

        if score < 0.65:
            return (False, score, f"Quality score too low ({score:.2f})")

        return (True, score, f"Quality score: {score:.2f}")
