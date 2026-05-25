"""
Auth Router + Doctors listing endpoint.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.auth_schemas import (
    RegisterRequest, LoginRequest, RefreshRequest,
    PasswordResetRequest, TokenResponse, UserResponse,
)
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token, get_current_user,
)
from app.core.database import supabase

router = APIRouter()


# ────────────────────────────────────────────
# POST /auth/register
# ────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest):
    # Check for duplicate email
    existing = supabase.table("users").select("id").eq("email", payload.email).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed = hash_password(payload.password)
    new_user = supabase.table("users").insert({
        "email": payload.email,
        "full_name": payload.full_name,
        "password_hash": hashed,
        "role": payload.role,
        "gender": payload.gender,
    }).execute()

    user_id = new_user.data[0]["id"]
    token_data = {"sub": user_id, "email": payload.email, "role": payload.role}

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


# ────────────────────────────────────────────
# POST /auth/login
# ────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    result = supabase.table("users").select("*").eq("email", payload.email).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = result.data[0]
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = {"sub": user["id"], "email": user["email"], "role": user["role"]}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


# ────────────────────────────────────────────
# POST /auth/refresh
# ────────────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest):
    decoded = decode_token(payload.refresh_token)
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    token_data = {"sub": decoded["sub"], "email": decoded["email"], "role": decoded["role"]}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


# ────────────────────────────────────────────
# POST /auth/logout
# ────────────────────────────────────────────
@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    # Stateless JWT – client discards the token.
    return {"message": "Logged out successfully"}


# ────────────────────────────────────────────
# GET /auth/me
# ────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)):
    result = supabase.table("users").select("*").eq("id", current_user["sub"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    u = result.data[0]
    return UserResponse(id=u["id"], email=u["email"], full_name=u["full_name"], role=u["role"], gender=u.get("gender"))


# ────────────────────────────────────────────
# GET /auth/doctors  – List all registered doctors (for patient to book)
# ────────────────────────────────────────────
@router.get("/doctors")
async def list_doctors(current_user: dict = Depends(get_current_user)):
    """Returns a list of all users with role='doctor' for appointment booking."""
    result = supabase.table("users") \
        .select("id, full_name, email, gender") \
        .eq("role", "doctor") \
        .execute()
    return result.data
