# OpenTelemetry Integration Plan

**Purpose:** Distributed tracing across PROVES Library multi-service architecture

**Status:** Planned for Phase 2 (MCP Server + Risk Scanner integration)

---

## 🎯 Why OpenTelemetry?

PROVES Library will have multiple services communicating over the network:

```
Risk Scanner → MCP Server → Neon PostgreSQL
    ↓              ↑
Agents ───────────┘
    ↓
Dependency Extractor
```

**Problems OpenTelemetry Solves:**
1. ❓ **Cross-service debugging:** "Scanner says submission failed, MCP says succeeded - who's right?"
2. ❓ **Performance bottlenecks:** "Cascade query takes 5s - is it network, MCP logic, or database?"
3. ❓ **Agent behavior:** "Which agents are hitting the MCP server most? What queries do they run?"
4. ❓ **Multi-agent coordination:** "Two agents trying to update same node - how to detect conflicts?"

**What OpenTelemetry Provides:**
- ✅ Distributed tracing with single trace ID across services
- ✅ Automatic instrumentation for FastAPI, HTTP requests, database queries
- ✅ Vendor-neutral (export to Jaeger, Grafana, Honeycomb, Datadog, etc.)
- ✅ Standard semantic conventions for GenAI systems

---

## 🏗️ Architecture

### Component Instrumentation

```python
┌─────────────────────────────────────────────┐
│          OpenTelemetry Tracing              │
├─────────────────────────────────────────────┤
│                                             │
│  Risk Scanner (requests instrumentation)    │
│     ↓ HTTP POST                             │
│  MCP Server (FastAPI instrumentation)       │
│     ↓ SQL                                   │
│  Neon PostgreSQL (psycopg2 instrumentation) │
│     ↑ SQL                                   │
│  Dependency Extractor                       │
│     ↑ MCP protocol                          │
│  Agents (LangChain instrumentation)         │
│                                             │
│  All export to: Jaeger/Grafana/Tempo        │
└─────────────────────────────────────────────┘
```

### Dual Observability: OpenTelemetry + LangSmith

```python
# Dependency Extractor
from opentelemetry import trace  # For cross-service tracing
from langsmith.wrappers import wrap_openai  # For LLM observability

# OpenTelemetry sees:
# - HTTP calls to MCP server
# - Database queries
# - End-to-end timing

# LangSmith sees:
# - LLM prompts and responses
# - Token usage and costs
# - Extraction quality
```

**They complement each other:**
- **OpenTelemetry:** Cross-service flows, performance, infrastructure
- **LangSmith:** LLM-specific reasoning, prompts, quality

---

## 📋 Implementation Phases

### Phase 1: Current (LangSmith Only)

**Status:** ✅ Complete

**What's instrumented:**
- Dependency extraction (LangSmith)
- LLM calls (LangSmith wrap_openai)

**Why no OpenTelemetry yet:**
- Single-process application
- No inter-service communication
- LangSmith sufficient for current needs

### Phase 2: MCP Server + Risk Scanner

**Status:** 🔜 Next (when MCP server is built)

**Add OpenTelemetry for:**

1. **MCP Server (FastAPI)**
   ```python
   from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

   app = FastAPI()
   FastAPIInstrumentor.instrument_app(app)  # Auto-trace all endpoints
   ```

2. **Risk Scanner (HTTP Client)**
   ```python
   from opentelemetry.instrumentation.requests import RequestsInstrumentor

   RequestsInstrumentor().instrument()  # Auto-trace HTTP calls
   ```

3. **Database Queries**
   ```python
   from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

   Psycopg2Instrumentor().instrument()  # Auto-trace SQL queries
   ```

**Example trace flow:**
```
Risk Scanner: scan_repository (15s)
  ├─ parse_files (5s)
  ├─ detect_patterns (8s)
  └─ submit_risks (2s)
      └─ HTTP POST → MCP Server (2s)
          └─ MCP: store_risk (1.8s)
              └─ Database: INSERT (1.5s)
```

### Phase 3: Multi-Agent System

**Status:** 🔮 Future

**Add OpenTelemetry for:**

