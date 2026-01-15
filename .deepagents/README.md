# DeepAgents Configuration

This folder contains the DeepAgents configuration for the PROVES Library project.

## Structure

```
.deepagents/
├── agents/          # Agent definitions and configurations
├── tools/           # Custom tools for agents
├── workflows/       # LangGraph workflow definitions
├── prompts/         # Prompt templates
└── README.md        # This file
```

## Purpose

The DeepAgents framework provides:
- **Agent Middleware**: TodoList, Filesystem, SubAgent tools
- **LangGraph Integration**: Build custom agentic workflows
- **RAG Capabilities**: Retrieval-augmented generation with agent decision-making

## Key Components

### Agents
Agent configurations for different tasks in the PROVES pipeline:
- Document extraction agents
- Verification agents
- Canonicalization agents

### Tools
Custom tools that agents can use:
- Database query tools
- Documentation retrieval tools
- Notion integration tools

### Workflows
LangGraph workflows that orchestrate agent behavior:
- Agentic RAG for documentation queries
- Multi-step extraction pipelines
- Human-in-the-loop verification flows

## Usage

See individual subdirectories for specific configurations and examples.

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Agentic RAG Tutorial](https://docs.langchain.com/docs/langgraph/tutorials/agentic-rag)
- [DeepAgents Package](https://pypi.org/project/deepagents/)
