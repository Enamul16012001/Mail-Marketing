from fastapi import APIRouter, HTTPException

from database import get_database

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search_emails(q: str = "", scope: str = "all"):
    """Search emails using full-text search.

    Args:
        q: Search query
        scope: "all", "pending", or "history"
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Search query is required")

    if scope not in ("all", "pending", "history"):
        raise HTTPException(status_code=400, detail="Scope must be 'all', 'pending', or 'history'")

    db = get_database()
    results = db.search_emails(q.strip(), scope)
    return {"query": q, "results": results, "count": len(results)}
