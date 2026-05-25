"""
Emergency Router – Emergency profile CRUD and SOS alerts.
GET /profile/{userId} is publicly readable for emergency responders.
POST and PUT require authentication to create/update profiles.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.core.security import get_current_user
from app.core.database import supabase
from app.schemas.records_schemas import EmergencyProfileResponse

router = APIRouter()


class EmergencyProfileUpsert(BaseModel):
    blood_type: Optional[str] = None
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    current_medications: Optional[List[str]] = None


# ── GET /emergency/profile/{user_id} ─────────────────────────
@router.get("/profile/{user_id}", response_model=EmergencyProfileResponse)
async def get_emergency_profile(user_id: str):
    """
    Public endpoint – returns minimal emergency data for a patient.
    Used by emergency responders via QR code scan.
    """
    result = supabase.table("emergency_profiles") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Emergency profile not found")
    return result.data[0]


# ── POST /emergency/profile ───────────────────────────────────
@router.post("/profile", response_model=EmergencyProfileResponse, status_code=201)
async def create_emergency_profile(
    payload: EmergencyProfileUpsert,
    current_user: dict = Depends(get_current_user),
):
    """Create the current user's emergency profile."""
    # Check if one already exists
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
