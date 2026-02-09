from fastapi import APIRouter

from database import get_database

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("")
async def get_analytics(days: int = 30):
    """Get analytics data for the given period.

    Args:
        days: Number of days to look back (default 30)
    """
    if days < 1:
        days = 1
    if days > 365:
        days = 365

    db = get_database()
    return db.get_analytics(days)
