from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.auth_service import get_auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class SetupRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(body: LoginRequest):
    """Authenticate and get JWT token."""
    auth = get_auth_service()
    token = auth.authenticate(body.username, body.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": token, "username": body.username}


@router.post("/setup")
async def first_user_setup(body: SetupRequest):
    """Create the first admin user. Only works when no users exist."""
    auth = get_auth_service()
    if auth.has_users():
        raise HTTPException(status_code=400, detail="Setup already completed. Users already exist.")

    if len(body.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    auth.create_user(body.username, body.password)
    token = auth.authenticate(body.username, body.password)
    return {"token": token, "username": body.username}


@router.get("/check")
async def check_setup():
    """Check if initial setup is needed."""
    auth = get_auth_service()
    return {"has_users": auth.has_users()}
