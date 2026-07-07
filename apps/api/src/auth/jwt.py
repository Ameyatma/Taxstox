"""JWT token generation and verification for TaxStox authentication.

M8: Added tenant_id and roles claims for multi-tenancy support.
"""

import contextvars
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ── Config ──────────────────────────────────────────────────────────

_SECRET = os.getenv("TAXSTOX_JWT_SECRET")
if not _SECRET:
    raise RuntimeError(
        "TAXSTOX_JWT_SECRET environment variable is required. "
        "Generate a strong secret: python -c 'import secrets; print(secrets.token_hex(32))'"
    )
SECRET_KEY: str = _SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

security = HTTPBearer(auto_error=False)

# M8: Context variable for tenant middleware to access JWT claims
_current_claims: contextvars.ContextVar[dict] = contextvars.ContextVar(
    "jwt_claims", default={}
)


# ── Token Functions ──────────────────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
    tenant_id: str | None = None,
    roles: list[str] | None = None,
) -> str:
    """Create a JWT access token.

    M8: Accepts optional tenant_id and roles claims for multi-tenancy.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    })
    if tenant_id:
        to_encode["tenant_id"] = tenant_id
    if roles:
        to_encode["roles"] = roles
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# ── Dependency ───────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """FastAPI dependency: extract and verify the current user.

    Returns payload: {sub, pan, email, tenant_id, roles}.
    M8: Stores claims in context var for tenant middleware access.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_token(token)
        _current_claims.set(payload)
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict | None:
    """Like get_current_user but returns None instead of 401."""
    if credentials is None:
        return None
    try:
        return decode_token(credentials.credentials)
    except JWTError:
        return None
