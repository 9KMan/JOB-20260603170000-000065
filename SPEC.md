# Job: Senior Python Developer — API-to-SQL Data Synchronization Platform
# Platform: Upwork | Budget: $15–35/hr | Duration: 1–3 months

## Business Problem Solved
Client needs a reliable data integration platform that synchronizes external REST APIs into a SQL database. Handles pagination, retries, rate limits, incremental updates, schema evolution, audit logging, and operational visibility — built as an extensible backend service.

## Stack
- Python 3.10+, FastAPI, SQLAlchemy, PostgreSQL
- Docker + docker-compose
- APScheduler (background jobs)
- structlog (structured logging)
- Alembic (migrations)
- pytest (tests)

## Architecture
1. **API Client Layer** — generic + per-source clients with pagination, retries, rate limiting
2. **Sync Engine** — incremental sync via last_sync tracking, upsert deduplication
3. **Schema Registry** — versioned record schemas for graceful API schema evolution
4. **Persistence Layer** — SQLAlchemy models, alembic migrations
5. **Job Scheduler** — APScheduler for periodic sync runs
6. **Observability** — /health, /metrics, structured audit logs

## Deliverables
1. Private GitHub repo with full working code
2. Docker build + docker-compose.yml
3. Alembic migrations
4. Structured logging + audit trail
5. README with architecture diagram and deployment docs
