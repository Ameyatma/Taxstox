"""Authentication API routes — register, login, profile."""

from fastapi import APIRouter, HTTPException, status, Depends

from src.models.user import UserCreate, UserLogin, UserResponse, TokenResponse
from src.auth.jwt import create_access_token, get_current_user
from src.db.database import create_user, authenticate_user, get_user_by_id

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
