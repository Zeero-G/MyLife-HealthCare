"""
Emergency Router – token-based public access; authenticated profile CRUD for owners.
"""

import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List

from app.core.config import settings
from app.core.security import get_current_user
from app.core.database import supabase
from app.core.audit import write_audit
from app.schemas.records_schemas import EmergencyProfileResponse

router = APIRouter()


class EmergencyProfileUpsert(BaseModel):
    blood_type: Optional[str] = None
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    current_medications: Optional[List[str]] = None


class EmergencyPublicProfileResponse(BaseModel):
    blood_type: Optional[str]
    allergies: List[str]
    chronic_conditions: List[str]
    current_medications: List[str]


class EmergencyAccessTokenResponse(BaseModel):
    token: str
    expires_at: str
    access_path: str


def _active_token_query(token: str):
    return supabase.table("emergency_access_tokens") \
        .select("*") \
        .eq("token", token) \
        .is_("revoked_at", "null") \
        .execute()


# ── GET /emergency/access/{token} ────────────────────────────
@router.get("/access/{token}", response_model=EmergencyPublicProfileResponse)
async def get_emergency_by_token(token: str):
    """Public endpoint – emergency-safe fields only, via opaque access token."""
    token_row = _active_token_query(token)
    if not token_row.data:
        raise HTTPException(status_code=404, detail="Invalid or revoked emergency access token")

    row = token_row.data[0]
    expires_at = row.get("expires_at")
    if expires_at:
        exp = datetime.fromisoformat(expires_at.replace("Z", ""))
        if exp < datetime.utcnow():
            raise HTTPException(status_code=410, detail="Emergency access token expired")

    profile = supabase.table("emergency_profiles") \
        .select("blood_type, allergies, chronic_conditions, current_medications") \
        .eq("user_id", row["user_id"]) \
        .execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Emergency profile not found")

    write_audit(row["user_id"], "emergency_profile_accessed", "emergency_profiles", row["user_id"])

    return profile.data[0]


# ── POST /emergency/access-token ───────────────────────────────
@router.post("/access-token", response_model=EmergencyAccessTokenResponse, status_code=201)
async def create_emergency_access_token(current_user: dict = Depends(get_current_user)):
    """Issue an opaque emergency QR/access token for the authenticated owner."""
    profile = supabase.table("emergency_profiles") \
        .select("id") \
        .eq("user_id", current_user["sub"]) \
        .execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Create an emergency profile before generating an access token")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=settings.EMERGENCY_TOKEN_EXPIRE_DAYS)

    supabase.table("emergency_access_tokens").insert({
        "user_id": current_user["sub"],
        "token": token,
        "expires_at": expires_at.isoformat(),
    }).execute()

    return EmergencyAccessTokenResponse(
        token=token,
        expires_at=expires_at.isoformat(),
        access_path=f"/emergency/access/{token}",
    )


# ── DELETE /emergency/access-token/{token} ─────────────────────
@router.delete("/access-token/{token}", status_code=204)
async def revoke_emergency_access_token(token: str, current_user: dict = Depends(get_current_user)):
    """Revoke an emergency access token owned by the current user."""
    row = supabase.table("emergency_access_tokens") \
        .select("id") \
        .eq("token", token) \
        .eq("user_id", current_user["sub"]) \
        .is_("revoked_at", "null") \
        .execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Token not found")

    supabase.table("emergency_access_tokens") \
        .update({"revoked_at": datetime.utcnow().isoformat()}) \
        .eq("token", token) \
        .execute()


# ── POST /emergency/profile ───────────────────────────────────
@router.post("/profile", response_model=EmergencyProfileResponse, status_code=201)
async def create_emergency_profile(
    payload: EmergencyProfileUpsert,
    current_user: dict = Depends(get_current_user),
):
    """Create the current user's emergency profile."""
    existing = supabase.table("emergency_profiles") \
        .select("id") \
        .eq("user_id", current_user["sub"]) \
        .execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Emergency profile already exists. Use PUT to update.")

    new_profile = {
        "user_id": current_user["sub"],
        "blood_type": payload.blood_type,
        "allergies": payload.allergies or [],
        "chronic_conditions": payload.chronic_conditions or [],
        "emergency_contact_name": payload.emergency_contact_name,
        "emergency_contact_phone": payload.emergency_contact_phone,
        "current_medications": payload.current_medications or [],
    }
    result = supabase.table("emergency_profiles").insert(new_profile).execute()
    return result.data[0]


# ── PUT /emergency/profile ────────────────────────────────────
@router.put("/profile", response_model=EmergencyProfileResponse)
async def update_emergency_profile(
    payload: EmergencyProfileUpsert,
    current_user: dict = Depends(get_current_user),
):
    """Update the current user's emergency profile."""
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    result = supabase.table("emergency_profiles") \
        .update(update_data) \
        .eq("user_id", current_user["sub"]) \
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Emergency profile not found. Create one first.")
    return result.data[0]


# ── POST /emergency/profile/upsert ───────────────────────────
@router.post("/profile/upsert", response_model=EmergencyProfileResponse)
async def upsert_emergency_profile(
    payload: EmergencyProfileUpsert,
    current_user: dict = Depends(get_current_user),
):
    """Create or update emergency profile in one call (upsert)."""
    existing = supabase.table("emergency_profiles") \
        .select("id") \
        .eq("user_id", current_user["sub"]) \
        .execute()

    profile_data = {
        "blood_type": payload.blood_type,
        "allergies": payload.allergies or [],
        "chronic_conditions": payload.chronic_conditions or [],
        "emergency_contact_name": payload.emergency_contact_name,
        "emergency_contact_phone": payload.emergency_contact_phone,
        "current_medications": payload.current_medications or [],
    }

    if existing.data:
        result = supabase.table("emergency_profiles") \
            .update(profile_data) \
            .eq("user_id", current_user["sub"]) \
            .execute()
    else:
        result = supabase.table("emergency_profiles") \
            .insert({"user_id": current_user["sub"], **profile_data}) \
            .execute()

    return result.data[0]
