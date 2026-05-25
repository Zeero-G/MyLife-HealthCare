from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"
    FAMILY_MEMBER = "family_member"

# ── Request schemas ──

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.PATIENT
    gender: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


# ── Response schemas ──

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    gender: Optional[str] = None
