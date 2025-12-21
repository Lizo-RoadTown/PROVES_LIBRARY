# MCP Server

MCP (Model Context Protocol) server for interrogating the PROVES Library.

## Purpose

Makes the knowledge library interrogatable rather than just searchable. Provides structured queries that AI tools can use to find relevant knowledge without dumping entire documentation into context windows.

## Architecture

```
mcp-server/
├── server.py          # FastAPI application
├── indexer.py         # Library indexing and search
├── mcp_protocol.py    # MCP protocol implementation
├── models.py          # Pydantic data models
├── config.py          # Configuration management
├── requirements.txt   # Python dependencies
└── README.md
```

## Endpoints

### `POST /search`
Search the library with semantic and keyword queries.

**Request:**
```json
{
  "query": "power system I2C conflicts",
  "domain": "software",  // optional: build, software, ops
  "tags": ["power", "i2c"],  // optional
  "limit": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "entry_id": "software-001",
      "title": "I2C Address Conflicts in Multi-Device Systems",
      "domain": "software",
      "excerpt": "When multiple I2C devices share...",
      "relevance_score": 0.95,
      "tags": ["power", "i2c", "hardware-integration"]
    }
  ],
  "total": 23
}
```

### `GET /entry/{entry_id}`
Fetch specific entry with full metadata and content.

**Response:**
```json
{
  "entry_id": "software-001",
  "title": "I2C Address Conflicts",
  "domain": "software",
  "metadata": {
    "type": "risk-pattern",
    "observed": "I2C conflicts in multi-sensor configurations",
    "sources": [...],
    "artifacts": [...],
    "tags": [...]
  },
  "content": "# Full markdown content...",
  "related_entries": ["software-015", "build-042"]
}
```

### `GET /list`
List entries by category.

**Query params:**
- `domain`: build | software | ops
- `type`: lesson | risk-pattern | config
- `tags`: comma-separated list

### `GET /artifacts/{entry_id}`
Get artifacts linked to an entry.

**Response:**
```json
{
  "entry_id": "software-001",
  "artifacts": [
    {
      "type": "component",
      "path": "github.com/proveskit/fprime-proves/...",
      "description": "I2C manager component"
    },
    {
      "type": "test",
      "path": "...",
      "description": "I2C conflict detection test"
    }
  ]
}
```

## Technology Stack

- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **SQLite** - Metadata indexing
- **sentence-transformers** - Semantic search embeddings
- **PyYAML** - Frontmatter parsing

## Installation

```bash
cd mcp-server
pip install -r requirements.txt
```

## Running

```bash
# Development
python server.py

# Production
uvicorn server:app --host 0.0.0.0 --port 8000
```

## Environment Variables

Create `.env` file:
```
LIBRARY_PATH=../library
INDEX_DB=index.db
EMBEDDING_MODEL=all-MiniLM-L6-v2
LOG_LEVEL=INFO
```

## Building the Index

```bash
python indexer.py --rebuild
```

This scans the `/library` directory, parses all markdown entries, extracts metadata, and builds:
1. SQLite database with metadata
2. Full-text search index
3. Embeddings for semantic search

## Testing

```bash
pytest tests/
```

## Next Steps

1. Implement `server.py` with FastAPI
2. Implement `indexer.py` for library parsing
3. Add MCP protocol wrapper
4. Create example queries
