"""Application routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.post("/sync")
async def trigger_sync():
    """Trigger a sync job."""
    return {"job_id": "sync-123", "status": "queued"}