"""Background job definitions."""

import logging

logger = logging.getLogger(__name__)


def run_sync_job(job_id: str):
    """Execute a sync job."""
    logger.info(f"Running sync job {job_id}")
    return {"job_id": job_id, "result": "success"}