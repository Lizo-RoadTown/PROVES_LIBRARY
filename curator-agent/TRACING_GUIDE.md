# Tracing Guide for Curator Agent

This guide explains how to set up and use OpenTelemetry tracing with the PROVES Curator Agent to observe agent behavior, debug issues, and monitor performance.

## Quick Start

### 1. Start the AI Toolkit Trace Collector

Before running your agent, open the trace viewer in VS Code:

```powershell
# In VS Code Command Palette (Ctrl+Shift+P)
AI ML Studio: Tracing - Open Trace Viewer
```

This starts the local OTLP collector at `http://localhost:4317` (gRPC) and opens the interactive trace viewer.

### 2. Install Tracing Dependencies

The required packages are already listed in `pyproject.toml`:

```bash
cd curator-agent
pip install -e .
```

This installs:
- `agent-framework` - Microsoft Agent Framework with OpenTelemetry support
- `opentelemetry-api` - OpenTelemetry Python API
- `opentelemetry-sdk` - OpenTelemetry SDK
- `opentelemetry-exporter-otlp` - OTLP exporter for gRPC/HTTP

### 3. Run Your Agent

The tracing is automatically set up in `run_with_approval.py`:

```bash
python run_with_approval.py
```

You should see:
```
✓ OpenTelemetry tracing enabled
  Endpoint: http://localhost:4317
  Service: curator-agent
  Sensitive data: Captured (prompts/completions included)
```

### 4. View Traces

Traces appear in the AI Toolkit Trace Viewer in real-time:
- **Trace timeline** - Shows execution flow and timing
- **Span details** - Inspect individual operations (LLM calls, tool invocations, sub-agents)
- **Attributes** - View prompts, completions, and other metadata
- **Performance metrics** - Latency, token usage, costs

## What Gets Traced Automatically

The Agent Framework automatically instruments:

1. **LLM Calls** - Claude model invocations with prompts/completions
2. **Tool Calls** - Sub-agent tool invocations (extractor, validator, storage)
3. **Workflow Operations** - LangGraph node execution and state transitions
4. **Errors** - Exceptions and retries
5. **Timing** - Latency for each operation

## Configuration Options

### Environment Variable Setup

Add to `.env`:

```bash
# OTLP Endpoint (optional - defaults to AI Toolkit gRPC)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Enable/disable sensitive data capture
OTEL_EXPORTER_OTLP_HEADERS=include_sensitive=true
```

### Custom Tracing Setup

For advanced use cases, modify `src/curator/tracing.py`:

```python
from src.curator.tracing import setup_tracing

# Use custom endpoint (e.g., Jaeger or local Grafana Loki)
setup_tracing(
    otlp_endpoint="http://localhost:4318",  # HTTP endpoint
    enable_sensitive_data=True
)
```

### Disable Tracing

To temporarily disable tracing without removing code:

```python
# In run_with_approval.py, comment out:
# setup_tracing()

# The agent will still work, but no traces will be collected
```

## Example Trace Output

When you run the agent with tracing enabled, you'll see spans like:

```
curator-agent
├── call_model (50ms)
│   └── claude-sonnet-4-5 [prompt: "Extract dependencies...", tokens: 2500/1200]
├── run_tools_with_gate (150ms)
│   ├── extractor_agent (120ms)
│   │   └── read_documentation_file (90ms)
│   ├── validator_agent (40ms)
│   └── storage_agent (50ms)
└── request_human_approval (interactive)
```

Each span includes:
- **Timing** - Total duration + breakdown of child operations
- **Attributes** - Operation name, parameters, model name
- **Metadata** - Token counts, error messages, sub-agent responses

## Troubleshooting

### "Connection refused" error

**Problem**: `ConnectionError: Connection refused on http://localhost:4317`

**Solution**:
1. Ensure AI Toolkit trace viewer is open: `AI ML Studio: Tracing - Open Trace Viewer`
2. Check that VS Code has the AI Toolkit extension installed
3. Verify firewall isn't blocking localhost:4317

### Traces not appearing

**Problem**: Agent runs but no traces in viewer

**Possible causes**:
- Tracing not initialized (check console output for "✓ OpenTelemetry tracing enabled")
- OTLP endpoint is wrong (should be `http://localhost:4317` for AI Toolkit)
- Agent framework not installed (`pip install agent-framework`)

**Solution**:
```bash
# Check if agent-framework is installed
pip list | grep agent-framework

# Reinstall if needed
pip install --upgrade agent-framework opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
```

### Too much/too little data in traces

**To include prompts and completions:**
```python
setup_tracing(enable_sensitive_data=True)
```

**To exclude sensitive data (PII redaction):**
```python
setup_tracing(enable_sensitive_data=False)
```

## Best Practices

1. **Always start trace viewer first** - Open `AI ML Studio: Tracing - Open Trace Viewer` before running agent
2. **Enable sensitive data for debugging** - Helps identify LLM errors and unexpected outputs
3. **Disable sensitive data for production** - Avoid capturing user data or API keys
4. **Use meaningful thread IDs** - `run_with_approval.py` uses `"curator-session-1"` by default; customize for different runs:
   ```python
   run_curator_with_approval(task, thread_id="extraction-2025-12-26")
   ```
5. **Monitor token usage** - Check trace viewer for `"usage"` attribute on LLM calls

## Integration with Other Tools

### LangSmith (Existing Integration)

Tracing works alongside your existing LangSmith setup:
- **LangSmith** (`LANGSMITH_WORKSPACE_ID`) - Full conversation history, cost tracking, feedback loops
- **OpenTelemetry** (AI Toolkit) - Real-time operational metrics, performance debugging

Both can be enabled simultaneously.

### Custom Spans

To add custom spans for your own code:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("my_custom_operation") as span:
    span.set_attribute("operation_type", "data_extraction")
    # Your code here
```

## References

- [Agent Framework Documentation](https://github.com/microsoft/agent-framework)
- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [OTLP Protocol Reference](https://opentelemetry.io/docs/reference/specification/protocol/)
- [AI Toolkit Tracing Guide](https://github.com/microsoft/ai-toolkit)
