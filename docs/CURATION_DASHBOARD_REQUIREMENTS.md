# PROVES Curation Dashboard: Must-Have Features

**What This Is:** A multi-team dashboard for engineers to curate knowledge extracted by the PROVES agentic workflow. This dashboard enables university teams to verify what autonomous agents extract from their documentation, query the verified knowledge library, and export to industry standards.

**Purpose:** Define requirements for the PROVES multi-team curation dashboard

**Date:** 2026-01-15

**Audience:** 8+ university teams contributing to PROVES library

**Context:** The PROVES system autonomously extracts technical knowledge (components, dependencies, interfaces) from satellite development documentation. This platform is where engineers review those extractions, verify accuracy, and contribute to a shared knowledge base that helps teams avoid repeated mistakes and preserve institutional knowledge across personnel transitions.

---

## Curation Dashboard: Must-Have Features

| Category | Feature | Description | Why (Reason) | Priority | Technical Requirement |
|----------|---------|-------------|--------------|----------|----------------------|
| **Team Management** | Team Accounts | Each university/lab has isolated account | 8+ universities need data isolation to prevent accidental cross-contamination and ensure each lab owns their portion of the library | P0 (Critical) | Multi-tenant DB with row-level security |
| | Team Member Auth | Email login for team members | Engineers need secure access to review their team's extractions without manual account creation | P0 | Auth system (Supabase Auth, Auth0, etc.) |
| | Team Assignment | Auto-route extractions to correct team | Extractions from each lab's repos/docs must automatically go to the right team's dashboard for review | P0 | Logic based on ecosystem/repo/namespace |
| | Admin Oversight | Super-admin can see all teams | Platform maintainer needs visibility across all teams for support and quality monitoring | P1 | Role-based access control |
| **Curation Workflow** | View Pending Extractions | Table of extractions awaiting review | Teams need to see what agent-extracted knowledge is waiting for human verification | P0 | Query staging_extractions by team |
| | Claim Batch | Lock a set of extractions for review | Prevents multiple team members from duplicating work on the same extractions simultaneously | P0 | batch_claims table + locking mechanism |
| | Claim Timeout | Auto-release unclaimed batches after X hours | If someone claims a batch but doesn't finish, it becomes available again so work doesn't get blocked | P0 | Scheduled job or trigger |
| | Review Interface | View entity, evidence, FRAMES dimensions | Engineers need to see extraction details, source evidence, and confidence scores to make approval decisions | P0 | Detail view with all extraction data |
| | Approve/Reject | Mark entities as verified or rejected | Only human-verified knowledge enters the library - this is the core verification step | P0 | Update validation_decisions table |
| | Bulk Actions | Approve/reject multiple at once | When reviewing similar extractions (same document), engineers can work faster with batch operations | P1 | Batch SQL updates |
| **Notifications** | Email on New Extractions | Notify team when new work arrives | Teams need to know when their repos have been processed and extractions are ready for review | P0 | Email service (SendGrid, Resend, etc.) |
| | Daily Digest | Summary of pending work | Reduces notification noise while keeping teams aware of pending curation workload | P1 | Scheduled email job |
| | Claim Expiry Warning | Alert when claim about to timeout | Prevents accidental loss of review progress when claims are about to expire | P1 | Scheduled check + notification |
| **Real-Time Updates** | Live Dashboard | See when others claim/approve | Team members need to coordinate - avoid claiming batches others are working on | P0 | WebSocket or Server-Sent Events |
| | Progress Tracking | Team stats (approved count, pending count) | Teams track their contribution to the shared library and see curation velocity | P1 | Aggregate queries + real-time updates |
| | Activity Feed | Recent team actions | Transparency - see what teammates are working on and recent verification decisions | P2 | Event log table |
| **Library Portal (MCP)** | Chat Interface | Ask questions about the library | Engineers need to query the knowledge graph without learning SQL or graph query languages | P0 | Chat UI + WebSocket to MCP server |
| | Query Library | "Show dependencies of RadioDriver" | Teams need to understand component relationships, dependencies, and design decisions in natural language | P0 | MCP server with Postgres access |
| | Graph Traversal | "What fails if PowerDriver fails?" | Engineers need cascade failure analysis to understand system risk without manual graph traversal | P1 | Graph query engine (ERV relationships) |
| | Query History | Save/recall previous queries | Common questions (dependency checks, failure analysis) should be reusable across team members | P1 | Query log table |
| | Team-Scoped Queries | Only search team's data by default | Engineers primarily care about their own system's knowledge, not other universities' satellites | P0 | Filter by team_id in MCP queries |
| **Export Capabilities** | Export to XTCE | Generate XTCE XML for YAMCS | Teams using YAMCS mission control need XTCE-formatted telemetry/command definitions | P1 | XTCE exporter using standard_mapping |
| | Export to SysML | Generate SysML v2 for MBSE tools | Teams using model-based systems engineering tools (Cameo, etc.) need SysML definitions | P1 | SysML exporter using standard_mapping |
| | Export to PyG | Generate graph data for ML training | Researchers need graph datasets in PyTorch Geometric format for training custom GNN models | P1 | PyG data formatter |
| | Team Data Only | Filter exports to team's entities | Teams export only their verified knowledge, not other universities' data | P0 | WHERE team_id filter |
| **Scalability** | Support 8-50 Teams | Handle growth without code changes | Started with 8 universities but need to scale as more labs join without re-architecting | P0 | Serverless architecture |
| | Concurrent Users | 50-100+ simultaneous users | Multiple team members per university reviewing extractions, running queries, analyzing repos | P0 | Horizontally scalable backend |
| | Multi-Region | Low latency globally (future) | Universities worldwide - need low latency for international collaboration | P2 | CDN + edge functions |
| **Data Integrity** | Team Isolation | Teams can't see others' data | University IP and research must remain isolated - no cross-contamination between labs | P0 | Row-level security (RLS) in Postgres |
| | Audit Trail | Track who approved what, when | Need to trace every verification decision back to the engineer who made it for accountability | P0 | validation_decisions, batch_claims logs |
| | Data Backup | Automatic backups | Verified knowledge is research data - must be protected against data loss | P0 | Managed DB (Neon, Supabase auto-backup) |
| **Developer Experience** | API Access | Programmatic access for power users | Advanced users want to automate curation, run batch queries, integrate with lab tools | P1 | REST/GraphQL API |
| | CLI Tool | Command-line interface for batch ops | Power users prefer CLI for scripting batch approvals, exports, and analysis | P2 | Python CLI using API |
| | Webhooks | Notify external systems on events | Teams want to trigger CI/CD, Slack notifications, or lab dashboards on verification events | P2 | Webhook dispatcher |

