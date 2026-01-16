# MCP Server: Feature Requirements

**What This Is:** A standalone Model Context Protocol (MCP) server that provides natural language query access to the PROVES knowledge graph. Engineers can ask questions about components, dependencies, and relationships without learning SQL or graph query languages.

**Purpose:** Define requirements for the PROVES MCP interrogation service

**Date:** 2026-01-15

**Audience:** Engineers querying the PROVES library, developers building MCP integrations

**Context:** The MCP server is a separate service from the curation dashboard. It connects directly to the Postgres database (read-only access) and exposes tools for querying entities, relationships, and running graph traversals. It can be used standalone (CLI, Claude Desktop) or integrated into dashboards.

---

## MCP Server: Must-Have Features

| Category | Feature | Description | Why (Reason) | Priority | Technical Requirement |
|----------|---------|-------------|--------------|----------|----------------------|
| **Query Capabilities** | Entity Search | Find entities by name, type, or attributes | Engineers need to locate specific components, ports, or parameters without knowing exact identifiers | P0 (Critical) | MCP tool: search_entities(query, entity_type, filters) |
| | Dependency Queries | "Show all dependencies of ComponentX" | Teams need to understand what a component relies on for design and testing decisions | P0 | MCP tool: get_dependencies(entity_id, depth, direction) |
| | Relationship Traversal | Follow edges in the knowledge graph | Engineers need to trace connections through the system (e.g., data flow, power distribution) | P0 | MCP tool: traverse_graph(start_entity, relationship_type, max_depth) |
| | Cascade Analysis | "What fails if ComponentX fails?" | Engineers need failure impact analysis to identify critical components and single points of failure | P1 | Graph traversal using ERV attributes (strength, mechanism) |
| | FRAMES Dimension Filtering | Filter by knownness, contact level, etc. | Engineers need to distinguish verified knowledge from assumptions when making critical decisions | P1 | Filter entities by FRAMES metadata in queries |
| **Team Scoping** | Team-Scoped Queries | Default to querying team's data only | Engineers primarily care about their own system's knowledge, not other universities' satellites | P0 | Filter by team_id in all queries |
| | Cross-Team Queries | Opt-in to query shared/public knowledge | Some components (I2C drivers, standard protocols) are shared - allow querying public entities | P1 | team_id filter with 'public' scope option |
| **Performance** | Query Caching | Cache frequent queries (dependencies, common traversals) | Common queries ("show dependencies") shouldn't hit DB every time - reduce latency and DB load | P1 | Redis cache or in-memory LRU cache |
| | Query Timeout | Limit max execution time (30s default) | Prevent runaway graph traversals from blocking the server or consuming resources | P0 | Timeout mechanism in query execution |
| | Result Limiting | Cap results to 1000 entities per query | Prevent memory exhaustion from overly broad queries (e.g., "show all components") | P0 | LIMIT clause in SQL, pagination support |
| **Query History** | Save Query History | Store queries per user/session | Common questions should be reusable - engineers can recall previous dependency checks or analyses | P1 | Query log table or file-based history |
| | Query Templates | Pre-built queries for common patterns | Engineers shouldn't have to re-type "show dependencies" - provide reusable templates | P2 | Template library in MCP server |
| **Integration** | Claude Desktop Integration | Use as MCP server in Claude Desktop | Engineers want to query the library directly from their Claude Desktop chat interface | P0 | MCP protocol compliance, stdio transport |
| | CLI Tool | Command-line interface for queries | Power users and scripts need programmatic access without GUI | P1 | CLI wrapper around MCP tools |
| | REST API | HTTP endpoint for web dashboards | Curation dashboard needs to embed query results - provide REST API alongside MCP | P1 | FastAPI/Flask HTTP wrapper |
| **Data Access** | Read-Only DB Access | Query core_entities, staging_extractions, relationships | MCP server should never modify data - only read verified and staged knowledge | P0 | Postgres read-only user with SELECT permissions |
| | Real-Time Updates | Subscribe to entity changes | When new entities are verified, dashboard should reflect updates without manual refresh | P2 | Postgres LISTEN/NOTIFY or polling |
| **Security** | Team Isolation | Users only see their team's data | University IP must remain isolated - MCP queries respect team boundaries | P0 | Row-level security or team_id filtering in queries |
| | Query Auditing | Log all queries with user/team | Track who's querying what for security audits and usage analytics | P1 | Query log with timestamp, user, team, query |
| **Scalability** | Concurrent Queries | Handle 50+ simultaneous queries | Multiple team members querying simultaneously - server must handle concurrent load | P0 | Async query execution, connection pooling |
| | Multi-Instance Deployment | Run multiple MCP server instances | Scale horizontally as more teams join - load balance across instances | P1 | Stateless server design, shared cache |

---

## Priority Legend
- **P0 (Critical):** Must have for MVP / launch blocker
- **P1 (High):** Needed soon after launch / core workflow
- **P2 (Medium):** Nice to have / can be added later

