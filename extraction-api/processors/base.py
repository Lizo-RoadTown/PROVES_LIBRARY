"""
Base Processor - Abstract interface for all extraction processors.

All processors share:
1. task_builder.py for FRAMES-aware prompt construction
2. agent_v3.graph for the Extractor → Validator → Storage pipeline

Each processor implements:
1. fetch() - Get content and context from source
2. process() - Run the full extraction pipeline
"""

import uuid
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class FetchResult:
    """Result from fetching a source."""
    snapshot_id: str
    raw_content: str
    context: Dict[str, Any]
    source_url: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class ProcessResult:
    """Result from processing an extraction job."""
    job_id: str
    source_url: str
    status: str  # "success", "failed", "rejected"
    stage: str  # "fetch", "extraction", "validation", "storage"
    message: str
    extractions_count: int = 0
    error_message: Optional[str] = None


class BaseProcessor(ABC):
    """
    Abstract base class for all source processors.

    Implements the Template Method pattern:
    - fetch() is abstract - each processor implements source-specific fetching
    - process() is concrete - shared pipeline invocation logic
    """

    def __init__(self):
        """Initialize processor with lazy-loaded dependencies."""
        self._graph = None
        self._task_builder = None

    @property
    def graph(self):
        """Lazy load the extraction graph (heavy dependencies)."""
        if self._graph is None:
            # Import from the V3 pipeline
            import sys
            from pathlib import Path

            # Add V3 path
            api_dir = Path(__file__).parent.parent
            project_root = api_dir.parent
            version3_dir = project_root / "production" / "Version 3"
            sys.path.insert(0, str(version3_dir))

            from agent_v3 import graph
            self._graph = graph
        return self._graph

    @property
    def task_builder(self):
        """Lazy load the task builder."""
        if self._task_builder is None:
            import task_builder
            self._task_builder = task_builder
        return self._task_builder

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return the source type identifier (e.g., 'web', 'discord', 'notion')."""
        pass

    @abstractmethod
    def fetch(
        self,
        source_config: Dict[str, Any],
        **kwargs
    ) -> FetchResult:
        """
        Fetch content from the source.

        Args:
            source_config: Source-specific configuration
                - For web: {"url": "https://..."}
                - For discord: {"channel_id": "...", "thread_id": "..."}
                - For notion: {"page_id": "..."}
            **kwargs: Additional processor-specific options

        Returns:
            FetchResult with snapshot_id, content, and context hints
        """
        pass

    def process(
        self,
        job_id: str,
        source_config: Dict[str, Any],
        team_id: Optional[str] = None,
        source_id: Optional[str] = None,
        context_override: Optional[Dict] = None,
    ) -> ProcessResult:
        """
        Run the full extraction pipeline for a job.

        This is the shared processing logic used by all processors:
        1. Fetch content from source
        2. Build FRAMES-aware task prompt
        3. Invoke agent_v3.graph (Extractor → Validator → Storage)
        4. Return result

        Args:
            job_id: Unique job identifier
            source_config: Source-specific configuration
            team_id: Optional team ID for multi-tenant tracking
            source_id: Optional source ID linking to team_sources
            context_override: Optional context to use instead of fetched context

        Returns:
            ProcessResult with status, stage, and message
        """
        # Step 1: Fetch content
        try:
            fetch_result = self.fetch(source_config)
            if not fetch_result.success:
                return ProcessResult(
                    job_id=job_id,
                    source_url=fetch_result.source_url,
                    status="failed",
                    stage="fetch",
                    message=f"Fetch failed: {fetch_result.error_message}",
                    error_message=fetch_result.error_message,
                )
        except Exception as e:
            return ProcessResult(
                job_id=job_id,
                source_url=source_config.get("url", "unknown"),
                status="failed",
                stage="fetch",
                message=f"Fetch error: {str(e)}",
                error_message=str(e),
            )

        # Step 2: Build FRAMES-aware task prompt
        context = context_override or fetch_result.context
        task_prompt = self.task_builder.build_extraction_task(
            url=fetch_result.source_url,
            context=context,
            source_type=self.source_type,
            team_id=team_id,
            source_id=source_id,
        )

        # Step 3: Invoke extraction pipeline
        try:
            thread_id = f"api-{job_id}-{uuid.uuid4().hex[:8]}"
            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 100,
            }

            result = self.graph.invoke(
                {"messages": [{"role": "user", "content": task_prompt}]},
                config,
            )

            # Parse result
            last_message = result["messages"][-1]
            final_message = (
                last_message.content
                if hasattr(last_message, "content")
                else last_message.get("content", str(last_message))
            )

            # Check for rejection
            if "REJECTED" in final_message.upper():
                return ProcessResult(
                    job_id=job_id,
                    source_url=fetch_result.source_url,
                    status="rejected",
                    stage="validation",
                    message=final_message[:500],
                )

            # Check for extraction failure
            if (
                "snapshot_id" not in final_message.lower()
                or "no couplings" in final_message.lower()
            ):
                return ProcessResult(
                    job_id=job_id,
                    source_url=fetch_result.source_url,
                    status="failed",
                    stage="extraction",
                    message="No couplings extracted",
                )

            # Success
            return ProcessResult(
                job_id=job_id,
                source_url=fetch_result.source_url,
                status="success",
                stage="storage",
                message=final_message[:500],
                extractions_count=self._count_extractions(final_message),
            )

        except Exception as e:
            return ProcessResult(
                job_id=job_id,
                source_url=fetch_result.source_url,
                status="failed",
                stage="extraction",
                message=f"Pipeline error: {str(e)}",
                error_message=str(e),
            )

    def _count_extractions(self, message: str) -> int:
        """
        Attempt to count extractions from the final message.
        This is a rough estimate based on candidate_key mentions.
        """
        import re
        # Count candidate_key occurrences - handles **candidate_key:** markdown format
        matches = re.findall(r'\*?\*?candidate_key\*?\*?:\*?\*?\s*`?([A-Za-z0-9_:\-\.]+)`?', message, re.IGNORECASE)
        return len(matches)