---

## Priority Legend
- **P0 (Critical):** Must have for MVP / launch blocker
- **P1 (High):** Needed soon after launch / core workflow
- **P2 (Medium):** Nice to have / can be added later

---

## Feature Count by Priority

| Priority | Count | % of Total |
|----------|-------|------------|
| P0 (Critical) | 17 | 57% |
| P1 (High) | 10 | 33% |
| P2 (Medium) | 3 | 10% |
| **Total** | **30** | **100%** |

---

## MVP Scope (P0 Features Only)

For fastest launch, focus on **17 P0 features**:

### Team Management (3 features)
- Team accounts with isolation
- Email authentication
- Auto-routing of extractions

### Curation Workflow (5 features)
- View pending extractions
- Claim batch system
- Claim timeout/auto-release
- Review interface
- Approve/reject actions

### Notifications (1 feature)
- Email alerts on new extractions

### Real-Time Updates (1 feature)
- Live dashboard status

### Library Portal (3 features)
- Chat interface (using MCP server)
- Library queries
- Team-scoped results

### Export (1 feature)
- Team data filtering

### Infrastructure (3 features)
- Row-level security
- Audit logging
- Automatic backups

**Estimated Timeline for P0 MVP:** 3-4 weeks with Next.js + Supabase stack (MCP server already exists)

---

## Recommended Tech Stack

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Hosting:** Vercel (free tier → $20/month)
- **UI:** Tailwind CSS + shadcn/ui components

### Backend/Database
- **Database:** Neon Postgres (existing) or Supabase Postgres
- **Auth:** Supabase Auth ($25/month after free tier)
- **Real-time:** Supabase Realtime (WebSocket subscriptions)

### MCP Server Integration
- **Platform:** Existing MCP server (mcp-server/)
- **Integration:** REST API wrapper or direct WebSocket
- **Cost:** Minimal (runs alongside dashboard or on Modal)

### Cost Estimate (8 teams, moderate usage)

| Service | Monthly Cost |
|---------|-------------|
| Supabase (DB + Auth + Realtime) | $25 |
| Vercel (Next.js hosting) | $20 |
| MCP Server (Modal or self-hosted) | $10-50 |
| **Total** | **$55-95** |

**At 50 teams:** ~$150-250/month

---

## User Workflow Examples

### 1. Team Member Reviews Extractions

```
1. Receives email: "23 new extractions ready for review"
2. Logs into dashboard → sees team's pending queue
3. Clicks "Claim Batch" → locks 23 extractions for 24 hours
4. Reviews each extraction:
   - Reads evidence
   - Checks FRAMES dimensions
   - Approves or rejects
5. Batch auto-submitted when complete
6. Other team members see real-time update
```

---

### 2. Team Lead Interrogates Library via Library Portal

