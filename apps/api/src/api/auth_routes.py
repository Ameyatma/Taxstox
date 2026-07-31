"""Authentication API routes — register, login, profile, password management."""

from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, HTTPException, status, Depends

from src.models.user import UserCreate, UserLogin, UserResponse, TokenResponse
from src.auth.jwt import create_access_token, get_current_user
from src.db.database import (
    create_user, authenticate_user, get_user_by_id, get_user_by_email,
    create_user_google, user_exists, update_user_profile, change_user_password,
)
from src.engine.gateway.rate_limit_dependency import require_rate_limit


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
async def register(
    body: UserCreate,
    _: None = Depends(require_rate_limit("/auth/register", 5, 60)),
):
    """Create a new account and return a JWT token."""
    try:
        user = create_user(
            email=body.email,
            pan=body.pan,
            name=body.name,
            password=body.password,
            dob=body.dob or "",
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
            pan=user.get("pan") or "",
            name=user["name"],
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserLogin,
    _: None = Depends(require_rate_limit("/auth/login", 20, 60)),
):
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
        pan=user.get("pan") or "",
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

    The token is cryptographically verified against Google's JWKS endpoint
    using the official google-auth library. This validates:
    - RSA signature (proves Google issued the token)
    - iss (issuer = accounts.google.com)
    - aud (audience = our client ID)
    - exp (expiry)
    """
    import logging
    logger = logging.getLogger(__name__)

    if not body.credential:
        raise HTTPException(status_code=400, detail="Missing Google credential.")

    # Verify the ID token cryptographically
    from src.auth.google_verifier import verify_google_id_token, get_client_id

    try:
        token_info = verify_google_id_token(body.credential)
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Invalid Google credential. Please sign in again.")

    email = (token_info.get("email") or "").lower()
    name = token_info.get("name") or token_info.get("given_name") or "Google User"
    google_id = token_info.get("sub") or ""

    if not email:
        raise HTTPException(status_code=400, detail="Email not found in Google token.")

    # Find or create user
    user = create_user_google(email, name, google_id)

    logger.info(
        "Google OAuth login successful",
        extra={"user_id": user["id"], "email_masked": f"{email[0]}***@{email.split('@')[1]}" if '@' in email else email[:3] + "***"},
    )

    token = create_access_token({"sub": user["id"], "pan": user.get("pan", ""), "email": user["email"]})
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user["id"], email=user["email"], pan=user.get("pan", ""), name=user.get("name", "")),
    )


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    """Initiate password reset. Generates a secure token and stores it.

    Returns an identical response whether or not the email is registered
    to prevent email enumeration.

    The reset token is stored as a SHA-256 hash with 15-minute expiry.
    In production, the raw token is emailed via SendGrid/Mailgun.
    For dev, the token is logged (stub).
    """
    import logging
    logger = logging.getLogger(__name__)

    email = body.email.strip().lower()
    from src.db.database import get_user_by_email

    user = get_user_by_email(email)

    if user:
        # Invalidate any existing unused tokens for this user
        from src.infrastructure.password_reset_repo import PsycopgPasswordResetRepository

        repo = PsycopgPasswordResetRepository()
        repo.invalidate_user_tokens(user["id"])

        # Generate new token and store hashed version
        raw_token = repo.create_token(user["id"])

        # In production: email the token via SendGrid/Mailgun
        # For dev: log it
        logger.info(
            "Password reset token generated",
            extra={
                "user_id": user["id"],
                "email_masked": f"{email[0]}***@{email.split('@')[1]}" if '@' in email else "***",
                "token_expires_in_minutes": PsycopgPasswordResetRepository.TOKEN_TTL_MINUTES,
            },
        )

    # Always return the same message
    return {"message": "If the email is registered, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(body: dict):
    """Complete password reset using a valid reset token.

    Body: {"email": "...", "token": "...", "new_password": "..."}
    """
    email = (body.get("email") or "").strip().lower()
    raw_token = (body.get("token") or "").strip()
    new_password = (body.get("new_password") or "").strip()

    if not email or not raw_token or not new_password:
        raise HTTPException(status_code=400, detail="Email, token, and new password are required.")

    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    from src.db.database import get_user_by_email, update_user_password

    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    from src.infrastructure.password_reset_repo import PsycopgPasswordResetRepository
    repo = PsycopgPasswordResetRepository()

    if not repo.verify_and_consume(user["id"], raw_token):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    # Update password
    update_user_password(user["id"], new_password)

    import logging
    logger = logging.getLogger(__name__)
    logger.info("Password reset completed", extra={"user_id": user["id"]})

    # Log the user in by returning a JWT
    token = create_access_token({"sub": user["id"], "pan": user.get("pan", ""), "email": user["email"]})
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user["id"], email=user["email"], pan=user.get("pan", ""), name=user.get("name", "")),
    )