1. **Agent Workflows**
   ```python
   from opentelemetry import trace

   tracer = trace.get_tracer(__name__)

   @traceable  # LangSmith
   def agent_workflow(task):
       with tracer.start_as_current_span("agent_workflow"):  # OpenTelemetry
           # LangSmith traces LLM reasoning
           # OpenTelemetry traces MCP queries
           results = query_mcp(...)
           return results
   ```

2. **LangChain Integration**
   ```python
   from opentelemetry.instrumentation.langchain import LangChainInstrumentor

   LangChainInstrumentor().instrument()  # Auto-trace agent steps
   ```

**Example trace flow:**
```
Curator Agent: process_new_docs (45s)
  ├─ fetch_docs (1s)
  ├─ extract_dependencies (30s)
  │   └─ LLM calls (tracked in LangSmith)
  ├─ query_knowledge (10s)
  │   ├─ MCP: /graph/search (3s)
  │   ├─ MCP: /graph/cascade (5s)
  │   └─ MCP: /graph/conflicts (2s)
  └─ store_results (4s)
      └─ MCP: /graph/update (3.5s)
```

---

## 🛠️ Technical Implementation

### 1. Add Dependencies

```python
# requirements.txt

# OpenTelemetry Core
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0

# Instrumentation Libraries
opentelemetry-instrumentation-fastapi>=0.41b0  # MCP server
opentelemetry-instrumentation-requests>=0.41b0  # HTTP client
opentelemetry-instrumentation-psycopg2>=0.41b0  # Database
opentelemetry-instrumentation-langchain>=0.41b0  # Agents (future)

# Exporters
opentelemetry-exporter-otlp>=1.20.0  # OTLP protocol (standard)
opentelemetry-exporter-jaeger>=1.20.0  # Jaeger (optional)
```

### 2. Configuration Module

**File:** `scripts/telemetry.py`

```python
#!/usr/bin/env python3
"""
OpenTelemetry configuration for PROVES Library
Provides unified tracing setup across all services
"""
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION


def setup_telemetry(service_name: str, service_version: str = "1.0.0"):
    """
    Initialize OpenTelemetry tracing for a service

    Args:
        service_name: Name of the service (e.g., "mcp-server", "risk-scanner")
        service_version: Version of the service

    Environment Variables:
        OTEL_EXPORTER_OTLP_ENDPOINT: Where to send traces (default: http://localhost:4317)
        OTEL_SERVICE_NAME: Override service name
        OTEL_ENABLED: Set to "false" to disable tracing
    """
    # Check if tracing is enabled
    if os.getenv("OTEL_ENABLED", "true").lower() == "false":
        print(f"⚠️  OpenTelemetry disabled for {service_name}")
        return

    # Create resource identifying this service
    resource = Resource(attributes={
        SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", service_name),
        SERVICE_VERSION: service_version,
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure OTLP exporter (sends to Jaeger, Grafana, etc.)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)

    # Add span processor (batches and exports spans)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    print(f"✅ OpenTelemetry enabled for {service_name}")
    print(f"   Exporting to: {otlp_endpoint}")


def get_tracer(name: str):
    """Get a tracer for manual instrumentation"""
    return trace.get_tracer(name)
```

### 3. MCP Server Integration

**File:** `mcp-server/server.py`

```python
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from scripts.telemetry import setup_telemetry

# Initialize telemetry
setup_telemetry("mcp-server", "1.0.0")

# Create FastAPI app
app = FastAPI(title="PROVES Library MCP Server")

# Instrument FastAPI (auto-traces all endpoints)
FastAPIInstrumentor.instrument_app(app)

# Instrument database (auto-traces all SQL queries)
Psycopg2Instrumentor().instrument()

@app.post("/risks")
async def submit_risk(risk_data: dict):
    """
    Submit a risk from scanner

    This endpoint is automatically traced by OpenTelemetry:
    - Request/response timing
    - Database queries
    - Errors and exceptions
    """
    # Store risk in database (auto-traced)
    result = db.store_risk(risk_data)
    return result

@app.get("/graph/cascade")
async def get_cascade(start_node: str, max_depth: int = 5):
    """
    Get cascade paths from a node

    Traced automatically:
    - SQL query timing
    - Result size
    - Processing time
    """
    paths = db.find_cascade_paths(start_node, max_depth)
    return {"paths": paths}
```

### 4. Risk Scanner Integration

