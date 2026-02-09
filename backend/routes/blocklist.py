from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.blocklist_service import get_blocklist_service

router = APIRouter(prefix="/api/blocklist", tags=["blocklist"])


class BlocklistRule(BaseModel):
    type: str  # "exact", "domain", "regex"
    value: str
    label: str = ""


class BlocklistTest(BaseModel):
    email: str


@router.get("")
async def get_blocklist():
    """Get all blocklist rules."""
    service = get_blocklist_service()
    return {"rules": service.get_rules()}


@router.post("")
async def add_blocklist_rule(rule: BlocklistRule):
    """Add a new blocklist rule."""
    if rule.type not in ("exact", "domain", "regex"):
        raise HTTPException(status_code=400, detail="Type must be 'exact', 'domain', or 'regex'")
    if not rule.value.strip():
        raise HTTPException(status_code=400, detail="Value is required")

    service = get_blocklist_service()
    rules = service.add_rule(rule.type, rule.value.strip(), rule.label.strip())
    return {"rules": rules}


@router.delete("/{index}")
async def remove_blocklist_rule(index: int):
    """Remove a blocklist rule by index."""
    service = get_blocklist_service()
    rules = service.remove_rule(index)
    return {"rules": rules}


@router.post("/test")
async def test_blocklist(body: BlocklistTest):
    """Test if an email address would be blocked."""
    service = get_blocklist_service()
    return {"email": body.email, "blocked": service.should_block(body.email)}
