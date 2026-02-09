from fastapi import APIRouter, HTTPException

from services.retry_service import get_retry_service

router = APIRouter(prefix="/api/retry", tags=["retry"])


@router.get("")
async def get_retry_queue():
    """Get all retry queue items."""
    service = get_retry_service()
    return {"items": service.get_queue()}


@router.post("/{retry_id}/retry")
async def manual_retry(retry_id: str):
    """Manually trigger a retry for a failed item."""
    service = get_retry_service()
    success = service.manual_retry(retry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Retry item not found")
    return {"success": True}


@router.delete("/{retry_id}")
async def cancel_retry(retry_id: str):
    """Cancel and remove a retry queue item."""
    service = get_retry_service()
    success = service.cancel_retry(retry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Retry item not found")
    return {"success": True}
