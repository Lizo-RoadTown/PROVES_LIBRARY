# Migration Log

Tracks all database migrations applied to the PROVES Library Supabase project.

**Project ID:** `guigtpwxlqwueylbbcpx`
**Database:** Supabase (migrated from Neon on 2026-01-15)

---

## Migration History

| Version | Name | Applied | Description |
|---------|------|---------|-------------|
| 000 | initial_base_schema | 2026-01-15 | Core tables: pipeline_runs, raw_snapshots, core_entities, entity_relationships |
| 001 | add_lineage_and_relationships | 2026-01-15 | Lineage tracking and relationship enhancements |
| 002 | create_urls_to_process | 2026-01-15 | URL processing queue |
| 003 | add_notion_integration | 2026-01-15 | Notion sync support |
| 004 | update_evidence_types | 2026-01-15 | Evidence type refinements |
| 005 | add_review_tracking | 2026-01-15 | Review status tracking |
| 006 | add_improvement_suggestions | 2026-01-15 | AI improvement suggestions |
| 007 | add_error_logging | 2026-01-15 | Error logging tables |
| 008 | add_dimensional_canonicalization | 2026-01-15 | Dimensional data normalization |
| 009 | add_verified_knowledge_layer | 2026-01-15 | Verified knowledge promotion |
| 010 | add_knowledge_epistemics_sidecar | 2026-01-15 | Epistemic metadata tracking |
| 011 | rollback_migration_008 | 2026-01-15 | Rollback of dimensional changes |
| 012 | enhance_human_approval_workflow | 2026-01-15 | Human approval workflow enhancements |
| 013 | add_promotion_tracking | 2026-01-15 | Knowledge promotion tracking |
| 014 | add_missing_entity_types | 2026-01-15 | Additional entity types |
| 015 | add_standard_mapping_enrichment | 2026-01-15 | Standard mapping enrichment |
| 016 | add_missing_neon_columns | 2026-01-15 | Columns needed for Neon compatibility |
| 017 | add_agent_oversight | 2026-01-16 | Agent oversight and monitoring |
| 018 | add_peer_reflection_views | 2026-01-16 | Peer reflection views |
| 019 | enhanced_human_review | 2026-01-17 | Enhanced human review workflow |
| 020 | user_attachments | 2026-01-17 | User attachments (student notebook) - pointers not copies |
| 021 | answer_evidence | 2026-01-17 | Answer evidence tracking for Ask surface |
| 20260115191105 | teams_and_batch_claims | 2026-01-15 | Teams and batch claim system |

---

## Skipped Files

These files don't follow the timestamp naming pattern and are skipped by Supabase CLI:
- `003b_add_missing_triggers.sql` - Supplemental triggers
- `005b_fix_review_decision_constraint.sql` - Constraint fix

---

## Key Tables by Feature

### Core Extraction Pipeline
- `pipeline_runs` - Pipeline execution tracking
- `raw_snapshots` - Raw extracted content
- `core_entities` - Normalized knowledge entities
- `entity_relationships` - Entity connections

### Human Review System
- `extractions` - Extracted content for review
- `review_sessions` - Review session tracking
- `extraction_suggestions` - AI-suggested improvements

### Team Management
- `teams` - University/lab accounts
- `team_members` - Engineers within teams
- `batch_claims` - Claim tracking for review batches
- `team_notifications` - In-app notifications

### Ask Surface (Student Notebook)
- `user_attachments` - User's attached repos/docs (pointers)
- `user_oauth_tokens` - OAuth tokens for GitHub/Drive
- `conversations` - Chat sessions
- `messages` - Chat messages
- `answer_evidence` - Sources used per answer
- `answer_metadata` - Confidence/freshness per answer

---

## Notes

### 2026-01-15: Neon to Supabase Migration
- Performed pg_dump from Neon
- Restored to Supabase
- All migrations 000-019 were included in dump
- Migration history was repaired via `npx supabase migration repair`

### 2026-01-17: Week 3-4 Dashboard Features
- Migration 020: User attachments for "student notebook" model
- Migration 021: Answer evidence tracking for evidence strip UI

---

## Commands

```bash
# List migration status
npx supabase migration list

# Push new migrations
npx supabase db push

# Mark migration as applied (if applied manually)
npx supabase migration repair --status applied <version>

# Create new migration
npx supabase migration new <name>
```