**File:** `risk-scanner/scanner.py`

```python
import requests
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry import trace
from scripts.telemetry import setup_telemetry, get_tracer

# Initialize telemetry
setup_telemetry("risk-scanner", "1.0.0")

# Instrument HTTP requests (auto-traces requests.post, requests.get, etc.)
RequestsInstrumentor().instrument()

# Get tracer for manual instrumentation
tracer = get_tracer(__name__)

def scan_repository(repo_path: str):
    """
    Scan repository for risks

    Uses both automatic and manual tracing:
    - HTTP POST to MCP server (automatic)
    - Custom spans for scan steps (manual)
    """
    with tracer.start_as_current_span("scan_repository") as span:
        span.set_attribute("repo.path", repo_path)

        # Parse files (manual span)
        with tracer.start_as_current_span("parse_files"):
            files = parse_files(repo_path)
            span.set_attribute("file.count", len(files))

        # Detect patterns (manual span)
        with tracer.start_as_current_span("detect_patterns"):
            risks = detect_patterns(files)
            span.set_attribute("risk.count", len(risks))

        # Submit risks (automatic HTTP tracing)
        with tracer.start_as_current_span("submit_risks"):
            for risk in risks:
                # This HTTP call is automatically traced
                response = requests.post(
                    "http://mcp-server:8000/risks",
                    json=risk
                )
                response.raise_for_status()

        return {"risks_found": len(risks)}
```

### 5. Dependency Extractor Integration

**File:** `scripts/dependency_extractor.py` (updated)

```python
from opentelemetry import trace
from langsmith import traceable
from langsmith.wrappers import wrap_openai
from scripts.telemetry import setup_telemetry, get_tracer

# Initialize telemetry
setup_telemetry("dependency-extractor", "1.0.0")

# Get tracer
tracer = get_tracer(__name__)

class DependencyExtractor:
    def __init__(self):
        self.client = wrap_openai(OpenAI())  # LangSmith tracing

    @traceable(name="extract_dependencies_from_document")  # LangSmith
    def extract_dependencies(self, document_text: str, document_name: str):
        """
        Extract dependencies with dual observability:
        - LangSmith: LLM prompts/responses
        - OpenTelemetry: Cross-service tracing
        """
        # LangSmith traces the LLM calls inside these functions
        chunks = self._chunk_document(document_text)

        all_dependencies = []
        for i, chunk in enumerate(chunks):
            chunk_deps = self._extract_from_chunk(chunk, document_name, i, len(chunks))
            all_dependencies.extend(chunk_deps)

        merged = self._merge_dependencies(all_dependencies)

        # Store in knowledge graph via MCP (OpenTelemetry traces this)
        with tracer.start_as_current_span("store_to_mcp") as span:
            span.set_attribute("dependency.count", len(merged))

            response = requests.post(
                "http://mcp-server:8000/dependencies",
                json={"document": document_name, "dependencies": merged}
            )
            span.set_attribute("mcp.response.status", response.status_code)

        return merged
```

---

## 🖥️ Backend Setup

### Option 1: Jaeger (Recommended for Development)

**Why Jaeger:**
- ✅ Free and open-source
- ✅ Excellent UI for trace visualization
- ✅ Easy Docker setup
- ✅ No account required

**Setup:**

```bash
# Run Jaeger in Docker
docker run -d \
  --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest

# Set environment variable
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# View traces at: http://localhost:16686
```

**What you see in Jaeger:**
- Service map (visual graph of services)
- Trace timeline (waterfall view of spans)
- Search traces by service, operation, tags
- Performance metrics (latency percentiles)

### Option 2: Grafana Tempo (Recommended for Production)

**Why Grafana Tempo:**
- ✅ Integrates with Grafana dashboards
- ✅ Scales to production workloads
- ✅ Free tier on Grafana Cloud
- ✅ Long-term trace storage

**Setup:**

```bash
# Grafana Cloud (free tier)
# 1. Sign up at https://grafana.com/auth/sign-up
# 2. Get OTLP endpoint from Grafana Cloud settings
# 3. Set environment variables

export OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-us-east-0.grafana.net/otlp
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic <your-token>"
```

### Option 3: Honeycomb (Best Query Capabilities)