---

## MVP Scope (P0 Features Only)

For fastest launch, focus on **9 P0 features**:

1. **Entity Search** - Find components, ports, parameters by name/type
2. **Dependency Queries** - Show what a component depends on
3. **Relationship Traversal** - Follow edges in the knowledge graph
4. **Team-Scoped Queries** - Default to team's data only
5. **Query Timeout** - Prevent runaway queries
6. **Result Limiting** - Cap results to prevent memory issues
7. **Claude Desktop Integration** - MCP protocol compliance
8. **Read-Only DB Access** - Query-only Postgres connection
9. **Team Isolation** - Enforce team boundaries in queries
10. **Concurrent Queries** - Handle multiple simultaneous queries

**Estimated Timeline for P0 MVP:** 1-2 weeks with existing MCP server foundation

---

## Recommended Tech Stack

### MCP Server Runtime
- **Framework:** Python MCP SDK (existing)
- **Transport:** stdio (for Claude Desktop), SSE (for web)
- **Database:** Postgres read-only connection to Neon

### Optional Components
- **Cache:** Redis or in-memory LRU (for P1 caching)
- **API:** FastAPI (if exposing REST endpoint for dashboard)
- **Deployment:** Modal.com (serverless, auto-scaling)

---

## Example Queries

### 1. Find a Component
```
User: "Find the RadioDriver component"
MCP Tool: search_entities(query="RadioDriver", entity_type="component")
Returns: {entity_id, canonical_key, ecosystem, confidence_score}
```

### 2. Show Dependencies
```
User: "What does RadioDriver depend on?"
MCP Tool: get_dependencies(entity_id="RadioDriver_uuid", direction="outbound")
Returns: [I2C_Bus, PowerDriver, ClockSource]
```

### 3. Cascade Failure Analysis
```
User: "What fails if I2C fails?"
MCP Tool: traverse_graph(start_entity="I2C_Bus", relationship_type="REQUIRES", direction="inbound")
Returns: [RadioDriver, SensorArray, PowerMonitor] + failure cascade visualization
```

---

## Integration with Curation Dashboard

The MCP server can be **embedded** in the curation dashboard via:

1. **REST API Endpoint** - Dashboard calls MCP tools via HTTP
2. **Shared WebSocket** - Real-time query results streamed to dashboard
3. **Standalone Service** - MCP server runs independently, dashboard consumes API

**Recommended:** Standalone service with REST API wrapper for dashboard integration.

---

## Database Schema Requirements

**No new tables needed** - MCP server reads from existing schema:

- `core_entities` - Verified entities
- `staging_extractions` - Pending entities (optional, for preview queries)
- `staging_relationships` - Entity relationships
- `knowledge_enrichment` - Standard mappings, aliases

**Required Indexes** (for performance):
- `core_entities(canonical_key)` - Fast entity lookup
- `core_entities(entity_type, ecosystem)` - Filtered searches
- `staging_relationships(source_entity_id)` - Dependency queries
- `staging_relationships(target_entity_id)` - Reverse dependency queries

---

## Open Questions

### Q1: Should MCP server query staging or only verified entities?
**Options:**
- A) Only `core_entities` (verified knowledge)
- B) Both `core_entities` + `staging_extractions` (with confidence filters)
- C) Configurable per query

**Recommendation:** A for MVP, B for advanced users (flag: `include_unverified=true`)

---

### Q2: How to handle large result sets?
**Options:**
- A) Hard limit (1000 results max, error if exceeded)
- B) Pagination (return first 100, allow fetching more)
- C) Streaming results (yield results as they're found)

**Recommendation:** B (pagination) for API, A (limit) for Claude Desktop

---

### Q3: Cache invalidation strategy?
**Options:**
- A) Time-based (5 min TTL)
- B) Event-based (invalidate on entity verification)
- C) Manual (admin command to clear cache)

**Recommendation:** A for MVP, B for production

---

## Success Metrics

### Performance
- Query response time < 5 seconds (p95)
- Support 50+ concurrent queries
- 90%+ cache hit rate for common queries

### Usage
- 5+ teams actively using MCP queries
- 100+ queries per day across all teams
- Query success rate > 95%

### Quality
- Zero data leaks (team isolation 100% enforced)
- Query audit log 100% complete
- Zero runaway queries (timeout enforcement working)

---

## References

**Related Documentation:**
- `mcp-server/docs/MCP_INTEGRATION.md` - Current MCP integration guide
- `mcp-server/docs/MCP_SETUP.md` - Setup instructions
- `docs/architecture/KNOWLEDGE_GRAPH_SCHEMA.md` - ERV relationship model
- `.deepagents/IMPLEMENTATION_ROADMAP.md` - Overall development roadmap

---

**Status:** Requirements defined, ready for MCP server enhancement and integration planning
