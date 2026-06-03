"""Configuration from environment variables."""
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://sync:***@localhost:5432/sync_db"
)
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.example.com")
API_KEY = os.environ.get("API_KEY", "")
SYNC_INTERVAL_SECONDS = int(os.environ.get("SYNC_INTERVAL_SECONDS", "300"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
RETRY_BACKOFF_SECONDS = int(os.environ.get("RETRY_BACKOFF_SECONDS", "5"))
RATE_LIMIT_PER_SECOND = int(os.environ.get("RATE_LIMIT_PER_SECOND", "10"))
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")