**Why Honeycomb:**
- ✅ Powerful query language
- ✅ Excellent for debugging complex issues
- ✅ Free tier (20M events/month)
- ✅ Great for production

**Setup:**

```bash
# 1. Sign up at https://www.honeycomb.io/
# 2. Get API key
# 3. Set environment variables

export OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io:443
export OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=<your-api-key>"
```

---

## 📊 Example Traces

### Trace 1: Risk Scanner → MCP Server → Database

```
scan_repository (15.2s)
├─ parse_files (5.1s)
│  ├─ parse file1.py (0.8s)
│  ├─ parse file2.py (1.2s)
│  └─ parse file3.py (3.1s)  ← SLOW FILE
├─ detect_patterns (8.3s)
│  ├─ pattern: null_pointer (2.1s)
│  ├─ pattern: resource_leak (3.2s)
│  └─ pattern: race_condition (3.0s)
└─ submit_risks (1.8s)
   ├─ HTTP POST /risks (0.6s)
   │  └─ MCP: store_risk (0.5s)
   │     └─ Database: INSERT risk (0.4s)
   ├─ HTTP POST /risks (0.6s)
   │  └─ MCP: store_risk (0.5s)
   │     └─ Database: INSERT risk (0.4s)
   └─ HTTP POST /risks (0.6s)
      └─ MCP: store_risk (0.5s)
         └─ Database: INSERT risk (0.4s)
```

**Insights:**
- file3.py is slow to parse (3.1s) - maybe large or complex
- Risk submission is efficient (0.6s each)
- Database is fast (0.4s per INSERT)

### Trace 2: Agent Query Cascade

```
agent_workflow (12.5s)
├─ fetch_docs (0.8s)
├─ extract_dependencies (7.2s)
│  └─ LLM calls (tracked in LangSmith)
└─ query_knowledge (4.5s)
   ├─ HTTP GET /graph/cascade (4.0s)
   │  └─ MCP: get_cascade (3.9s)
   │     └─ Database: recursive CTE (3.7s)  ← BOTTLENECK
   ├─ HTTP GET /graph/search (0.3s)
   │  └─ MCP: search_nodes (0.2s)
   │     └─ Database: vector search (0.15s)
   └─ HTTP GET /graph/conflicts (0.2s)
      └─ MCP: detect_conflicts (0.15s)
         └─ Database: conflict query (0.12s)
```

**Insights:**
- Recursive CTE for cascade is expensive (3.7s)
- Vector search is fast (0.15s) - good indexing
- Consider caching cascade results

### Trace 3: Multi-Agent Coordination

```
Service Map:
┌────────────┐      ┌────────────┐      ┌──────────┐
│   Curator  │─────>│ MCP Server │─────>│ Database │
│   Agent    │      │            │      │          │
└────────────┘      └────────────┘      └──────────┘
      ↑                    ↑                   ↑
      │                    │                   │
┌────────────┐             │                   │
│  Builder   │─────────────┘                   │
│   Agent    │                                 │
└────────────┘                                 │
      ↑                                        │
      │                                        │
┌────────────┐                                 │
│ Validator  │─────────────────────────────────┘
│   Agent    │
└────────────┘

Concurrent requests:
T=0s:   Curator → /graph/search
T=0.1s: Builder → /graph/cascade
T=0.2s: Validator → /graph/validate
T=0.5s: Curator → /graph/update
T=0.6s: Builder → /graph/conflicts  ← Conflict detected!
```

**Insights:**
- Three agents hitting MCP server concurrently
- Builder and Curator both trying to update same node
- Trace shows exact timing of conflict

---

## 🎯 Success Metrics

### Performance Monitoring

**Key metrics to track:**

```python
# Latency percentiles (ms)
mcp.endpoint.latency.p50: 50ms
mcp.endpoint.latency.p95: 200ms
mcp.endpoint.latency.p99: 500ms

# Request rate (req/s)
mcp.requests.rate: 10 req/s

# Error rate (%)
mcp.errors.rate: 0.1%

# Database query time (ms)
database.query.time.avg: 100ms
database.query.time.p99: 1000ms

# Risk scanner throughput (risks/min)
scanner.risks.rate: 50 risks/min
```

### Trace-Based Debugging

**Questions OpenTelemetry answers:**

