# Agentic Systems

This directory contains the autonomous agents that power knowledge curation and code generation in the PROVES Library system.

## Overview

The PROVES Library uses **agentic systems** (AI-powered autonomous agents) to handle complex tasks that require reasoning, context understanding, and decision-making. These agents work alongside the core infrastructure (library, MCP server, scanner) but are kept separate because they:

1. Use LLM-based reasoning (Claude, GPT-4, or local models)
2. Operate autonomously with human-in-the-loop review
3. Learn and improve from feedback
4. Can be swapped, upgraded, or run in parallel

## Agent Architecture

```
agents/
├── curator/              # Knowledge curation agent
│   ├── agent.py         # Main curator logic
│   ├── prompts/         # LLM prompts for normalization
│   ├── validators/      # Quality checks
│   └── README.md
├── builder/              # Code generation agent
│   ├── agent.py         # Main builder logic
│   ├── templates/       # Code templates
│   ├── generators/      # Component generators
│   └── README.md
└── shared/               # Shared utilities
    ├── llm_client.py    # LLM API wrapper
    ├── prompt_utils.py  # Prompt engineering helpers
    └── feedback_loop.py # Learning from rejections
```

## Agent Responsibilities

### Curator Agent (`agents/curator/`)

**Purpose:** Transform raw knowledge captures into structured library entries

**Workflow:**
1. Receive raw capture from risk scanner
2. Parse context, resolution, and metadata
3. Extract citations from sources
4. Generate proper frontmatter (tags, categorization)
5. Format markdown content
6. Detect duplicates or conflicts with existing entries
7. Present normalized entry for human review
8. Learn from approval/rejection patterns

**Key Logic:**
- Citation extraction and validation
- Tag suggestion based on content
- Duplicate detection (semantic similarity)
- Entry quality scoring
- Feedback learning loop

**LLM Usage:**
- Summarize technical context
- Extract key concepts for tags
- Suggest related entries
- Normalize writing style

### Builder Agent (`agents/builder/`)

**Purpose:** Generate F Prime components, tests, and configs from library patterns

**Workflow:**
1. Receive request (from scanner or user)
2. Look up relevant patterns in library via MCP
3. Select appropriate template
4. Generate code using pattern knowledge
5. Add inline documentation with citations
6. Create test scaffold
7. Validate generated code
8. Present for human review

**Key Logic:**
- Pattern → Component mapping
- Template selection and instantiation
- Code validation (syntax, style)
- Test generation
- Integration with existing codebases

**LLM Usage:**
- Understand natural language requirements
- Adapt patterns to specific contexts
- Generate edge case tests
- Write clear documentation

## Shared Infrastructure

### LLM Client (`shared/llm_client.py`)

Wrapper for different LLM providers:
- Anthropic Claude (via API)
- OpenAI GPT-4 (via API)
- Local models (via Ollama or similar)

**Features:**
- Prompt templating
- Token usage tracking
- Cost monitoring
- Rate limiting
- Error handling and retries

### Feedback Loop (`shared/feedback_loop.py`)

Learns from human approval/rejection:
- Tracks what gets approved vs rejected
- Identifies patterns in feedback
- Adjusts prompts and thresholds
- Improves over time

## Human-in-the-Loop Philosophy

**Critical principle:** Agents propose, humans approve.

- Agents never commit directly to library
- All entries require human review
- Rejections are learning opportunities
- Humans can override any agent decision
- Transparency in agent reasoning (show prompts, show sources)

## Development Phases

### Phase 1 (Current): Foundation
- Core infrastructure (library, MCP, scanner)
- No agents yet

### Phase 2: Curator Agent
- Implement basic normalization
- Add citation extraction
- Build review workflow
- Integrate with scanner

### Phase 3: Builder Agent
- F Prime component generator
- Test scaffold generator
- Config template system

### Phase 4: Advanced Features
- Feedback learning
- Multi-agent collaboration
- Autonomous pattern discovery

## Agent Configuration

Agents are configured via `agents/config.yaml`:

```yaml
curator:
  enabled: true
  llm_provider: anthropic  # anthropic | openai | ollama
  model: claude-sonnet-3-5
  temperature: 0.2
  max_tokens: 4000
  review_required: true
  quality_threshold: 0.7

builder:
  enabled: false  # Not yet implemented
  llm_provider: anthropic
  model: claude-sonnet-3-5
  temperature: 0.3
  validate_code: true
  generate_tests: true

shared:
  cost_limit_daily: 10.00  # USD
  cache_prompts: true
  log_level: INFO
```

## Running Agents

### Curator Agent

```bash
# Process a raw capture
cd agents/curator
python agent.py --input ../../risk-scanner/captures/draft-abc123.md --output review

# Batch process all pending captures
python agent.py --batch --pending
```

### Builder Agent

```bash
# Generate component from pattern
cd agents/builder
python agent.py --pattern software-001 --output generated/

# Generate from natural language
python agent.py --describe "I2C manager with multiplexer support" --output generated/
```

## Testing Agents

```bash
# Test curator normalization
pytest agents/curator/tests/

# Test builder generation
pytest agents/builder/tests/

# Test with mock LLM (no API calls)
pytest agents/ --mock-llm
```

## Cost Management

Agents track LLM API costs:
- Per-request cost logging
- Daily spend limits
- Warnings at thresholds
- Cost reports

Check costs:
```bash
python agents/shared/cost_tracker.py --report --last-30-days
```

## Next Steps

1. **Implement Curator Agent** (see `agents/curator/README.md`)
2. Add prompt templates for normalization
3. Build citation extraction logic
4. Create review workflow integration
5. Test with real captures from scanner

## Design Principles

1. **Transparency:** Always show agent reasoning and sources
2. **Safety:** Humans approve all outputs
3. **Learning:** Improve from feedback
4. **Cost-conscious:** Track and limit API usage
5. **Vendor-neutral:** Support multiple LLM providers
6. **Modular:** Agents can run independently or together
