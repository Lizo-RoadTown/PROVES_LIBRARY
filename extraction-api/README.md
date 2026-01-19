# PROVES Extraction API

Docker-based API for triggering the PROVES extraction pipeline from the curation dashboard.

## Quick Start

### Local Development (without Docker)

```bash
cd extraction-api
pip install -r requirements.txt
uvicorn app:app --reload --port 8080
```

### With Docker

```bash
# From project root
docker-compose -f extraction-api/docker-compose.yml up -d

# Check logs
docker-compose -f extraction-api/docker-compose.yml logs -f

# Stop
docker-compose -f extraction-api/docker-compose.yml down
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/extract` | POST | Trigger extraction for URLs |
| `/extract/job` | POST | Process a crawl job from dashboard |
| `/tasks/{task_id}` | GET | Get extraction task status |
| `/jobs/{job_id}` | GET | Get crawl job status |

## Usage Examples

### Trigger extraction for URLs

```bash
curl -X POST http://localhost:8080/extract \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://docs.proveskit.space/en/latest/"]}'
```

### Check task status

```bash
curl http://localhost:8080/tasks/{task_id}
```

## Environment Variables

The API uses the same `.env` file as the main project:

- `DIRECT_URL` or `PROVES_DATABASE_URL` - Database connection
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `ANTHROPIC_API_KEY` - For Claude extractions

## Deployment

### Railway

1. Create new project in Railway
2. Connect to this repo (or copy files to new repo)
3. Set environment variables
4. Deploy

### Render

1. Create new Web Service
2. Connect to repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`

### Fly.io

```bash
fly launch
fly secrets set DATABASE_URL=...
fly deploy
```

## Dashboard Integration

The curation dashboard calls this API when you click "Run Extraction":

```typescript
// In useSources.ts
const triggerExtraction = async (sourceId: string) => {
  const response = await fetch(`${EXTRACTION_API_URL}/extract/job`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: sourceId })
  });
  return response.json();
};
```
