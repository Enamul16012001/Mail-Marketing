import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from database import get_database
from config import JWT_SECRET_KEY

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """JWT authentication service."""

    def __init__(self):
        self.db = get_database()

    def create_user(self, username: str, password: str) -> bool:
        """Create a new user."""
        hashed = pwd_context.hash(password)
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), username, hashed, datetime.now().isoformat())
            )
            conn.commit()
        return True

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Verify credentials and return a JWT token."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()

        if not row or not pwd_context.verify(password, row["password_hash"]):
            return None

        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        token = jwt.encode(
            {"sub": username, "exp": expire},
            JWT_SECRET_KEY,
            algorithm=ALGORITHM
        )
        return token

    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return username."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            return payload.get("sub")
        except JWTError:
            return None

    def has_users(self) -> bool:
        """Check if any users exist."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0] > 0


# Singleton
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