```
1. Opens "Library Portal" tab in dashboard
2. Types in chat: "Show all components in our satellite that depend on I2C"
3. MCP server queries knowledge graph (scoped to team's data)
4. Returns:
   - RadioDriver
   - SensorArray
   - PowerMonitor
5. Follow-up: "What happens if I2C fails?"
6. MCP runs cascade analysis using ERV relationships
7. Returns failure impact visualization
```

---

### 3. Engineer Exports Team Data to XTCE

```
1. Goes to "Export" tab in dashboard
2. Selects format: XTCE (for YAMCS mission control)
3. Applies filters: team_id='university_xyz', verified_only=true
4. Clicks "Generate Export"
5. Dashboard calls export service using standard_mapping tables
6. Downloads XTCE XML file
7. Imports into YAMCS for mission control configuration
```

---

## Database Schema Additions Needed

### Migration 016: Teams and Batch Claims

**New Tables:**
1. `teams` - Team/university accounts
2. `team_members` - User accounts linked to teams
3. `batch_claims` - Track who claimed what, when
4. `team_notifications` - Email notification log

**Schema Updates:**
- `staging_extractions.assigned_team_id` - Link extractions to teams
- `raw_snapshots.owning_team_id` - Link sources to teams
- `core_entities.created_by_team_id` - Track which team created entity

**Security:**
- Row-level security policies (teams only see their data)
- Admin role bypass

See: `neon-database/migrations/016_add_multi_team_support.sql` (to be created)

---

## Open Questions

### Q1: Team Assignment Logic
**How do we route extractions to the right team?**

Options:
- A) By `ecosystem` field (e.g., `ecosystem='university_xyz_cubesat'`)
- B) By source repository URL
- C) By namespace pattern
- D) Manual assignment during ingestion

**Recommendation:** Hybrid - auto-assign by ecosystem, allow manual override

---

### Q2: Claim Duration
**How long before unclaimed batches auto-release?**

Options:
- 24 hours (recommended)
- 48 hours
- 1 week
- Configurable per team

**Recommendation:** 24 hours default, configurable

---

### Q3: Notification Frequency
**How often to email teams?**

Options:
- A) Immediate (per extraction) - could be noisy
- B) Hourly batching
- C) Daily digest
- D) Threshold-based (e.g., when 10+ pending)

**Recommendation:** Daily digest + threshold alerts for large batches

---

## Next Steps

### Phase 1: Foundation (Weeks 1-2)
- [ ] Create Migration 016 (teams, claims, notifications tables)
- [ ] Set up Next.js project skeleton
- [ ] Configure Supabase auth + RLS policies
- [ ] Basic team dashboard (view extractions)

### Phase 2: Core Workflow (Weeks 3-4)
- [ ] Claim batch system
- [ ] Review/approve interface
- [ ] Email notifications
- [ ] Real-time updates (WebSocket)

### Phase 3: Agent Integration (Weeks 5-6)
- [ ] MCP server on Modal
- [ ] Chat interface in dashboard
- [ ] Basic library queries
- [ ] Graph traversal

### Phase 4: ML Analysis (Weeks 7-8)
- [ ] Repo upload/GitHub integration
- [ ] GNN analysis pipeline on Modal GPU
- [ ] Progress tracking
- [ ] Results visualization

### Phase 5: Export (Weeks 9-10)
- [ ] XTCE export (using standard_mapping tables)
- [ ] SysML export
- [ ] PyG export
- [ ] Team data filtering

---

## Success Metrics

### Engagement
- 80%+ of extractions reviewed within 48 hours
- Average claim duration < 6 hours
- 5+ teams actively using platform

### Quality
- 90%+ approval rate on extractions
- <5% duplicate/incorrect entities
- Audit trail 100% complete

### Performance
- Dashboard loads < 2 seconds
- Agent queries respond < 5 seconds
- GNN analysis completes < 10 minutes per repo

### Scale
- Support 50 teams without performance degradation
- Handle 1000+ simultaneous queries
- Process 100+ concurrent ML jobs

---

## References

**Related Documentation:**
- `.deepagents/IMPLEMENTATION_ROADMAP.md` - Current development phase
- `.deepagents/standards/PROVES_CANONICAL_NAMING.md` - Entity type vocabulary
- `docs/architecture/KNOWLEDGE_GRAPH_SCHEMA.md` - ERV relationship model
- `docs/HUMAN_APPROVAL_WORKFLOW_GUIDE.md` - Current Notion-based workflow

**External Standards:**
- `.deepagents/standards/XTCE_VOCABULARY.md` - XTCE/YAMCS mapping
- `.deepagents/standards/SYSML_V2_VOCABULARY.md` - SysML v2 mapping
- `.deepagents/standards/PYTORCH_GEOMETRIC_VOCABULARY.md` - PyG mapping

---

**Status:** Requirements defined, ready for technical design and implementation planning
