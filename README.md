# API-to-SQL Data Synchronization Platform

Synchronizes external REST API data into PostgreSQL with incremental updates, deduplication, audit logging, and operational visibility.

## Business Problem Solved

Most API integrations hardcode field mappings and break when the source API changes schema. This platform uses a **versioned SchemaRegistry** — each source has a declared schema with typed fields. When the API evolves, you register a new schema version; the sync engine normalizes records through it, and old records keep their original schema version. Zero downtime, full audit trail.

## Architecture

```
External APIs → ApiClient → SyncEngine → PostgreSQL
                    ↓
              SchemaRegistry (versioned)
                    ↓
              SyncLog + AuditEntry (full audit)
```

**Key components:**

- `src/config.py` — All settings from environment variables (DATABASE_URL, API_BASE_URL, API_KEY, SYNC_INTERVAL_SECONDS, etc.)
- `src/models.py` — SQLAlchemy models: `SourceRecord` (upsert target), `SyncLog` (per-run audit), `AuditEntry` (structured event log)
- `src/api_client.py` — HTTP client with retry (exponential backoff), rate limiting, and cursor-based pagination
- `src/schema_registry.py` — Versioned schema registry with `validate()` and `transform()`; handles API schema evolution gracefully
- `src/sync_engine.py` — Incremental sync using PostgreSQL upsert (`ON CONFLICT DO UPDATE`) keyed on `source_name + external_id`
- `src/jobs.py` — APScheduler periodic job; configurable interval via `SYNC_INTERVAL_SECONDS`
- `src/routes.py` — FastAPI: `/health` (db connectivity), `/metrics` (record count + last sync time)

## Quick Start

```bash
git clone https://github.com/9KMan/JOB-20260603170000-000065.git
cd JOB-20260603170000-000065
docker-compose up -d
```

App starts on **port 8000**:

- `GET /health` — health check with database connectivity status
- `GET /metrics` — `{"total_records": N, "last_sync_at": "..."}`

## Configuration

All settings via environment variables (no hardcoded secrets):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://sync:***@localhost:5432/sync_db` | PostgreSQL connection |
| `API_BASE_URL` | `https://api.example.com` | External API base URL |
| `API_KEY` | `(empty)` | API authentication key |
| `SYNC_INTERVAL_SECONDS` | `300` | Interval between sync runs |
| `MAX_RETRIES` | `3` | HTTP retry attempts |
| `RETRY_BACKOFF_SECONDS` | `5` | Base backoff between retries |
| `RATE_LIMIT_PER_SECOND` | `10` | API rate limit (calls/sec) |

## Database Schema

- **`source_records`** — Deduplicated records per source. Upsert via `UNIQUE(source_name, external_id)`. `payload` stores the full raw record as JSON. `schema_version` tracks which API schema version was used.
- **`sync_logs`** — Per-run audit: `records_fetched`, `records_written`, `records_updated`, `status`, `error_message`, timestamps.
- **`audit_entries`** — Structured log entries (structlog → JSON) for all sync events; useful for debugging and compliance.

## Schema Evolution

When the source API changes:

1. Add new schema to `src/schema_registry.py` → `SCHEMAS`
2. Register it: `registry.register("source_name", new_schema)`
3. New records normalized with new schema; old records keep their original `schema_version`
4. No migration needed for historical records

## Adding a New API Source

1. Register the schema in `src/schema_registry.py`
2. Add source name to `sources` list in `src/jobs.py`
3. Run Alembic migration: `docker-compose exec app alembic revision --autogenerate -m "add source X"`
4. Restart the container

## Running Migrations

```bash
docker-compose exec app alembic upgrade head
docker-compose exec app alembic history  # check current revision
```

## Monitoring

```bash
curl http://localhost:8000/health   # {"status": "healthy", "database": "connected"}
curl http://localhost:8000/metrics  # {"total_records": N, "last_sync_at": "..."}
docker-compose logs -f app          # structured JSON logs
```

## Local Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker-compose up db -d
PYTHONPATH=. python -m src.main
```