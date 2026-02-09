from fastapi import Request
from fastapi.responses import JSONResponse

from services.auth_service import get_auth_service

# Paths that don't require authentication
PUBLIC_PATHS = [
    "/api/auth/login",
    "/api/auth/setup",
    "/api/auth/check",
    "/api/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/",
]


async def auth_middleware(request: Request, call_next):
    """JWT authentication middleware."""
    path = request.url.path

    # Allow CORS preflight requests
    if request.method == "OPTIONS":
        return await call_next(request)

    # Allow public paths
    if any(path == p or path.startswith(p + "/") for p in PUBLIC_PATHS):
        return await call_next(request)

    # Only protect /api/ routes
    if not path.startswith("/api"):
        return await call_next(request)

    # Check Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Not authenticated"}
        )

    token = auth_header.split(" ", 1)[1]
    auth = get_auth_service()
    username = auth.verify_token(token)
    if not username:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or expired token"}
        )

    request.state.user = username
    return await call_next(request)
