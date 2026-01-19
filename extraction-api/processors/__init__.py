"""
PROVES Extraction Processors

Each processor handles a specific source type (web, discord, notion, etc.)
but all use the shared task_builder for FRAMES-aware prompts and
agent_v3.graph for the actual extraction pipeline.

Available processors:
- WebProcessor: Documentation websites
- DiscordProcessor: Discord channels/threads
- NotionProcessor: Notion pages/databases
"""

from .base import BaseProcessor
from .web import WebProcessor

__all__ = ["BaseProcessor", "WebProcessor"]
