"""
Extractor Sub-Agent
Specialized agent for extracting dependencies from documentation
"""
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langsmith import traceable


@tool
def read_document(doc_path: str) -> str:
    """Read and return the contents of a documentation file."""
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        chars = len(content)

        # Return full content up to 50K chars (enough for most docs)
        # This allows the extractor to actually analyze dependencies
        max_chars = 50000
        if chars > max_chars:
            content = content[:max_chars] + f"\n\n... (truncated, showing first {max_chars} of {chars} characters)"
        
        return f"Document: {doc_path}\nSize: {chars} characters, {len(lines)} lines\n\nFull Content:\n{content}"
    except Exception as e:
        return f"Error reading document: {str(e)}"


@tool
def extract_dependencies_using_claude(text: str, document_name: str) -> str:
    """
    Extract dependencies from text using Claude Sonnet 4.5.

    Identifies:
    - Component names
    - Dependency relationships (ERV types)
    - Criticality levels (HIGH/MEDIUM/LOW)
    - Context and reasoning
    """
    from langchain_anthropic import ChatAnthropic

    try:
        model = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            temperature=0,
        )

        extraction_prompt = f"""Analyze this technical documentation and extract ALL software/hardware dependencies.

Document: {document_name}

Text to analyze:
{text}

For each dependency, identify:
1. Component name (what depends on something else)
2. Depends on (what it needs/requires)
3. Relationship type: depends_on, requires, enables, conflicts_with, mitigates, causes
4. Criticality: HIGH (critical for operation), MEDIUM (important but has workarounds), LOW (nice-to-have)
5. Context (line numbers, specific details)

Format each dependency as:
- Component: <name>
- Depends on: <target>
- Type: <relationship>
- Criticality: <level>
- Context: <details>

Extract ALL dependencies, including:
- Runtime dependencies (code depends on libraries)
- Build dependencies (requires specific tools)
- Hardware dependencies (software needs specific hardware)
- Configuration dependencies
- Cross-system dependencies
"""

        response = model.invoke(extraction_prompt)
        return f"Extraction Results:\n\n{response.content}"

    except Exception as e:
        return f"Error during extraction: {str(e)}"


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
        read_document,
        extract_dependencies_using_claude,
    ]

    agent = create_react_agent(model, tools)
    return agent
