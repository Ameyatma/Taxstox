"""Authentication API routes — register, login, profile, password management."""

from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, HTTPException, status, Depends

from src.models.user import UserCreate, UserLogin, UserResponse, TokenResponse
from src.auth.jwt import create_access_token, get_current_user
from src.db.database import create_user, authenticate_user, get_user_by_id, update_user_profile, change_user_password


class ProfileUpdate(BaseModel):
    name: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class GoogleAuthRequest(BaseModel):
    credential: str  # Google ID token

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate):
    """Create a new account and return a JWT token."""
    try:
        user = create_user(
            email=body.email,
            pan=body.pan,
            name=body.name,
            password=body.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    token = create_access_token({
        "sub": user["id"],
        "pan": user["pan"],
        "email": user["email"],
    })

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            pan=user["pan"],
            name=user["name"],
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    """Authenticate with email and password. Returns JWT token."""
    user = authenticate_user(body.email.strip().lower(), body.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token({
        "sub": user["id"],
        "pan": user.get("pan", ""),
        "email": user["email"],
    })

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            pan=user.get("pan", ""),
            name=user.get("name", ""),
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    user = get_user_by_id(current_user["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return UserResponse(
        id=user["id"],
        email=user["email"],
        pan=user["pan"],
        name=user["name"],
        created_at=user.get("created_at"),
    )


@router.put("/profile", response_model=UserResponse)
async def update_profile(body: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Update the current user's profile (name only)."""
    updated = update_user_profile(current_user["sub"], body.name)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserResponse(
        id=updated["id"],
        email=updated["email"],
        pan=updated["pan"],
        name=updated["name"],
        created_at=updated.get("created_at"),
    )


@router.post("/change-password")
async def change_password(body: PasswordChange, current_user: dict = Depends(get_current_user)):
    """Change the current user's password."""
    if len(body.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters.",
        )
    success = change_user_password(current_user["sub"], body.current_password, body.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    return {"message": "Password changed successfully."}


@router.post("/google", response_model=TokenResponse)
async def google_auth(body: GoogleAuthRequest):
    """Sign in / sign up with Google ID token.

    Verifies the token with Google, then creates or retrieves the user.
    """
    import json
    import urllib.request

    # Verify token with Google
    try:
        verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={body.credential}"
        resp = urllib.request.urlopen(verify_url)
        token_info = json.loads(resp.read())

        if "error" in token_info:
            raise HTTPException(status_code=400, detail="Invalid Google token.")

        email = token_info.get("email", "").lower()
        name = token_info.get("name", "Google User")
        google_id = token_info.get("sub", "")

        if not email:
            raise HTTPException(status_code=400, detail="Email not found in Google token.")

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to verify Google token.")

    # Find or create user
    from src.db.database import get_db, hash_password
    import uuid

    conn = get_db()
    try:
        row = conn.execute("SELECT id, email, pan, name FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            user = dict(row)
        else:
            user_id = str(uuid.uuid4())[:12]
            now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO users (id, email, pan, name, password_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, email, "", name, hash_password(google_id), now),
            )
            conn.commit()
            user = {"id": user_id, "email": email, "pan": "", "name": name}
    finally:
        conn.close()

    token = create_access_token({"sub": user["id"], "pan": user.get("pan", ""), "email": user["email"]})
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user["id"], email=user["email"], pan=user.get("pan", ""), name=user.get("name", "")),
    )


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    """Initiate password reset. Sends a reset token to the registered email.

    Note: Full email delivery requires SendGrid/Mailgun integration.
    For now, returns a reset token directly (dev mode).
    """
    import uuid
    from src.db.database import get_db

    email = body.email.strip().lower()
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()

    # Always return success to prevent email enumeration
    if not row:
        return {"message": "If the email is registered, a reset link has been sent."}

    reset_token = str(uuid.uuid4())[:12]
    # In production: store token + expiry in DB, email it via SendGrid
    # For dev: return token directly
    return {
        "message": "If the email is registered, a reset link has been sent.",
        "reset_token": reset_token,  # Dev mode only — remove in production
    }
