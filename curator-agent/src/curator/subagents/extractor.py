"""
Extractor Sub-Agent
Specialized agent for extracting dependencies from documentation
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../scripts'))

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langsmith import traceable
from dependency_extractor import process_document_pipeline


@tool
def chunk_document(doc_path: str) -> str:
    """Read and chunk a documentation file for processing."""
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simple chunking
        paragraphs = content.split('\n\n')
        num_chunks = (len(paragraphs) + 9) // 10  # ~10 paragraphs per chunk

        return f"Document loaded: {len(content)} characters, {len(paragraphs)} paragraphs, ~{num_chunks} chunks"
    except Exception as e:
        return f"Error reading document: {str(e)}"


@tool
def extract_dependencies_from_text(text: str, document_name: str) -> str:
    """Extract dependencies from a text chunk using LLM."""
    from dependency_extractor import DependencyExtractor

    try:
        extractor = DependencyExtractor()
        deps = extractor.extract_dependencies(text, document_name)

        summary = f"Extracted {len(deps)} dependencies:\n"
        for dep in deps[:5]:  # Show first 5
            summary += f"  - {dep.get('component')} {dep.get('relationship_type')} {dep.get('depends_on')} ({dep.get('criticality')})\n"

        if len(deps) > 5:
            summary += f"  ... and {len(deps) - 5} more\n"

        return summary
    except Exception as e:
        return f"Error extracting: {str(e)}"


@traceable(name="extractor_subagent")
def create_extractor_agent():
    """
    Create the extractor sub-agent

    This agent specializes in:
    - Reading documentation files
    - Chunking large documents
    - Extracting dependencies using LLM
    - Identifying ERV relationship types
    - Assessing criticality levels
    """
    model = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0.1,
    )

    tools = [
        chunk_document,
        extract_dependencies_from_text,
    ]

    agent = create_react_agent(model, tools)
    return agent
