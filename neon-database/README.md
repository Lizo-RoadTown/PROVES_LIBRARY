# Neon Database

This directory contains all database-related scripts, migrations, and documentation for the PROVES Library PostgreSQL database hosted on Neon.

## Structure

### scripts/

Database management scripts:

- **run_migration.py** - Run database migrations
- **verify_migration.py** - Verify migration status and check schema

### migrations/

SQL migration files in numbered order:

- **001_initial_schema.sql** - Initial database schema (candidates, extractions)
- **002_add_notion_sync.sql** - Add Notion sync columns
- **003_add_timestamps.sql** - Add timestamp tracking
- **004_create_ontology_tables.sql** - Ontology schema (ecosystems, methods, evidence types)
- **005_add_improvement_suggestions.sql** - Meta-learning suggestions table
- **006_add_suggestion_indexes.sql** - Performance indexes for suggestions
- **007_add_error_logging.sql** - Error logging columns and views

### docs/

Database documentation (to be added):

- Schema diagrams
- Migration guides
- Query examples

## Database Connection

The database connection is configured via environment variables in `.env`:

```bash
NEON_DATABASE_URL=postgresql://user:password@host/database
```

## Running Migrations

```bash
# Run all pending migrations
python neon-database/scripts/run_migration.py

# Verify current migration status
python neon-database/scripts/verify_migration.py
```

## Database Tables

### Core Tables

- **candidates** - Source candidates (GitHub repos, documentation)
- **staging_extractions** - Extracted evidence pending review
- **improvement_suggestions** - Meta-learning suggestions from pattern analysis

### Ontology Tables

- **ecosystems** - Aerospace ecosystems (F Prime, cFS, etc.)
- **methods** - Proving techniques and methods
- **evidence_types** - Types of evidence for validation

### Support Tables

- **migration_history** - Tracks applied migrations
- **all_errors** (view) - Aggregated error logs from all tables