1. **"Why is cascade query slow?"**
   - Filter traces where `/graph/cascade` duration > 2s
   - Group by query parameters
   - Find common slow patterns

2. **"Which agent is causing load?"**
   - Group traces by `service.name`
   - Count requests per agent
   - Identify heavy users

3. **"Where are errors occurring?"**
   - Filter traces with `error=true`
   - See exact failure point in trace
   - Understand error propagation

4. **"Is database or network the bottleneck?"**
   - Compare database span duration vs total request duration
   - Calculate `db_time / total_time` ratio
   - Identify if network latency is issue

---

## 🚀 Rollout Plan

### Week 1: Infrastructure Setup

- [ ] Add OpenTelemetry dependencies to requirements.txt
- [ ] Create `scripts/telemetry.py` configuration module
- [ ] Set up Jaeger locally for development
- [ ] Document environment variables in `.env.example`

### Week 2: MCP Server Instrumentation

- [ ] Instrument FastAPI application
- [ ] Instrument database queries (psycopg2)
- [ ] Add custom spans for business logic
- [ ] Test trace visualization in Jaeger

### Week 3: Risk Scanner Instrumentation

- [ ] Instrument HTTP client (requests)
- [ ] Add custom spans for scan steps
- [ ] Test end-to-end traces (scanner → MCP → database)
- [ ] Optimize based on trace insights

### Week 4: Integration & Documentation

- [ ] Update AGENT_HANDOFF.md with tracing info
- [ ] Add troubleshooting guide
- [ ] Create example queries for common scenarios
- [ ] Train team on using Jaeger UI

### Future: Production Deployment

- [ ] Set up Grafana Cloud (or Honeycomb)
- [ ] Configure production exporters
- [ ] Set up alerts for latency/errors
- [ ] Create dashboards for key metrics

---

## 📚 Resources

**OpenTelemetry Documentation:**
- Overview: https://opentelemetry.io/docs/what-is-opentelemetry/
- Python SDK: https://opentelemetry.io/docs/languages/python/
- Instrumentation: https://opentelemetry.io/docs/languages/python/instrumentation/
- Semantic Conventions: https://opentelemetry.io/docs/specs/semconv/

**Backend Documentation:**
- Jaeger: https://www.jaegertracing.io/docs/
- Grafana Tempo: https://grafana.com/docs/tempo/latest/
- Honeycomb: https://docs.honeycomb.io/

**Integration Guides:**
- FastAPI: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html
- Requests: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/requests/requests.html
- psycopg2: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/psycopg2/psycopg2.html

---

## 🔄 Integration with Existing Tools

### OpenTelemetry + LangSmith

**Complementary observability:**

```python
# dependency_extractor.py

from opentelemetry import trace  # Cross-service tracing
from langsmith import traceable  # LLM observability

@traceable  # LangSmith sees LLM calls
def extract_dependencies(doc):
    with trace.get_tracer(__name__).start_as_current_span("extract"):  # OpenTelemetry sees everything else
        # LangSmith: prompt, response, tokens
        deps = llm.extract(doc)

        # OpenTelemetry: HTTP timing, database queries
        store_to_mcp(deps)

        return deps
```

**View in both tools:**
- **LangSmith:** Detailed LLM prompt engineering and quality
- **Jaeger:** End-to-end request flow and performance

### OpenTelemetry + Neon Database

**Automatic query tracing:**

```python
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

Psycopg2Instrumentor().instrument()

# Now all database queries are automatically traced:
result = db.fetch_one("SELECT * FROM kg_nodes WHERE id = %s", (node_id,))

# Trace shows:
# - SQL query text
# - Query duration
# - Rows returned
# - Connection pool stats
```

---

## 🎓 Next Steps

1. **Read this document** to understand the plan
2. **Set up Jaeger locally** when you build MCP server
3. **Instrument MCP server** as first step
4. **Add risk scanner instrumentation** second
5. **Iterate based on trace insights** to optimize performance

**The beauty of OpenTelemetry:** You add it once, it works everywhere, and you can change backends anytime.

---

**Last Updated:** 2024-12-20
**Status:** Planned for Phase 2 (MCP Server + Risk Scanner)
**Owner:** To be assigned when Phase 2 begins
