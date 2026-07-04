"""User model for authentication and profile."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator
import re


class UserCreate(BaseModel):
    """Request model for user registration."""
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    pan: str = Field(..., min_length=10, max_length=10)
    name: str = Field(..., min_length=1, max_length=255)
    dob: str = Field(default="", max_length=10)  # YYYY-MM-DD from date picker

    @field_validator("pan")
    @classmethod
    def pan_must_be_valid(cls, v: str) -> str:
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", v.upper()):
            raise ValueError("PAN must be 10 characters: 5 letters, 4 digits, 1 letter (e.g., CFFPM4503N)")
        return v.upper()

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v.lower().strip()


class UserLogin(BaseModel):
    """Request model for user login."""
    email: str
    password: str


class UserResponse(BaseModel):
    """Public user data returned to clients."""
    id: str
    email: str
    pan: str
    name: str
    created_at: Optional[str] = None


class UserInDB(BaseModel):
    """Internal user representation with hashed password."""
    id: str
    email: str
    pan: str
    name: str
    hashed_password: str
    created_at: str


class TokenResponse(BaseModel):
    """JWT token returned on successful login/register."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
